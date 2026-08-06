import louie
import os
import queue
from PIL import Image , ImageFile
import inotify.adapters
from threading import Thread
import binascii
import configparser
import time
import mutagen
from utils.exceldate import convert,DateToExcel,Excel_Now,Timestamp_modified,Timestamp_Now
import re
from pymongo import MongoClient ,ASCENDING ,DESCENDING,ASCENDING,TEXT
from mutagen.mp3 import EasyMP3
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from utils.string import ReprInt
import threading
from updatesavedqueries import Update_Queries
from io import BytesIO
import base64
import time
from os import listdir
from os.path import isfile, join



class Autoimport(Thread):

    def thumbnailer(self,owner, img_path, dirhash, overwrite):
        try:  # Exit of already imported
            if overwrite == True or owner.db.thumbnails.find_one({'dirhash': int(dirhash)}) == None:
                img_path_real = os.path.realpath(img_path)
                im = Image.open(img_path_real)
                size = 256, 256
                im.thumbnail(size, Image.ANTIALIAS)
                buffered = BytesIO()
                im.convert('RGB').save(buffered, format="JPEG")
                # encode the image
                thumb_encoded_string = base64.b64encode(buffered.getvalue()).decode()
                # updatedb
                s = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
                img_path = os.path.relpath(img_path, s)
                owner.db.thumbnails.update({"dirhash": dirhash}, { "$set":{"last_modified_epoch": round(time.time()), "dirhash": dirhash, "cover_256": thumb_encoded_string, "path": img_path}} , upsert=True)
                # reload ..
                self.owner.send_message("Cover changed")
        except:
            pass

    def import_audio_file(self,file):

        root =os.path.dirname(file)
        filename, file_extension = os.path.splitext(os.path.basename(file))
        if file_extension[1:] not in self.audioextension: return
        f = os.path.join(root, file)

        dirname = (os.path.dirname(f)).replace(os.path.join(os.getenv("HOME"), '.Player', 'mediafiles'), "")[1:]
        found = self.owner.db.mediafiles.find({"dirname": dirname, "filename": filename, "extension": file_extension[1:]})

        c_folder = os.path.basename(os.path.normpath(root))
        subfolder = True if True in [c_folder.startswith(i) for i in self.owner.album_sub_folder] else False
        if subfolder ==True:
            dirhash = binascii.crc32(os.path.abspath(os.path.join(dirname, os.pardir)).encode("UTF-8"))
        else:
            dirhash = binascii.crc32(dirname.encode("UTF-8"))

        self.owner.db.mediafiles.delete_many( {"dirname": dirname, "filename": filename, "extension": file_extension[1:]})


        overwrite = True
        if  overwrite == True:
            print(f"Import : {f}")

            si = mutagen.File(f).info
            info = {"mediatype": "audio", "mediasubtype": "music", "last_modified_timestamp": Timestamp_modified(f),
                    "date_imported": Excel_Now()
                , "date_imported_timestamp": Timestamp_Now(), "dirname": dirname, "dirhash": dirhash,
                    "filename": filename, "cover": False
                , "extension": file_extension[1:]}

            for i in ["channels","sample_rate","length","bitrate"] :
                if hasattr(si, i):
                    info[i]= getattr(si, i)

            # Copy cover
            info["cover"] = False
            #owner.plugins_action('before_image_import')
            for image_name in self.cover_names:
                rel = os.path.dirname(os.path.abspath(f))
                img = os.path.realpath(f)
                if subfolder == True:
                    img = os.path.abspath(os.path.join(img, os.pardir))
                img = os.path.join(os.path.dirname(img), image_name)
                rel = os.path.join(rel, image_name)
                if os.path.isfile(img):
                    info["cover"] = True
                    self.thumbnailer(self.owner,rel, dirhash,overwrite)
                    break

            # Erase if not found
            if info["cover"] == False:
                self.owner.db.thumbnails.update({"dirhash": dirhash}, {"dirhash": dirhash }, upsert=True)

            #Get tags
            tags = {}

            if file_extension[1:] == 'mp3':
                if os.path.isfile(f):
                    if mutagen.File(f).tags != None:
                        txxx = [f for f in [f.desc for f in mutagen.File(f).tags.getall("TXXX")] ]
                        for tag in txxx :
                            if tag not in self.owner.txxx:
                                vkeys = EasyID3.valid_keys.keys()
                                vkeys = [f for f in vkeys if f not in ['catalognumber','performer']] # catalognumber IS in valid keys BUT not in the EasyMP3 results ?? must be REGISTERED !
                                if tag not in  vkeys:                    # DO NOT REMOVE THIS !
                                    self.owner.txxx.append(tag)          # DO NOT REGISTER existing Valid tags as TXXX !
                                    EasyID3.RegisterTXXXKey(tag, tag)

                        tags = EasyMP3(f)
                        tags = eval(str(tags))

            elif file_extension[1:] == 'm4a':
                tags = eval(str(EasyMP4(f)))
            else:
                tags = mutagen.File(f)

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

            if "year" in dic:
                dic["date"] = dic["year"]
                dic.pop("year", None)

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

            for tag in self.owner.SingleValueTags:
                if tag in dic:
                    if isinstance(dic[tag],list):
                        if len(dic[tag])>0:
                            dic[tag] = dic[tag][0]
            try:
                result =self.owner.db.mediafiles.update({"dirname": dirname, "filename": filename, "extension": file_extension[1:]}, dic,upsert=True)
                # Correct values in the playlist
                i = -1
                for l in self.owner.player_state["queue"]:
                    i+=1
                    if (l["dirname"] == dirname and l["filename"] == filename and l["extension"] == file_extension[1:]):
                        dic["_id"]= str(result["upserted"])
                        dic["file"]= l["file"]
                        self.owner.player_state["queue"][i] = dic
                        self.owner.send_message("playlist changed")
                        if self.owner.player_state["position"] == i :
                            self.owner.send_message("audio changed")

            except pymongo.errors.PyMongoError as e:
                print("error")

            print('Fichier importé :')
            #print(dic)
            try:
                self.owner.plugins_action('after_auto_import')
            except:
                pass
            try:
                self.owner.send_message('auto import')
            except:
                pass

        # Wait for an empty queue ...
        if len(self.q.queue) == 0:
            self.owner.send_message("Scanning Music File" )
            self.owner.update_queries = Update_Queries(self.owner,self.owner.requestfind)
            self.owner.update_queries.start()
            louie.send("lib_updated", self)

    def worker(self):
        while True:
            file = self.q.get()
            try:
                self.import_audio_file(file)
            except:
                pass
            self.q.task_done()

    def pause(self):
        self.enpause = True

    def reprise(self):
        self.enpause = False

    def __init__(self, owner):
        Thread.__init__(self)
        self.owner = owner
        self.enpause = False

        def get_cover_names(image_names, imageextension):
            n = []
            e = []
            n.extend([x.lower() for x in image_names])
            n.extend([x.upper() for x in image_names])
            n.extend([x.capitalize() for x in image_names])
            n = list(set(n))
            e.extend([x.lower() for x in imageextension])
            e.extend([x.upper() for x in imageextension])
            e = list(set(e))
            return [name + '.' + ext for ext in e for name in n]

        home = os.getenv("HOME")
        if os.path.isfile(os.path.join(home, '.Player', 'config','config.ini')):
            _config =  configparser.ConfigParser()
            _config.read(os.path.join(home, '.Player', 'config','config.ini'))
            self.audioextension = _config['Tags']['audioextension'].split(',')
            self.imageextension = _config['Tags']['imageextension'].split(',')
            self.image_names = _config['Tags']['image_names'].split(',')
            self.cover_names = get_cover_names(self.image_names, self.imageextension)

        self.q = queue.Queue()
        num_threads = 1
        threads = []
        for i in range(num_threads):
            t = Thread(target=self.worker)
            t.start()
            threads.append(t)

    def run(self):
        p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Music')
        i = inotify.adapters.InotifyTree(p)
        for event in i.event_gen():
            try:

                if event is  None or event[3].startswith(".") or self.enpause == True:
                    continue

                if len(event[1]) == 1:
                    if event[1][0] == 'IN_CREATE'  :
                        f = os.path.join(event[2] ,event[3])
                        self.q.put(f)
                        print(f" Fichier crée : {f}")
                    if event[1][0] == 'IN_CLOSE_WRITE' :
                        f = os.path.join(event[2] ,event[3])
                        self.q.put(f) # Messages continuels et import incessant ....
                        print(f" Fichier édité : {f}")
                    if event[1][0] == 'IN_MOVED_TO' :
                        time.sleep(5)
                        f = os.path.join(event[2] ,event[3])
                        self.q.put(f)
                        print(f" Fichier renommé : {f}")
                    if event[1][0] == 'IN_MOVED_FROM' :
                        time.sleep(5)
                        f = os.path.join(event[2] ,event[3])
                        self.q.put(f)
                        print(f" Fichier renommé : {f}")
                    if event[1][0] == 'IN_DELETE' :
                        f = os.path.join(event[2] ,event[3])
                        self.q.put(f)
                        print(f" Fichier supprimé : {f}")

                if len(event[1]) == 2:
                    if event[1][0] == 'IN_CREATE'  :
                        fo = os.path.join(event[2] ,event[3])
                        onlyfiles = [os.path.join(fo,f )for f in listdir(fo) if isfile(join(fo, f))]
                        for  f in onlyfiles:
                            self.q.put(f)
                        print(f" Dossier crée : {fo}")
                    if event[1][0] == 'IN_CLOSE_WRITE' :
                        fo = os.path.join(event[2] ,event[3])
                        onlyfiles = [os.path.join(fo,f ) for f in listdir(fo) if isfile(join(fo, f))]
                        for  f in onlyfiles:
                            self.q.put(f)
                        print(f" Dossier édité : {fo}")
                    if event[1][0] == 'IN_MOVED_TO' :
                        fo = os.path.join(event[2] ,event[3])
                        onlyfiles = [os.path.join(fo,f )for f in listdir(fo) if isfile(join(fo, f))]
                        time.sleep(5)
                        for  f in onlyfiles:
                            self.q.put(f)
                        print(f" Dossier renommé : {fo}")
                    if event[1][0] == 'IN_MOVED_FROM' :
                        fo = os.path.join(event[2] ,event[3])
                        fo = fo.replace(os.path.join(os.getenv("HOME"), '.Player', 'mediafiles'), "")[1:]
                        self.owner.db.mediafiles.delete_many({"dirname": fo})

                        self.owner.send_message("Scanning Music File")
                        self.owner.update_queries = Update_Queries(self.owner, self.owner.requestfind)
                        self.owner.update_queries.start()
                        louie.send("lib_updated", self)
                        print(f" Dossier renommé : {fo}")
                    if event[1][0] == 'IN_DELETE' :
                        fo = os.path.join(event[2] ,event[3])
                        fo = fo.replace(os.path.join(os.getenv("HOME"), '.Player', 'mediafiles'), "")[1:]
                        self.owner.db.mediafiles.delete_many( {"dirname": fo})

                        self.owner.send_message("Scanning Music File")
                        self.owner.update_queries = Update_Queries(self.owner, self.owner.requestfind)
                        self.owner.update_queries.start()
                        louie.send("lib_updated", self)
                        print(f" Dossier supprimé : {fo}")
            except:
                pass
