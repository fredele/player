import gi
import pulsectl
gi.require_version('Gst', '1.0')
import io
import urllib.parse
import json
#from streamer import send_audio_file
from streamer3 import send_audio_file
from gi.repository import Gst
import logging
import markdown
import louie
from twisted.web.static import DirectoryLister
from twisted.web.static import File
from twisted.python.threadpool import ThreadPool
from utils.web import get_adresse_ip_locale
import subprocess
from os import getpid
from PIL import Image
from utils.string import to_unicode , char_position , EmptyValue
from utils.template import my_template
from functools import wraps
import threading
import hashlib
from pymongo.errors import ConnectionFailure
import shutil
import optparse
import os ,sys
import simplejson as json
import configparser
import mutagen
from mutagen.mp3 import EasyMP3
from mutagen.easymp4 import EasyMP4
from mutagen.easyid3 import EasyID3
import signal
from os import listdir
from os.path import isfile, join
import urllib.parse
from updatesavedqueries import Update_Queries
from upnpclient.discover_upnp import get_upnp_renderers
from coherence.base import Coherence
import base64
import random
from bson.objectid import ObjectId
from flask import g ,Response, stream_with_context
from flask import send_file, redirect
from pymongo import MongoClient,ASCENDING, TEXT
from datetime import datetime
from time import sleep
from bson import BSON, decode_all
from flask_httpauth import HTTPTokenAuth
from itsdangerous import TimedJSONWebSignatureSerializer as JWT
from flask_httpauth import HTTPBasicAuth
from requests.auth import HTTPBasicAuth as basicaut
from  players.gplayer import GPlayer
from  players.upnpplayer import UpnpPlayer
import time
import socket
import os
import glob
import copy
from utils.timeex import timing
from utils.exceldate import Timestamp_Now
from utils.xspfparser import parseFile
from utils.omplparser import read_opml
from usb_copy import USBCopyMonitor
from flask import render_template
from flask import abort
from utils.RSSparsers import Podcast
from utils.string import to_int ,naturalsort, BoolStr,StrBool, is_number, ReprInt
import requests
from flask_socketio import SocketIO
from flask import Flask
from flask_cors import CORS
from OpenSSL import crypto
from twisted.internet import reactor,ssl
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol , listenWS
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource
from utils.tags import gettags, replacetags
from  io import BytesIO
from autoimport import Autoimport
from utils.proc import set_proc_name
from utils.string import clean
from flask import request
from html.parser import HTMLParser
from lxml import etree
from rip_cd import launch_rip
from logging.handlers import RotatingFileHandler
from change_stream_thread import ChangeStream
from download import streamdirhash
app = Flask(__name__,static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')
CORS(app)
app.last_time =0
socketio = SocketIO(app)
app.basicauth = HTTPBasicAuth()
app.config['SECRET_KEY'] = 'secret_key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jwt = JWT(app.config['SECRET_KEY'],expires_in=360000000000000000000000) #10H
app.tokenauth = HTTPTokenAuth('Bearer')

#app.token = "eyJhbGciOiJIUzUxMiIsImlhdCI6MTY1MzEyNDExNywiZXhwIjozNjAwMDAwMDAwMDAwMDE2NTMxMjQxMTd9.eyJ1c2VybmFtZSI6IjVFODg0ODk4REEyODA0NzE1MUQwRTU2RjhEQzYyOTI3NzM2MDNEMEQ2QUFCQkRENjJBMTFFRjcyMUQxNTQyRDgifQ.xJ0F0cO9vaTkmr2Ji10KtaYoxRwRTfc-t72LrkvgUKu_Q_aTTOXEOXz3t3eZmk14o52PFpiqaXt6_csVsY-JMw"


INACTIVITY_TIMEOUT = 5 * 60  # X minutes -> X*60 secondes
CHECK_INTERVAL = 60  # fréquence de vérification en secondes

last_activity = time.monotonic()
last_activity_lock = threading.Lock()

def monitor_inactivity():
    global last_activity
    while True:
        time.sleep(CHECK_INTERVAL)
        with last_activity_lock:
            elapsed = time.monotonic() - last_activity
        #logging.debug("Check for last query : %s seconds.", elapsed)
        if elapsed >= INACTIVITY_TIMEOUT:
            try:

                import os
                # shutdown
                #os.system("sudo shutdown -h now")

            except Exception:
                pass
            break



def GetPlayer(player_id):
    for player in app.players:
        if player_id == player["id"]:
            break
    if "player" in player:
        return player["player"]
    else:
        return None

def send_message(message):
    msg = {}
    msg['message'] = message
    msg['value'] = ''
    if  hasattr(app, 'player_id'):
      msg['id'] = app.player_id
    else:
        msg['id'] = '-1'
    WSServerProtocol.broadcast_message(msg)

def send_message_value(message,value):
    msg = {}
    msg['message'] = message
    msg['value'] = value
    if hasattr(app, 'player_id'):
        msg['id'] = app.player_id
    else:
        msg['id'] = '-1'
    WSServerProtocol.broadcast_message(msg)

def plugins_action(function_name, param='none',param2='none'):
    plugin_files =sorted([f for f in listdir(plugins_dir) if isfile(join(plugins_dir, f)) and f.rsplit('.', 1)[1] == 'py'])
    for _filename_ in plugin_files:
        if os.path.isfile(os.path.join(os.path.join(os.getenv("HOME"), '.Player', 'plugins'), _filename_)):
            try:
                if param != 'none' and param2!= "none":
                    p = _filename_.split('.')[0] + '.'+ function_name +'(app,'+'"' +str(param)+ '"' + ','+str(param2) + ')'
                if param != 'none'and param2 == "none":
                    p = _filename_.split('.')[0] + '.'+ function_name +'(app,'+ str(param) + ')'
                if param == 'all' and param2 == "none":
                    p = _filename_.split('.')[0] + '.'+ function_name +'(app,"all")'
                if param == 'none' and param2 == "none":
                    p = _filename_.split('.')[0] + '.' + function_name + '(app)'
                exec(p)

            except Exception as e:
                pass

def shutdown_server():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    GetPlayer(player_id).set_stop()
    reactor.stop()
    #kill the process
    os.kill(app.pid, signal.SIGTERM)
    return ""

def update_playlist():

    # Update the playlists ...

    time.sleep(1) # Wait db writing ...
    for player in app.players:
        try:  # if there's no queue ..
            playlist = GetPlayer(player['id']).queue
            files = [ObjectId(str(file['_id'])) for file in playlist]
            cursor = app.db.mediafiles.find({"_id": {"$in": files}})
            for doc in cursor:
                id = (doc['_id'])
                i = 0
                for q in playlist:
                    if q['_id'] == str(id):
                        doc['_id'] = str(doc['_id'])
                        doc['file'] = os.path.join(app.mediafiles_dir, str(doc['dirname']), str(doc['filename']) + '.' + str(doc['extension']))
                        playlist[i] = doc
                    i += 1
            GetPlayer(player['id']).queue = playlist
        except:
            pass

def _writetag(i,field,value):
    """
    Write the tags to the file
    """
    os.chdir(app.root_path)
    try:
        if i['extension'] in app.audioextension:
            p = os.path.join(app.mediafiles_dir, str(i['dirname']), str(i['filename']) + '.' + str(i['extension']))
            p = os.path.realpath(p)
            if os.path.exists(p):
                filename, file_extension = os.path.splitext(os.path.basename(p))
                if file_extension[1:] == 'mp3':
                    for txxx in app.txxx:
                        EasyID3.RegisterTXXXKey(txxx, txxx)
                    tags = EasyMP3(p)


                elif file_extension[1:] == 'm4a':
                    tags = EasyMP4(p)
                else:
                    tags = mutagen.File(p)

                if isinstance(value, str) :
                    value = [value]

                if isinstance(value, int) :
                    value = [str(value)]

                values = [str(v) for v in value]
                if value != "" and len(value)>0:
                    if field in app.SingleValueTags:
                        v = values[0]
                        if v == "":
                            tags.pop(field)
                        else:
                            tags[field] = v
                    else:
                        if values in EmptyValue :
                            tags.pop(field)
                        values = list(dict.fromkeys(values))
                        if isinstance(values,list):
                            if len(values)==1:
                                values = values[0]
                        tags[field] = values

                tags.save()

    except:
        logging.warning("Error in writetag : " + str(p))

def _writetags(i,field,value,mode):
    """
    Write the tags to the file
    modes : add, del or removeadd (deleteall and replace)
    """
    os.chdir(app.root_path)
    try:
        if i['extension'] in app.audioextension:
            p = os.path.join(app.mediafiles_dir, str(i['dirname']), str(i['filename']) + '.' + str(i['extension']))
            p = os.path.realpath(p)
            if os.path.exists(p):
                filename, file_extension = os.path.splitext(os.path.basename(p))
                if file_extension[1:] == 'mp3':
                    for txxx in app.txxx:
                        EasyID3.RegisterTXXXKey(txxx, txxx)
                    tags = EasyMP3(p)


                elif file_extension[1:] == 'm4a':
                    tags = EasyMP4(p)
                else:
                    tags = mutagen.File(p)

                v = []
                if field in tags:
                    v = tags[field][:]
                    v = [val for val in v if val != value]
                if mode == 'removeadd':
                    v = []
                if mode in ['add','removeadd']:
                    v.append(value)
                    if field in ['discnumber','tracknumber']:
                        v = [value]
                try:
                    if len(v) == 0:
                        tags.pop(field, None)
                    if len(v) == 1:
                        tags[field] = v[0]
                    if len(v) > 1:
                        tags[field] = v
                    tags.save()
                except:
                    pass

    except:
        pass

def json_resp(data):
    """
    Format the response in JSON
    """
    return app.response_class(
            response=json.dumps(data,iterable_as_array=True),status=200, mimetype='application/json' )  #

def getfiles(dir):
    """
    Get additionnal files from the folders
    """
    os.chdir(app.root_path)
    d = os.path.join(app.mediafiles_dir, dir)
    files = []
    try:
        folders =  list(set([ os.path.join(d, f)for f in app.art_folder if f in os.listdir(d)]))
        for folder in folders :
            parent = os.path.basename(folder)
            if os.path.isdir(folder):
                for file in os.listdir(folder):
                    for ext in app.imageextension:
                        if file.endswith("."+ext):
                            f = os.path.join(folder, file)
                            if  os.path.isfile(f) == True :
                                files.append(os.path.join(parent, file))
    except:
        pass
    res = {"images": naturalsort(files)}
    txt_name = app.text_name
    ext = txt_name.split('.')[1]
    md = os.path.join(d,txt_name)
    if os.path.isfile(md) == True:
        try:
            with open(md, "r", encoding='utf-8', errors='ignore') as myfile:
                data = myfile.read()
                #data = data.replace("\n","</br>")
                data = markdown.markdown(data)
            res['text'] = (data.encode('utf8'))
        except:
            res['text'] =''
    return res


@app.errorhandler(401)
def custom_401(error):
    """
    401 Unauthorized
    :param error:
    :return: json response
    """
    return Response( json.dumps({"response":'Not authenticated as Admin !'}), 401, "",mimetype='application/json') #{'WWW-Authenticate':'Basic realm="Login Required"'}
    return abort(404)

def spectrum(el,id,vals):
    if(el == "spectrum"):
        val = ';'.join([str(int(f)) for f in vals])
        WSServerProtocol.broadcast_message('##'+id+':'+val)
    if(el == "level"):
        val = ';'.join([str(int(f)) for f in vals])
        WSServerProtocol.broadcast_message('#'+id+':'+val)

def audio_changed(id):
    msg = {}
    msg['message'] = 'audio changed'
    msg['id'] = id
    #print(msg)
    WSServerProtocol.broadcast_message(msg)

def queue_changed(id,a):
    #print('queue changed')
    msg = {}
    msg['message'] = 'playlist changed'
    msg['id'] = id
    WSServerProtocol.broadcast_message(msg)

def dsp_changed(id):
    msg = {}
    msg['message'] = 'dsp changed'
    msg['id'] = id
    WSServerProtocol.broadcast_message(msg)

def state_changed(id,state):
    #print('state changed')
    msg = {}
    msg['message'] = 'state changed'
    msg['value'] = str(state)
    msg['id'] = id
    print(f"message:state changed value:{msg['value']}")
    WSServerProtocol.broadcast_message(msg)
    time.sleep(.1)

class WSServerProtocol(WebSocketServerProtocol):
    connections = list()
    def onConnect(self, request):
        pass

    def onClose(self, wasClean, code, reason):
        try:
            self.connections.remove(self)
        except:
            pass

    def onOpen(self):
        self.connections.append(self)
        #print(self.peer)
        #print('Connection numbers : ' + str(len(self.connections)))

    @classmethod
    def broadcast_message(cls, data):
        payload = json.dumps(data, ensure_ascii = False).encode('utf8')
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendMessage, c, payload)

    # simply echo back the message ...
    def onMessage(self, payload, isBinary):
        if not isBinary:
            self.broadcast_message("echo:" + str(payload))

def handle_message(msg):
    if msg is not None:
        t = msg.type
        if t == Gst.MessageType.ERROR:
            pass
        elif t == Gst.MessageType.EOS:
            pass
        elif t == Gst.MessageType.DURATION_CHANGED:
            pass
        elif t == Gst.MessageType.STATE_CHANGED:
            pass

@app.template_filter('fname')
def fname(s):
    return s.rsplit('/',1)[1]

@app.context_processor
def passer_titre():
    return dict(titre="Bienvenue !")

@app.route("/v1/Transcode/<string:codec>/<int:bitrate>/<path:filename>")
def transcodedfile(codec, bitrate, filename):
    fileid = os.path.splitext(filename)[0]
    fileid = fileid.split("?", 1)[0]
    range_header = request.headers.get('Range', None)
    print(f"range_header:{range_header}")
    return send_audio_file(app, fileid, codec, bitrate, range_header)

@app.route("/v1/Transcode/<path:fileid>")
def transcodedfile_query_legacy(fileid):
    fileid = fileid.split("?", 1)[0]
    fileid = os.path.splitext(fileid)[0]
    codec = request.args.get('codec', 'mp3')
    bitrate = request.args.get('bitrate', '128')
    range_header = request.headers.get('Range', None)
    print(f"range_header:{range_header}")
    return send_audio_file(app, fileid, codec, bitrate, range_header)



@app.route("/v1/Zip/<dirhash>")
def zipdirhash(dirhash):
    range_header = request.headers.get('Range', None)
    print(f"range_header:{range_header}")
    return streamdirhash(app,dirhash,range_header)


