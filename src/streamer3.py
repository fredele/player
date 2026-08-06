# On-the-fly transcoding and chunked transfert - DOES WORK ...

import os
from bson.objectid import ObjectId
from flask import Flask, Response, send_file, abort,request
import gi
import threading
import hashlib
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst, GstPbutils
import time

Gst.init(None)

app = Flask(__name__)

class TranscodeToFileThread(threading.Thread):
    def __init__(self, input_path, output_path,codec,bitrate):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pipeline = None
        self.codec =codec
        self.bitrate = bitrate

    def run(self):
        encoders = { "mp3" : "lamemp3enc", "flac" : "flacenc","ogg" : "vorbisenc", "opus" : "opusenc"}
        pipeline_str = f"""
            filesrc location="{self.input_path}" !
            decodebin !
            audioconvert ! audioresample !
            {encoders[self.codec]} target=1 bitrate={self.bitrate} !
            filesink location="{self.output_path}" append=false
        """
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.pipeline.set_state(Gst.State.PLAYING)
        bus = self.pipeline.get_bus()
        bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
        self.pipeline.set_state(Gst.State.NULL)


def send_audio_file(app,fileid,codec,bitrate, range_header):

    doc = app.db.mediafiles.find_one({"_id": ObjectId(fileid)})
    if not doc:
        return abort(404)
    source_path = os.path.join(app.mediafiles_dir, doc["dirname"], f"{doc['filename']}.{doc['extension']}")
    file = hashlib.sha256((fileid + codec+bitrate).encode('utf-8')).hexdigest()
    cached_file = os.path.join("/tmp", f"{file}.{codec}")

    if not  range_header or range_header =='bytes=0-':
        if not os.path.isfile(cached_file):
            transcoder = TranscodeToFileThread(source_path, cached_file,codec,bitrate)
            transcoder.start()
        else:
            transcoder = None

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
        with open(cached_file, "rb") as f:
            f.seek(start)
            pos = start
            while True:
                if end is not None and pos > end:
                    break
                chunk = f.read(4096)
                if not chunk:
                    if transcoder == None:
                        break
                    if transcoder.is_alive():
                        time.sleep(0.1)
                        continue
                    else:
                        break
                yield chunk
                pos += len(chunk)


    MIN_REQUIRED_SIZE = 150000

    timeout = time.time() + 10
    while not os.path.exists(cached_file) or os.path.getsize(cached_file) < MIN_REQUIRED_SIZE:
        if time.time() > timeout:
            return Response("Temporary File incomplet", status=503)
        time.sleep(0.1)

    file_size = os.path.getsize(cached_file)
    end_value = end if end is not None else file_size - 1
    content_length = end_value - start + 1
    content_types = {"mp3": "audio/mpeg", "flac": "audio/flac", "ogg":"audio/ogg","opus":"audio/opus"}
    if range_header and range_header !='bytes=0-':    #gmediarender uses this, not the hardware player ...
        #print(f"range_header:{range_header}")
        headers = {
            "Content-Type": content_types[codec],
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end_value}/{file_size}",
        }

        with open(cached_file, "rb") as f:
            try:
                f.seek(start)
                data = f.read(content_length)
                return Response(data, status=206, headers=headers)
            except:
                headers = {
                  "Content-Range": f"bytes */{file_size}"
                }
                return Response( status=416, headers=headers)
    else:
        headers = {
            "Content-Type": content_types[codec],
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }

        return Response(generate(), status=200 , headers=headers)
