#!/usr/bin/python3
#-*- coding: utf-8 -*-

import louie
from louie import dispatcher
import logging
import time
import mutagen

import os
import re
import binascii
from pymongo import MongoClient,ASCENDING
from utils.fileos import isfile_insensitive
from shutil import copyfile
from threading import Thread
from threading import Lock
from utils.string import to_unicode
from utils.exceldate import convert,DateToExcel,Excel_Now,Timestamp_modified,Timestamp_Now
from PIL import Image , ImageFile
import PIL.ExifTags
ImageFile.LOAD_TRUNCATED_IMAGES = True
import logging
import json
import datetime
from mutagen.mp3 import EasyMP3
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

from main import send_message
import configparser
from io import BytesIO
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.string import to_int ,naturalsort,IfExistsDic ,BoolStr,StrBool,BoolInt,RepresentsInt ,is_number, ReprInt
from updatesavedqueries import Update_Queries


def append_unique_shared(values, value, lock=None):
    if lock is not None:
        with lock:
            if value not in values:
                values.append(value)
        return
    if value not in values:
        values.append(value)


def register_txxx_key(owner, tag, shared_state_lock=None):
    if tag in owner.txxx:
        return

    if shared_state_lock is not None:
        with shared_state_lock:
            if tag not in owner.txxx:
                owner.txxx.append(tag)
                EasyID3.RegisterTXXXKey(tag, tag)
        return

    if tag not in owner.txxx:
        owner.txxx.append(tag)
        EasyID3.RegisterTXXXKey(tag, tag)


def get_cover_names(image_names,imageextension):
    n = []
    e = []
    n.extend([x.lower() for x in image_names])
    n.extend([x.upper() for x in image_names])
    n.extend([x.capitalize() for x in image_names])
    n = list(set(n))
    e.extend([x.lower() for x in imageextension])
    e.extend([x.upper() for x in imageextension])
    e = list(set(e))
    return  [  name+'.' + ext for ext in e for name in n]

class Update_Folders(Thread):

    def __init__(self, mongo_addr, folders, owner=None):
        Thread.__init__(self)
        self.folders = folders
        self.owner = owner
        self.mongo_addr = mongo_addr

    def run(self):
        try:
            self.owner.send_message("Update Library")
            def worker():
                for folder in self.folders:
                    thr = Update_Lib(self.mongo_addr, folder=folder, owner=self.owner)
                    thr.start()
                    thr.join()  # Attend que le thread Update_Lib se termine avant de passer au suivant
                    time.sleep(.1)
            t = Thread(target=worker)
            t.start()
            t.join()  # Attend que tous les dossiers soient traités

            if (self.owner.update_queries != None):
                self.owner.update_queries.do_stop()
            self.owner.update_queries = Update_Queries(self.owner, self.owner.requestfind)
            self.owner.update_queries.start()

            if self.owner is not None:
                time.sleep(2)
                self.owner.plugins_action('after_library_update', self.folders)
                self.owner.send_message("Library Updated")
                louie.send("lib_updated", self)

        except Exception:
            logging.exception("Update_Folders failed")
            if self.owner is not None:
                self.owner.send_message("Library Updated")
                louie.send("lib_updated", self)
                self.owner.plugins_action('after_library_update', self.folders)
            if (self.owner.update_queries != None):
                self.owner.update_queries.do_stop()
            self.owner.update_queries = Update_Queries(self.owner, self.owner.requestfind)
            self.owner.update_queries.start()