@app.route('/img/<path:filename>')
def redirect_img_to_assets(filename):
    return redirect(f'/assets/{filename}', code=301)  # 301 pour une redirection permanente

@app.route('/v1/Pulseaudio/Outputs')
@app.tokenauth.login_required
def pulse_outs():
    res = {}
    res['response'] = 'Error'

    pulseoutputs = []
    pulsecurrentpulse = "Not Playing ?"
    try:
        with pulsectl.Pulse('volume-increaser') as pulse:
            for output in pulse.sink_list():
                pulseoutputs.append(urllib.parse.quote(str(output.name).encode("UTF-8")))
            for output in pulse.sink_input_list():
                if output.proplist["application.name"] == "Player":
                    try:
                        for sink in pulse.sink_list():
                            if sink.index == output.sink :
                                pulsecurrentpulse =  urllib.parse.quote(str(sink.name).encode("UTF-8"))
                    except:
                        pulsecurrentpulse = "Not Playing ?"
        res['response'] = 'OK'
        res['outputs'] = pulseoutputs
        res['current'] = pulsecurrentpulse
    except:
        return json_resp(res)
    return json_resp(res)

@app.route('/v1/Pulseaudio/SetOutput')
@app.tokenauth.login_required
def pulse_set_out():
    res = {}
    res['response'] = 'Error'
    try:
        output_name = None
        player_input = None
        if 'output' in request.args:
            output_name = urllib.parse.unquote(request.args["output"])
            with pulsectl.Pulse('volume-increaser') as pulse:
                for input in pulse.sink_input_list():
                    if input.proplist["application.name"] == "Player" :
                        player_input = input
                for sink in pulse.sink_list():
                    if sink.name == output_name:
                        new_output_sink = sink
                if (player_input != None and new_output_sink != None):
                    pulse.sink_input_move(player_input.index, new_output_sink.index)
                    res['output'] = urllib.parse.quote(new_output_sink.name.encode("UTF-8"))
                    res['response'] = 'OK'
        return json_resp(res)
    except:
        return json_resp(res)


def ParseSub(data):
    data = data.decode('utf-8')
    pars = HTMLParser()
    data = pars.unescape(data)
    data = data.split("<LastChange>")[1].split("</LastChange>")[0]
    root = etree.fromstring(data)
    vals = {}

    for child in root[0]:
        try:
            vals[child.tag.split("}")[1]] = child.attrib
        except:
            pass
    return vals

