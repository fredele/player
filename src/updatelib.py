#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gc
import argparse
import base64
import binascii
import logging
import math
import os
import queue
import re
import threading
import time
import configparser
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Optional
from scannotifier import ScanNotifier
import mutagen
from PIL import Image, ImageFile
from pymongo import MongoClient
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.mp3 import EasyMP3

from utils.exceldate import Excel_Now, Timestamp_Now, Timestamp_modified, convert
from utils.fileos import isfile_insensitive
from utils.string import ReprInt

ImageFile.LOAD_TRUNCATED_IMAGES = True

from updatesavedqueries import Update_Queries


def alphagroup(dictionary, field, groupnumber=3):
    """Create group_<field> from the first character of each field value."""
    if field not in dictionary or not isinstance(groupnumber, int) or groupnumber <= 0:
        return dictionary

    values = dictionary[field] if isinstance(dictionary[field], (list, tuple)) else [dictionary[field]]
    groups = set()

    for value in values:
        if value is None:
            continue
        if isinstance(value, int) and not isinstance(value, bool):
            groups.add("0 - 9")
            continue
        value = str(value).strip()
        if not value:
            continue

        first = value[0]
        if first.isdigit():
            groups.add("0 - 9")
            continue
        if not first.isalpha():
            continue

        position = ord(first.lower()) - ord("a")
        if not 0 <= position <= 25:
            continue
        start = (position // groupnumber) * groupnumber
        end = min(start + groupnumber - 1, 25)
        groups.add(f"{chr(97 + start).upper()} - {chr(97 + end).upper()}")

    dictionary["group_" + field] = sorted(groups, key=lambda item: (item == "0 - 9", item))
    return dictionary

def get_cover_names(image_names, image_extension):
    names = []
    extensions = []
    names.extend([x.lower() for x in image_names])
    names.extend([x.upper() for x in image_names])
    names.extend([x.capitalize() for x in image_names])
    names = list(set(names))
    extensions.extend([x.lower() for x in image_extension])
    extensions.extend([x.upper() for x in image_extension])
    extensions = list(set(extensions))
    return [name + '.' + ext for ext in extensions for name in names]


@dataclass
class ScanRequest:
    operation: str = "incremental"
    folder: str = "all"
    overwrite: bool = False
    rebuild: bool = False
    scanfolder: bool = False


class LibraryScannerService:
    """Autonomous music-library scan service.

    This service works without direct access to the Flask app state and can be
    started, stopped, and controlled through a queue and notifier callback.
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db=None,
        media_root: Optional[str] = None,
        notifier: Optional[Callable] = None,
        max_workers: int = 4,
        audio_extensions=None,
        image_names=None,
        image_extensions=None,
        album_sub_folder=None,
    ):
        if  mongo_uri is not None:
            self.mongo_client = MongoClient(mongo_uri)
            self.mongo_uri = mongo_uri
            self.db = self.mongo_client.player
        else:
            self.mongo_client = None
            self.db = db

        if self.db is None:
            raise ValueError("A MongoDB database or mongo_uri must be provided.")
        
        self.media_root = media_root or os.path.join(os.getenv("HOME", "."), ".Player", "mediafiles")
        self.notifier = notifier or self._default_notifier
        self.max_workers = max(max_workers, 1)
        self.audio_extensions = set((audio_extensions or ["mp3", "flac", "wav", "m4a", "aac", "ogg"]))
        self.image_names = image_names or ["cover", "folder", "art", "front"]
        self.image_extensions = image_extensions or ["jpg", "jpeg", "png", "bmp"]
        self.album_sub_folder = album_sub_folder or []

        self._stop_event = threading.Event()
        self._queue = queue.Queue()
        self._lock_scanning = threading.Lock()
        self._thread = threading.Thread(target=self._worker_loop, name="library-scanner", daemon=True)
        self._shared_state_lock = threading.Lock()

        self.current_scan = None
        self.current_folder = ""
        self.running = False
        self.imported_dirhashs = []
        self.imported_ids = []
        self.custom_txxx = []

    @staticmethod
    def _default_notifier(event, **payload):
        logging.info("Library scanner event %s payload=%s", event, payload)

    def emit(self, event, **payload):
        self.notifier(event, **payload)

    def start(self):
        if self._thread.is_alive():
            return self
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, name="library-scanner", daemon=True)
        self._thread.start()
        return self

    def schedule_scan(self, operation="incremental", folder="all", overwrite=False, rebuild=False, scanfolder=False):
        """Schedule a scan request.

        Returns the ScanRequest on success, or False if a scan is already running.
        """
        self._stop_event.clear()
        request = ScanRequest(
            operation=operation,
            folder=folder,
            overwrite=overwrite,
            rebuild=rebuild,
            scanfolder=scanfolder,
        )

        with self._lock_scanning:
            # If a scan is already running, refuse to schedule a second one.
            if self.is_running:
                return False

            # otherwise enqueue and ensure worker thread is started
            self._queue.put(request)
            if not self._thread.is_alive():
                self.start()

        return request

    def request_stop(self):
        self._stop_event.set()
        self._queue.put(None)

    @property
    def is_running(self):
        return self._thread.is_alive()

    def join(self, timeout=None):
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _worker_loop(self):
        self.running = True
        try:
            while True:
                if self._stop_event.is_set():
                    self.running = False
                    return

                try:
                    item = self._queue.get(timeout=0.25)
                except queue.Empty:
                    continue

                if item is None:
                    self._queue.task_done()
                    break

                self.current_scan = item
                try:
                    self._run_scan(item)
                except Exception:
                    logging.exception("Library scan failed")
                    self.emit("library_scan_error", message="Scan failed")
                finally:
                    self.current_scan = None
                    self.current_folder = ""
                    self._queue.task_done()
                    # If there are no pending requests, stop the worker thread
                    try:
                        if self._queue.empty():
                            return
                    except Exception:
                        pass
        finally:
            self.running = False

    def _run_scan(self, request: ScanRequest):
      
        self.imported_dirhashs.clear()
        self.imported_ids.clear()
        if request.rebuild:
            self.db.mediafiles.drop()

        if request.folder == "all":
            search_root = os.path.join(self.media_root, "Music")
        else:
            search_root = os.path.join(self.media_root, request.folder)
      
        self.emit("library_scan_started", operation=request.operation, folder=request.folder)
        self.plugins_action('before_server_update')
        
        if not os.path.isdir(search_root):
            self.emit("library_scan_finished", operation=request.operation, folder=request.folder, scanned=0)
            return

        files_to_scan = []
        for root, _, filenames in os.walk(search_root, followlinks=True):
            if self._stop_event.is_set():
                self.emit("library_scan_stopped", operation=request.operation, folder=request.folder)
                return
            self.current_folder = root
            for filename in sorted(filenames):
                _, ext = os.path.splitext(filename)
                if ext.lower().lstrip(".") in self.audio_extensions:
                    files_to_scan.append((root, filename))
        total_files = len(files_to_scan)
        completed_files = 0
        last_progress = 0
        
        # Aucun fichier à importer
        if total_files == 0:
            self.notifier(
                "library_scan_progress",
                progress=100,
                total=0,
                completed=0,
                message="100/100"
            )
        else:
            self.notifier(
                "library_scan_progress",
                progress=0,
                total=total_files,
                completed=0,
                message="0/100"
            )
      
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for root, filename in files_to_scan:
                    if self._stop_event.is_set():
                        break
                    futures.append(executor.submit(self._import_audio_file, root, filename, request.overwrite))
                for future in as_completed(futures):
                    if self._stop_event.is_set():
                        break
                    try:
                        future.result()
                    except Exception:
                        logging.exception("Error while importing music file")
                        
                        
                    completed_files += 1
                    progress = (
                        completed_files * 100
                    ) // total_files

                    # Un seul événement par pourcentage
                    if progress > last_progress:
                        last_progress = progress

                        self.notifier(
                            "library_scan_progress",
                            progress=progress,
                            total=total_files,
                            completed=completed_files,
                            message=f"{progress}/100"
                        )
        
        self._cleanup_missing_files()
        self.plugins_action('after_library_update', "all")
        self.emit("library_scan_finished", operation=request.operation, folder=request.folder, scanned=len(files_to_scan))
    
        # --- Ajout anti-fuite ---
        self.imported_dirhashs.clear()
        self.imported_ids.clear()
        self.current_scan = None
        self.current_folder = ""
        
    def _cleanup_missing_files(self):
        try:
            cursor = self.db.mediafiles.find({"dirname": {"$exists": True}})
            for document in cursor:
                if self._stop_event.is_set():
                    break
                dirname = document.get("dirname", "")
                filename = document.get("filename", "")
                extension = document.get("extension", "")
                candidate = os.path.join(self.media_root, dirname, f"{filename}.{extension}")
                if not os.path.exists(candidate):
                    self.db.mediafiles.delete_one({"_id": document.get("_id")})
        except Exception:
            logging.exception("Cleanup of missing files failed")

    def _register_txxx_key(self, tag, shared_state_lock=None):
        if tag in self.custom_txxx:
            return

        if shared_state_lock is not None:
            with shared_state_lock:
                if tag not in self.custom_txxx:
                    self.custom_txxx.append(tag)
                    EasyID3.RegisterTXXXKey(tag, tag)
            return

        if tag not in self.custom_txxx:
            self.custom_txxx.append(tag)
            EasyID3.RegisterTXXXKey(tag, tag)

    def _thumbnailer(self, img_path, dirhash, overwrite):
        try:
            if not overwrite and self.db.thumbnails.find_one({"dirhash": int(dirhash)}) is not None:
                return

            with Image.open(os.path.realpath(img_path)) as image:
                image = image.convert("RGB")
                image.thumbnail((256, 256), getattr(Image, "Resampling", Image).LANCZOS)
                buffer = BytesIO()
                image.save(buffer, format="JPEG")

            thumb = base64.b64encode(buffer.getvalue()).decode("utf-8")
            relative_path = os.path.relpath(img_path, self.media_root)
            self.db.thumbnails.update_one(
                {"dirhash": int(dirhash)},
                {"$set": {"last_modified_epoch": round(time.time()), "dirhash": int(dirhash), "cover_256": thumb, "path": relative_path}},
                upsert=True,
            )
            self.emit("cover_changed", dirhash=str(dirhash))
        except Exception:
            logging.exception("Thumbnail generation failed for %s", img_path)

    def _import_audio_file(self, root, file_name, overwrite):
        if self._stop_event.is_set():
            return

        filename, file_extension = os.path.splitext(file_name)
        ext = file_extension.lower().lstrip(".")
        if ext not in self.audio_extensions:
            return

        full_path = os.path.join(root, file_name)
        relative_dir = os.path.relpath(os.path.dirname(full_path), self.media_root)
        relative_dir = relative_dir.replace(os.sep, "/")
        if relative_dir == ".":
            relative_dir = ""
        if relative_dir.startswith(".") or "/." in relative_dir:
            return

        query = {"dirname": relative_dir, "filename": filename, "extension": ext}
        if self.db.mediafiles.count_documents(query) > 0 and not overwrite:
            return

        self.emit("library_file_importing", path=full_path, folder=relative_dir)

        c_folder = os.path.basename(os.path.normpath(root))
        subfolder = any(c_folder.startswith(prefix) for prefix in self.album_sub_folder)
        if subfolder:
            dirhash = binascii.crc32(os.path.abspath(os.path.join(relative_dir, os.pardir)).encode("UTF-8")) & 0xFFFFFFFF
        else:
            dirhash = binascii.crc32(relative_dir.encode("UTF-8")) & 0xFFFFFFFF

        with self._shared_state_lock:
            if dirhash not in self.imported_dirhashs:
                self.imported_dirhashs.append(dirhash)

        media_file = mutagen.File(full_path)
        if media_file is None or getattr(media_file, "info", None) is None:
            logging.warning("Skipping unreadable media file: %s", full_path)
            return

        info = {
            "mediatype": "audio",
            "mediasubtype": "music",
            "last_modified_timestamp": Timestamp_modified(full_path),
            "date_imported": Excel_Now(),
            "date_imported_timestamp": Timestamp_Now(),
            "dirname": relative_dir,
            "dirhash": int(dirhash),
            "filename": filename,
            "cover": False,
            "extension": ext,
            "size": os.stat(full_path).st_size,
        }

        stream_info = media_file.info
        for key in ["channels", "sample_rate", "length", "bitrate"]:
            if hasattr(stream_info, key):
                info[key] = getattr(stream_info, key)

        info["cover"] = False
        for image_name in get_cover_names(self.image_names, self.image_extensions):
            candidate = os.path.join(root, image_name)
            if subfolder:
                candidate = os.path.abspath(os.path.join(root, os.pardir, image_name))
            if isfile_insensitive(candidate):
                info["cover"] = True
                self._thumbnailer(candidate, dirhash, overwrite)
                break

        if not info["cover"]:
            self.db.thumbnails.update_one({"dirhash": int(dirhash)}, {"$set": {"dirhash": int(dirhash)}}, upsert=True)

        tags = {}
        try:
            if ext == "mp3":
                file_tags = mutagen.File(full_path)
                if file_tags is not None and file_tags.tags is not None:
                    txxx_tags = [tag.desc.lower() for tag in file_tags.tags.getall("TXXX")]
                    for tag in txxx_tags:
                        self._register_txxx_key(tag, self._shared_state_lock)
                tags = EasyMP3(full_path)
            elif ext == "m4a":
                tags = EasyMP4(full_path)
            else:
                tags = mutagen.File(full_path) or {}
        except Exception:
            logging.exception("Error reading tags for %s", full_path)
            return

        materialized = {**convert(tags), **convert(info)}

        if "tracknumber" in materialized and materialized["tracknumber"]:
            try:
                materialized["tracknumber"] = int(re.split(r"[\s,.|/|\|-|_]+", str(materialized["tracknumber"][0]))[0])
            except Exception:
                materialized["tracknumber"] = 0

        if "totaltracks" in materialized and materialized["totaltracks"]:
            try:
                materialized["totaltracks"] = int(re.split(r"[\s,.|/|\|-|_]+", str(materialized["totaltracks"][0]))[0])
            except Exception:
                materialized["totaltracks"] = 0

        if "discnumber" in materialized and materialized["discnumber"]:
            try:
                disc_elems = re.split(r"[\s,.|/|\|-|_]+", str(materialized["discnumber"][0]))
                materialized["discnumber"] = int(disc_elems[0]) if disc_elems else 0
            except Exception:
                materialized["discnumber"] = 0

        if "date" in materialized and materialized["date"]:
            match = re.findall(r"(?<!\d)\d{4}(?!\d)", str(materialized["date"]))
            if match:
                materialized["date"] = int(match[0])
            else:
                materialized.pop("date", None)

        def normalize_to_int(tree):
            for key, value in list(tree.items()):
                if isinstance(value, dict):
                    normalize_to_int(value)
                elif isinstance(value, list):
                    tree[key] = [ReprInt(item) for item in value]
                elif isinstance(value, str):
                    tree[key] = ReprInt(value)
            return tree

        materialized = normalize_to_int(materialized)

        # Store the decade for valid years (e.g. 1987 -> 1980).
        date_value = materialized.get("date")
        try:
            if isinstance(date_value, (list, tuple)):
                date_value = date_value[0] if date_value else None
            date_int = int(date_value)
            if date_int > 1900:
                materialized["date_decade"] = int(str(date_int)[:-1] + "0")
        except (TypeError, ValueError, IndexError):
            pass

        raw_artists = materialized.get("artist")

        for tag in ["albumartist", "artist", "album", "title"]:
            if tag in materialized and isinstance(materialized[tag], list) and materialized[tag]:
                # Keep the existing behavior for the main display fields.
                materialized[tag] = materialized[tag][0]

        def first_alphabetic_upper(value):
            """Return the first alphabetic character of a metadata value."""
            if value is None:
                return None

            # Mutagen may expose a tag as a list, even when it contains one value.
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None

            if value is None:
                return None

            value = str(value).strip()
            if not value:
                return None

            first = value[0]
            return first.upper() if first.isalpha() else None

        album_alphabet = first_alphabetic_upper(materialized.get("album"))
        if album_alphabet is not None:
            materialized["album_alphabet"] = album_alphabet

        # Store one initial for each artist name when the tag contains several artists.
        artists = raw_artists
        if not isinstance(artists, (list, tuple)):
            artists = [artists]

        artist_alphabets = []
        for artist in artists:
            initial = first_alphabetic_upper(artist)
            if initial is not None and initial not in artist_alphabets:
                artist_alphabets.append(initial)

        if artist_alphabets:
            materialized["artist_alphabet"] = artist_alphabets

        def invert(value):
            """Return 'First Last' as 'Last, First' for a name value."""
            if isinstance(value, (list, tuple)):
                value = value[0] if value else ""
            if value is None:
                return ""
            value = str(value).strip()
            if " " in value:
                parts = value.split()
                return parts[-1] + ", " + " ".join(parts[:-1])
            return value

        for field in ("composer", "conductor"):
            if field in materialized:
                materialized[field + "_invert"] = invert(materialized[field])

        # Create navigation groups for artist and album using groups of 3 letters.
        alphagroup(materialized, "artist", groupnumber=3)
        alphagroup(materialized, "album", groupnumber=3)

        self.db.mediafiles.update_one(query, {"$set": materialized}, upsert=True)

        if self.db.mediadirs.find_one({"dirhash": int(dirhash)}) is None:
            dir_document = {key: value for key, value in materialized.items() if key not in ["filename", "extension", "size", "cover"]}
            self.db.mediadirs.update_one({"dirhash": int(dirhash)}, {"$set": dir_document}, upsert=True)

    def close(self):
        self.request_stop()
        if self.mongo_client is not None:
            self.mongo_client.close()

    def plugins_action(self,function_name, param='none',param2='none'):
        plugins_dir = os.path.join(os.getenv("HOME"), '.Player', 'plugins')
        plugin_files =sorted([f for f in os.listdir(plugins_dir) if os.path.isfile(os.path.join(plugins_dir, f)) and f.rsplit('.', 1)[1] == 'py'])
        for _filename_ in plugin_files:
            if os.path.isfile(os.path.join(os.path.join(os.getenv("HOME"), '.Player', 'plugins'), _filename_)):
                try:
                    if param != 'none' and param2!= "none":
                        p = _filename_.split('.')[0] + '.'+ function_name +'(app,'+'"' +str(param)+ '"' + ','+str(param2) + ')'
                    if param != 'none'and param2 == "none":
                        p = _filename_.split('.')[0] + '.'+ function_name +'(app,'+ str(param) + ')'
                    if param == 'all' and param2 == "none":
                        p = _filename_.split('.')[0] + '.'+ function_name +'(app,"all")'
                    if param == 'none' and param2 == "none":
                        p = _filename_.split('.')[0] + '.' + function_name + '(app)'
                    exec(p)

                except Exception as e:
                    pass
            
            
def Update_Music_Folders(dirnames, mongo_uri: Optional[str] = None, db=None, media_root: Optional[str] = None,
                         notifier: Optional[Callable] = None, max_workers: int = 4, overwrite: bool = False,
                         rebuild: bool = False):
    """Importe séquentiellement une liste de dossiers dans la base.

    - `dirnames` : liste de chemins relatifs à `media_root` (ex: 'Music/Disque 1/...')
    - Les événements sont émis via `notifier` si fourni (même format que `LibraryScannerService`).

    Cette fonction exécute les scans de façon synchrone (bloquante) et retourne
    après le traitement de tous les dossiers fournis.
    """
    scanner = LibraryScannerService(mongo_uri=mongo_uri, db=db, media_root=media_root,
                                    notifier=notifier, max_workers=max_workers)

    for folder in dirnames:
        try:
            req = ScanRequest(operation="incremental", folder=folder, overwrite=overwrite, rebuild=rebuild, scanfolder=False)
            # Appel synchrone du scan pour ce dossier
            scanner._run_scan(req)
        except Exception:
            logging.exception("Update_Music_Folders: failed importing %s", folder)

    # No refresh queries here ...
    try:
        scanner.close()
    except Exception:
        pass



def build_parser():
    parser = argparse.ArgumentParser(description="Standalone library scanner service")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="MongoDB URI")
    parser.add_argument("--media-root", default=os.path.join(os.getenv("HOME", "."), ".Player", "mediafiles"), help="Root folder of the media library")
    parser.add_argument("--max-workers", type=int, default=4, help="Max worker threads")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()

    notifier = ScanNotifier(os.path.join(os.getenv("HOME"), '.Player', 'run', 'scan.sock'))

    p = os.path.join(os.getenv("HOME"), ".Player", "config", "config.ini")
    mongo_uri = args.mongo_uri

    if not mongo_uri and os.path.isfile(p):
        config = configparser.ConfigParser()
        config.read(p)

        mongo = config["MongoDB"]

        address = mongo.get("address", "localhost")
        port = mongo.getint("port", 27017)
        user = mongo.get("user", "")
        password = mongo.get("password", "")

        if user:
            mongo_uri = (
                f"mongodb://{quote_plus(user)}:{quote_plus(password)}"
                f"@{address}:{port}"
            )
        else:
            mongo_uri = f"mongodb://{address}:{port}"
        
    
    service = LibraryScannerService(
        mongo_uri=mongo_uri,
        media_root=args.media_root,
        notifier=notifier,
        max_workers=args.max_workers,
    )

    service.schedule_scan(operation="incremental", folder="all")

    try:
        while service.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        service.request_stop()
        service.join(timeout=3)
