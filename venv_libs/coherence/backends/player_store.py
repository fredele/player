from coherence.backend import BackendItem, BackendStore
from coherence.upnp.core import DIDLLite
from coherence.upnp.core.DIDLLite import  Resource
from twisted.python import util
import requests
import json
import urllib.parse
import re
import time
from utils.tags import gettags
from pymongo import MongoClient
from utils.string import to_int , BoolStr,StrBool
from utils.string import char_position
import copy
import hashlib
import socket
import os
import configparser
import louie
import glob
from utils.xspfparser import parseFile
from utils.omplparser import read_opml
from utils.RSSparsers import Podcast

_config = configparser.ConfigParser()
inifile = os.path.join(app.config_folder, 'config.ini')
if os.path.isfile(inifile):
     _config.read(inifile)
     port = _config['Server']['httpport']
     host = _config['HttpServer']['address']
     http_server_addr = 'http://'+ host + ':' + port
     mongo_addr =  _config['MongoDB']['address']

def requestfind(request,db):
    strquery =   str(request["query"])
    # replace $time with the current date
    tags = gettags(strquery)
    countt = [t.rsplit('_', 1)[1] for t in tags if 'time_' in t]
    vals = {}
    for ct in countt:
        try:
            t =  int(time.time()) - int(ct)
            vals['$time_' + ct + '$'] = t
        except:
            pass

    def replacetime(d):
        # replaces the string repr. with the int value ...
        if isinstance(d, dict):
            for k, v in d.items():
                if not isinstance(v, str):
                    replacetime(v)
                else:
                    for k1, v1 in vals.items():
                        if k1 in v:
                            d[k] = v1
        elif isinstance(d, list):
            for i in d:
                replacetime(i)

        return d
    try:
        query = eval(strquery)
    except:
        pass
        # décode str en dict
    query =replacetime(query)
    key = request.get('field', "")
    sorttag =  request["sorttag"].split('$',1)[0] if "sorttag" in request else key
    if  "sort" in request:
        sort = request["sort"]
    else:
        if len(request["sorttag"].split('$',1)) == 2 :
            sort = request["sorttag"].split('$',1)[1] if "sorttag" in request else "ASCENDING"
        else:
            sort= "ASCENDING"

    sortdic = {sorttag : -1 if sort  == "DESCENDING" else 1}
    display = request.get( 'display', "")
    full = request.get("full", "false")
    basequery = copy.deepcopy(query)
    tags = gettags(display)
    displaytags = [t for t in tags if not t.endswith("_count")]
    counttags = [t for t in tags if t.endswith("_count")]
    counttags = [t.replace("_count","") for t in counttags]

    # The Last filtered key and value is :
    lastfield = list(query["$and"][-1].keys())[0]
    lastfieldvalue = list(query["$and"][-1].values())[0]

    # Get the full albums
    if full.lower() == "true":
        dirhash_values = db.mediafiles.find(basequery).distinct('dirhash')
        basequery = {'$and': [{'dirhash': {'$in': [f for f in dirhash_values]} }]}
    result = []
    try:
        s = urllib.parse.quote(str(query)) + sort + sorttag + display + full
    except:
        return ""
    has = hashlib.sha256(s.encode('utf-8')).hexdigest()
    full = BoolStr(full)


    def displayed(r,val):
        try:
            if isinstance(r[val],list):
                result =str(r[val][0])

                try:
                    if isinstance(eval(result), list):
                        if len(eval(result))>0:
                            result = ", ".join(sorted([str(item) for sublist in r[val] for item in sublist]))
                        else:
                            result = ", ".join([str(eval(e)) for e in r[val]])
                except:
                    pass
            else:
                result =str(r[val])

            return result
        except:
            return ""

    def add_count_tag(tag):
        if tag not in grp:
            grp[tag + "_count"] = {"$addToSet": "$" + tag}
        if tag not in prj:
            prj[tag + "_count"] = {"$size": "$" + tag + "_count"}

    def add_display_tag(tag):
        if tag not in grp:
            grp[tag ] = {"$addToSet": "$" + tag}
        if tag not in prj:
            prj[tag] =  "$" + tag
    grp = {"_id": "$" + key, "files": {"$sum": 1}, "dirhashs": {"$addToSet": "$dirhash"}}
    prj = {"_id": 0, "keyval": "$_id", "files": 1, "dirhashs": "$dirhashs"}
    for tag in counttags:
        add_count_tag(tag)
    for tag in displaytags:
        add_display_tag(tag)
    sort = -1 if sort =="DESCENDING" else 1
    search = db.mediafiles.aggregate([
        {"$match": basequery},
        {"$unwind": "$" + key},
        {"$group": grp},
        {"$project": prj},
        {"$sort": sortdic}  #Beware of parallel indexing, does not work with multiple sorting ...
    ])
    result = list(search)
    result = [l for l in result if l['keyval'] not in ['',['']]]
    # Delete all result not beginning with the correct Letter on "alphabet" tag ...
    if "alphabet" in lastfield and key != "dirhash":
        try:
            result = [i for i in result if i["keyval"].lower().startswith(lastfieldvalue.lower() )]
        except:
            pass
    # Delete all result not beginning in this group tag ...
    if "group_" in lastfield and key != "dirhash":
        try:
            g1 = char_position(lastfieldvalue[0])
            g2 = char_position(lastfieldvalue[-1])
            result = [i for i in result if (  g1 <= char_position(i["keyval"].lower()) and  char_position(i["keyval"].lower())  <= g2 ) ]
        except:
            pass
    for r in result:
        query = copy.deepcopy(basequery)
        query_and = query['$and']
        query_and.append({key: r["keyval"]})
        r["query"] =   query
        displayval = copy.deepcopy(display)
        displayval =  displayval.replace('$' + key + '$',   displayed(r,"keyval"))
        displayval = displayval.replace('$' +sorttag+ '$', displayed(r,sorttag))
        for tag in displaytags:
            displayval = displayval.replace('$' + tag + '$', displayed(r,tag))
        for tag in counttags:
            displayval = displayval.replace('$' + tag + '_count$', displayed(r,tag+"_count"))
        r["display"] = displayval if displayval != "" else r["keyval"]
        r["covers"] = r["dirhashs"]
        if 'dirhashs' in r:
            del r['dirhashs']
    try:
         q =urllib.parse.quote(str(basequery))
         db.savedqueries.update({"hashquery": has},
              {
                  "hashquery": has,
                  "query" : q,
                  "lasttime": int(round(time.time())),
                  "field" : key,
                  "sort" : sort,
                  "sorttag" : sorttag,
                  "display" : display,
                  "full": StrBool(full),
                  "displayed" : 0,
                  "result": result,
              } , upsert=True)

    except:
        pass
    return { 'key': key, 'result': result}