@app.route('/v1/Stats')
@app.tokenauth.login_required
def stats():
    res = {}
    c = app.db.mediafiles.find().distinct('artist')
    res['artist_count'] =  len(c)
    c = app.db.mediafiles.find().distinct('album')
    res['album_count'] = len(c)
    c = app.db.mediafiles.find().distinct('genre')
    res['genre_count'] = len(c)

    path = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Music", ))

    def get_folder_size(path: str) -> int:
        """
        Retourne la taille d'un dossier en octets sous Linux.
        :param path: Chemin du dossier
        :return: Taille du dossier en octets
        """
        if not os.path.isdir(path):
            return 0

        result = subprocess.run(['du', '-sb', path], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Erreur lors de l'exécution de 'du': {result.stderr}")

        return int(result.stdout.split()[0])

    #res["size"] = get_folder_size(path)

    return json_resp(res)


@app.route('/v1/<string:dirhash>/<string:filename>')
def file_listing(dirhash,filename):
    c = app.db.mediafiles.find_one({"dirhash": int(dirhash)})
    if c is not None:
        path = str(c["dirname"])
        path = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", path,filename))
        if os.path.exists(path):
            return send_file(path)
        else:
            return abort(404)
    else:
        return abort(404)


@app.route('/upnp/<string:playerid>', methods=['NOTIFY'])
def upnp_subscription(playerid):
    if player["type"] == "upnp":
        try:
            GetPlayer(playerid).put_event({"id": playerid, "data": request.data})
        except:
            return abort(404)
        return Response("",status=200)
    else:
        return abort(404)

def on_upnp_started():
    #print("upnp started ...")
    pass

@app.route('/v1/Players/Get')
#@app.tokenauth.login_required
def get_players():
    players = []
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        if hasattr(app,"player_id") :
            player_id = app.player_id


    res = {}

    if (len(request.args) == 0): # Returns saved players only
        players = os.path.join(os.getenv("HOME"), '.Player', 'config', "players.json")
        with open(players, 'r') as j:
            try:
                contents = json.loads(j.read())
                res['players']= contents["players"]
            except:
                return abort(404)

        try:
            player = [p for p in app.players if p["id"] == player_id][0]
            res["player"] = {"type": player["type"], "id": player["id"], "name": player["name"]}
            if "player" in player:
                res["player"]["player"] = "Object"

            if player["type"] == "gstreamer":
                res["player"]["loaded"] = True
                res["player"]["online"] = True

            if "address" in player:
                addr = player['address']
                try:
                    requests.get(addr, timeout=1)
                    res["player"]["online"] = True
                except:
                    res["player"]["online"] = False

            if "volume_control" in player:
                res["player"]["volume_control"] = player["volume_control"]
            else:
                res["player"]["volume_control"] = True
        except:
            pass
        res['response'] = "OK"
        return json_resp(res)


    if (request.args["devices"] == "detected"): # Do no discover new devices, just check if online
        players = app.players
        for player in players :
            if player["type"] == "upnp":
                addr = player['address']
                try:
                    requests.get(addr, timeout=1)
                    player["online"] = True
                except:
                    player["online"] = False



    if (request.args["devices"] == "detect"): # Discover new devices and check if online for all devices

        players = get_upnp_renderers(app.host)

        for player in players:
            player["type"] = "upnp"
            player["gapless"] = False
            player["volume_control"] = False
    try:
        player = [p for p in app.players if p["id"] == player_id][0]
        res["player"] = {"type": player["type"],"id": player["id"], "name": player["name"]}
        if "player" in player:
            res["player"]["player"] = "Object"

        if  player["type"] == "gstreamer":
            res["player"]["loaded"] = True
            res["player"]["online"] = True

        if "address" in player:
            addr = player['address']
            try:
                requests.get(addr, timeout=1)
                res["player"]["online"] = True
            except:
                res["player"]["online"] = False

        if "volume_control" in player:
            res["player"]["volume_control"] = player["volume_control"]
        else:
            res["player"]["volume_control"] = True
    except:
        pass
    res["players"] = []
    for p in players:
        res["players"].append({
            "id": p["id"],
            "type": p["type"],
            "name": p["name"],
            "volume_control": p["volume_control"] if "volume_control" in p else "without",
            "gapless": p["gapless"] if "gapeless" in p else "without",
            "transcode": p.get("transcode", False),
            "codec": p.get("codec", "mp3"),
            "bitrate": int(p.get("bitrate", 128)),
            "online": p["online"] if "online" in p else "without",
            "address": p.get("address","none"),
            "player": "Objet",
        })
    res["response"] = "OK"
    return json_resp(res)

@app.route('/v1/SetPlayer/<string:id>')
#@app.tokenauth.login_required
def set__player(id):
    res = {}
    for player in app.players:
        if player['id'] == id:
            break
    res["type"] = player["type"]
    try:

        if set_player(app,id) == False:
            res["response"] = "OK"
            res["type"] = player["type"]
            res["id"] = id
            res["name"] = player["name"]
            res["loaded"] = False
            if "volume_control" in player:
                res["volume_control"] = player["volume_control"]
            if "address" in player:
                addr = player['address']
                try:
                    requests.get(addr, timeout=1)
                    res["online"] = True
                except:
                    res["online"] = False
            return json_resp(res)
    except:
        res["response"] = "OK"
        res["type"] = player["type"]
        res["id"] = id
        res["name"] = player["name"]
        res["loaded"] = False
        res["online"] = False
        return json_resp(res)

    try:
        player.set_pipeline()
        player.set_volume(app.volumelevel)
    except:
        pass

    if 'address' in player:
        addr = player['address']
        try:
            requests.get(addr, timeout=1)
            res["online"] = True
        except:
            res["online"] = False

    if app._config["Player"]["last"] != id :
        app._config["Player"]["last"] = id
        p = os.path.join(os.getenv("HOME"), '.Player', 'config', options.config)
        if os.path.isfile(p):
            pass
        else:
            p = os.path.join(os.getenv("HOME"), '.Player', 'config', 'config.ini')
        with open(p, 'w') as configfile:
            app._config.write(configfile)
    res["response"] = "OK"
    res["id"] = player['id']
    res["name"] = player["name"]
    res["loaded"] = True
    if "volume_control" in player:
        res["volume_control"] = player["volume_control"]
    else:
        player["volume_control"] = True
    return json_resp(res)


def set_player(app,id):

    for player in app.players:
        if player['id'] == id:
            break

    if player["type"] == "gstreamer":
        if 'player' not in player:
            player["player"] = GPlayer(app, state_changed, audio_changed, spectrum)
            player["player"].id = id
            player["player"].set_pipeline(app.outputs[app.current_output]['gstpipeline'])
            app.player_id = id
        else:
            pass

    elif player["type"] == "upnp":
        # Toujours réinitialiser
        if 'player' not in player:
            addr = player["address"]

            try:
                requests.get(addr, timeout=1)
                online = True
            except:
                online = False
            if online == True :
                player["player"] = UpnpPlayer(app, state_changed, audio_changed)
                player["player"].id = id
                player["player"].transcode = bool(player.get("transcode", False))
                player["player"].transcode_codec = str(player.get("codec", "mp3")).lower()
                player["player"].transcode_bitrate = int(player.get("bitrate", 128))
                gapless = player.get("gapless",True)
                subscription_callback = getattr(app, 'subscription_callback', '')
                if player["player"].set_device(id, addr, subscription_callback, gapless, reactor) == False :
                    player["player"].id = player["id"]
                    player["player"].name = player["name"]
                    player["player"].loaded = False

        else:
            pass

    else:
        pass

    return True

@app.before_request
def touch_activity():
    global last_activity
    with last_activity_lock:
        last_activity = time.monotonic()
    #logging.debug("Activité détecté ..")


@app.before_first_request
def init():

    app.imported_ids = []
    app.running_saved_queries = []
    app.requestfind = requestfind
    app.updating = None
    app.mute = False
    app.mediafiles_dir = os.path.join(os.getenv("HOME"), '.Player','mediafiles')
    app.docs_dir = os.path.join(os.getenv("HOME"), '.Player', 'docs')

    names = app.db.list_collection_names()
    if not 'mediafiles' in names :
        app.db.create_collection('mediafiles')
    if not 'mediadirs' in names :
        app.db.create_collection('mediadirs')
    if not 'thumbnails' in names:
        app.db.create_collection('thumbnails')
        app.db.thumbnails.create_index('dirhash', default_language='english', language_override="dummy")
        app.db.thumbnails.create_index('last_modified_epoch', default_language='english', language_override="dummy")
    if not 'internals' in names:
        app.db.create_collection('internals')
        app.db.internals.insert_one({"last_scan": "0"}).inserted_id
    if not 'savedqueries' in names:
        app.db.create_collection('savedqueries')


    try:
        app.internals = app.db.internals.find_one()
    except:
        pass
    app.SingleValueTags = app._config['Tags']['singlevalue'].split(',')
    app.OnlyFilesTags = ["_id", "tracknumber","channels","sample_rate","length","bitrate","extension","size", ""]
    indexes = app._config['Tags']['indexes'].split(',')
    indexes.append('dirname')
    indexes.append('dirhash')
    db_indexes = list(app.db.mediafiles.index_information().keys())
    db_indexes = [name.rstrip('_1') for name in db_indexes if name != '_id_']
    missing = [idx for idx in indexes if idx not in db_indexes]
    for index in missing:
        app.db.mediafiles.create_index(index)
        app.db.mediadirs.create_index(index)

    try:
        app.player.set_pipeline()
    except:
        pass
    app.send_message = send_message
    app.send_message_value = send_message_value
    app.change_stream =  ChangeStream(app)
    app.change_stream.start()
    app.plugins_action('server_before_first_request')





@app.route("/v1/Shutdown")
@app.tokenauth.login_required
def shutdown():
    # edit visudo with YOUR_USERNAME_HERE ALL=(ALL) NOPASSWD: ALL
    os.system("sudo shutdown -h now")
    return ""

@app.route("/v1/Goodbye")
@app.tokenauth.login_required
def Goodbye():
    #app.pm.save_pipelines()
    res = {}
    res['response'] = 'OK'
    return json_resp(res)

@app.route("/v1/Cache/ClearQueries")
@app.tokenauth.login_required
def ClearQueriesCache():
    app.db.savedqueries.drop()
    res = {}
    res['response']  = 'OK'
    return json_resp(res )


@app.route("/v1/Playlists/Get")
@app.tokenauth.login_required
def Playlists_Get():
    res = app.playlists
    return json_resp(res)

@app.route('/v1/test')
def test():
    return 'Player server is Running'

@app.route("/")
def home():
    res = render_template("/browse.html")
    return  res

@app.route("/web")
def homeweb():
    res = render_template("/browseweb.html")
    return  res

@app.route("/embded/<dirhash>")
def embded_dirhash(dirhash):
    res = render_template("/embded.html")
    return  res

@app.route("/html/<htmlfile>")
def get_html(htmlfile):
    if htmlfile != "null":
        return render_template("/"+str(htmlfile))
    else:
        return ""

@app.basicauth.verify_password
def verify_password(username, password):
    auth = request.authorization

    def verifypassword(hash, password):
        if hashlib.sha256(password.encode('utf-8')).hexdigest().lower() == hash.lower():
            return True
        else:
            return False
    r = False
    for user in app.users:
        if username == user["name"]:
            r = True
            break


    if r == True:
        r = verifypassword(user['password'], password)
        return r
    else:
        return False


@app.route('/v1/Login')
@app.basicauth.login_required
def login():
    res = {}

    user = request.authorization['username']
    password = request.authorization['password']
    ip = request.remote_addr
    res["ip"] = ip
    parts = app.host.split(".")
    # On same LAN, 1.192.168.1.XX ...
    if ip.startswith(".".join(parts[:3])):
        location = "local"
    else:
        location = "external"
    
    if app.host.startswith("172"):
        location = "docker"

    res["location"] = location
    try:

        def get_user_by_name( name):
            for user in app.users:
                if user['name'] == name:
                    return user

        token = app.jwt.dumps({'username': get_user_by_name(user)["password"]})
        res["user"]=app.tokenauth.username()
        res["token"] = str(token.decode('UTF-8'))
        res["isAdmin"] = get_user_by_name(user)["isAdmin"]
        res["response"] = "OK"
        app.bearers.append({res["token"]:res["user"]})
    except:
        res["response"] = "Error in login : {user:token} required "
        return json_resp(res)
    return json_resp(res)

@app.tokenauth.verify_token
def verify_token(token):
    g.user = None
    try:
        data = app.jwt.loads(token)
    except:
        return False
    if 'username' in data:
        g.user = data['username']
        return True
    return False

@app.route("/v1/Ports")
@app.tokenauth.login_required
def send_ip():
    res = {}
    res['response'] = "OK"
    res['hostname']  = socket.gethostname()
    res['ip'] = get_adresse_ip_locale()
    res['httpport'] = app._config['Server']['httpport']
    res['wsport'] = app._config['Server']['wsport']
    res['mongodb'] =app.mongo_addr
    res['server'] = app._config['Server']['server']
    app.server_mode = res['server']
    return json_resp(res )

def adminlogrequired(func):
    @wraps(func)
    def admin_check(*args, **kwargs):
        try:
            b = request.headers.environ['HTTP_AUTHORIZATION'].replace('Bearer ', '')
        except:
            return abort(401) #No autorization ..
        r = False
        for bearer in app.bearers:
            if b in bearer:
                user = bearer.get(b)
                for u in app.users:
                    if u["name"] == user:
                        if u["isAdmin"] == True:
                            r = True
                            break
        if r == True:
            return func(*args, **kwargs)
        else:
            # access denied
            return abort(401)
    return admin_check


@app.route("/v1/Menu/Get")
#@app.tokenauth.login_required

def menu():
    res = {}
    menu = {}

    if 'file' in request.args :
        file = request.args['file']
        if not file.endswith(".json"):
            file += ".json"

        v = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config")), file)
        if os.path.exists(v):
            with open(v) as f:
                menu = json.load(f)
        else:
                v = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config")), 'views.json')
                with open(v) as f:
                    menu = json.load(f)
    else:
        v = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config")),'views.json')
        with open(v) as f:
            menu = json.load(f)


    v =  os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Podcasts"))
    podcasts = []
    files = sorted([file for file in glob.glob(os.path.join(v,"*.opml"))])
    for file in files:
        if os.path.isfile(file):
            podcasts.append({ "name": os.path.splitext(os.path.basename(file))[0],"file":os.path.basename(file)})
    menu['podcast'] = podcasts

    v =  os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Radios"))
    radios= []
    files = sorted([file for file in glob.glob(  os.path.join(v,"*.xspf"))])
    for file in files:
        if os.path.isfile(file):
            radios.append({ "name":os.path.splitext(os.path.basename(file))[0] ,"file":os.path.basename(file) })
    menu['radios'] = radios
    v = os.path.join(os.path.join(os.getenv("HOME"), ".Player", "mediafiles", "Playlists"))

    playlists= []
    files = sorted([file for file in glob.glob(  os.path.join(v,"*.xspf"))])
    for file in files:
        if os.path.isfile(file):
            playlists.append({ "name":os.path.splitext(os.path.basename(file))[0],"file":os.path.basename(file)})
    menu['playlists'] = playlists
    return json_resp(menu)


@app.route('/v1/Players/Set', methods=['POST'])
def save_players():
    if 'players_file' not in request.files or 'filename' not in request.form:
        return json_resp({"error": "Missing parameters"}), 400

    file = request.files['players_file']
    filename = request.form['filename']

    try:
        # Vérifier que le fichier est un .json
        if not filename.endswith(".json"):
            return json_resp({"error": "Only .json files are allowed"}), 400

        # Lire le contenu et parser pour vérifier la validité JSON
        content = file.read().decode("utf-8")
        players_json = json.loads(content)  # Lève une exception si invalide
        players_json["players"].insert(0,  {"id": "0", "type": "gstreamer", "name": "Interne","volume_control":True,"gapless":True})
        # Enregistrer le fichier dans ~/.Player/config
        config_dir = os.path.join(os.path.expanduser("~"), ".Player", "config")
        os.makedirs(config_dir, exist_ok=True)
        filepath = os.path.join(config_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(players_json, f, indent=2, ensure_ascii=False)

        incoming = players_json.get("players", [])

        # Indexer les players actuels par (id, type) pour recherche rapide
        existing_map = {}
        for p in getattr(app, "players", []):
            if p.get("address"):
                key = (p.get("type"), p.get("address"))
            else:
                key = (p.get("type"), p.get("name"))
            existing_map[key] = p

        # Pour générer de nouveaux ids sans collision : chercher le max numérique existant si possible
        def make_new_id():
            existing_ids = []
            for p in getattr(app, "players", []):
                try:
                    existing_ids.append(int(p.get("id")))
                except Exception:
                    pass
            next_id = max(existing_ids) + 1 if existing_ids else 0
            # s'assurer que ce next_id n'est pas déjà utilisé (au cas où certains ids ne sont pas numériques)
            used = {p.get("id") for p in getattr(app, "players", [])}
            while str(next_id) in used:
                next_id += 1
            return str(next_id)

        new_list = []

        for pdata in incoming:
            # déterminer clé de matching comme ci-dessus (sans se fier à pdata["id"])
            if pdata.get("address"):
                key = (pdata.get("type"), pdata.get("address"))
            else:
                key = (pdata.get("type"), pdata.get("name"))

            if key in existing_map:
                existing = existing_map.pop(key)  # on le consomme
                # Mettre à jour les champs sauf "id" et en préservant "player" s'il y est
                for field, value in pdata.items():
                    if field in ("id",):  # ignorer l'id entrant
                        continue
                    existing[field] = value
                existing.setdefault("saved", "yes")
                new_list.append(existing)
            else:
                # nouvel item : lui assigner un id unique
                entry = pdata.copy()
                entry["id"] = make_new_id()
                entry.setdefault("saved", "yes")
                new_list.append(entry)

        # for leftover in existing_map.values():
        #     new_list.append(leftover)

        old_players_by_id = {
            str(p.get("id")): p for p in getattr(app, "players", [])
            if isinstance(p, dict) and "id" in p
        }

        for player in new_list:
            old_player = old_players_by_id.get(str(player.get("id")))
            if old_player and "player" in old_player:
                player["player"] = old_player["player"]
                player["saved"] = "yes"

        app.players = new_list

        for p in app.players:
            if p.get("type") == "upnp" and "player" in p and hasattr(p["player"], "transcode"):
                p["player"].transcode = bool(p.get("transcode", False))
                p["player"].transcode_codec = str(p.get("codec", "mp3")).lower()
                p["player"].transcode_bitrate = int(p.get("bitrate", 128))

        if hasattr(app, "player_id") and app.player_id:
            current_player = next((p for p in app.players if str(p.get("id")) == str(app.player_id)), None)
            if current_player is not None:
                if "player" not in current_player or current_player["player"] is None:
                    set_player(app, current_player["id"])
                app.player = next((p.get("player") for p in app.players if str(p.get("id")) == str(app.player_id)), None)
            else:
                app.player = None
        else:
            app.player = None

        return json_resp({"status": "OK", "saved_to": filepath})

    except Exception as e:
        return json_resp({"error": str(e)}), 500

@app.route('/v1/Menu/Set', methods=['POST'])
def save_menu():
    if 'menu_file' not in request.files or 'filename' not in request.form:
        return json_resp({"error": "Missing parameters"}), 400

    file = request.files['menu_file']
    filename = request.form['filename']

    try:
        # Vérifier que le fichier est un .json
        if not filename.endswith(".json"):
            return json_resp({"error": "Only .json files are allowed"}), 400

        # Lire le contenu et parser pour vérifier la validité JSON
        content = file.read().decode("utf-8")
        menu_json = json.loads(content)  # Lève une exception si invalide

        # Enregistrer le fichier dans ~/.Player/config
        config_dir = os.path.join(os.path.expanduser("~"), ".Player", "config")
        os.makedirs(config_dir, exist_ok=True)
        filepath = os.path.join(config_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(menu_json, f, indent=2, ensure_ascii=False)

        return json_resp({"status": "OK", "saved_to": filepath})

    except Exception as e:
        return json_resp({"error": str(e)}), 500

def AlbumStats(dirhash):
    """Get stats from an album
    """
    length = 0
    cursor = app.db.mediafiles.find({'dirhash': dirhash})
    cursor = [x for x in cursor]
    track_nbrs = len(cursor)
    for i in cursor:
        length += i.get('length', 0)
    return { 'length': length, 'track_nbrs' :track_nbrs}


@app.route("/v1/Library/Search")
@app.tokenauth.login_required
def LibrarySearch():
    res = {}
    try:
        if 'field' in request.args and 'value' in request.args and 'query' in request.args:
            field =  request.args['field']
            value = request.args['value'] # MUST be a string
            query =eval(urllib.parse.unquote(request.args['query']))

            result = app.db.mediadirs.aggregate(
                [
                {'$match': query},
                {'$match': { field: { '$regex': value,'$options': 'i'   }}},
                {'$group': {'_id': {'search_field': '$' + field, 'dirhash': '$dirhash', 'artist': '$artist', 'album': '$album'},'count': {'$sum': 1}}}
            ])

            if  field == "artist":
                sorted_dictionaries = sorted([doc for doc in result], key=lambda x:(x['_id']['artist'][0], x['_id']['album']))
            elif  field == "album":
                sorted_dictionaries = sorted([doc for doc in result], key=lambda x: x['_id']['album'])
            elif  field == "title":
                sorted_dictionaries = sorted([doc for doc in result], key=lambda x:(x['_id']['artist'][0], x['_id']['album']))
            else :
                sorted_dictionaries = sorted([doc for doc in result], key=lambda x: x['_id']['album'])

            res['Result'] = sorted_dictionaries
            res['Response'] = 'OK'
            res['field'] = field
    except:
        res['Response'] = 'Error'
    return json_resp(res)

@app.route("/v1/Player/Radio")
@app.tokenauth.login_required
def radiomode():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if "query" in request.args:
        cursor = app.db.mediafiles.find(eval(urllib.parse.unquote(request.args["query"]))) #.limit(10000)
    if "ids" in request.args:
        ids = urllib.parse.unquote(request.args["ids"]).split(";")
        ids = [ObjectId(id) for id in ids]
        cursor = app.db.mediafiles.find({"_id": {"$in": ids}})
    cursor = list(cursor)
    GetPlayer(player_id).set_queue([])
    length = len(cursor)
    j = 0
    for i in random.sample(range(0,length), min(length-1,1000)) :
        try:
            cursor[i]['_id'] = str(cursor[i]['_id'])
            cursor[i]['file'] = os.path.join(app.mediafiles_dir, cursor[i]['dirname'], cursor[i]['filename'] + '.' + cursor[i]['extension'])
            GetPlayer(player_id).append_queue(cursor[i])
            j+=1
            if j ==100:
                break
        except:
            pass

    GetPlayer(player_id).set_stop()
    GetPlayer(player_id).set_queue_position(0)
    GetPlayer(player_id).set_path(GetPlayer(player_id).get_current(),GetPlayer(player_id).queue_position)
    GetPlayer(player_id).set_play()
    res = {'Response': 'OK'}
    queue_changed( GetPlayer(player_id).id,'radiomode')
    return json_resp(res)


@app.route("/v1/Player/DSP/Get")
@app.tokenauth.login_required
def dsp_get():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    dsps = eval( urllib.parse.unquote(request.args['props']))
    for dsp in dsps:
        for prop in dsp['props'] :
            try:
                prop['value'] = GetPlayer(player_id).get(dsp['name'], prop['name'])
            except:
                pass

    # Fill app.pm.pipeline
    for dsp in dsps:
        for el in app.pm.pipeline:
            if 'name' in el:
                if dsp['name'] == el['name']:
                    el['props'] = dsp['props']

    res = {'Response':'OK', 'pipeline' : app.pm.pipeline}
    return json_resp(res)

#TODO:POST
@app.route("/v1/Player/DSP/Set")
@app.tokenauth.login_required
def dsp_set():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if is_number(request.args['value']) == True:
        val = float(request.args['value'])
    if BoolStr(request.args['value']) is not None:
        val = BoolStr(request.args['value'])

    GetPlayer(player_id).set(request.args['name'], request.args['property'], val)
    res = {'Response':'OK', 'pipeline' : app.pm.pipeline}

    dsp_changed(player_id)
    return json_resp(res)

@app.route("/v1/Player/Next")
@app.tokenauth.login_required
def Next():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    GetPlayer(player_id).set_next()
    res =  _info(GetPlayer(player_id))
    return json_resp(res)

@app.route("/v1/Player/Previous")
@app.tokenauth.login_required
def Previous():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    GetPlayer(player_id).set_previous()
    res =  _info(GetPlayer(player_id))
    return json_resp(res)

@app.route("/v1/Player/Seek/Set")
@app.tokenauth.login_required
def Set():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    state = GetPlayer(player_id).get_state()
    if 'SeekAt' in request.args:
        seek_ns = 1000000 * int(request.args['SeekAt'])
        ready  = GetPlayer(player_id).playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)
        sleep(.3) #Wait for the seek to occur

    if 'SeekForward' in request.args:
        pos_to_seek = int(GetPlayer(player_id).playbin.query_position(Gst.Format.TIME)[1]) + int(request.args['SeekForward'])*1000000
        duration = int(GetPlayer(player_id).playbin.query_duration(Gst.Format.TIME)[1])
        if pos_to_seek  < duration - int(request.args['SeekForward'])*1000000 :
            ready = GetPlayer(player_id).playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, pos_to_seek)
            sleep(.3)  # Wait for the seek to occur

    if 'SeekBackward' in request.args:
        pos_to_seek = int(GetPlayer(player_id).playbin.query_position(Gst.Format.TIME)[1]) - int(request.args['SeekBackward'])*1000000
        if pos_to_seek  > 0 :
            ready = GetPlayer(player_id).playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, pos_to_seek)
            sleep(.3)  # Wait for the seek to occur

    res ={}
    state_changed(None)
    res =  _state(GetPlayer(player_id))
    return json_resp(res)

@app.route("/v1/Player/RestartQueue")
@app.tokenauth.login_required
def Restartqueue():
    '''
    Set the restart queue
    '''
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    if 'val' in request.args:
        app.restartqueue = BoolStr(request.args['val'])
    state_changed(None)
    res =  _state(GetPlayer(player_id))
    return json_resp(res)

