# On-the-fly transcoding and chunked transfert - DOES NOT WORK ...

import os
from bson.objectid import ObjectId
from flask import Flask, Response, send_file, abort, request
from flask import current_app as app
from pathlib import Path
import gi
import threading
import queue
import hashlib
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst, GstPbutils
import time
import math

CACHE_DIR = app.transcoded_folder
os.makedirs(CACHE_DIR, exist_ok=True)

MIMETYPES = {
    'mp4': 'video/mp4',
    'm4a': 'audio/x-m4a',
    'flac': 'audio/x-flac',
    'mp3': 'audio/mpeg',
    'ogg': 'audio/x-vorbis',
    'opus': 'audio/x-vorbis',  # ou 'audio/opus'
    'wma': 'audio/x-ms-wma',
    'wav': 'audio/x-wav',
}


def normalize_codec(codec):
    codec_name = str(codec or "mp3").lower().strip()
    if codec_name not in MIMETYPES:
        raise ValueError(f"Codec non supporté: {codec}")
    return codec_name


def cleanup_transcode_cache(max_files=200, max_age_seconds=86400):
    try:
        if not os.path.isdir(CACHE_DIR):
            return
        now = time.time()
        entries = []
        for name in os.listdir(CACHE_DIR):
            if name.endswith('.tmp'):
                path = os.path.join(CACHE_DIR, name)
                try:
                    os.remove(path)
                except OSError:
                    pass
                continue

            path = os.path.join(CACHE_DIR, name)
            if os.path.isfile(path):
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                entries.append((mtime, path))

        entries.sort(key=lambda item: item[0])
        for _, path in entries[:-max_files] if len(entries) > max_files else []:
            try:
                os.remove(path)
            except OSError:
                pass

        for mtime, path in entries:
            if now - mtime > max_age_seconds:
                try:
                    os.remove(path)
                except OSError:
                    pass
    except Exception:
        pass

Gst.init(None)

app = Flask(__name__)

class TranscodeToFileThread(threading.Thread):
    """Transcode en mémoire et pousse les données dans une queue (appsink),
    sans écrire de fichier temporaire ni de fichier final."""
    def __init__(self, input_path, codec, bitrate):
        super().__init__()
        self.input_path = input_path
        self.codec = codec
        self.bitrate = bitrate
        self.pipeline = None
        self.queue = queue.Queue()
        self.error = None

    def run(self):
        encoders = {
            "mp3": f"lamemp3enc target=1 cbr=true bitrate={self.bitrate}",
            "flac": "flacenc quality=5",
            "ogg": f"vorbisenc bitrate={self.bitrate}",
            "opus": f"opusenc bitrate={self.bitrate}",
            "wav": "audio/x-raw,format=S16LE,rate=44100,channels=2 ! wavenc",
        }


        pipeline_str = f"""
            filesrc location="{self.input_path}" !
            decodebin !
            audioconvert ! audioresample !
            {encoders[self.codec]} !
            appsink name=sink emit-signals=true sync=true
        """

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)

            # Connecte le callback appsink pour pousser chaque buffer dans la queue.
            appsink = self.pipeline.get_by_name("sink")
            if appsink is not None:
                appsink.connect("new-sample", self.on_new_sample)


            self.pipeline.set_state(Gst.State.PLAYING)
            bus = self.pipeline.get_bus()
            bus.timed_pop_filtered(
                Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR
            )
        except Exception as exc:
            self.error = exc
            print(f"[transcode:error] {os.path.basename(self.input_path)} {exc}")
        finally:
            self.queue.put(None)  # sentinelle : fin de flux pour generate()
            if self.pipeline is not None:
                self.pipeline.set_state(Gst.State.NULL)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.ERROR
        buf = sample.get_buffer()
        if buf is None:
            return Gst.FlowReturn.ERROR
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if not result:
            return Gst.FlowReturn.ERROR
        try:
            data = bytes(mapinfo.data)
            self.queue.put(data)
        finally:
            buf.unmap(mapinfo)
        return Gst.FlowReturn.OK