def FindFiles(db,query,sorttags):
    """
    Returns all tag values  for a selection of files sorted by a list of tags
    used by Control Query View
    """
    sorte = sorttags.split('$')[1]
    tag =  sorttags.split('$')[0]

    cursor = db.mediafiles.find(eval(urllib.parse.unquote(query))).limit(1000)
    if sorte =="ASCENDING":
        cursor = sorted(cursor, key=lambda k: [
            k.get(tag , []) if isinstance(k.get(tag , []), list) else [k.get(tag , [])],
            k.get('album', []) if isinstance(k.get('album', []), list) else [k.get('album', [])],
            1000 * to_int(k.get("discnumber", 0)) + to_int(k.get("tracknumber", 0))])
    else:

        cursor = sorted(cursor, key=lambda k: [
            [ -g for g in k.get(tag , [])] if isinstance(k.get(tag , []), list) else [-k.get(tag , [])],
            k.get('dirname', []) if isinstance(k.get('dirname', []), list) else [k.get('dirname', [])], #todo : à vérifier
            k.get('album', []) if isinstance(k.get('album', []), list) else [k.get('album', [])],
            1000 * to_int(k.get("discnumber", 0)) + to_int(k.get("tracknumber", 0))])
    cursor = [f for f in cursor]
    for i in cursor:
        i['_id'] = str(i['_id'])
    return cursor