class Update_Lib(Thread):
    home = os.getenv("HOME")
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    if os.path.isfile(os.path.join(home, '.Player', 'config','config.ini')):
        _config =  configparser.ConfigParser()
        _config.read(os.path.join(home, '.Player', 'config','config.ini'))
        audioextension = _config['Tags']['audioextension'].split(',')
        videoextension = _config['Tags']['videoextension'].split(',')
        imageextension = _config['Tags']['imageextension'].split(',')
        image_names = _config['Tags']['image_names'].split(',')

    def __init__(self,mongoaddr, callback=None, owner=None, overwrite=False, rebuild = False, folder='all',scanfolder = False):
        Thread.__init__(self)
        self.scanfolder = scanfolder
        client = MongoClient(mongoaddr)
        self.db = client.player
        self.callback = callback
        self.folder = folder
        self.owner = owner
        if self.owner is not None:
            self.owner.imported_dirhashs = []
        self.overwrite = overwrite
        self.rebuild = rebuild
        self.stop = False
        self._shared_state_lock = Lock()
        if owner is not None:
            os.chdir(owner.root_path)

    def do_stop(self):
        self.stop = True

    def run(self):
        try:

            if  self.owner is not None :
                self.owner.send_message("Update Library")
                self.owner.scan_lock = True
            if self.owner is not None:
                self.owner.plugins_action('before_server_update')
            def extension(f):
                try :
                    return f.rsplit('.', 1)[1]
                except (AttributeError, IndexError):
                    return ''

            if  self.owner is not None :
                if self.owner.updating == True:
                    return
                self.owner.updating = True
                if self.owner is not None and self.folder == 'all':
                    self.owner.send_message("Update Library")

            #Remove ALL the content
            if self.rebuild == True:
                self.db.mediafiles.drop()

            if self.folder == 'all':
                searchfolder = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles','Music')
            else:
                searchfolder = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles',self.folder)
            try:
                max_threads = int(self.owner.scan_threads)
            except (AttributeError, TypeError, ValueError):
                max_threads = 5
            if self.scanfolder == True:
                try:
                    dirnames = self.db.mediafiles.find().distinct('dirname')
                    dirnames = [os.path.join(os.getenv("HOME"), '.Player', 'mediafiles',f) for f in dirnames]
                except Exception:
                    dirnames = []

            for root, dirs, files in os.walk(searchfolder,followlinks=True):
                i=0
                if self.owner is not None:
                    self.owner.current_scan_folder = root

                if self.scanfolder == True:
                    # Check only new folders
                    if root not in dirnames:
                        with ThreadPoolExecutor(max_workers=max_threads) as executor:
                            futures = []
                            for audio_file in files:
                                futures.append(
                                    executor.submit(
                                        import_audio_file,
                                        self.owner,
                                        self.db,
                                        root,
                                        audio_file,
                                        self.overwrite,
                                        self._shared_state_lock
                                    )
                                )
                            for future in as_completed(futures):
                                try:
                                    future.result()
                                except Exception as e:
                                    logging.debug("Error importing file in %s: %s", root, e)
                else:
                    # Check all files
                    with ThreadPoolExecutor(max_workers=max_threads) as executor:
                        futures = []
                        for audio_file in files:
                            futures.append(
                                executor.submit(
                                    import_audio_file,
                                    self.owner,
                                    self.db,
                                    root,
                                    audio_file,
                                    self.overwrite,
                                    self._shared_state_lock
                                )
                            )
                        for future in as_completed(futures):
                            try:
                                future.result()
                            except Exception as e:
                                logging.debug("Error importing file in %s: %s", root, e)
        except Exception:
            logging.exception("Error on Import")
            if self.owner is not None:
                self.owner.send_message("Error on Import")
        if self.callback is not None:
            self.callback()
        try:
            if self.scanfolder == True:
                if self.folder == 'all':
                    dirnames = self.db.mediafiles.find().distinct('dirname') #Musique/Musiques
                    dirnamesfull = [os.path.join(os.getenv("HOME"), '.Player', 'mediafiles',f) for f in dirnames]
                    for dir in dirnamesfull:
                        if os.path.exists(dir) == False:
                            f = dir.replace(os.path.join(os.getenv("HOME"), '.Player', 'mediafiles'),'')[1:]
                            cursor = self.db.mediafiles.delete_many({'dirname': f})
        except Exception:
            if self.owner is not None:
                self.owner.send_message("Error on Import")
            logging.exception("Error while cleaning missing directories")

        else:
            # Check missing files from DB
            try:
                if self.folder == 'all':
                    # Do not check on re-import
                    cursor = self.db.mediafiles.find({"dirname" : {"$exists": True}})
                    for i in cursor:
                        if self.stop is False:
                            try:
                                s = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
                                s = os.path.join(s, i["dirname"],i["filename"] + '.' + i["extension"])
                                s = os.path.realpath(s)
                                if not os.path.exists( s):
                                    self.db.mediafiles.delete_one({'_id': i['_id']})
                                if i["dirname"].split("/")[-1][0] == "." :
                                    self.db.mediafiles.delete_one({'_id': i['_id']})
                            except (KeyError, TypeError, OSError):
                                pass
            except Exception:
                logging.exception("Error during DB cleanup")
            cursor = self.db.mediafiles.delete_many({'dirname': {'$exists': False}})
        # Wait end of DB writings ...
        time.sleep(2)
        try:
            if self.folder == 'all' and self.owner is not None:
                self.owner.plugins_action('after_library_update',"all")
                self.owner.imported_dirhashs = []
            if self.callback is not None:
                self.callback()

            if  self.owner is not None :
                self.owner.updating = False
                self.owner.scan_lock = False

            if self.folder == 'all' and self.owner is not None:
                self.owner.send_message("Library Updated")
                louie.send( "lib_updated", self)
            if  self.owner is not None:
                if (self.owner.update_queries != None):
                    self.owner.update_queries.do_stop()
                self.owner.update_queries =  Update_Queries(self.owner, self.owner.requestfind)
                self.owner.update_queries.start()
        except Exception:
            logging.exception("Final library update cleanup failed")
            if self.owner is not None:
                self.owner.scan_lock = False
                self.owner.updating = False
            if self.folder == 'all' and self.owner is not None:
                self.owner.send_message("Library Updated")
                louie.send("lib_updated", self)
                if (self.owner.update_queries != None):
                    self.owner.update_queries.do_stop()
                self.owner.update_queries = Update_Queries(self.owner, self.owner.requestfind)
                self.owner.update_queries.start()


