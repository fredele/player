# On-the-fly transcoding and chunked transfert - DOES WORK ! 


import os
from bson.objectid import ObjectId
from flask import Flask, Response, send_file, abort, request
from flask import current_app as app
from pathlib import Path
import gi
import threading
import hashlib
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst, GstPbutils
import time
import math

CACHE_DIR = app.transcoded_folder
os.makedirs(CACHE_DIR, exist_ok=True)

SUPPORTED_CODECS = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
    "wav": "audio/wav",
}

def normalize_codec(codec):
    codec_name = str(codec or "mp3").lower().strip()
    if codec_name not in SUPPORTED_CODECS:
        raise ValueError(f"Codec non supporté: {codec}")
    return codec_name


def cleanup_transcode_cache(max_files=200, max_age_seconds=86400):
    try:
        if not os.path.isdir(CACHE_DIR):
            return
        now = time.time()
        entries = []
        for name in os.listdir(CACHE_DIR):
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
    def __init__(self, input_path, output_path, codec, bitrate):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pipeline = None
        self.codec = codec
        self.bitrate = bitrate

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
            identity sync=False !
            filesink location="{self.output_path}" append=false
        """
        
        try:
            print(f"[transcode:start] {os.path.basename(self.output_path)} codec={self.codec} bitrate={self.bitrate} source={self.input_path}")
            self.pipeline = Gst.parse_launch(pipeline_str)
            self.pipeline.set_state(Gst.State.PLAYING)
            bus = self.pipeline.get_bus()
            bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
        except Exception as exc:
            print(f"[transcode:error] {os.path.basename(self.output_path)} {exc}")
        finally:
            if self.pipeline is not None:
                self.pipeline.set_state(Gst.State.NULL)
            print(f"[transcode:end] {os.path.basename(self.output_path)}")


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
    duration = float(doc.get("length") or 0)
    
    estimated_size = None
    if codec in ("mp3", "ogg", "opus") and duration > 0:
        estimated_size = int(duration * bitrate * 1000 / 8)
        
    if codec == "wav":
        bitrate = 1411  # 16 bits * 44100 Hz * 2 channels / 1000
        def estimate_wav_size(duration, sample_rate=44100, channels=2, bits=16):
            bytes_per_frame = channels * (bits // 8)
            frames = math.floor(duration * sample_rate)
            data_size = frames * bytes_per_frame
            return 44 + data_size
        estimated_size = estimate_wav_size(duration)

    file_hash = hashlib.sha256((fileid + player_id + codec + str(bitrate)).encode('utf-8')).hexdigest()
    cached_file = os.path.join(CACHE_DIR, f"{file_hash}.{codec}")
    cache_key = os.path.basename(cached_file)
    transcoder = None

    # New request / initial playback request: delete old cached file if present and start new encoding
    if not range_header or range_header == 'bytes=0-':
        if os.path.exists(cached_file):
            try:
                os.remove(cached_file)
                print(f"[transcode:remove-old] {cache_key}")
            except OSError as exc:
                print(f"[transcode:remove-error] {cache_key} {exc}")

        try:
            transcoder = TranscodeToFileThread(source_path, cached_file, codec, bitrate)
            transcoder.daemon = True
            transcoder.start()
        except Exception as exc:
            print(f"[transcode:error] {cache_key} {exc}")
            raise
    else:
        # Range request: if file doesn't exist yet, it might still be generating or needs starting
        if not os.path.exists(cached_file):
            try:
                transcoder = TranscodeToFileThread(source_path, cached_file, codec, bitrate)
                transcoder.daemon = True
                transcoder.start()
            except Exception as exc:
                print(f"[transcode:error] {cache_key} {exc}")

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
        
    def generate(estimated_size=None):
        wait_started = time.time()
        prebuffer_bytes = 8192
        sent_bytes = 0

        print(f"[http:start] {cache_key} estimated_size={estimated_size}")

        try:
            while estimated_size is None or sent_bytes < estimated_size:
                if not os.path.exists(cached_file):
                    if transcoder is not None and transcoder.is_alive():
                        if time.time() - wait_started > 30:
                            print(f"[http:timeout-no-file] {cache_key}")
                            break
                        time.sleep(0.1)
                        continue

                    print(f"[http:no-file] {cache_key}")
                    break

                file_size = os.path.getsize(cached_file)

                if file_size == 0:
                    if transcoder is None or not transcoder.is_alive():
                        print(f"[http:empty-file] {cache_key}")
                        break

                    if time.time() - wait_started > 30:
                        print(f"[http:timeout-empty-file] {cache_key}")
                        break

                    time.sleep(0.1)
                    continue

                if (
                    file_size < prebuffer_bytes
                    and transcoder is not None
                    and transcoder.is_alive()
                    and time.time() - wait_started <= 30
                ):
                    time.sleep(0.1)
                    continue

                try:
                    with open(cached_file, "rb") as f:
                        f.seek(start + sent_bytes)

                        while estimated_size is None or sent_bytes < estimated_size:
                            pos = start + sent_bytes

                            if end is not None and pos > end:
                                break

                            remaining = (
                                4096 if estimated_size is None
                                else estimated_size - sent_bytes
                            )

                            if end is not None:
                                remaining = min(remaining, end - pos + 1)

                            if remaining <= 0:
                                break

                            chunk = f.read(min(4096, remaining))

                            if not chunk:
                                if transcoder is not None and transcoder.is_alive():
                                    time.sleep(0.1)
                                    continue
                                break

                            sent_bytes += len(chunk)
                            yield chunk

                except FileNotFoundError:
                    if transcoder is not None and transcoder.is_alive():
                        time.sleep(0.1)
                        continue
                    print(f"[http:read-error] {cache_key}: fichier introuvable")
                    break

                except OSError as exc:
                    print(f"[http:read-error] {cache_key} {exc}")
                    break

                if transcoder is None or not transcoder.is_alive():
                    break

        except GeneratorExit:
            print(
                f"[http:generator-closed] {cache_key} "
                f"sent={sent_bytes} "
                f"elapsed={time.time() - wait_started:.1f}s"
            )
            raise

        except Exception as exc:
            print(f"[http:error] {cache_key} {exc}")
            raise

        finally:
            print(
                f"[http:end] {cache_key} "
                f"sent={sent_bytes} "
                f"estimated_size={estimated_size} "
                f"elapsed={time.time() - wait_started:.1f}s"
            )
 
    file_size = os.path.getsize(cached_file) if os.path.exists(cached_file) else 0
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
            with open(cached_file, "rb") as f:
                f.seek(start)
                data = f.read(content_length)
                return Response(data, status=206, headers=headers)
        except Exception:
            return Response(status=416, headers={"Content-Range": f"bytes */{file_size}"})

    headers = {
        "Content-Type": SUPPORTED_CODECS[codec],
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    if estimated_size is not None:
        headers["Content-Length"] = str(estimated_size)
        return Response(generate(estimated_size), status=200, headers=headers)
    else:
        headers["Transfer-Encoding"] = "chunked"
        return Response(generate(), status=200, headers=headers)