@app.route("/v1/Player/Volume/Get")
@app.tokenauth.login_required
def Volume_Get():
    res = {}
    res["response"] = "OK"
    try:
        res["volume"] = app.volumelevel
    except:
        res["volume"] = 0
    return json_resp(res)

@app.route("/v1/Player/Volume/Set")
@app.tokenauth.login_required
def Volume_Set():
    '''
    Set the volume in a range of 0 - 1
    '''
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    if 'val' in request.args:
        val =float(request.args['val'])
        # Set the volume
        send_message_value('vol changed', round(val, 2))
        if app.mute == False:
            GetPlayer(player_id).set_volume(float(val))
            app.volumelevel = round(float(val),2)
        res['volume'] = round(float(request.args['val']),2)

    if 'mute' in request.args:
        if request.args['mute'] == 'true':
            app.mute = True
            app.volumelevel = GetPlayer(player_id).get_volume()
            GetPlayer(player_id).set_volume(0)

        if request.args['mute'] == 'false':
            app.mute = False
            GetPlayer(player_id).set_volume(app.volumelevel)
        send_message_value('mute changed', app.mute)

    res = {}
    res["response"] = "OK"
    res["volume"] = app.volumelevel
    return json_resp(res)

@app.route("/v1/Player/CurrentPosition")
@app.tokenauth.login_required
def CurrentPosition():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    res["response"] = "OK"
    try:
        if len(GetPlayer(player_id).queue)>0:
            p= GetPlayer(player_id).get_current()
            if "dirhash" in p :
                res['dirhash'] = p["dirhash"]
            if "_id" in p:
                res['_id'] = p["_id"]
            if 'covers' in p:
                res['covers'] = p["covers"]
            res['position'] = GetPlayer(player_id).get_position()
            res['duration'] = GetPlayer(player_id).get_duration()
            res['state'] = GetPlayer(player_id).get_state()
    except:
        res["response"] = "Error"
    return json_resp(res)

@app.route("/v1/Scanning")
@app.tokenauth.login_required
def Scanning():
    res = {}
    res['scanning'] = app.updating
    res['response'] = 'OK'
    return res

@app.route("/v1/Player/TrackInfo")
@app.tokenauth.login_required
def TrackInfo():
    """Compute display for a given id """
    id = urllib.parse.unquote(request.args["id"])
    displaystr = ""
    separator = ", "
    if 'displaystr' in request.args:
        displaystr = request.args['displaystr']

    if 'separator' in request.args:
        separator = request.args['separator']

    cursor = app.db.mediafiles.find({'_id': ObjectId(id)})
    file = cursor[0]
    d = clean(replacetags(displaystr, file, separator))
    res = {}
    res['display'] = d
    res['response'] = "OK"
    return json_resp(res)

@app.route("/v1/Player/CurrentTrack")
@app.tokenauth.login_required
def Info():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    displaystr = ""
    separator = ", "
    if 'displaystr' in request.args:
        displaystr = request.args['displaystr']

    if 'separator' in request.args:
        separator = request.args['separator']
    try:
        res = _info(GetPlayer(player_id),displaystr=displaystr, separator = separator)
    except:
        res =""

    return json_resp(res)

def _info(player,displaystr ="", separator= ", "):
    # Long polling - seek info, position from player
    res = {}
    res['display'] = ""
    try:
        current_file =player.get_current()
    except:
        res['response'] = 'Error'
        return res

    d = clean(replacetags(displaystr, current_file, separator ))

    res['display'] = clean(d)
    res['queue_position'] =   player.queue_position
    res['queue_length'] =   int(len(player.queue) - 1)

    if len(player.queue)>0:
        try:
            p = player.get_current()
        except:
            pass
        if 'dirhash' in p:
            res['dirhash'] = p['dirhash']
        if '_id' in p:
            res['_id'] = p["_id"]
        if 'covers' in p:
            res['covers'] = p["covers"]
        res['state'] = player.get_state()
    res['duration'] = int(float(player.get_current()["length"]) * 1000)
    res['mute'] = StrBool(app.mute)
    res['volume'] =player.get_volume()
    app.volume = res['volume']
    res['scanning'] = app.updating
    res['restartqueue'] = app.restartqueue
    res['response'] = 'OK'
    return res

@app.route("/v1/Player/State")
@app.tokenauth.login_required
def State():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res ={}
    res =  _state(GetPlayer(player_id))
    return json_resp(res)

def _state(player):
    # Long polling - seek info, position from player
    res = {}
    if player == None:
        return res
    res['queue_position'] =   player.queue_position
    res['queue_length'] =   int(len(player.queue) - 1)
    if len(player.queue)>0:
        res['playing'] = player.get_current()
        res['position'] = player.get_position()
        res['duration'] = player.get_duration()
    res['mute'] = StrBool(app.mute)

    try:
        res['state'] = player.get_state()
    except:
        pass
    res['restartqueue'] = app.restartqueue
    return res

@app.route("/v1/Queue/Get")
@app.tokenauth.login_required
def get_queue():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if GetPlayer(player_id) == None:
        return abort(404)
    if 'displaystr' in request.args:
        for item in GetPlayer(player_id).queue:
            item["display"] =replacetags(request.args["displaystr"],item, ', ')
    return json_resp({"queue": GetPlayer(player_id).queue, "position": GetPlayer(player_id).queue_position})

@app.route("/v1/Queue/Clear")
@app.tokenauth.login_required
def clear_queue():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    if 'ids' in request.args:
        indexes = [int(x) for x in request.args['ids'].split(';')]
        for i in sorted(indexes, reverse=True):
            del GetPlayer(player_id).queue[i]
            if i == GetPlayer(player_id).queue_position :
                GetPlayer(player_id).set_pause()
            if i < GetPlayer(player_id).queue_position :
                GetPlayer(player_id).set_queue_position( GetPlayer(player_id).queue_position - 1)
    else:
        GetPlayer(player_id).queue_position = 0
        GetPlayer(player_id).queue = []
        GetPlayer(player_id).set_stop()

    if int(GetPlayer(player_id).playbin.get_state(0)[1]) == 1:
        res['state'] = 'stopped'
    if int(GetPlayer(player_id).playbin.get_state(0)[1]) == 4:
        res['state'] = 'playing'
    if int(GetPlayer(player_id).playbin.get_state(0)[1]) == 3:
        res['state'] = 'paused'
    queue_changed(GetPlayer(player_id).id,'clear')
    res["queue"] = GetPlayer(player_id).queue
    res["position"]=  GetPlayer(player_id).queue_position
    return json_resp(res)

@app.route("/v1/Queue/Delete")
@app.tokenauth.login_required
def queue_delete():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if 'id' in request.args :
        id = int(request.args["id"])
        queue = GetPlayer(player_id).queue
        if id != GetPlayer(player_id).queue_position:
            queue.pop(id)
        if id < GetPlayer(player_id).queue_position:
            GetPlayer(player_id).set_queue_position(GetPlayer(player_id).queue_position -1)

        GetPlayer(player_id).queue = queue
        queue_changed(GetPlayer(player_id).id, 'delete')
        res = {"result": "OK", "queue" : GetPlayer(player_id).queue, "position": GetPlayer(player_id).queue_position}
    else:
        res = {"result": "Error"}
    return json_resp(res)

@app.route("/v1/Queue/Move")
@app.tokenauth.login_required
def queue_move():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if 'from' in request.args and 'to' in request.args:
        id_from = int(request.args["from"])
        id_to = int(request.args["to"])
        queue = GetPlayer(player_id).queue
        item = queue[id_from]
        if  id_from < id_to :
            queue.pop(id_from)
            queue.insert(id_to-1, item)
        if  id_from > id_to :
            queue.pop(id_from)
            queue.insert(id_to, item)

        # Set GetPlayer(player_id).queue_position
        if id_from == GetPlayer(player_id).queue_position : # move current playing
            if id_from < id_to:
                GetPlayer(player_id).queue_position = id_to-1;
            if id_from > id_to:
                GetPlayer(player_id).queue_position = id_to;

        elif id_from < GetPlayer(player_id).queue_position and GetPlayer(player_id).queue_position < id_to:
            GetPlayer(player_id).set_queue_position(GetPlayer(player_id).queue_position -1);

        elif id_from > GetPlayer(player_id).queue_position and GetPlayer(player_id).queue_position >= id_to:
            GetPlayer(player_id).set_queue_position(GetPlayer(player_id).queue_position +1);
        else:
            pass
        GetPlayer(player_id).queue = queue
        queue_changed(GetPlayer(player_id).id, 'move')
        res = {"result": "OK", "queue" : GetPlayer(player_id).queue, "position": GetPlayer(player_id).queue_position}

    else:
        res = {"result": "Error"}
    return json_resp(res)

@app.route("/v1/Queue/Add")
@app.tokenauth.login_required
def queue_add():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    action =''
    app.addqueue = True
    player = GetPlayer(player_id)
    try:
        # For UnP Players NOT online at startup
        player.set_volume(app.volumelevel)

    except:
        pass

    if 'clear' in request.args:
        if request.args["clear"] == 'true':
            player.set_queue_position(0)
            player.set_queue([])
            res['state'] = player.get_state()

    if 'ids' in request.args:
        q = urllib.parse.unquote(request.args["ids"]).split(";")
        for id in q:
            cursor = app.db.mediafiles.find({'_id': ObjectId(id)})
            file =cursor[0]
            file['_id'] = str(file['_id'])
            file['file'] = os.path.join(app.mediafiles_dir, file['dirname'], file['filename'] + '.' + file['extension'])
            player.append_queue(file)
        res = {"result": "OK"}

    if 'query' in request.args:
        q = eval(urllib.parse.unquote(request.args["query"]))
        cursor = app.db.mediafiles.find(q).sort([("album", ASCENDING),("discnumber", ASCENDING) ,("tracknumber", ASCENDING)])
        i =0  # No more than 100 files ..
        for file in cursor:
            i +=1
            file['_id'] = str(file['_id'])
            try:
                file['file'] = os.path.join(app.mediafiles_dir, file['dirname'], file['filename'] + '.' + file['extension'])
            except:
                i-=1
            if i >100:
                break
            player.append_queue(file)
        res = {"result": "OK"}

    elif 'dirhash' in request.args:
        s = json.loads(urllib.parse.unquote(request.args["dirhash"]))
        fs = []
        cursor = app.db.mediafiles.find({'dirhash' : int(s)})
        for file in cursor:
            file['_id'] = str(file['_id'])
            file['file'] = os.path.join(app.mediafiles_dir, file['dirname'], file['filename'] + '.' + file['extension'])
            fs.append(file)
        fs = sorted(fs, key=lambda k: 1000 * to_int(k.get("discnumber", 0)) + to_int(k.get("tracknumber", 0)))
        player.queue.extend(fs)
        res = {"result": "OK"}

    elif 'stream' in request.args:
        app._id += 1
        file = {}
        file['_id'] = str(app._id)
        file['uri'] = request.args['stream']
        if 'title' in request.args:
            l=  []
            l.append(request.args['title'])
            file['title'] = l
        if 'cover' in request.args:
            l=  []
            l.append(request.args['cover'])
            file['covers'] = l
        if 'length' in request.args:
            file['length'] = float(request.args['length']) *1.0
        else:
            file['length'] = 0
        player.append_queue(file)
        res = {"result": "OK"}

    if 'play' in request.args:
        if request.args["play"] == 'true' :
            GetPlayer(player_id).set_queue_position(0)
            _play(player.id, fromqueueadd = True)

    res["queue"] = GetPlayer(player_id).queue
    res["position"] = GetPlayer(player_id).queue_position
    queue_changed(GetPlayer(player_id).id,'add')
    return json_resp(res)

@app.route("/v1/Player/Stop")
@app.tokenauth.login_required
def Stop():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    GetPlayer(player_id).playbin.set_property("uri","")
    time.sleep(.1)
    GetPlayer(player_id).set_stop()
    res = {"result": "OK"}
    return json_resp(res)

@app.route("/v1/Player/Play")
@app.tokenauth.login_required
def Play():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    res = {}
    _play(player_id)
    res = _info(GetPlayer(player_id))
    return json_resp(res)

def get_uri_from_path(dic,position = None):
    path= dic['file']
    os.chdir(app.root_path)
    f =urllib.parse.quote(os.path.abspath(path))
    uri = f.replace("file://", "")
    p = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
    h = app.http_server_adr
    uri = uri.replace(p, h)
    print(f"set_uri: {uri}")
    return uri

def _play(player_id,fromqueueadd = False):
    res = {}
    time.sleep(.5)
    GetPlayer(player_id)
    if 'id' in request.args:
        GetPlayer(player_id).set_stop()
        GetPlayer(player_id).set_queue_position(int(request.args['id']))
        if 'file' in GetPlayer(player_id).get_current():
            GetPlayer(player_id).set_path(GetPlayer(player_id).get_current(),int(GetPlayer(player_id).queue_position))
        elif 'uri' in GetPlayer(player_id).get_current():
            GetPlayer(player_id).set_uri(GetPlayer(player_id).get_current(),int(GetPlayer(player_id).queue_position))
        else:
            pass
        GetPlayer(player_id).set_play()

    elif 'stream' in request.args:
        stream = urllib.parse.unquote(request.args['stream'])
        app.stream = stream
        GetPlayer(player_id).set_stop()
        GetPlayer(player_id).set_queue([])
        ap = {}
        ap["uri"] = stream
        app._id += 1
        ap["_id"] = str(app._id)
        ap['length'] = 0
        if 'cover' in request.args:
            cover = urllib.parse.unquote(request.args['cover'])
            ap['covers'] = []
            ap['covers'].append(cover)
        if 'length' in request.args:
            ap['length'] = float(request.args['length'])
        if 'title' in request.args:
            l = []
            l.append(request.args['title'])
            ap['title'] = l
        GetPlayer(player_id).append_queue(ap)
        GetPlayer(player_id).set_queue_position(0)
        GetPlayer(player_id).set_uri(ap)
        GetPlayer(player_id).set_play_uri()
        time.sleep(.1)
        GetPlayer(player_id).set_play()
    else:
        # without args
        if fromqueueadd == True:
            GetPlayer(player_id).set_stop()
            time.sleep(.5)

        if len(GetPlayer(player_id).queue) > 0:
            if GetPlayer(player_id).get_state() != 'playing': # Not playing

                if 'file' in GetPlayer(player_id).get_current():
                    GetPlayer(player_id).set_path(GetPlayer(player_id).get_current())
                elif 'uri' in GetPlayer(player_id).get_current():
                    GetPlayer(player_id).set_uri(GetPlayer(player_id).get_current())
                GetPlayer(player_id).set_play()  #  play/pause button

            else: # playing : set pause ...
                if 'file' in GetPlayer(player_id).get_current():
                    # file
                    GetPlayer(player_id).set_pause()
                    return
                if 'uri' in GetPlayer(player_id).get_current():
                    if 'http' in GetPlayer(player_id).get_current()['uri']:
                        if int(GetPlayer(player_id).get_current()['length']) != 0:
                            # podcast
                            GetPlayer(player_id).set_stop()
                        else:
                            # radio
                            GetPlayer(player_id).set_pause()
                else:
                    GetPlayer(player_id).set_pause() #  play/pause button
    res =  _info(GetPlayer(player_id))
    return json_resp(res)