def get_audio_metadata(file_path):
    """Extrait la durée, le taux d'échantillonnage et les canaux de n'importe quel format via le Discoverer de GStreamer."""
    Gst.init(None)
    
    discoverer = GstPbutils.Discoverer.new(5 * Gst.SECOND)
    uri = Gst.filename_to_uri(os.path.abspath(file_path))
    
    try:
        info = discoverer.discover_uri(uri)
        duration = info.get_duration() / Gst.SECOND
        
        audio_streams = info.get_audio_streams()
        if audio_streams:
            sample_rate = audio_streams[0].get_sample_rate()
            channels = audio_streams[0].get_channels()
        else:
            sample_rate = 44100
            channels = 2
            
        return duration, sample_rate, channels
    except Exception as e:
        print(f"❌ Erreur GStreamer Discoverer pour {file_path} : {e}")
        return None, None, None

def send_audio_file(app, player_id, fileid, codec, bitrate, range_header):
    cleanup_transcode_cache(10, 86400)

    try:
        codec = normalize_codec(codec)
    except ValueError:
        return Response(f"Codec non supporté: {codec}", status=400)

    try:
        bitrate = int(bitrate)
    except (TypeError, ValueError):
        bitrate = 128

    doc = app.db.mediafiles.find_one({"_id": ObjectId(fileid)})
    if not doc:
        return abort(404)

    source_path = os.path.join(app.mediafiles_dir, doc["dirname"], f"{doc['filename']}.{doc['extension']}")

    if not os.path.exists(source_path):
        print(f"⏩ Fichier introuvable dans le dossier, ignoré : {source_path}")
        return abort(404)

    print(f"--- 1. Analyse : {source_path} ---")
    duration, sample_rate, channels = get_audio_metadata(source_path)
    estimated_size = None

    if codec in ("mp3", "ogg", "opus") and duration > 0:
        estimated_size = int(duration * bitrate * 1000 / 8)

    elif codec == "wav":
        bits_per_sample = 16
        bytes_per_second = sample_rate * (bits_per_sample // 8) * channels
        estimated_data_size = int(duration * bytes_per_second)
        wav_header_size = 44  # En-tête standard WAV
        estimated_size = estimated_data_size + wav_header_size

    file = hashlib.sha256((fileid + player_id + codec + str(bitrate)).encode('utf-8')).hexdigest()
    cache_key = file
    transcoder = None
    transcoding_state = "idle"

    transcoding_state = "in_progress"
    try:
        print(f"[transcode:start] {cache_key} codec={codec} bitrate={bitrate} source={source_path}")
        transcoder = TranscodeToFileThread(source_path, codec, bitrate)
        transcoder.daemon = True
        transcoder.start()
    except Exception as exc:
        transcoding_state = "error"
        print(f"[transcode:error] {cache_key} {exc}")
        raise

    def generate(estimated_size=None):
        wait_started = time.time()
        sent_bytes = 0
        print(f"[http:start] {cache_key} estimated_size={estimated_size}")

        try:
            while True:
                try:
                    data = transcoder.queue.get(timeout=1.0)
                except queue.Empty:
                    if not transcoder.is_alive():
                        break
                    continue
                if data is None:
                    # Sentinelle : fin de flux (EOS ou erreur)
                    break
                if data:
                    sent_bytes += len(data)
                    yield data

        except Exception as exc:
            print(f"[http:error] {cache_key} {exc}")
            raise
        finally:
            print(
                f"[http:end] {cache_key} "
                f"sent={sent_bytes} "
                f"elapsed={time.time() - wait_started:.1f}s"
            )

    headers = {
        "Content-Type": MIMETYPES[codec],
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    headers["Transfer-Encoding"] = "chunked"
    return Response(generate(estimated_size), status=200, headers=headers)
