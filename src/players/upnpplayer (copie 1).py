# LongPolling version

import time
from requests.utils import requote_uri
import threading
import queue
import os
import urllib.parse
import logging
from upnpclient.didl import set_TrackMetaData
from upnpclient.upnp import Device
from html.parser import HTMLParser
from lxml import etree
from utils.time import HHMMSSToMs ,MsToMMSS
from twisted.internet import task
from copy import copy

class UpnpPlayer:

    def __init__(self, app, state_changed, audio_changed):
        self.previous_state = None
        self.is_changing_track = False
        self.transcode = False  #NOTE: Set to True to enable transcoding
        self.Has_Next_AVTransport = True
        self.app = app
        self.state_changed = state_changed
        self.audio_changed = audio_changed
        self.msg_count = 0
        self.q = queue.Queue()
        self.queue = []
        self.queue_position = 0
        self.count = 0
        self.position = 0
        self.duration = 0
        self.current_music_file_nbr = 0
        self.current_music_file = ""
        self.old_message = None
        self.upnp_state = {}
        self.state = None
        self.next_position = None

        self.bock_task = False
        self.upnp__keys_to_watch = \
            [ 'AVTransportURI','NextAVTransportURI', 'TransportState']

        # Initialize upnp_state
        for key in self.upnp__keys_to_watch:
            self.upnp_state[key] = {'val': ""}

        self.oldCurrentURI = None
        self.oldNextURI = None

    def set_device(self,id, device_xml_url, subscription_callback,gapless, reactor):
        self.queue = []
        self.queue_position = 0
        self.app.set_device = True

        self.id = id
        try:
            self.device = Device(device_xml_url)
        except:
            return False
        self.RenderingControl = self.device.RenderingControl
        self.AVTransport = self.device.AVTransport
        self.ConnectionManager = self.device.ConnectionManager

        # Set Has_Next_AVTransport for this device
        if "SetNextAVTransportURI" in [action.name for action in self.AVTransport.actions]:
            self.Has_Next_AVTransport = True
        else:
            self.Has_Next_AVTransport = False
        logging.info(f"Setting renderer to : {device_xml_url}")
        logging.info(f"Is this player gapless ? {self.Has_Next_AVTransport}" )
        # init volume
        try:
            self.default_volume = self.app.defaultvolume
            self.set_volume(self.default_volume)
            self.volume_restore = self.default_volume
            self.app.volumelevel = self.default_volume
        except:
            pass

        self.device_xml_url = device_xml_url
        self.subscription_callback = subscription_callback + "/" +str(self.id)
        logging.info(f"subscription callback is {subscription_callback}")
        # Subscribe to events ..
        try:
            self.RenderingControl_sub = self.RenderingControl.subscribe(self.subscription_callback)  # GetMute,GetVolume
            logging.info("RenderingControl Subscription OK")
        except:
            logging.info("ERROR in RenderingControl subscribe")
        try:
            self.AVTransport_sub = self.AVTransport.subscribe(self.subscription_callback)  # GetPositionInfo
            logging.info("AVTransport Subscription OK")
        except:
            logging.info("ERROR in AVTransport subscribe")
        try:
            self.ConnectionManager_sub = self.ConnectionManager.subscribe(self.subscription_callback)
            logging.info("ConnectionManager Subscription OK")
        except:
            logging.info("ERROR in AVTransport subscribe")

        threading.Thread(target=self.upnp_message_worker, daemon=True).start()

        self.renew_subscriptions_task = task.LoopingCall(self.renew_subscriptions)
        self.renew_subscriptions_task.start(1000)

        self.ask_transport_task = task.LoopingCall(self.ask_transport)
        try:
            self.ask_transport_task.start(10)
        except:
            pass

        self.set_stop() # Arrêter la lecture si on passe à ce player ...
        try:
            self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=None, CurrentURIMetaData=None)
        except:
            pass
        try:
            self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
        except:
            pass
        self.app.set_device = False
        return True

    def ask_transport(self):

        GetMediaInfo  = self.AVTransport.GetMediaInfo(InstanceID=0)
        CurrentURI =GetMediaInfo['CurrentURI']
        NextURI = GetMediaInfo['NextURI']
        if  self.oldCurrentURI != CurrentURI:
            logging.info(f"CurrentURI is : {CurrentURI}")
            self.oldCurrentURI = CurrentURI
        if  self.oldNextURI != NextURI:
            logging.info(f"NextURI is : {NextURI}")
            self.oldNextURI = NextURI

        if CurrentURI != "" and NextURI in [None,""] and self.Has_Next_AVTransport == True:
            logging.info(f"No Next URI, setting it ...")
            self.on_AVTransportURI_Has_Next( CurrentURI)


        TransportInfo =self.AVTransport.GetTransportInfo(InstanceID=0)

        if TransportInfo['CurrentTransportState'] == "STOPPED":
            self.state = "stopped"

            # On ne réagit que si l'appareil jouait juste avant ET qu'on n'est pas déjà en train de changer de piste
            if not self.Has_Next_AVTransport:
                if self.previous_state == "playing" and not self.is_changing_track and not self.bock_task:
                    if self.queue_position < len(self.queue) - 1:
                        logging.info("Piste terminée naturellement (non-gapless). Passage à la suivante...")
                        self.set_next()

        if TransportInfo['CurrentTransportState'] == "PLAYING":
            self.state = "playing"

        if TransportInfo['CurrentTransportState'] == "PAUSED_PLAYBACK":
            self.state = "paused"

        # Mise à jour de l'état précédent à la fin de la vérification
        self.previous_state = copy(self.state)

        if TransportInfo['CurrentTransportState'] == "PLAYING":
            self.state = "playing"
        if TransportInfo['CurrentTransportState'] == "PAUSED_PLAYBACK":
            self.state = "paused"

        if self.state !=   self.upnp_state['TransportState']['val']:
            self.upnp_state['TransportState']['val'] = copy(self.state)
            self.state = self.get_state()
        # Envoyer les messages plus souvent ...
        self.on_state_change(self.state)

    def renew_subscriptions(self):
        try:
            sub = self.RenderingControl.subscribe(self.subscription_callback)
            sub = self.AVTransport.subscribe(self.subscription_callback)
            sub = self.ConnectionManager.subscribe(self.subscription_callback)
            self.app.reactor.callLater(1000, self.renew_subscriptions)
        except:
            print("ERROR in  renew_subscription")

    def put_event(self, msg):
        #logging.info(f"new message : {str(msg)}")
        self.q.put(msg)

    def upnp_message_worker(self):
        """Blocks repeated messages"""
        while True:
            time.sleep(.1)
            self.msg_count += 1
            # logging.info( f"Getting next message {self.msg_count} ...",)
            message = self.q.get()
            parsed_message = self.upnp_message_parse(message)
            if parsed_message == {}:
                continue
            if self.old_message == parsed_message:
                # logging.info("Same message .. do nothing")
                continue
            self.old_message = copy(parsed_message)
            if message != {} or message != None:
                self.upnp_message_process(parsed_message)
            else:
                pass
            self.q.task_done()

    def upnp_message_parse(self, msg):
        """Parses the SOAP eventing response data"""

        if msg["id"] != self.id:
            return # block messages coming from other players ...
        data= msg["data"]
        data = data.decode('utf-8')
        parser = HTMLParser()
        data = parser.unescape(data)
        if "<LastChange>" in data :
            data = data.split("<LastChange>")[1].split("</LastChange>")[0]
        else:
            return
        root = etree.fromstring(data)
        vals = {}
        for child in root[0]:
            try:
                key = child.tag.split("}")[1]
                # only watch variable we are interested in ...
                if key in self.upnp__keys_to_watch:
                    vals[key] = child.attrib
            except:
                pass
        return vals

    def upnp_message_process(self, parsed_message):
        #logging.info(parsed_message)
        """Fire callbacks according to upnp_state  ..."""
        if parsed_message == None :
            return

        if 'TransportState' in parsed_message:
            if self.upnp_state['TransportState']['val'] != parsed_message['TransportState']['val']:
                logging.info(f"TransportState changed to : {parsed_message['TransportState']['val']}")
                state = None
                if parsed_message['TransportState']['val'] == "OK":
                    state = None
                if parsed_message['TransportState']['val'] == "STOPPED":
                    state = "stopped"
                    self.upnp_state['TransportState']['val'] = state
                if parsed_message['TransportState']['val'] == "PLAYING":
                    state = "playing"
                    self.upnp_state['TransportState']['val'] = state
                if parsed_message['TransportState']['val'] == "PAUSED_PLAYBACK":
                    state = "paused"
                self.upnp_state['TransportState']['val'] = parsed_message['TransportState']['val']
                if state != None:
                    self.on_state_change(state)

    def set_uri(self, dic, position=None):

        if self.state == "paused":
            return
        if "file" in dic["uri"]:

            uri = dic['file']
            uri = uri.replace("file://", "")
            uri = uri.replace(os.path.join(os.getenv("HOME"), '.Player', "mediafiles"), "")
            uri = urllib.parse.quote(uri)
            uri = self.app.webadr + uri
            dic['uri'] = uri
            if self.transcode == True:
                dic["uri"] = self.app.webadr + "/v1/Transcode/" + dic["_id"]

        meta = set_TrackMetaData(self.app,dic)

        if position is not None:
            try:
                self.ask_transport_task.stop()
            except:
                pass
            # Ne passe pas par ici lors du changement de piste suivante automatique ... mais en manuel
            self.queue_position = position
            try:
                self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=dic["uri"], CurrentURIMetaData=meta)
            except:
                pass
            time.sleep(0.8)
            try:
                self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
            except:
                pass


            time.sleep(0.8)
            logging.info(f"Set meta : {meta}")
            logging.info(f"Set AVTransport : {dic['uri']}")
            self.audio_changed(self.id)
            self.next_position = position
            time.sleep(0.8)
            try:
                self.ask_transport_task.start(10)
            except:
                pass
            return
        else:
            self.bock_task = True
            # Quand on change d' album
            self.queue_position = 0
            self.next_position = 0
            try:
                self.ask_transport_task.stop()
            except:
                pass
            try:
                self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=dic["uri"], CurrentURIMetaData=meta)
            except:
                pass
            time.sleep(0.8)
            try:
                self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
                logging.info(f"Set NextAVTransport to ''")
            except:
                pass
            time.sleep(0.2)
            logging.info(f"Set meta : {meta}")
            logging.info(f"Set AVTransport : {dic['uri']}")
            self.audio_changed(self.id)
            try:
                self.ask_transport_task.start(10)
            except:
                self.bock_task = False
            self.bock_task = False

    def set_path(self, dic,position = None):

        uri = dic["file"]
        uri = uri.replace(os.path.join(os.getenv("HOME"), '.Player', "mediafiles"), "")
        uri = urllib.parse.quote(uri)
        uri = self.app.webadr + uri
        dic["uri"] =uri
        if self.transcode == True:
            dic["uri"] = self.app.webadr + "/v1/Transcode/" + dic["_id"]
        self.set_uri(dic,position)
        time.sleep(0.8)

    def get_volume(self):
        try:
            vol = self.RenderingControl.GetVolume(InstanceID=0, Channel="Master")
            vol = int(vol['CurrentVolume'])/100
        except:
            return 0
        return vol

    def set_volume(self, vol):
        try:
            self.RenderingControl.SetVolume(InstanceID=0, Channel="Master", DesiredVolume=int(vol * 100))
        except:
            pass
        self.volume_restore = round(vol, 2)

    def get_position(self):
        try:
            position = self.AVTransport.GetPositionInfo(InstanceID=0)
        except:
            return 0
        self.position = HHMMSSToMs(position['RelTime'])
        return int(self.position)

    def get_duration(self):

        # try:
        #     position = self.AVTransport.GetPositionInfo(InstanceID=0)
        # except:
        #     return 0.
        #self.duration = HHMMSSToMs(position['TrackDuration'])

        try:
            self.duration =  int(self.queue[int(self.queue_position)]["length"]*1000)

        except:
            return 0
        return int(self.duration)

    def get_state(self):
        return self.state

    def set_play(self):
        try:
            self.AVTransport.Play(InstanceID=0, Speed="1")
        except:
            pass
        self.state = "playing"
        time.sleep(0.2)
        self.state_changed(self.id,self.state)

    def set_play_uri(self):
        try:
            self.AVTransport.Play(InstanceID=0, Speed="1")
        except:
            logging.info(f"Error in AVTransport.Play")
        time.sleep(0.5)
        self.state_changed(self.id,self.state)

    def set_pause(self):
        try:
            self.AVTransport.Pause(InstanceID=0)
        except:
            pass
        
        self.state = "paused"
        time.sleep(0.2)
        self.state_changed(self.id,self.state)

    def set_stop(self):
        try:
            self.AVTransport.Stop(InstanceID=0)
        except:
            pass
        self.state = "stopped"
        time.sleep(0.5)
        self.state_changed(self.id,self.state)
        time.sleep(1)

    def set_ready(self):
        pass

    def set_pipeline(self):
        try:
            self.set_volume(self.volume_restore)
        except:
            pass

    def quit(self):
        try:
            self.set_stop()
            self.old_message = None
        except:
            pass
        self.renew_subscriptions_task.stop()
        try:
            self.ask_transport_task.stop()
        except:
            pass

        self.RenderingControl.unsubscribe(self.subscription_callback)
        self.AVTransport_sub.unsubscribe(self.subscription_callback)
        self.ConnectionManager_sub.unsubscribe(self.subscription_callback)

        self.RenderingControl_sub = None
        self.AVTransport_sub = None
        self.ConnectionManager_sub = None

    def on_state_change(self,state):
        #logging.info(f"State changed to: {state}")
        self.state = state
        self.state_changed(self.id,self.state)
          
    def on_AVTransportURI_Has_Next(self,current_uri):
        # Set NextAV ...
        if self.bock_task == True:
            return
        if current_uri == "":
            return
        if self.queue == []:
            return
        if  self.next_position == None:
            self.queue_position = 0
            self.next_position = 0
        else :
            try:
                self.queue_position = copy(self.next_position)
            except:
                pass
        # Déclenche la MAJ du HP de la Playliste
        try:
            dic = self.queue[self.queue_position+1]
            self.audio_changed(self.id) # seulement s'il y a une prochaine piste ...
            logging.info(f"Audio changed to: {dic}")
        except:
            return # out of range
        if 'file' in dic and (self.Has_Next_AVTransport == True):

            uri = dic['file']
            uri = uri.replace("file://", "")
            uri = uri.replace(os.path.join(os.getenv("HOME"), '.Player', "mediafiles"), "")
            uri = urllib.parse.quote(uri)
            uri = self.app.webadr + uri
            dic['uri'] = uri
            if self.transcode == True:
                dic['uri'] = self.app.webadr + "/v1/Transcode/" + dic["_id"]
        meta = set_TrackMetaData(self.app, dic)
        try:
            self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI=dic['uri'], NextURIMetaData=meta)
            time.sleep(0.8)
            logging.info(f"Set Next AVTransport : {dic['uri']}")
            if self.queue_position == self.next_position:  # Do NOT increment more than One ...
                self.next_position = self.next_position + 1
        except:
            pass

    def set_queue(self,list):
        self.queue = []
        self.queue.clear()
        self.queue = list.copy()
        pass

    def set_queue_position(self,pos):
        self.queue_position = pos

    def append_queue(self,list):
        self.queue.append(list.copy())

    def get_current(self):
        try:
            return self.queue[int(self.queue_position)]
        except:
            return []

    def set_next(self):
        if int(self.queue_position) < int(len(self.queue) - 1):
            try:
                self.ask_transport_task.stop()
            except:
                pass
            self.set_stop()
            time.sleep(0.8)
            self.queue_position = int(self.queue_position) + 1
            if 'file' in self.queue[int(self.queue_position)]:
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
                time.sleep(0.8)
            elif 'uri' in self.queue[int(self.queue_position)]:
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
                time.sleep(0.8)
            else:
                pass
            try:
                self.ask_transport_task.start(10)
            except:
                pass
            self.set_play()

    def set_previous(self):
        if int(self.queue_position) > 0:
            try:
                self.ask_transport_task.stop()
            except:
                pass
            self.set_stop()
            time.sleep(0.8)
            self.queue_position = int(self.queue_position) - 1
            if 'file' in self.queue[int(self.queue_position)]:
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
                time.sleep(0.8)
            elif 'uri' in self.queue[int(self.queue_position)]:
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
                time.sleep(0.8)
            else:
                pass
            try:
                self.ask_transport_task.start(10)
            except:
                pass
            self.set_play()