@app.route("/v1/Mediafile/<media>/<filename>")
def get_mediafile(media,filename):
    '''
    Get the image with the file path
    :param media:
    :param filename:
    :return:
    '''
    fp = os.path.join(app.mediafiles_dir,media,filename)
    if os.path.exists(fp):
        if fp.endswith(( '.jpg', '.jpeg')):
            return send_file(fp, mimetype='image/jpeg')
        elif fp.endswith(('.png')):
            return send_file(fp, mimetype='image/png')
    else:
        return abort(404)

@app.route("/v1/SideFiles")
@app.tokenauth.login_required

def get_files_list():
    '''
    Get additionnal files (images and markdown)
    :param dirhash:
    :return:
    '''
    res = []
    if  app._config['HttpServer']['activate'] == "True":
        if "query" not in request.args : return json_resp([])
        q = eval(urllib.parse.unquote(urllib.parse.unquote(request.args["query"])))
        cursor = app.db.mediafiles.find_one(q)
        if cursor is not None :
            res = getfiles(cursor['dirname'])
            if "images" in res:
                res["images"] = ["/" +  str(cursor['dirhash']) + "/"+ f for f in res["images"]]
            return json_resp(res)
        else:
            return json_resp([])
    else:
        addr = app.http_server_adr + "/v1/SideFiles?query=" + request.args["query"]
        headers = {'Authorization': "Bearer {}".format(app.token)}
        r =  requests.get(addr, headers=headers)
        js = json.loads(r.text)
        return js

@app.route("/v1/SideFile/<dirhash>/<folder>/<filename>")
def get_file2(dirhash,folder,filename):
    if app._config['HttpServer']['activate'] == "True":
        os.chdir(app.root_path)
        res = {}
        res["response"] = "OK"
        cursor = app.db.mediafiles.find_one({'dirhash': int(dirhash)})
        folder1 = os.path.join(app.mediafiles_dir, cursor['dirname'])
        fname = os.path.join(folder1,folder,filename)
        fname = os.path.realpath(fname)
        if 'thumbnail' in request.args:
            im = Image.open(fname)
            size = int(request.args['thumbnail']), int(request.args['thumbnail'])
            im.thumbnail(size, Image.ANTIALIAS)
            buffered = BytesIO()
            im.convert('RGB').save(buffered, format="JPEG")
            buffered.seek(0)
            return send_file(buffered, mimetype='image/jpeg')
        else:
            return send_file(fname, mimetype='image/jpeg',cache_timeout=1)
    else:
        addr = app.http_server_adr + "/v1/SideFile/" + dirhash +"/" + folder + "/" + filename
        if 'thumbnail' in request.args:
            addr = addr + "?thumbnail=" + request.args['thumbnail']
        headers = {'Authorization': "Bearer {}".format(app.token)}
        r = requests.get(addr, headers=headers, stream=True)
        if r.status_code == 404 :
            return abort(404)
        else:
            return r.content


@app.route("/v1/SideFile/<dirhash>/<filename>")
def get_file(dirhash,filename):
    os.chdir(app.root_path)
    res = {}
    res["response"] = "OK"
    cursor = app.db.mediafiles.find_one({'dirhash': int(dirhash)})
    folder = os.path.join(app.mediafiles_dir, cursor['dirname'])
    fname = os.path.join(folder,filename)
    fname = os.path.realpath(fname)
    return send_file(fname, mimetype='image/jpeg',cache_timeout=1)

@app.route("/v1/Web/Assets/<file>")
def get_assets(file):
    p = os.path.dirname(sys.argv[0])  +'/web/static/assets/'+file
    if os.path.exists(p):
        return send_file(p, mimetype='image/jpeg')


@app.route("/v1/Thumbnails/Epoch")
def thumb_epoch():
    res = []
    try:
        q = app.db.thumbnails.find({'last_modified_epoch': {'$gt': round(time.time()) - 60*60*24}}) # Last Day
        for thumb in q:
            res.append(thumb['dirhash'])
        return json_resp(res)
    except :
        return json_resp({"Response":"Error"})

@app.route("/v1/Thumbnails/<dirhash>.jpg")
def thumb(dirhash):
    try:
        q = app.db.thumbnails.find_one({'dirhash': int(dirhash)})
    except:
        return abort(404)
    if q != None:
        if 'cover_256' in q :
            b = BytesIO(base64.b64decode(q['cover_256']))
            b.seek(0)
            return send_file(b, mimetype='image/jpeg')
        else:
            return abort(404)
    else:
        return abort(404)

@app.route("/v1/Covers/<dirhash>.jpg")
def cover(dirhash):
    if app._config['HttpServer']['activate'] == "True":

        try:
            q = app.db.thumbnails.find_one({'dirhash': int(dirhash)})
        except:
            return abort(404)
        if 'path' in q :
            p = os.path.join(os.getenv("HOME"), '.Player', "mediafiles",q['path'])
            if os.path.exists(p):
                if 'thumbnail' in request.args:
                    im = Image.open(p)
                    size = int(request.args['thumbnail']), int(request.args['thumbnail'])
                    im.thumbnail(size, Image.ANTIALIAS)
                    buffered = BytesIO()
                    im.convert('RGB').save(buffered, format="JPEG")
                    buffered.seek(0)
                    return send_file(buffered, mimetype='image/jpeg')
                else:
                    return send_file(p, mimetype='image/jpeg')
            else:
                # return thumbnail if file is missing ...
                q = app.db.thumbnails.find_one({'dirhash': int(dirhash)})
                if q != None:
                    if 'cover_256' in q:
                        b = BytesIO(base64.b64decode(q['cover_256']))
                        b.seek(0)
                        return send_file(b, mimetype='image/jpeg')
                    else:
                        return abort(404)
                else:
                    return abort(404)
        else:
            return abort(404)
    else:
        addr = app.http_server_adr + "/v1/Covers/" + dirhash + ".jpg"
        req = requests.get(addr, headers={'Authorization': "Bearer {}".format(app.token)}, stream=True)
        if req.status_code == 404 :
            return abort(404)
        else:
            buffered  =io.BytesIO( req.content)
            if 'thumbnail' in request.args:
                buffered.seek(0)
                im = Image.open(buffered)
                size = int(request.args['thumbnail']), int(request.args['thumbnail'])
                im.thumbnail(size, Image.ANTIALIAS)
                buffered = BytesIO()
                im.convert('RGB').save(buffered, format="JPEG")
                buffered.seek(0)
                return send_file(buffered, mimetype='image/jpeg')
            else:
                return send_file(buffered, mimetype='image/jpeg')

@app.route("/v1/Library/CreateIndexes")
@app.tokenauth.login_required
def create_indexes():
    res = {}
    #app.db.mediafiles.drop_indexes()
    try:
        app.db.mediafiles.create_index([("dirname", ASCENDING), ("filename", ASCENDING), ("extension", ASCENDING)],unique=True)
    except:
        pass
    if ('indexes' in request.args) :
        indexes = request.args['indexes'].split(',')
        for index in indexes:
            try:
                app.db.mediafiles.create_index(index)
            except:
                pass
    res['Response'] = 'OK'
    return json_resp(res)


@app.route("/v1/Library/Radio/Get")
@app.tokenauth.login_required
def get_radio():
    res = []
    if 'file' in request.args :
        r = []
        dict = {}
        directory = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles','Radios')
        os.chdir(app.root_path)
        os.chdir(directory)
        try:
            ra = parseFile(directory  + "/" + request.args["file"] )
        except:
            ra = []
            res = {"result": "Error"}
            return json_resp({'items': res})
        for radio in ra['tracklist']:
            item = {}
            if 'title' in radio:
                item['display'] = urllib.parse.unquote(radio['title'])
                item['title'] = urllib.parse.unquote(radio['title'])
            item["cover"] = False
            if 'image'in radio:
                addr = request.host_url.replace("localhost",app.host)
                item['covers'] =[urllib.parse.unquote(addr +'v1/Mediafile/Radios/'+radio['image'])]
                item["cover"] = True
            if 'location'in radio:
                item['url'] = urllib.parse.unquote(radio['location'])
            item['type'] = 'radio'
            item['length'] = 0
            r.append(item)
        res = r
        app.radios = res

        return json_resp( {'items':res})

@app.route("/v1/Library/Playlist/Get")
@app.tokenauth.login_required
def get_playlist():
    res = []
    if 'name' in request.args :
        r = []
        dict = {}
        directory = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles','Playlists')
        os.chdir(app.root_path)
        os.chdir(directory)
        files = [file for file in glob.glob("*.xspf")]
        for file in files:
            if os.path.splitext(os.path.basename(file))[0] ==request.args['name']:
                if os.path.isfile(file):
                    g = XspfParser()
                    g.parseFile(file)
                    ra = g.getResult()
                    for radio in ra['tracklist']:
                        item = {}
                        if 'title' in radio:
                            item['display'] = urllib.parse.unquote(radio['title'])
                            item['title'] = urllib.parse.unquote(radio['title'])
                        if 'image'in radio:
                            item['covers'] =[urllib.parse.unquote(radio['image'])]
                        if 'location'in radio:
                            item['url'] = urllib.parse.unquote(radio['location'])
                        item['type'] = 'playlist'
                        item['length'] = 0
                        r.append(item)

                    res = r
                    app.playlist= res
    return json_resp(res)


@app.route("/v1/Podcast/Decode")
@app.tokenauth.login_required
def parse_podcast():
    @timing
    def getcontent(res):
        podcast = Podcast(res)
        return podcast
    r = []
    if 'rss' in request.args:
        rss = urllib.parse.unquote(request.args['rss'])
        response = requests.get(rss)
        podcast = getcontent(response.content)
        for it in podcast.items:
            item = {}
            item['display'] = it.title
            item['title'] = it.title
            item['cover'] =False
            item['covers'] = []
            if 'cover' in request.args:
                item['covers'] = [request.args['cover']]
            else:
                if  hasattr(podcast,'image_url'):
                    if podcast.image_url != None:
                        item['cover'] = True
                        item['covers'] = [podcast.image_url]
            item['url'] = it.url
            if hasattr(it,'itunes_duration'):
                item['length'] = it.itunes_duration
            r.append(item)
        app.podcasts = r
    return json_resp(r)


@app.route("/v1/Library/Podcast/Get")
@app.tokenauth.login_required
def get_podcasts():
    res = {}
    file = urllib.parse.unquote(request.args['file'])
    levels = urllib.parse.unquote(request.args['levels'])
    os.chdir(app.root_path)
    res['items'] = read_opml(file,levels)
    return json_resp(res)


@app.route("/v1/Library/Backup")
@app.tokenauth.login_required
def Library_Backup():
    '''Save MongoDB Collection'''
    res = {}
    os.chdir(app.root_path)

    with open(os.path.join(os.getenv("HOME"), '.Player','backups',datetime.now().strftime("%Y%m%d%H%M%S")+'_mediafiles.bson'), 'wb+') as f:
        for doc in app.db.mediafiles.find():
            f.write(BSON.encode(doc))
    with open(os.path.join(os.getenv("HOME"), '.Player','backups',datetime.now().strftime("%Y%m%d%H%M%S")+'_thumbnails.bson'), 'wb+') as f:
        for doc in app.db.thumbnails.find():
            f.write(BSON.encode(doc))

    res['Response'] = 'OK'
    return json_resp(res)

@app.route("/v1/Library/Restore")
@app.tokenauth.login_required
def Library_Restore():
    '''Restore MongoDB Collection'''
    app.db.mediafiles.drop()
    app.db.thumbnails.drop()
    os.chdir(app.root_path)
    res = {}
    f = []
    for root, dirs, files in os.walk(os.path.join(os.getenv("HOME"), '.Player','backups')):
        files = [f for f in files]
    f = files
    f = sorted(f, reverse=True)
    if len(f)>=2:
        p = os.path.join(os.getenv("HOME"), '.Player','backups')
        p1 = os.path.join(p, f[1] )
        p2 = os.path.join(p, f[0])
        with open( p1, 'rb') as fi:
            fa = decode_all(fi.read())
            for f in fa:
                try:
                    app.db.mediafiles.insert(f)
                except:
                    pass

        with open( p2,'rb') as fi:
            fa = decode_all(fi.read())
            for f in fa:
                try:
                    app.db.thumbnails.insert(f)
                except:
                    pass

        app.db.mediafiles.create_index([('title', TEXT), ('album', TEXT),('artist', TEXT),('composer', TEXT)], default_language='english', language_override="dummy")
        try:
            for index in ['dirname','dirhash','album','artist','composer','performer','date']:
                app.db.mediafiles.create_index(index)
        except:
            pass

    res['Response'] ='OK'
    return json_resp(res)


def updated_clbk():
    pass

@app.route('/v1/UpdateCover', methods = ['GET', 'POST'])
#@app.tokenauth.login_required
@adminlogrequired
def upload_file():

    res = {}
    if request.method == 'POST':
      f = request.files['file']
      if 'query' in request.args:
          query =eval(urllib.parse.unquote(request.args["query"]))
          cursor = app.db.mediafiles.find_one(query)
          path = cursor["dirname"]
          dirhash = cursor["dirhash"]

      # Test if folder begins with "CD" ...
      c_folder = os.path.basename(os.path.normpath(path))
      subfolder = True if True in [c_folder.startswith(i) for i in app.album_sub_folder] else False
      if subfolder == True:
          path = os.path.normpath(os.path.join(path, os.pardir))
      path = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', path,f.filename)

      #Save the renamed file to disk
      npath = path.replace(os.path.basename(path), "cover.jpg")
      if (os.path.exists(npath)):
          os.remove(npath)

      logging.info(f'Saving Image to: {npath}')
      f.save(npath)
      time.sleep(2)
      # Update the cover in the database
      im = Image.open(npath)
      size = 256, 256
      im.thumbnail(size, Image.ANTIALIAS)
      buffered = BytesIO()
      im.convert('RGB').save(buffered, format="JPEG")
      # encode the image
      thumb_encoded_string = base64.b64encode(buffered.getvalue()).decode()
      npath = os.path.relpath(npath, os.path.join(os.getenv("HOME"), ".Player", "mediafiles"))

      # updatedb
      app.db.thumbnails.update_one({"dirhash": dirhash},{"$set": {"last_modified_epoch": round(time.time()), "dirhash": dirhash,
                                                        "cover_256": thumb_encoded_string, "path": npath}},upsert=True)

      res['dirhash'] = dirhash
      res['response'] = 'OK'
      return json_resp(res)