def MsToMMSS(value):
    q, s = divmod(value/1000, 60)
    h, m = divmod(q, 60)
    if h ==0 :
        return "%02d:%02d" % ( m, s)
    else :
        return "%02d:%02d:%02d" % (h, m, s)

class TrackItem(BackendItem):
    logCategory = 'trackitem'
    def __init__(self, id, parent_id,  addr,it,store=None,container_class=DIDLLite.MusicTrack ):
        BackendItem.__init__(self)
        self.id = id
        self.addr = addr
        self.parent_id = parent_id
        self.store = store
        self.it = it
        if "title" in it:
            self.title = it["title"][0] if type(it["title"]) is list else it["title"]
        try:
            if "album" in it:
                self.album = it["album"][0] if type(it["album"]) is list else it["album"]
            if "artist" in it:
                self.artist = ", ".join(sorted(it["artist"])) if type(it["artist"]) is list else it["artist"]
        except:
            pass
        self.item = container_class(id, parent_id, self.name)

        if "title" in it:
            self.item.title = self.title
        if "artist" in it:
            self.item.artist = self.artist
        if "album" in it:
            self.item.album = self.album
        if "dirhash" in it :
            dirhash = str(it["dirhash"])
            thumbnail_url = self.store.address + '/v1/Covers/' + dirhash + ".jpg" + "?thumbnail=800"
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url
        if "image" in it :
            thumbnail_url =  self.store.address  + urllib.parse.quote('/v1/Mediafile/Radios/' + it['image'])
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url

        if "tracknumber" in it:
            self.item.originalTrackNumber = it["tracknumber"]

        if it['extension'] == 'mp4':
            self.mimetype = 'video/mp4'
        if it['extension'] == 'm4a':
            self.mimetype = 'audio/x-m4a'
        if it['extension'] == 'flac':
            self.mimetype = "audio/x-flac"
        if it['extension'] == 'mp3':
            self.mimetype = 'audio/mpeg'
        if it['extension'] == 'ogg':
            self.mimetype = 'audio/x-vorbis'
        if it['extension'] == 'opus':
            self.mimetype = 'audio/x-vorbis' #'audio/opus'
        if it['extension'] == 'wma':
            self.mimetype = "audio/x-ms-wma"
        if it['extension'] == 'wav':
            self.mimetype = "audio/x-wav"
        self.item.mimetype = self.mimetype
        if "dirname" in it:
            self.url_addr = self.store.address + "/" + urllib.parse.quote(it["dirname"] )+ "/" + urllib.parse.quote(it["filename"]) + "." + it["extension"]
        else:
            self.url_addr = self.store.address
        res = Resource(self.url_addr,f'http-get:*:{self.mimetype}:*')
        if "length" in it:
            res.duration = str(MsToMMSS(it["length"]*1000))
        self.item.res.append(res)
        pass

    def get_url(self):
      return self.url_addr

    def get_item(self):
        return self.item

    def get_name(self):
        return self.title

    def get_id(self):
        return self.id

class BroadCastRadio(BackendItem):
    logCategory = 'trackitem'
    def __init__(self, id, parent_id,  addr,it,store=None,container_class=DIDLLite.AudioBroadcast ):
        BackendItem.__init__(self)
        self.id = id
        self.addr = addr
        self.parent_id = parent_id
        self.store = store
        self.it = it
        if "title" in it:
            self.title = it["title"][0] if type(it["title"]) is list else it["title"]
        self.item = container_class(id, parent_id, self.name)
        if "title" in it:
            self.item.title = self.title
        if "image" in it :
            thumbnail_url =  self.store.address  + urllib.parse.quote('/v1/Mediafile/Radios/' + it['image'])
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url
        self.mimetype = 'audio/mpeg'
        self.url_addr = addr
        res = Resource(self.url_addr,f'http-get:*:{self.mimetype}:*')
        if "length" in it:
            res.duration = it["length"]
        self.item.res.append(res)
        pass

    def get_url(self):
      return self.url_addr

    def get_item(self):
        return self.item

    def get_name(self):
        return self.title

    def get_id(self):
        return self.id


