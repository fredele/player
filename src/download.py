
import os
import zipstream
from bson.objectid import ObjectId
from flask import Flask, Response, send_file, abort,request
import threading
import time

app = Flask(__name__)

class ZipDirhash(threading.Thread):
    def __init__(self,app, dirhash,zip_path):
        super().__init__()
        self.app =app
        self.dirhash = dirhash
        self.zip_path = zip_path
        self.files = []
        cursor = self.app.db.mediafiles.find({'dirhash': int(dirhash)})
        cursor = [x for x in cursor]
        for file in cursor:
            source_path = os.path.join(app.mediafiles_dir, file["dirname"], f"{file['filename']}.{file['extension']}")
            self.files.append( {
                'file': source_path,
                'name': f"{file['filename']}.{file['extension']}"
            })
        folder = os.path.join(app.mediafiles_dir,file["dirname"])
        for file in os.listdir(folder):
            for ext in ["jpg","jpeg","png"]:
                if file.endswith("." + ext):
                    f = os.path.join(folder, file)
                    if os.path.isfile(f) == True:
                        filepath = os.path.join(folder, file)
                        self.files.append({
                            'file': filepath,
                            'name': f"{file}"
                        })

    def run(self):
        # use ZIP_DEFLATED for standard compression instead of a simple copie
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_STORED)
        for item in self.files:
            z.write(item['file'], arcname=item['name'])
        with open(self.zip_path, 'wb') as f:
            for chunk in z:
                f.write(chunk)


def streamdirhash(app,dirhash,range_header):
    cursor = app.db.mediafiles.find_one({'dirhash': int(dirhash)})
    if not cursor:
        # Si dirhash inconnu, on peut retourner 404 ou response vide
        return Response(status=404)
    dirname = os.path.basename(cursor["dirname"])
    zip_path = f"/tmp/{dirname}.zip"

    if not  range_header or range_header =='bytes=0-':
        if not os.path.isfile(zip_path):
            transcoder = ZipDirhash(app,dirhash,zip_path)
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
        try:
            with open(zip_path, "rb") as f:
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
        finally:
            try:
                if os.path.isfile(zip_path):
                    os.remove(zip_path)
            except Exception:
                pass

    MIN_REQUIRED_SIZE = 150000

    timeout = time.time() + 10
    while not os.path.exists(zip_path) or os.path.getsize(zip_path) < MIN_REQUIRED_SIZE:
        if time.time() > timeout:
            return Response("Temporary File incomplet", status=503)
        time.sleep(0.1)

    file_size = os.path.getsize(zip_path)
    end_value = end if end is not None else file_size - 1
    content_length = end_value - start + 1
    if range_header and range_header !='bytes=0-':
        zipfilename = os.path.basename(zip_path)
        headers = {
            "Content-Type": "application/zip",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end_value}/{file_size}",
            "Content-Disposition": f'attachment; filename="{zipfilename}"'
        }

        with open(zip_path, "rb") as f:
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
        zipfilename = os.path.basename(zip_path)
        headers = {
            "Content-Type": "application/zip",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
            "Content-Disposition": f'attachment; filename="{zipfilename}"'
        }

        return Response(generate(), status=200 , headers=headers)