@app.route("/v1/Library/Scan/Update/Files")
@adminlogrequired
@app.tokenauth.login_required
def Library_Scan_Update_Files():
    '''Add new files without altering what's there'''
    if app.scan_lock == False:
        app.db.internals.update_one({"_id": app.internals["_id"]},{"$set":  {"last_scan": Timestamp_Now()}}, upsert=False)
        Update_Lib( app.mongo_addr,callback= updated_clbk, owner= app, overwrite=False,scanfolder=False).start()
    else:
        pass
    res = {"result": "OK"}
    return json_resp(res)

@app.route("/v1/Library/Scan/Update/Folders")
@adminlogrequired
@app.tokenauth.login_required
def Library_Scan_Update_Folders():
    '''Add new folder's files without altering what's there
    Scan Folder button'''

    if app.scan_lock == False:
        #app.db.internals.update_one({"_id": app.internals["_id"]},{ "$set":{"last_scan": Timestamp_Now()}}, upsert=False)
        Update_Lib( app.mongo_addr,callback= updated_clbk, owner= app, overwrite=False,scanfolder=True).start()
    else:
        pass
    res = {"result": "OK"}
    return json_resp(res)

def rescan_clbk():
    msg = {}
    msg['message'] = 'rescanned'
    msg['id'] =app.player_id
    WSServerProtocol.broadcast_message(msg)

@app.route("/v1/Library/Scan/Rebuild")
@app.tokenauth.login_required
@adminlogrequired
def Library_Scan_Rebuild():
    '''Erase ALL and rebuild '''

    if not hasattr(app, 'up'):
        app.db.internals.update_one({"_id": app.internals["_id"]},{ "$set": {"last_scan": Timestamp_Now()}}, upsert=False)
        Update_Lib(app.mongo_addr, callback= rescan_clbk , owner= app, overwrite=True, rebuild =True).start()
        res = {"Library": "Start rescanning"}
    return json_resp(res)


@app.route("/v1/Library/SetTag") #, methods = ['GET', 'POST']
@app.tokenauth.login_required
@adminlogrequired
def Set_Tag():
    """Set a given tag of given file ids"""
    try:
        app.auto_import.pause()
        res = {}
        #TODO : Enable /Disable this feature ?
        #writetag = BoolStr(request.json['write_tag'])

        if ('ids' in request.args) and ('value' in request.args) and ('tag' in request.args):
            value = request.args["value"].split(";")
            value = [ReprInt(s.strip()) for s in value]
            tag = request.args["tag"]
            ids = request.args["ids"].split(";")
            ids = [ObjectId(id) for id in ids]

            value = value[0] if len(value) == 1 or tag in app.SingleValueTags else value

            cursor = app.db.mediafiles.find( {"_id": {"$in": ids}})
            dirhashs = app.db.mediafiles.find( {"_id": {"$in": ids}}).distinct("dirhash")
            dirnames = app.db.mediafiles.find({"_id": {"$in": ids}}).distinct("dirname")

            app.plugins_action('before_library_settag', tag, dirnames)

            if value in EmptyValue:
                app.db.mediafiles.update_many({"_id": {"$in": ids}}, {"$unset": tag}, upsert=False)
            else:
                app.db.mediafiles.update_many({"_id": {"$in": ids}}, {"$set": {tag : value}}, upsert=False)

            for i in [f for f in cursor]:
                try:
                    _writetag(i, tag, value)
                except:
                    pass

            for dirhash in dirhashs:
                alltagvalues = app.db.mediafiles.find({"dirhash":  dirhash}).distinct(tag)
                mr = app.db.mediadirs.update_one({"dirhash" : dirhash}, {'$set' : { tag : alltagvalues }}, upsert=True)
                pass

            time.sleep(1)
            app.plugins_action('after_library_settag', tag, dirnames)

        res['result'] = 'OK'
    except Exception as e:
        res['result'] = 'Error'

    if (app.update_queries != None):
        app.update_queries.do_stop()
    app.update_queries = Update_Queries(app,requestfind)
    app.update_queries.start()
    update_playlist()
    louie.send("lib_updated")
    app.send_message("Tags Edited")

    def reprise_auto_import():
        app.auto_import.reprise()
    if app._config['AutoImport']['activate'] == "True":
        threading.Timer(5.0, reprise_auto_import).start()

    return json_resp(res)

@app.route("/v1/Library/GetValues", methods = ['GET', 'POST'])
@app.tokenauth.login_required
def GetAllValuesOfField():
    '''

    :return: All values found in this set of files,
    if the value exists in all files or not
    Must Be POST to  send all the ids
    DO NOT SEND QUERY
    '''
    all_val  = []
    unc = []
    res = {}
    values = {}
    def unique(val):
        return val if len([i for i in array if len([j for j in array if val in j]) == len(array)]) > 0 else None

    if request.method == 'GET': #POST
        unc = []
        if 'tags' in request.args:
            fields = urllib.parse.unquote(request.args["tags"]).split(";")
            if ('ids' in request.args):
                ids = [ObjectId(id) for id in request.args["ids"].split(";")]
                cursor = app.db.mediafiles.find({"_id": {"$in": ids}})
                cursor = [i for i in cursor]
                for i in cursor:
                    i['_id'] = str(i['_id'])
                for field in fields:
                    array = [[i.get(field, [])] if not isinstance(i.get(field, []), list) else i.get(field, []) for i in
                             cursor]
                    all_val = list(set(x for l in array for x in l))
                    ucursor = [unique(i) for i in all_val if unique(i) is not None]
                    unc = [f for f in all_val if f not in ucursor]
                    values[field] = {"all_tags": [ReprInt(x) for x in all_val], "common_tags": [ReprInt(x) for x in ucursor],"uncommon_tags": [ReprInt(x) for x in unc]}
                    if all_val in [[],['']]:
                        del values[field]
                    res["values"] = values

            elif 'query' in request.args:

                query = urllib.parse.unquote(request.args['query'])
                query = eval(urllib.parse.unquote(str(query)))
                cursor = app.db.mediafiles.find(query)
                cursor = [i for i in cursor]
                for i in cursor:
                    i['_id'] = str(i['_id'])
                for field in fields:
                    array = [ [i.get(field,[])] if not isinstance(i.get(field,[]),list) else i.get(field,[]) for i in cursor]
                    all_val = list(set(x for l in array for x in l))
                    ucursor = [unique(i)  for i in all_val if unique(i) is not None]
                    unc =  [f for f in all_val if f not  in ucursor]
                    values[field] = {"all_tags" :  [ReprInt(x) for x in all_val],  "common_tags": [ReprInt(x) for x in ucursor], "uncommon_tags": [ReprInt(x) for x in unc]}
                    if all_val in [[],['']]:
                        del values[field]
                    res["values"] = values

            else: # No query,No ids ...
                cursor = app.db.mediafiles.find().distinct(str(request.json['field']))
                unc=[]
                if request.json['field'] in ['discnumber','tracknumber']:
                    cursor = [i for i in range(50)]
                return json_resp({"all_tags" : list(set([ ReprInt(x) for x in cursor] ))})
        if 'ids' in request.args:
            res["param"] = {"ids": request.args["ids"]}
        elif 'query' in request.args:
            res["param"] = {"query": urllib.parse.quote(request.args["query"])}
        else:
            pass
    res = json_resp(res)
    return res



@app.route("/v1/Library/FindFiles")
@app.tokenauth.login_required
def findfiles():
    """
    Returns all tag values  for a selection of files sorted by a list of tags
    used by Control Query View
    """
    if "query" in request.args :
        cursor = app.db.mediafiles.find(eval(urllib.parse.unquote(request.args["query"]))).limit(1000)
        cursor = sorted(cursor, key=lambda k: [  to_unicode(k.get('album', [])) if isinstance(to_unicode(k.get('album',[])), list ) else to_unicode([k.get('album',[])]), 1000 * to_int(k.get("discnumber", 0)) + to_int(k.get("tracknumber", 0))])
    if "ids" in request.args :
        ids = urllib.parse.unquote(request.args["ids"]).split(";")
        ids = [ObjectId(id) for id in ids]
        cursor = app.db.mediafiles.find({"_id": {"$in": ids}}).limit(1000)
        cursor = sorted(cursor, key=lambda k: [ to_unicode(k.get('album', [])) if isinstance(to_unicode(k.get('album',[])), list ) else to_unicode([k.get('album',[])]), 1000 * to_int(k.get("discnumber", 0)) + to_int(k.get("tracknumber", 0))])


    if "sorttags" in request.args:

        sorttags = urllib.parse.unquote(request.args["sorttags"])
        sorte = sorttags.split('$')[1]
        tag =  sorttags.split('$')[0]


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
    return json_resp({'response': 'OK', 'files': cursor})



@app.route("/v1/Library/Find")
@app.tokenauth.login_required
def find( ):
    """
    Returns the widgets content for a grid display
    used by Control player view
    """
    try:
        res = requestfind(request.args,app.db)
        if res == "error":
            return json_resp({"response": "No more pages"})
        return json_resp({'response': 'OK', 'key': res["key"],'page_nbr': res["page_nbr"] , 'result': res["result"], 'query' : res["query"] })
    except:
        json_resp({'response': 'Error'})



def requestfind(request,db,query_hash =None):
    """
    query : the query which selects a subset of files
    field: tag giving for each widget  a different tag value
    sorttag : optionnal, tag on which the result is sorted + optionnal ASC or DESC sorting ...
    display: optionnal, set a different value for the display fo each widget
    full: optionnal, DOES NOT WORK mith mediadirs
    page_nbr:  get the page you want
    response_count : number of items in a page
    Note : sort on multiple tags does not work, NOT implemented...
    """

    page_nbr = int(request.get("page_nbr", 0))
    response_count = int(request.get("response_count", 1500))
    key = urllib.parse.unquote(request.get('field', ""))
    sorttag = urllib.parse.unquote(request["sorttag"].split('$', 1)[0] if "sorttag" in request else key)
    if "sort" in request:
        sort = urllib.parse.unquote(request["sort"])
    else:
        if len(request["sorttag"].split('$', 1)) == 2:
            sort = request["sorttag"].split('$', 1)[1] if "sorttag" in request else "ASCENDING"
        else:
            sort = "ASCENDING"

    sort =  -1 if sort == "DESCENDING" else 1
    display = urllib.parse.unquote(request.get('display', ""))
    full = request.get("full", "false")
    
    strquery =   urllib.parse.unquote(request.get("query", ""))
    if strquery == "null":
        return json_resp({'response': 'No error'})
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
        dirhash_values = app.db.mediafiles.find(basequery).distinct('dirhash')
        basequery = {'$and': [{'dirhash': {'$in': [f for f in dirhash_values]} }]}
    result = []
    try:
        s = urllib.parse.quote(str(query)) + str(sort) + sorttag + display + str(page_nbr) + str(response_count) + full
    except:
        return ""
    if query_hash == None:
        has = hashlib.sha256(s.encode('utf-8')).hexdigest()
        #print(f"query hash from this query : {has}")
        full = BoolStr(full)
    else:
        has = query_hash
        #print(f"query hash to update : {has}")

    # Decoding the query ends here ..

    if app.debug != "yes": # Default no , -d yes to activate
        try:
            cursorsavedquery = db.savedqueries.find({'hashquery': has})
            cs = [x for x in cursorsavedquery]
            if len(cs) >= 1:
                result = cs[0]['''result''']
                q = cs[0]['''query''']
                # Query has been found, return it ... and update the count !
                db.savedqueries.update_one({'hashquery': has}, {"$set": {"displayed": 1 + cs[0]["displayed"]}})
                return { 'key': key, 'result': result , 'page_nbr' : page_nbr,"query" :q }
        except:
            json_resp({'response': 'Error', })
    send_message_value('Calculating query', str(has))
    def displayed(r,val):
        try:
            if isinstance(r[val],list):
                result =r[val]
                if isinstance(result, list):
                    result = ", ".join([str(e) for e in result])

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

    # ############# MongoDB / With aggregation
    tags = []
    if app.db_name == "mongodb":
        def add_count_tag(tag):
            if tag not in grp:
                grp[tag + "_count"] = {"$addToSet": "$" + tag}
                tags.append(tag)
            if tag not in prj:
                prj[tag + "_count"] = {"$size": "$" + tag + "_count"}

        def add_display_tag(tag):
            if tag not in grp:
                grp[tag ] = {"$addToSet": "$" + tag}
                tags.append(tag)
            if tag not in prj:
                prj[tag] =  "$" + tag

        grp = {"_id": "$" + key, "files": {"$sum": 1}, "dirhashs": {"$addToSet": "$dirhash"}}
        prj = {"_id": 0, "keyval": "$_id", "files": 1, "dirhashs": "$dirhashs"}

        for tag in counttags:
            add_count_tag(tag)

        for tag in displaytags:
            add_display_tag(tag)

        try:
            sortvals = list(sorted(app.db.mediafiles.find(basequery).distinct(sorttag)))
        except:
            sortvals = list(sorted([str(x) for x in app.db.mediafiles.find(basequery).distinct(sorttag)]))

        if sort == -1:
            sortvals.reverse()
        sortvals = list( sortvals[(page_nbr * response_count):min((page_nbr * response_count) + response_count, len(sortvals))])

        if sortvals == []:
            return  "error"
        q= copy.deepcopy(basequery)
        q["$and"].append({sorttag :{"$in":sortvals}})

        m = app.db.mediafiles
        search = m.aggregate([
            {"$match": q},
            {"$unwind": "$" + key},
            {"$group": grp},
            {"$project": prj},
            {"$sort": {sorttag: sort}}  #Beware of parallel indexing, does not work with multiple sorting ...
        ])
        result = list(search)
        for l in result:
            for tag in tags:
                try:
                    l[tag] = [ x for xs in l[tag] for x in xs] if type(l[tag][0]) is list else  l[tag]
                except:
                    pass
        res = []
        for l in result :
            if l['keyval'] not in ['', ['']] :
                if l[sorttag][0] in sortvals: # limit result to this sortag page values
                    res.append(l)
        result = res



    #Delete all result not beginning with the correct Letter on "alphabet" tag ...
    if "alphabet" in lastfield and key != "dirhash":
        try:
            result = [i for i in result if i["keyval"].lower().startswith(lastfieldvalue.lower() )]
        except:
            pass

    # Delete all result not beginning in this group tag ...
    if "group_" in lastfield and key != "dirhash":
        try:
            result = [i for i in result if (  char_position(lastfieldvalue[0]) <= char_position(i["keyval"].lower()) and  char_position(i["keyval"].lower())  <= char_position(lastfieldvalue[-1]) ) ]
        except:
            pass

    for r in result:
        try:
            query = copy.deepcopy(basequery)
            query_and = query['$and']
            query_and.append({key: r["keyval"]})
            r["query"] =   urllib.parse.quote(str(query).encode("UTF-8"))
            displayval = copy.deepcopy(display)
            displayval =  displayval.replace('$' + key + '$',   displayed(r,"keyval"))
            displayval = displayval.replace('$' +sorttag+ '$', displayed(r,sorttag))
            for tag in displaytags:
                displayval = displayval.replace('$' + tag + '$', displayed(r,tag))
            for tag in counttags:
                displayval = displayval.replace('$' + tag + '_count$', displayed(r,tag+"_count"))
            r["display"] = displayval if displayval != "" else r["keyval"]
            if "covers" not in r :
                r["covers"] = r["dirhashs"]
            r.pop('dirhashs')
        except Exception as e:
            print(e)



    try:
         q =urllib.parse.quote(str(basequery))
         # update the query ...
         update = db.savedqueries.update_one({"hashquery": has},
            {"$set": {
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
                  "page_nbr": page_nbr,
                  "response_count": response_count,
              }} , upsert=True)

         print("Insert hash :" + str(has))
         #print(s)
    except Exception as e:
        print(e)
    return { 'key': key,'page_nbr' : page_nbr ,"query" :q,'result': result}