class BroadCastPodcast(BackendItem):
    logCategory = 'trackitem'
    def __init__(self, id, parent_id,  addr,it,store=None,container_class=DIDLLite.AudioBroadcast ):
        BackendItem.__init__(self)
        self.id = id
        self.addr = addr
        self.parent_id = parent_id
        self.store = store
        self.it = it
        if "title" in it:
            self.title = it["title"][0] if type(it["title"]) is list else it["title"]
        self.item = container_class(id, parent_id, self.name)
        if "title" in it:
            self.item.title = self.title
        if "image" in it :
            thumbnail_url =  it['image']
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url
        self.mimetype = 'audio/mpeg'
        self.url_addr = addr
        res = Resource(self.url_addr,f'http-get:*:{self.mimetype}:*')
        if "length" in it:
            res.duration = it["length"]
        self.item.res.append(res)
        pass

    def get_url(self):
      return self.url_addr

    def get_item(self):
        return self.item

    def get_name(self):
        return self.title

    def get_id(self):
        return self.id

class Container(BackendItem):
    logCategory = 'container'


    def __init__(self, id, parent_id, dic, store=None, children_callback=None,container_class=DIDLLite.Container):
        BackendItem.__init__(self)
        self.store = store
        self.id = id
        self.parent_id = parent_id
        self.name = re.sub("[\(\[].*?[\)\]]", "", dic["display"])
        self.mimetype = 'directory'
        self.item = container_class(id, parent_id, self.name)

        if "covers" in dic :
            dirhash = str(dic["covers"][0])
            thumbnail_url = self.store.address + '/v1/Thumbnails/' + dirhash + ".jpg"
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url
        else:
            self.item.albumArtURI = self.store.address + '/v1/Web/Assets/cd.png'
            if parent_id == 0 :                                     # menu element
                self.item.albumArtURI = self.store.address + '/v1/Web/Assets/icon.png'
            try:
                if self.store.containers[parent_id].parent_id ==0 : # submenu element
                    self.item.albumArtURI = self.store.address + '/v1/Web/Assets/icon.png'
            except:
                pass

        if "image" in dic :
            thumbnail_url = dic["image"]
            self.item.icon = thumbnail_url
            self.item.albumArtURI = thumbnail_url

        self.update_id = 0
        if children_callback is not None:
            self.children = children_callback
        else:
            self.children = util.OrderedDict()

        if store is not None:
            self.get_url = lambda: store.urlbase + str(self.id)

    def add_child(self, child):
        id = child.id
        self.children[id] = child
        if self.item.childCount is not None:
            self.item.childCount += 1

    def get_children(self, start=0, end=0):
        self.info(f'container.get_children {start} {end}')

        if callable(self.children):
            return self.children(start, end - start)
        else:
            children = list(self.children.values())
        if end == 0:
            return children[start:]
        else:
            return children[start:end]

    def remove_children(self):
        if not callable(self.children):
            self.children = util.OrderedDict()
            self.item.childCount = 0

    def get_child_count(self):
        if self.item.childCount is not None:
            return self.item.childCount

        if callable(self.children):
            return len(self.children())
        else:
            return len(self.children)

    def get_item(self):
        return self.item

    def get_name(self):
        return self.name

    def get_id(self):
        return self.id

