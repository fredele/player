# stream alsa loopback to http.

import subprocess
import threading
import flask
import time
from flask import Response

app = flask.Flask(__name__)

class MP3Streamer:
    def __init__(self, alsa_device="hw:3,1", bitrate=192):
        self.alsa_device = alsa_device
        self.bitrate = bitrate
        self.process = None
        self.lock = threading.Lock()

    def start(self):
        """Lance le pipeline GStreamer avec sortie vers stdout."""
        self.process = subprocess.Popen(
            [
                "gst-launch-1.0", "-q",
                "alsasrc", f"device={self.alsa_device}", "!",
                "audioconvert", "!",
                "lamemp3enc", f"bitrate={self.bitrate}", "cbr=true", "!",
                
                "fdsink", "fd=1",
            ],
            stdout=subprocess.PIPE,
            bufsize=0
        )

    def stream(self):
        """Générateur Flask pour envoyer le flux MP3 en HTTP."""
        if not self.process:
            raise RuntimeError("Le processus GStreamer n’est pas lancé.")
        while True:
            data = self.process.stdout.read(4096)
            if not data:
                break
            yield data

    def stop(self):
        with self.lock:
            if self.process:
                self.process.terminate()
                self.process.wait()
                self.process = None

# Instance globale du streamer
streamer = MP3Streamer()
streamer.start()

@app.route("/stream.mp3")
def stream_mp3():
    return Response(
        streamer.stream(),
        mimetype="audio/mpeg",
        headers={
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Accept-Ranges": "bytes"
        }
    )

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True)
    finally:
        streamer.stop()