def clbk():
    msg = {}
    msg['message'] = 'reload'
    msg['id'] = app.player_id
    WSServerProtocol.broadcast_message(msg)

@app.route("/v1/Library/Import")
#@adminlogrequired
def Library_import():
    #TODO : continue ...
    os.chdir(app.root_path)
    if 'folder' in request.args:
        f =urllib.parse.unquote(request.args["folder"])
        dirnames = f.split(";")
        worker = Update_Folders(app.mongo_addr, dirnames, owner=app)
        worker.start()

    if 'last' in request.args:
        minutes = "-"+str([urllib.parse.unquote(request.args["last"])][0])
        app.mediafiles_dir = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles')
        cmd = ['find', '-L' ,f'{app.mediafiles_dir}', '-type', 'd' , '-mmin' ,minutes, '-links', '-3']
        folders = subprocess.check_output(cmd).splitlines()
        folders = [f.decode("utf-8").replace("/artwork","") for f in folders]
        folders = ['Music' + f.split('/Music')[1] for f in folders ]
        worker = Update_Folders(app.mongo_addr, folders, owner=app)
        worker.start()

    return json_resp({'response': 'OK'})

@app.route("/v1/Library/Reimport")
#@adminlogrequired
def Library_Reimport():
    if app.scan_lock == True:
        return json_resp({'response': 'Error'})
    os.chdir(app.root_path)
    if 'query' in request.args:
        q = eval(urllib.parse.unquote(request.args["query"]))
        app.db.savedqueries.delete_many({"query": urllib.parse.quote(str(copy.deepcopy(q)["$and"].pop()))})
        if list(q['$and'][-1].keys())[0] == 'dirhash':
            dirnames = app.db.mediafiles.find({"$and":[q['$and'][-1]]}).distinct("dirname")
            dirhashs = [list(q['$and'][-1].values())[0]]
        else:
            dirnames = app.db.mediafiles.find(q).distinct("dirname")
            dirhashs = app.db.mediafiles.find(q).distinct("dirhash")
        app.db.mediafiles.delete_many({"dirhash" : { "$in" : dirhashs}})
        app.db.thumbnails.delete_many({"dirhash" : { "$in" : dirhashs}})
        app.db.mediadirs.delete_many({"dirhash" : { "$in" : dirhashs}})

        time.sleep(1)
        worker= Update_Folders(app.mongo_addr,dirnames, owner=app)
        worker.start()

    return json_resp({'response': 'OK','dirhashs': dirhashs})

@app.route("/v1/Display/Covers")
@app.tokenauth.login_required
def Display_Covers():
    if 'query' in request.args:
        query = request.args['query']
        query = eval(urllib.parse.unquote(query))
        f = app.db.mediafiles.find_one(query)
        if f == None:
            return json_resp({'response': 'No dirhash', 'dirhash': []})
        return json_resp({'response': 'OK', 'dirhash': f['dirhash'] , 'dirname': f['dirname'], 'query' : urllib.parse.quote(str(query))})
    else:
        return json_resp({'response': 'No query', 'dirhash': []})

@app.route("/v1/Display/Group")
@app.tokenauth.login_required
def Display_Group():

    res = {}
    separator = ' ,'
    if 'separator' in request.args:
        separator = request.args['separator']

    if  'displaystr' in request.args:
        displaystr = urllib.parse.unquote(request.args['displaystr'])
        tags = gettags(displaystr)

    if 'dirhash' in request.args:
        dirhash = int(request.args['dirhash'])
        for tag in tags:
            m = app.db.mediafiles.find({"dirhash": dirhash}).distinct(tag)

            if separator == "json":
                res[tag] = json.dumps(sorted([i for i in m]))
            else:
                res[tag] = separator.join(sorted([i for i in m]))

    if 'ids' in request.args:
        ids = urllib.parse.unquote(request.args["ids"]).split(";")
        try:
            ids = [ObjectId(id) for id in ids]
        except:
            return json_resp({'response': 'Error'})
        query = {"_id": {"$in": ids}}
        for tag in tags:
            m = app.db.mediafiles.find(query).distinct(tag)
            if separator == "json":
                res[tag] = json.dumps(sorted([str(i) for i in m]))
            else:
                res[tag] = separator.join(sorted([str(i) for i in m]))

    if 'query' in request.args:
        query =urllib.parse.unquote(request.args['query'])
        query = eval(urllib.parse.unquote(str(query)))

        for tag in tags:
            m = app.db.mediafiles.find(query).distinct(tag)

            if separator == "json":
                res[tag] = json.dumps(sorted([str(i) for i in m]))
            else:
                res[tag] = separator.join(sorted([str(i) for i in m]))

    albumdisplaystr = displaystr
    for tag in res:
        s= ""
        for val in eval(res[tag]):
            s += f'<span class="{tag}">{val}</span>, '

        albumdisplaystr = clean(albumdisplaystr.replace("$" + tag + "$", s[:-2]))
    res = {}
    res['response'] = 'OK'
    res['display'] = clean(albumdisplaystr)
    if 'query' in request.args:
        res['query'] = urllib.parse.quote(str(query))

    return json_resp(res)

@app.route("/v1/Display/Files")
@app.tokenauth.login_required
def Display_Files():
    res = {}
    if  'displaystr' in request.args:
        displaystr = urllib.parse.unquote(request.args['displaystr'])
        tags = gettags(displaystr)

    if 'query' in request.args:
        query =eval(urllib.parse.unquote(request.args['query']))

    if 'ids' in request.args:
        ids = urllib.parse.unquote(request.args["ids"]).split(";")
        ids = [ObjectId(id) for id in ids]
        query = {"_id": {"$in": ids}}

    filetags = ["discnumber", "tracknumber", "_id", "length","dirhash","dirname","filename","extension"]
    tags = [item for sublist in [el.split(';') for el in tags] for item in sublist]
    filetags.extend(tags)
    cursor = app.db.mediafiles.find(query)
    files = [f for f in cursor]
    for f in files:
        allkeys = f.copy().keys()
        for k in allkeys:
            if k not in filetags:
                del f[k]
    for i in files:
        i['_id'] = str(i['_id'])

    def s(k):
        try:
            dn = k.get("discnumber", 0)
            if isinstance(dn, list):
                dn = dn[0]
            d = to_int(dn)
        except:
            d = to_int(0)
        try:
            tn = k.get("tracknumber", 0)
            if isinstance(tn, list):
                tn = tn[0]
            t = to_int(tn)
        except:
            t = 0
        return [1000 * (d) + (t)]

    files = sorted(files, key=lambda k: s(k))
    displays = []
    for f in files:
        display = replacetags(displaystr, f, ', ')
        displays.append({"display": clean(display), "_id": f["_id"], "length": f["length"],"dirhash": f["dirhash"],"dirname": f["dirname"],"filename": f["filename"],"extension": f["extension"]})
    res =  {}
    res['response'] = "OK"
    res['display'] = displays
    if 'query' in request.args:
        res['query'] = urllib.parse.quote(request.args['query'])
    return json_resp(res)




@app.route("/v1/Player/Outputs/Get")
#@app.tokenauth.login_required
def Output_Get():
    output = os.path.join(os.getenv("HOME"), '.Player', 'config', "outputs.json")
    with open(output, 'r') as j:
        try:
            contents = json.loads(j.read())
        except:
            return abort(404)
    app.outputs = contents["outputs"]
    logging.debug("current_output : " + str(app.current_output))
    return json_resp({'response': 'OK', 'outputs': app.outputs, "current" :  app.current_output})