class PlayerStore(BackendStore):

    logCategory = 'player_store'
    implements = ['MediaServer']
    description = "Description"
    options = [
        {'option': 'name', 'type': 'string', 'default': 'my media',
         'help': 'the name under this MediaServer '
                 'shall show up with on other UPnP clients'},
        {'option': 'version', 'type': 'int', 'default': 2, 'enum': (2, 1),
         'help': 'the highest UPnP version this MediaServer shall support',
         'level': 'advance'},
        {'option': 'uuid', 'type': 'string',
         'help': 'the unique (UPnP) identifier for this MediaServer,'
                 ' usually automatically set',
         'level': 'advance'}

    ]
    def on_lib_updated(self):
        self.containers = {}
        self.containers[0] = Container(0, -1, {"display": "root"}, store=self)
        self.containers[1] = Container(1, 0, {"display": 'Disques'}, store=self)
        self.containers[0].add_child(self.containers[1])
        self.containers[2] = Container(2, 0, {"display": 'Radios'}, store=self)
        self.containers[0].add_child(self.containers[2])
        self.containers[3] = Container(3, 0, {"display": 'Podcasts'}, store=self)


    def getnextID(self):
        ret = self.next_id
        self.next_id += 1
        return ret

    def get_menu(self):
        v = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config")), "views.json")
        if os.path.exists(v):
            with open(v) as f:
                self.menu = json.load(f)

    def __init__(self, server, **kwargs):
        BackendStore.__init__(self, server, **kwargs)
        louie.connect(self.on_lib_updated, "lib_updated")
        self.mongo_addr = "mongodb://" + mongo_addr
        self.MongoConnection = MongoClient(self.mongo_addr)
        self.db = self.MongoConnection.player
        self.address = http_server_addr
        self.headers =""
        self.next_id = 1000
        self.server = server
        self.containers = {}
        self.name = kwargs.get('name', 'my media')
        self.content = kwargs.get('content', None)
        self.wmc_mapping.update({'14': '0', '15': '0','16': '0','17': '0'})
        self.containers[0] = Container(0, -1, {"display" :"root"}, store=self)
        self.containers[1] = Container(1 , 0, {"display" : 'Disques'},store=self)
        self.containers[0].add_child(self.containers[1])
        self.containers[2 ] = Container(2, 0, {"display" :'Radios'},store=self)
        self.containers[0].add_child(self.containers[2])
        self.containers[3 ] = Container(3 , 0, {"display" :'Podcasts'},store=self)
        self.containers[0].add_child(self.containers[3])
        self.init_completed = True

    def upnp_init(self):
        pass

    def get_by_id(self, id):
        if isinstance(id,(bytes, bytearray)):
            id = id.decode("utf-8")

        if "@" in id:
            id = id.split("@")[0]
        id = int(id)
        if id == 0:
            if len(self.containers[1].children) == 0 :
                # Library
                self.get_menu()
                for music_item in self.menu["music"]:
                    name = music_item["name"]
                    nextid = self.getnextID()
                    self.containers[nextid] = Container(nextid, 1, {"display": name}, store=self)
                    self.containers[nextid].query = music_item["query"]
                    self.containers[nextid].levels = music_item["levels"]
                    self.containers[nextid].level = 0
                    self.containers[nextid].type = "MusicTracks"
                    self.containers[1].add_child(self.containers[nextid])
                # Radios
                v = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Radios"))
                radios = []
                files = sorted([file for file in glob.glob(os.path.join(v, "*.xspf"))])
                for file in files:
                    if os.path.isfile(file):
                        radios.append({"name": os.path.splitext(os.path.basename(file))[0], "file": os.path.basename(file)})
                for radiofile in radios:
                    nextid = self.getnextID()
                    self.containers[nextid] = Container(nextid, 2, {"display": radiofile["name"]}, store=self)
                    self.containers[nextid].type ="Radios"
                    self.containers[2].add_child(self.containers[nextid])
                    try:
                        ra = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Radios",radiofile["file"]))
                        ra = parseFile(ra)
                    except:
                        return
                    j =nextid
                    for radio in ra['tracklist']:
                        nextid = self.getnextID()
                        item = {}
                        item['title'] = radio['title']
                        item['image'] = radio['image']
                        item['extension'] = radio['location'].split(".")[-1]
                        self.containers[nextid] = BroadCastRadio(nextid, j,radio['location'], item, store=self)
                        self.containers[j].add_child(self.containers[nextid])
                # Podcasts
                v = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Podcasts"))
                podcasts = []
                files = sorted([file for file in glob.glob(os.path.join(v, "*.opml"))])
                for file in files:
                    if os.path.isfile(file):
                        podcasts.append(
                            {"name": os.path.splitext(os.path.basename(file))[0], "file": os.path.basename(file)})
                for podcastfile in podcasts:
                    nextid = self.getnextID()
                    self.containers[nextid] = Container(nextid, 3, {"display": podcastfile["name"]}, store=self)
                    self.containers[nextid].type = "Podcasts Menu"
                    self.containers[3].add_child(self.containers[nextid])
                    file = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Podcasts", podcastfile["file"]))
                    pocds = read_opml(file,"1")
                    j = nextid
                    for pocd in pocds:
                        nextid = self.getnextID()
                        item = {"display": pocd['display'], "image":pocd['covers'][0], "query": pocd['query']}
                        self.containers[nextid] = Container(nextid, j, item,  store=self)
                        self.containers[j].add_child(self.containers[nextid])
                        self.containers[nextid].type = "Podcasts RSS"
                        self.containers[nextid].url =pocd['url']
                    pass

            else :
                return self.containers[0]

        full = "false"
        try:
            item1 = self.containers[id]
        except:
            return None

        if isinstance(item1, TrackItem):
            return item1

        if isinstance(item1, BroadCastRadio):
            return item1

        if isinstance(item1, BroadCastPodcast):
            return item1

        if len(item1.children)!=0:
            return item1

        if hasattr(item1, 'type'):
            if item1.type == "Podcasts RSS":
                #get and decode podcast
                response = requests.get(item1.url)

                def getcontent(res):
                    podcast = Podcast(res)
                    return podcast

                podcast = getcontent(response.content)
                for it in podcast.items:
                    item = {}
                    item['title'] = it.title
                    item['image'] = item1.item.albumArtURI
                    item['addr'] = it.url
                    item['length'] = it.itunes_duration
                    nextid = self.getnextID()
                    self.containers[nextid] = BroadCastPodcast(nextid,item1.id, it.url, item, store=self)
                    self.containers[item1.id].add_child(self.containers[nextid])
                return item1


        if hasattr(item1, 'query') and len(item1.levels) > item1.level :
            query = item1.query
            level = item1.level
            field = item1.levels[level][0]
            if "$full" in field:
                field = field.split("$")[0]
                full ="true"
            sort = item1.levels[level][1]

            if len(item1.levels[level]) > 2:
                display = item1.levels[level][2]
                display = re.sub("[\(\[].*?[\)\]]", "", display)


            req = {"query" : query, "field": field ,"sorttag": sort, "display" : display, "full" : full}

            req1 = requestfind(req,self.db)
            for item in req1["result"]:
                nextid = self.getnextID()
                self.containers[nextid] = Container(nextid, id, item, store=self)
                self.containers[nextid].query = item["query"]
                self.containers[nextid].level = item1.level + 1
                self.containers[nextid].levels = item1.levels
                item1.add_child(self.containers[nextid])
            return item1

        elif hasattr(item1, 'query') and len(item1.levels) == item1.level: # Last level
            sorttag = "album$ASCENDING"
            query = urllib.parse.quote(str(item1.query))
            l = item1.levels[item1.level-1]
            req = FindFiles(self.db,query,  sorttag)
            for item in req:
                nextid = self.getnextID()
                self.containers[nextid] = TrackItem(nextid, id,self.address, item, store=self)
                self.containers[id].add_child(self.containers[nextid])
            return item1
        else:
            return item1


    def get_id_by_name(self, name):
        pass

    def get_url_by_name(self, parent='0', name=''):
        pass

if __name__ == '__main__':
    from twisted.internet import reactor
    from coherence.base import Coherence
    config = {'plugins': [{'backend': 'PlayerStore', 'name': 'Player', 'uuid': 'PlayerStore'}], 'logging': {}}
    def set_upnp_config(config):
        Coherence(config)
    reactor.callWhenRunning(set_upnp_config, config)
    reactor.run()