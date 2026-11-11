# On-the-fly transcoding and chunked transfert - DOES NOT WORK ...

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
import queue


SUPPORTED_CODECS = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
    "wav": "audio/wav",
}



Gst.init(None)

app = Flask(__name__)

import time
import subprocess
from flask import Response

def send_audio_file(app,player_id, fileid, codec, bitrate,range):
    
    doc = app.db.mediafiles.find_one({"_id": ObjectId(fileid)})
    if not doc:
        return abort(404)

    file_path = os.path.join(app.mediafiles_dir, doc["dirname"], f"{doc['filename']}.{doc['extension']}")

    
    encoders = {
        "mp3": f"lamemp3enc target=1 cbr=true bitrate={bitrate}",
        "flac": "flacenc quality=5",
        "ogg": f"vorbisenc bitrate={bitrate}",
        "opus": f"opusenc bitrate={bitrate}",
        "wav": "audio/x-raw,format=S16LE,rate=44100,channels=2 ! wavenc",
    }

    pipeline_cmd = f"""
        filesrc location="{file_path}" !
        decodebin !
        audioconvert ! audioresample !
        {encoders[codec]} !
        identity sync=True !
        appsink name=mysink emit-signals=True sync=True max-buffers=20 max-bytes=2097152 max-time=2000000000
    """
    
    pipeline = Gst.parse_launch(pipeline_cmd)
    appsink = pipeline.get_by_name("mysink")
    
    # File d'attente tampon (ex: 50 blocs d'avance)
    audio_queue = queue.Queue(maxsize=100)

    def producer():
        """ Thread séparé qui tire les samples de GStreamer en continu """
        pipeline.set_state(Gst.State.PLAYING)
        try:
            while True:
                sample = appsink.emit("pull-sample")
                if not sample:
                    break
                
                buffer = sample.get_buffer()
                success, map_info = buffer.map(Gst.MapFlags.READ)
                if success:
                    # Copie des données pour éviter les conflits mémoire GStreamer
                    chunk_data = bytes(map_info.data)
                    buffer.unmap(map_info)
                    
                    # Bloque si la file est pleine (régulation naturelle)
                    audio_queue.put(chunk_data)
        except Exception:
            pass
        finally:
            pipeline.set_state(Gst.State.NULL)
            audio_queue.put(None)  # Signal de fin (EOS)

    # Lancement du producteur en arrière-plan
    t = threading.Thread(target=producer, daemon=True)
    t.start()
    def generate():
        """ Consommateur Flask : lit dans la file tamponnée """
        try:
            while True:
                chunk = audio_queue.get()
                if chunk is None:
                    break
                yield chunk
        finally:
            # Nettoyage si le client se déconnecte prématurément
            pipeline.set_state(Gst.State.NULL)

    headers = {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Accept-Ranges": "bytes",
        "transferMode.dlna.org": "Streaming",
        "contentFeatures.dlna.org": "DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01500000000000000000000000000000",
    }

    return Response(generate(), status=200, headers=headers)