@app.route('/v1/Outputs/Set', methods=['POST'])
def save_outputs():
    if 'outputs_file' not in request.files or 'filename' not in request.form:
        return json_resp({"error": "Missing parameters"}), 400

    file = request.files['outputs_file']
    filename = request.form['filename']

    try:
        # Vérifier que le fichier est un .json
        if not filename.endswith(".json"):
            return json_resp({"error": "Only .json files are allowed"}), 400

        # Lire le contenu et parser pour vérifier la validité JSON
        content = file.read().decode("utf-8")
        outputs_json = json.loads(content)  # Lève une exception si invalide

        # Enregistrer le fichier dans ~/.Player/config
        config_dir = os.path.join(os.path.expanduser("~"), ".Player", "config")
        os.makedirs(config_dir, exist_ok=True)
        filepath = os.path.join(config_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(outputs_json, f, indent=2, ensure_ascii=False)

        #TODO: Mettre à jour les player dans app.player ...
        return json_resp({"status": "OK", "saved_to": filepath})

    except Exception as e:
        return json_resp({"error": str(e)}), 500


@app.route("/v1/Player/Output/Set")
@app.tokenauth.login_required
def Output_Set():
    if "player_id" in request.args:
        player_id = request.args["player_id"]
    else:
        return abort(404)
    if 'nbr' in request.args:
        cf = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config", app.config_file)))
        parser = configparser.ConfigParser()
        parser.read(cf)
        parser.set("Output", "last", str(request.args['nbr']))

        with open(cf, 'w') as configfile:
            parser.write(configfile)
        app.current_output = int(request.args['nbr'])
        logging.debug("current_output : " + str(app.current_output))
        output = app.outputs[app.current_output]["gstpipeline"]
        icon = os.path.join(os.getenv("HOME"), ".Player","config", "player.xpm")
        output = output.replace("$icon$",icon )
        try:
            GetPlayer(player_id).set_pipeline(output)
        except:
            pass
        dsp_changed(player_id)


    res = {'Response': 'OK', 'nbr':   int(request.args['nbr'])  }
    return json_resp(res)

@app.route("/v1/Player/Lang/Get")
#@app.tokenauth.login_required
def Lang_Get():
    p = os.path.join(os.getenv("HOME"), '.Player', 'config', 'lang.json')
    if os.path.isfile(p):
          with open(p, 'r') as l:
            try:
                contents = json.loads(l.read())
                return json_resp({'response': 'OK', 'lang': contents})
            except:
                return abort(404)
    else:
        return abort(404)

@app.route("/v1/Player/Output/GetParams")
@app.tokenauth.login_required
def Output_HW_Params():
    res = {}
    try:
        hw_params = "cat " +app.outputs[app.current_output]["device"] + "hw_params"
        ret = subprocess.check_output(hw_params,shell=True).decode('utf-8')
        for value in ret.splitlines():
            k =str(value.split(":")[0].strip())
            v= str(value.split(":")[1].strip())
            res[k]= v
        res['Response']= 'OK'
        return json_resp(res)
    except:
        res['Response']= 'Error'
        return json_resp(res)

@app.route("/v1/Upnp/Reload")
@app.tokenauth.login_required
def Upnp_Reload():
    louie.send("upnp_reload", app)

# images ...
@app.route("/Docs/<folder>/<folder2>/<filename>")
#@app.tokenauth.login_required
def Docs2(folder,folder2, filename):
    if app._config['HttpServer']['activate'] == "True":
        fname = str(os.path.join (app.docs_dir, folder,folder2,filename))
        if os.path.isfile(fname) == True:
            return  send_file(fname, mimetype='image/jpeg',cache_timeout=1)
        else:
            return abort(404)
    else:
        r = requests.get(app.http_server_adr + "/Docs/" +folder + "/" + folder2 + "/" + filename + ".html", headers={'Authorization': "Bearer {}".format(app.token)}).content
        if r.status_code == 404 :
            return abort(404)
        else:
            return r.content


@app.route("/Docs/<folder>/<filename>.html")
#@app.tokenauth.login_required
def Docs(folder, filename):
    if app._config['HttpServer']['activate'] == "True":
        md = str(os.path.join (app.docs_dir, folder,filename)) + ".md"
        if os.path.isfile(md) == True:
            try:
                with open(md, "r", encoding='utf-8', errors='ignore') as myfile:
                    data = myfile.readlines()
                    data = '\n'.join(data)
                    #data = pypandoc.convert_text(data, 'html', format='md')
            except:
                return abort(404)

            return render_template('docs.html', data=data)

        else:
            return abort(404)
    else:
        r= requests.get(app.http_server_adr + "/Docs/" +folder + "/" + filename + ".html", headers={'Authorization': "Bearer {}".format(app.token)})
        if r.status_code == 404 :
            return abort(404)
        else:
            return r.content

@app.route("/v1/Commands/Get")
#@app.tokenauth.login_required
def Commands_Get():
    res = {}
    commands_file = os.path.join(os.getenv("HOME"), '.Player', 'config', "commands.json")
    if os.path.isfile(commands_file):
        res["response"] = "OK"
        with open(commands_file, 'r') as j:
            try:
                contents = json.loads(j.read())
                res["commands"] = contents["commands"]
            except:
                res["response"] = "Error"
    else:
        res["response"] = "Error"
    return json_resp(res)

@app.route("/v1/Commands/Run")
@app.tokenauth.login_required
def Commands_Run():
    res ={}
    res["response"] = "OK"
    if 'cmd' in request.args:
        cmd = urllib.parse.unquote(request.args['cmd'])
        cmd = cmd.split()
        try:
            subprocess.call(cmd)
        except:
            res["response"] = "Error"
    else :
        res["response"] = "Error"
    return json_resp(res)

@app.route("/v1/Rip/")
@app.tokenauth.login_required
def ripcd():
    launch_rip(app,app._config["Rip"]["tmp"],app._config["Rip"]["dest"])
    return json_resp({"response":"OK"})

@app.route("/v1/Settings/Get")
@app.tokenauth.login_required
def Get_Settings():
    res = {}
    res["indexes"] = app._config["Tags"]["indexes"]
    res["singlevalue"] = app._config["Tags"]["singlevalue"]
    res["txxx"] = app._config["Tags"]["txxx"]
    res["volume"] = app._config["Player"]["volume"]
    res["response"] ="OK"
    return json_resp(res)

@app.route("/v1/Settings/Set")
@app.tokenauth.login_required
def Set_Settings():
    cf = os.path.join(os.path.abspath(os.path.join(os.getenv("HOME"), ".Player", "config", app.config_file)))
    parser = configparser.ConfigParser()
    parser.read(cf)
    parser.set("Tags", "indexes", str(urllib.parse.unquote(request.args['indexes'])))
    parser.set("Tags", "singlevalue", str(urllib.parse.unquote(request.args['singlevalue'])))
    parser.set("Tags", "txxx", str(urllib.parse.unquote(request.args['txxx'])))
    parser.set("Player", "volume", str(urllib.parse.unquote(request.args['volume'])))
    app._config["Tags"]["indexes"]= str(urllib.parse.unquote(request.args['indexes']))
    app._config["Tags"]["singlevalue"]=str(urllib.parse.unquote(request.args['singlevalue']))
    app._config["Tags"]["txxx"]=str(urllib.parse.unquote(request.args['txxx']))
    app._config["Player"]["volume"]=str(urllib.parse.unquote(request.args['volume']))
    with open(cf, 'w') as configfile:
        parser.write(configfile)
    return json_resp({"response":"OK"})


def create_self_signed_cert(certfile, keyfile, certargs, cert_dir="."):
    C_F = os.path.join(cert_dir, certfile)
    K_F = os.path.join(cert_dir, keyfile)
    if not os.path.exists(C_F) or not os.path.exists(K_F):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)
        cert = crypto.X509()
        cert.get_subject().C = certargs["Country"]
        cert.get_subject().ST = certargs["State"]
        cert.get_subject().L = certargs["City"]
        cert.get_subject().O = certargs["Organization"]
        cert.get_subject().OU = certargs["Org. Unit"]
        cert.get_subject().CN = 'Example'
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(315360000)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')
        open(C_F, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(K_F, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == '__main__':

    app.player = None
    app.savedqueries = []
    path = os.path.join(os.getenv("HOME"), '.Player' , 'logs')
    if not os.path.exists(os.path.dirname(path)):
        os.mkdir( path)
    logfile = os.path.join(os.getenv("HOME"), '.Player', 'logs', 'log.txt')
    logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        RotatingFileHandler(logfile, maxBytes=10_000_000, backupCount=1),
        logging.StreamHandler()   # stdout/stderr
    ]
)
    app.pid = getpid()
    set_proc_name('Player')
    DirectoryLister.template = my_template
    def create_folder(f):
        # Create target Directory if don't exist
        if not os.path.exists(f):
            os.mkdir(f)

    def create_data():
        src = os.path.abspath(os.path.join('..', 'init_config'))
        dst = os.path.join(os.getenv("HOME"), '.Player/config')
  
        try:
            shutil.copytree(src, dst)
        except Exception as e:
            print("COPY PLUGINS ERROR:", e)
            pass # Tree already exists

        src = os.path.abspath(os.path.join('..', 'init_plugins'))
        dst = os.path.join(os.getenv("HOME"), '.Player/plugins')
        print(src)
        print(dst)
        try:
            mongolock = os.path.join(os.getenv("HOME"), '.Player/database/mongod.lock')
            os.remove(mongolock)
        except:
            pass #No mongo.lock file
        try:
            shutil.copytree(src, dst)
        except Exception as e:
            print("COPY PLUGINS ERROR:", e)
            pass # Tree already exists
    # Set initial folders
    os.chdir(app.root_path)
    app.mediafiles_folder = os.path.abspath(os.path.join(app.root_path, "..", "mediafiles"))
    app.main_folder = os.path.abspath(os.path.join(app.root_path, ".."))
    app.choose = False
    app.time = int(round(time.time() * 1000))

    # Create Folders ...
   
    parser = optparse.OptionParser()
    parser.add_option("-d", "--debug",help="set debug flag",default="no")
    parser.add_option("-c", "--config", help="set config file", default="config.ini")

    options, _ = parser.parse_args()
    app.debug = options.debug
    app.send_message = send_message
    app.send_message_value = send_message_value

    from updatelib import Update_Lib, Update_Folders

    app.Update_Folders = Update_Folders
    app.Update_Lib = Update_Lib
    os.chdir(app.root_path)
    app._config = configparser.ConfigParser()

    if os.path.isfile(os.path.join(os.getenv("HOME"), '.Player', 'config',options.config)):
        app._config.read(os.path.join(os.getenv("HOME"), '.Player', 'config',options.config))
        app.config_file = options.config
    else :
        app._config.read(os.path.join(os.getenv("HOME"), '.Player', 'config', 'config.ini'))
        app.config_file = 'config.ini'

    plugins_dir = os.path.join(os.getenv("HOME"), '.Player', 'plugins')
    sys.path.insert(1, plugins_dir )

    for _filename_ in sorted([f for f in listdir(plugins_dir) if isfile(join(plugins_dir, f)) and f.rsplit('.', 1)[1] =='py']):
        if os.path.isfile(os.path.join(os.path.join(os.getenv("HOME"), '.Player', 'plugins'), _filename_)):
            try:
                exec('import ' +_filename_.split('.')[0])
            except:
                pass
    app.Plugins_dir = plugins_dir
    app.plugins_action = plugins_action
    plugins_action('server_start')
    output = os.path.join(os.getenv("HOME"), '.Player', 'config', "outputs.json")

    with open(output , 'r') as j:
        try:
            contents = json.loads(j.read())
        except:
            print("Error while reading outputs file")
        app.outputs = contents["outputs"]
    app.output_last= app._config['Output']['last']
    logging.debug("output_last : " + app.output_last)
    try:
        app.current_output = int(app.output_last)
        logging.debug("current_output : " + str(app.current_output))
    except:
        app.output_last= 0
        app.current_output = int(app.output_last)
        logging.debug("current_output : " + str(app.current_output))

    app.users = []
    try:
        app.users = json.load(open(os.path.join(os.getenv("HOME"), '.Player', 'config', "users.json")))
    except:
        logging.warning("users file not valid !")


    app.ssl = app._config['Server']['ssl']
    if app.ssl ==  'True':
        context = ('cert.crt', 'cert.key')  # certificate and key files
        contextFactory = ssl.DefaultOpenSSLContextFactory('mydomain.com.key', 'mydomain.com.crt')
    app.audioextension = app._config['Tags']['audioextension'].split(',')
    app.videoextension = app._config['Tags']['videoextension'].split(',')
    app.imageextension = app._config['Tags']['imageextension'].split(',')
    app.image_names = app._config['Tags']['image_names'].split(',')

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


    app.volumelevel = float(app._config["Player"]["volume"])
    app.defaultvolume = app.volumelevel
    app.cover_names = get_cover_names(app.image_names,app.imageextension)
    app.text_name = app._config['Tags']['text_name']
    app.album_sub_folder = app._config['Tags']['album_sub_folder'].split(',')
    #app.host = app._config['Server']['host']
    app.host = get_adresse_ip_locale()
    app.httpport = app._config['Server']['httpport']




    app.wsport = app._config['Server']['wsport']
    app.scan_threads = app._config['Scan']['threads']
    app.mongo_db_type = app._config['MongoDB']['database']
    n =  app._config['Tags']['art_folder'].split(',')
    n.extend([x.lower() for x in n])
    n.extend([x.upper() for x in n])
    n.extend([x.capitalize() for x in n])
    app.art_folder = n
    app.txxx= []
    app.bearers = []
    app.scan_lock = False

    app.m_connection ='../mongodb/mongod --dbpath "' + os.path.join(os.getenv("HOME"), '.Player', 'database') +'"'   +  ' --storageEngine ' + app.mongo_db_type #wiredTiger or mmapv1
    app.m_connection += ' --replSet mediafiles_changes '

    if app._config['MongoDB']['bind_ip_all']:
        app.m_connection += ' --bind_ip_all'
    if app._config['MongoDB']['port'] not in ['','localhost'] :
        app.m_connection += " --port " + app._config['MongoDB']['port']


    app.mongo_addr = 'mongodb://'
    if app._config['MongoDB']['user'] != '' and app._config['MongoDB']['password'] != '':
        app.mongo_addr += app._config['MongoDB']['user'] +':'+app._config['MongoDB']['password'] + '@'
    app.mongo_addr += app._config['MongoDB']['address']

    if app._config['MongoDB']['port']  !='':
        app.mongo_addr += ':' + app._config['MongoDB']['port']
    reactor_args = {}

    # create a WebSocketServerFactory resource for our WebSocket server
    factory = WebSocketServerFactory(u"ws://" + str(app.host)+':' +str(app._config['Server']['wsport']))

    
    factory.protocol = WSServerProtocol
    app.wssp = WSServerProtocol
    listenWS(factory)

    # create thread pool used to serve WSGI requests
    thread_pool = ThreadPool(maxthreads=10)
    thread_pool.start()
    reactor.addSystemEventTrigger('before', 'shutdown', thread_pool.stop)
    wsResource = WebSocketResource(factory)

    # create a WSGI resource for our Flask server
    wsgiResource = WSGIResource(reactor, thread_pool, app) #reactor.getThreadPool()
    p  = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles','Music')
    static_resource = File(p)

    # http://localhost:8000/Music/ -> Browse Directory of Local Files ...
    prot = "http://"
    if app._config['HttpServer']['activate'] == "True":
        rootResource = WSGIRootResource(wsgiResource, {b'Music': static_resource, b'ws': wsResource})
        if app.ssl == 'True':
            prot ="https://"
        app.http_server_adr = prot + str(app.host) + ":" + str(app.httpport)
    else:
        rootResource = WSGIRootResource(wsgiResource, { b'ws': wsResource})
        app.http_server_adr = prot + app._config['HttpServer']['address'] + ":" + str(app._config['HttpServer']['port'])
    app.http_server_adr = prot + str(app.host) + ":" + str(app.httpport)

    site = Site(rootResource)
    if app.ssl == 'True':
        reactor.listenSSL(int(app.httpport), site, contextFactory)
    else:
        reactor.listenTCP(int(app.httpport), site, interface="0.0.0.0")

    path = os.path.join(
        os.getenv("HOME"),
        "MyPlayer",
        "player",
        "src",
        "coherence"
    )
    config = {'plugins': [], 'logging': {}}

    def set_upnp_config(config):

        Coherence(path,config) # Commenter si upnp à part ...
        pass
    if app._config['Upnp']['player'] == "True":
        name = app._config['Upnp']['name']
        uuid = app._config['Upnp']['uuid']
        config['plugins'].append({'backend': 'PlayerStore', 'name': name, 'uuid': uuid})

    app.txxx = app._config['Tags']['txxx'].split(",")
    players = os.path.join(os.getenv("HOME"), '.Player', 'config', "players.json")
    with open(players, 'r') as j:
            contents = json.loads(j.read())
    app.players = contents["players"]
    for player in app.players:
        player["saved"]= "yes"

    preferred_player_id = str(app._config.get("Player", "last", fallback="")).strip()
    matched_player = None
    if preferred_player_id:
        matched_player = next((p for p in app.players if str(p.get("id")) == preferred_player_id), None)
    if matched_player is None and app.players:
        preferred_player_id = str(app.players[0].get("id", ""))
        matched_player = app.players[0]

    app.webadr = "http://" + str(app.host) + ":" + str(app.httpport)
    app.subscription_callback = app.http_server_adr + '/upnp'

    if matched_player is not None:
        app.player_id = preferred_player_id
        if "player" not in matched_player:
            set_player(app, preferred_player_id)
        app.player = matched_player.get("player")
    else:
        app.player_id = ""
        app.player = None

    reactor.callWhenRunning(set_upnp_config, config)
    app.auto_import = Autoimport(app)
    if app._config['AutoImport']['activate'] == "True":
        app.auto_import.start()
    app.reactor = reactor
    app.old_subs = None

    if app._config['HttpServer']['activate'] != "True":
        app.token = json.loads(requests.get(app.http_server_adr + '/v1/Login', verify=True, auth=basicaut('user', 'password')).text)["token"]
    louie.connect(on_upnp_started, "upnpstarted")
    if app._config['MongoDB']['embded'] == 'True':
        app.mongod = subprocess.Popen(app.m_connection, shell=True)
        app.mongo_addr ="mongodb://localhost:27017"
    print("mongo_addr :" + app.mongo_addr)                      
    app.MongoConnection = MongoClient(app.mongo_addr)
    if app._config['MongoDB']['embded'] == 'True':
        try:
            app.MongoConnection.admin.command('ismaster')
        except ConnectionFailure:
            print("Server not available")

    app.db = app.MongoConnection.player
    if "mongo" in app.m_connection :
        app.db_name = "mongodb"
    elif "ferret" in app.m_connection :
        app.db_name = "ferretdb"
    else:
        pass

    app.podcasts = []
    app.radios = []
    app.playlists = []
    directory = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Playlists')
    os.chdir(directory)
    files = [file for file in glob.glob("*.xspf")]
    for file in files:
        if os.path.isfile(file):
            app.playlists.append(os.path.splitext(os.path.basename(file))[0])
    app._id = 0
    app.updating = False
    app.restartqueue = False
    app.ripping = False
    app.update_lib = Update_Lib
    app.update_queries = None


    def start_monitor_thread():
        t = threading.Thread(target=monitor_inactivity, daemon=True)
        t.start()


    start_monitor_thread()
    if app._config['USB']['import'] == "True":
        monitor = USBCopyMonitor(app)
        monitor.start()

    reactor.run()