def thumbnailer(owner, img_path,dirhash,overwrite):
    try: # Exit of already imported
        if  overwrite == True or owner.db.thumbnails.find_one({'dirhash': int(dirhash)})==None:
            img_path_real = os.path.realpath(img_path)
            im = Image.open(img_path_real)
            size = 256, 256
            im.thumbnail(size, Image.ANTIALIAS)
            buffered = BytesIO()
            im.convert('RGB').save(buffered, format="JPEG")
            # encode the image
            thumb_encoded_string = base64.b64encode(buffered.getvalue()).decode()
            #updatedb
            s = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
            img_path = os.path.relpath(img_path,s)
            owner.db.thumbnails.update_one({"dirhash": dirhash },{"$set": { "last_modified_epoch": round(time.time()),"dirhash": dirhash , "cover_256": thumb_encoded_string, "path": img_path}}, upsert=True)
            #reload ..
            owner.send_message_value('Cover changed', str(dirhash))
    except Exception:
        logging.exception("Thumbnail generation failed for %s", img_path)

def import_audio_file(owner, db, root, file, overwrite, shared_state_lock=None):
    '''
    Insert only one file
    '''
    filename, file_extension = os.path.splitext(os.path.basename(file))
    if file_extension[1:] not in Update_Lib.audioextension: return
    f = os.path.join(root, file)

    dirname = (os.path.dirname(f)).replace(os.path.join(os.getenv("HOME"), '.Player', 'mediafiles'), "")[1:]
    if "/." in dirname:
        return  #Do not import files in hidden folders
    try:
        fc = db.mediafiles.count_documents({"dirname": dirname, "filename": filename, "extension": file_extension[1:]})
    except Exception:
        fc = 0

    if fc == 0 or overwrite == True:  # File not found in DB, insert it !

        owner.send_message("Importing : " + dirname)
        c_folder = os.path.basename(os.path.normpath(root))
        subfolder = True if True in [c_folder.startswith(i) for i in owner.album_sub_folder] else False
        if subfolder ==True:
            dirhash = binascii.crc32(os.path.abspath(os.path.join(dirname, os.pardir)).encode("UTF-8"))
        else:
            dirhash = binascii.crc32(dirname.encode("UTF-8"))

        if shared_state_lock is not None:
            with shared_state_lock:
                append_unique_shared(owner.imported_dirhashs, dirhash)
        else:
            append_unique_shared(owner.imported_dirhashs, dirhash)
        logging.debug("Update_Lib|run|File found:" + str(f))

        media_file = mutagen.File(f)
        if media_file is None or media_file.info is None:
            logging.warning("Skipping unreadable media file: %s", f)
            return
        si = media_file.info
        info = {"mediatype": "audio", "mediasubtype": "music", "last_modified_timestamp": Timestamp_modified(f),
                "date_imported": Excel_Now()
            , "date_imported_timestamp": Timestamp_Now(), "dirname": dirname, "dirhash": dirhash,
                "filename": filename, "cover": False
            , "extension": file_extension[1:], "size" : os.stat(f).st_size}

        for i in ["channels","sample_rate","length","bitrate"] :
            if hasattr(si, i):
                info[i]= getattr(si, i)


            # Copy cover
        info["cover"] = False
        owner.plugins_action('before_image_import')
        for image_name in get_cover_names(Update_Lib.image_names, Update_Lib.imageextension):
                #img = os.path.realpath(f)
            if subfolder == True:
                img = os.path.abspath(os.path.join(f, os.pardir))
            img = os.path.join(os.path.dirname(f), image_name)
            if isfile_insensitive(img):
                info["cover"] = True
                thumbnailer(owner,img, dirhash,overwrite)
                break



            # Erase if not found
        if info["cover"] == False:
            owner.db.thumbnails.update_one({"dirhash": dirhash}, {"$set": {"dirhash": dirhash }}, upsert=True)

            #Get tags
        tags = {}
        if file_extension[1:] == 'mp3':
            if os.path.isfile(f):
                if mutagen.File(f).tags != None:
                    txxx = [f for f in [f.desc.lower() for f in mutagen.File(f).tags.getall("TXXX")] ]
                    for tag in txxx :
                        vkeys = EasyID3.valid_keys.keys()
                        vkeys = [f for f in vkeys if f not in ['catalognumber', 'performer']] # catalognumber IS in valid keys BUT not in the EasyMP3 results ?? must be REGISTERED !
                        if tag not in  vkeys:                    # DO NOT REMOVE THIS !
                            register_txxx_key(owner, tag, shared_state_lock)

                    try:
                        audio = EasyMP3(f)
                        tags = audio
                    except Exception as exc:
                        logging.warning("Error importing MP3 tags for %s: %s", f, exc)
                        return

        elif file_extension[1:] == 'm4a':
            try:
                audio = EasyMP4(f)
                tags = audio
            except Exception as exc:
                logging.warning("Error importing M4A tags for %s: %s", f, exc)
                return
        else:
            try:
                audio = mutagen.File(f)
                if audio is None:
                    return
                tags = audio
            except Exception as exc:
                logging.warning("Error importing tags for %s: %s", f, exc)
                return

        dic = {**convert(tags), **convert(info)}


            # Correct the values
        if "tracknumber" in dic:
            if len(dic["tracknumber"]) > 0:
                try:
                    dic["tracknumber"] = int(re.split(r'[\s,.|/|\|-|_]+', dic["tracknumber"][0])[0])
                except:
                    dic["tracknumber"] = 0

        if "totaltracks" in dic:
            if len(dic["totaltracks"]) > 0:
                try:
                    dic["totaltracks"] = int(re.split(r'[\s,.|/|\|-|_]+', dic["totaltracks"][0])[0])
                except:
                    dic["totaltracks"] = 0

        if "discnumber" in dic:
            if len(dic["discnumber"]) > 0:
                elems = re.split(r'[\s,.|/|\|-|_]+', dic["discnumber"][0])
                try:
                    if len(elems) != 0:
                        dic["discnumber"] = int(elems[0])
                except:
                    dic["discnumber"] = 0

        if "date" in dic:
            if len(dic["date"]) > 0:
                v = re.findall(r"(?<!\d)\d{4,4}(?!\d)", str(dic["date"]))
                if len(v) > 0:
                    dic["date"] = int(v[0])
                else:
                    dic.pop("date", None)


        def str_to_int(d):
            # interpret string as numbers
            for k, v in d.items():
                if isinstance(v, dict):
                    str_to_int(v)
                elif isinstance(v, list):
                    i = 0
                    for l in range(len(v)):
                        v[i] = ReprInt(v[i])
                elif isinstance(v, str):
                    d[k] = ReprInt(v)
            return d

        dic = str_to_int(dic)



        for tag in owner.SingleValueTags:
            if tag in dic:
                if isinstance(dic[tag],list):
                    if len(dic[tag])>0:
                        dic[tag] = dic[tag][0]
        try:
            res =db.mediafiles.update_one({"dirname": dirname, "filename": filename, "extension": file_extension[1:]}, {"$set":dic},upsert=True)
            if shared_state_lock is not None:
                with shared_state_lock:
                    if res.upserted_id is not None:
                        append_unique_shared(owner.imported_ids, res.upserted_id)
            else:
                if res.upserted_id is not None:
                    append_unique_shared(owner.imported_ids, res.upserted_id)

            try:
                md = db.mediadirs.find_one({"dirhash": dic['dirhash']}) #1416115518
                if md == None:
                    # First file of this dirhash found ...
                    dic ={key: value for key, value in dic.items() if key not in owner.OnlyFilesTags}
                    res = db.mediadirs.update_one({"dirhash": dic['dirhash']}, {"$set": dic}, upsert=True)
                else:
                    # Add existing values to the new ones ...
                    d = {}
                    for key in dic:
                        if key not in owner.OnlyFilesTags and key in dic:
                            if key in md:
                                val_md = md[key] if type(md[key]) is list else [md[key]]
                            else:
                                val_md = []
                            val_mf = dic[key] if type(dic[key]) is list else [dic[key]]
                            val_md.extend(val_mf)
                            val = list(dict.fromkeys(val_md))  # Unique value ...
                            d[key] = val
                    d['dirhash'] = d['dirhash'][0] if type(d['dirhash']) == list else d['dirhash']
                    d['dirhash'] = d['dirhash'][0] if type(d['dirhash']) == list else d['dirhash']
                    res = db.mediadirs.update_one({"dirhash": d['dirhash']}, {"$set": d}, upsert=True)
            except Exception as e:
                print(e)

            owner.send_message("Importing : " + dirname)
            logging.debug("Importing : " + str(dic))
        except Exception as error:
            owner.send_message("Error on Audio File Import")

