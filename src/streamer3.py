# On-the-fly transcoding and chunked transfert - DOES WORK ...

import os
from bson.objectid import ObjectId
from flask import Flask, Response, send_file, abort, request
import gi
import threading
import hashlib
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst, GstPbutils
import time

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".Player", "cache", "transcode")
os.makedirs(CACHE_DIR, exist_ok=True)
TRANSCODE_LOCKS = {}
TRANSCODE_LOCKS_GUARD = threading.Lock()
SUPPORTED_CODECS = {"mp3": "audio/mpeg", "flac": "audio/flac", "ogg": "audio/ogg", "opus": "audio/opus"}


def normalize_codec(codec):
    codec_name = str(codec or "mp3").lower().strip()
    if codec_name not in SUPPORTED_CODECS:
        raise ValueError(f"Codec non supporté: {codec}")
    return codec_name


def get_transcode_lock(cache_key):
    with TRANSCODE_LOCKS_GUARD:
        lock = TRANSCODE_LOCKS.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            TRANSCODE_LOCKS[cache_key] = lock
        return lock


def cleanup_transcode_cache(max_files=200, max_age_seconds=86400):
    try:
        if not os.path.isdir(CACHE_DIR):
            return
        now = time.time()
        entries = []
        for name in os.listdir(CACHE_DIR):
            if name.endswith('.tmp') or name.endswith('.lock'):
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
    def __init__(self, input_path, output_path, final_output_path, codec, bitrate, lock_file=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.final_output_path = final_output_path
        self.pipeline = None
        self.codec = codec
        self.bitrate = bitrate
        self.lock_file = lock_file

    def run(self):
        encoders = {"mp3": "lamemp3enc", "flac": "flacenc", "ogg": "vorbisenc", "opus": "opusenc"}
        pipeline_str = f"""
            filesrc location="{self.input_path}" !
            decodebin !
            audioconvert ! audioresample !
            {encoders[self.codec]} target=1 bitrate={self.bitrate} !
            filesink location="{self.output_path}" append=false
        """
        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
            self.pipeline.set_state(Gst.State.PLAYING)
            bus = self.pipeline.get_bus()
            bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
        except Exception as exc:
            print(f"[transcode:error] {os.path.basename(self.final_output_path)} {exc}")
        finally:
            if self.pipeline is not None:
                self.pipeline.set_state(Gst.State.NULL)

            if self.output_path and os.path.exists(self.output_path):
                try:
                    if self.final_output_path and self.final_output_path != self.output_path:
                        if os.path.exists(self.final_output_path):
                            os.remove(self.final_output_path)
                        os.replace(self.output_path, self.final_output_path)
                except OSError as exc:
                    print(f"[transcode:rename-error] {self.final_output_path} {exc}")

            if self.output_path and os.path.exists(self.output_path):
                try:
                    os.remove(self.output_path)
                except OSError:
                    pass

            if self.lock_file and os.path.exists(self.lock_file):
                try:
                    os.remove(self.lock_file)
                except OSError:
                    pass


def send_audio_file(app, fileid, codec, bitrate, range_header):
    cleanup_transcode_cache(10,86400)

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
    file = hashlib.sha256((fileid + codec + str(bitrate)).encode('utf-8')).hexdigest()
    cached_file = os.path.join(CACHE_DIR, f"{file}.{codec}")
    tmp_file = f"{cached_file}.tmp"
    lock_file = os.path.join(CACHE_DIR, f"{file}.{codec}.lock")
    cache_key = os.path.basename(cached_file)
    lock = get_transcode_lock(cache_key)
    transcoder = None
    transcoding_state = "idle"

    if not range_header or range_header == 'bytes=0-':
        with lock:
            if not os.path.isfile(cached_file):
                transcoding_state = "in_progress"
                try:
                    if os.path.exists(tmp_file):
                        os.remove(tmp_file)
                    with open(lock_file, 'w', encoding='utf-8') as f:
                        f.write('1')
                    print(f"[transcode:start] {cache_key} codec={codec} bitrate={bitrate} source={source_path}")
                    transcoder = TranscodeToFileThread(source_path, tmp_file, cached_file, codec, bitrate, lock_file=lock_file)
                    transcoder.daemon = True
                    transcoder.start()
                except Exception as exc:
                    transcoding_state = "error"
                    print(f"[transcode:error] {cache_key} {exc}")
                    if os.path.exists(tmp_file):
                        try:
                            os.remove(tmp_file)
                        except OSError:
                            pass
                    if os.path.exists(lock_file):
                        try:
                            os.remove(lock_file)
                        except OSError:
                            pass
                    raise
            else:
                transcoding_state = "finished"
                transcoder = None
    else:
        transcoder = None
        transcoding_state = "finished" if os.path.exists(cached_file) else "in_progress"

    if range_header:
        try:
            range_value = range_header.strip().lower()
            assert range_value.startswith("bytes=")
            byte_range = range_value.replace("bytes=", "").split("-")
            start = int(byte_range[0])
            end = int(byte_range[1]) if byte_range[1] else None
        except Exception:
            return Response(status=416)
    else:
        start = 0
        end = None

    def generate():
        wait_started = time.time()
        prebuffer_bytes = 8192
        while True:
            target = cached_file if os.path.exists(cached_file) else tmp_file
            if not os.path.exists(target):
                if transcoder is not None and transcoder.is_alive():
                    if time.time() - wait_started > 30:
                        break
                    time.sleep(0.1)
                    continue
                break

            file_size = os.path.getsize(target)
            if file_size == 0:
                if transcoder is None or not transcoder.is_alive():
                    break
                if time.time() - wait_started > 30:
                    break
                time.sleep(0.1)
                continue

            if file_size < prebuffer_bytes and (transcoder is not None and transcoder.is_alive()):
                if time.time() - wait_started > 30:
                    pass
                else:
                    time.sleep(0.1)
                    continue

            try:
                with open(target, "rb") as f:
                    f.seek(start)
                    pos = start
                    while True:
                        if end is not None and pos > end:
                            break
                        chunk = f.read(4096)
                        if not chunk:
                            if transcoder is not None and transcoder.is_alive():
                                time.sleep(0.1)
                                continue
                            break
                        yield chunk
                        pos += len(chunk)
            except OSError:
                break
            break

    if os.path.exists(cached_file):
        file_size = os.path.getsize(cached_file)
    else:
        file_size = os.path.getsize(tmp_file) if os.path.exists(tmp_file) else 0

    end_value = end if end is not None else max(file_size - 1, 0)
    content_length = end_value - start + 1 if file_size > 0 else 0

    if range_header and range_header != 'bytes=0-':
        headers = {
            "Content-Type": SUPPORTED_CODECS[codec],
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end_value}/{file_size}",
        }

        try:
            with open(cached_file if os.path.exists(cached_file) else tmp_file, "rb") as f:
                f.seek(start)
                data = f.read(content_length)
                return Response(data, status=206, headers=headers)
        except Exception:
            return Response(status=416, headers={"Content-Range": f"bytes */{file_size}"})

    headers = {
        "Content-Type": SUPPORTED_CODECS[codec],
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Transfer-Encoding": "chunked"
    }

    return Response(generate(), status=200, headers=headers)
