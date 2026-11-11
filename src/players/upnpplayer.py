import os
import urllib.parse
from copy import copy
from html.parser import HTMLParser
from lxml import etree

from requests.utils import requote_uri
from twisted.internet import defer, task

from upnpclient.didl import set_TrackMetaData
from upnpclient.upnp import Device
from utils.player_logging import log_debug, log_warning
from utils.time import HHMMSSToMs, MsToMMSS


class UpnpPlayer:

    def _debug(self, action, **details):
        log_debug("UpnpPlayer", action, **details)

    def _warning(self, action, **details):
        log_warning("UpnpPlayer", action, **details)

    def __init__(self, app, state_changed, audio_changed):
        self.previous_state = None
        self.is_changing_track = False
        self.transcode = False  # NOTE: Set to True to enable transcoding
        self.Has_Next_AVTransport = True
        self.app = app
        self.reactor = None
        self.state_changed = state_changed
        self.audio_changed = audio_changed
        self.msg_count = 0
        self.q = defer.DeferredQueue()
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
        self.sleep_time = 0.3
        self.bock_task = False
        self.is_worker_running = False
        self.upnp__keys_to_watch = [
            'AVTransportURI', 'NextAVTransportURI', 'TransportState'
        ]

        # Initialize upnp_state
        for key in self.upnp__keys_to_watch:
            self.upnp_state[key] = {'val': ""}

        self.oldCurrentURI = None
        self.oldNextURI = None

    def sleep_async(self, seconds):
        """Pause asynchrone qui ne bloque pas la boucle Twisted."""
        return task.deferLater(self.app.reactor, seconds, lambda: None)

    def _schedule_state_change(self, delay, state):
        reactor = self.reactor or getattr(self.app, 'reactor', None)
        if reactor is not None:
            reactor.callLater(delay, self.state_changed, self.id, state)
        else:
            self.state_changed(self.id, state)

    def set_device(self, id, device_xml_url, subscription_callback, gapless, reactor):
        self.queue = []
        self.queue_position = 0
        self.app.set_device = True
        self.reactor = reactor

        self.id = id
        self._debug("set_device|start", player_id=self.id, device_url=device_xml_url, callback=subscription_callback)
        try:
            self.device = Device(device_xml_url)
        except Exception as e:
            self._warning("set_device|device_init_failed", player_id=self.id, device_url=device_xml_url, error=str(e))
            return False

        self.RenderingControl = self.device.RenderingControl
        self.AVTransport = self.device.AVTransport
        self.ConnectionManager = self.device.ConnectionManager

        # Set Has_Next_AVTransport for this device
        if "SetNextAVTransportURI" in [action.name for action in self.AVTransport.actions]:
            self.Has_Next_AVTransport = True
        else:
            self.Has_Next_AVTransport = False

        self._debug("set_device|renderer_config", player_id=self.id, device_url=device_xml_url, gapless=self.Has_Next_AVTransport)

        # init volume
        try:
            self.default_volume = self.app.defaultvolume
            self.set_volume(self.default_volume)
            self.volume_restore = self.default_volume
            self.app.volumelevel = self.default_volume
        except Exception:
            pass

        self.device_xml_url = device_xml_url
        self.subscription_callback = f"{subscription_callback}/{self.id}"
        self._debug("set_device|subscription_callback", player_id=self.id, callback=self.subscription_callback)

        # Subscribe to events ..
        try:
            self.RenderingControl_sub = self.RenderingControl.subscribe(self.subscription_callback)
            self._debug("set_device|renderingcontrol_subscription_ok", player_id=self.id)
        except Exception:
            self._warning("set_device|renderingcontrol_subscription_failed", player_id=self.id)
        try:
            self.AVTransport_sub = self.AVTransport.subscribe(self.subscription_callback)
            self._debug("set_device|avtransport_subscription_ok", player_id=self.id)
        except Exception:
            self._warning("set_device|avtransport_subscription_failed", player_id=self.id)
        try:
            self.ConnectionManager_sub = self.ConnectionManager.subscribe(self.subscription_callback)
            self._debug("set_device|connectionmanager_subscription_ok", player_id=self.id)
        except Exception:
            self._warning("set_device|connectionmanager_subscription_failed", player_id=self.id)

        self.upnp_message_worker()

        # Boucle de renouvellement des abonnements (toutes les 1000 secondes)
        self.renew_subscriptions_task = task.LoopingCall(self.renew_subscriptions)
        self.renew_subscriptions_task.start(1000)

        # Sondage de l'état de transport (toutes les 10 secondes)
        self.ask_transport_task = task.LoopingCall(self.ask_transport)
        try:
            self.ask_transport_task.start(10)
        except Exception:
            pass

        self.set_stop()  # Arrêter la lecture si on passe à ce player ...
        try:
            self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=None, CurrentURIMetaData=None)
        except Exception:
            pass
        try:
            self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
        except Exception:
            pass
        self.app.set_device = False
        return True

    def ask_transport(self):
        try:
            GetMediaInfo = self.AVTransport.GetMediaInfo(InstanceID=0)
            CurrentURI = GetMediaInfo['CurrentURI']
            NextURI = GetMediaInfo['NextURI']

            if self.oldCurrentURI != CurrentURI:
                self._debug("ask_transport|current_uri", player_id=self.id, current_uri=CurrentURI)
                self.oldCurrentURI = CurrentURI
            if self.oldNextURI != NextURI:
                self._debug("ask_transport|next_uri", player_id=self.id, next_uri=NextURI)
                self.oldNextURI = NextURI

            if CurrentURI != "" and NextURI in [None, ""] and self.Has_Next_AVTransport:
                self._debug("ask_transport|missing_next_uri_setting_next", player_id=self.id, current_uri=CurrentURI)
                self.on_AVTransportURI_Has_Next(CurrentURI)

            TransportInfo = self.AVTransport.GetTransportInfo(InstanceID=0)
            current_state = TransportInfo['CurrentTransportState']

            if current_state == "STOPPED":
                self.state = "stopped"
                if not self.Has_Next_AVTransport:
                    if self.previous_state == "playing" and not self.is_changing_track and not self.bock_task:
                        if self.queue_position < len(self.queue) - 1:
                            self._debug("ask_transport|auto_next_track", player_id=self.id, queue_position=self.queue_position, queue_length=len(self.queue))
                            self.set_next()

            elif current_state == "PLAYING":
                self.state = "playing"
            elif current_state == "PAUSED_PLAYBACK":
                self.state = "paused"

            self.previous_state = copy(self.state)

            if self.state != self.upnp_state['TransportState']['val']:
                self.upnp_state['TransportState']['val'] = copy(self.state)
                self.state = self.get_state()

            self.on_state_change(self.state)
        except Exception as e:
            self._warning("ask_transport|failed", player_id=getattr(self, 'id', 'unknown'), error=str(e))

    def renew_subscriptions(self):
        """Renouvelle les abonnements UPnP à intervalle régulier via LoopingCall."""
        try:
            self.RenderingControl.subscribe(self.subscription_callback)
            self.AVTransport.subscribe(self.subscription_callback)
            self.ConnectionManager.subscribe(self.subscription_callback)
            self._debug("renew_subscriptions|ok", player_id=self.id)
        except Exception as e:
            self._warning("renew_subscriptions|failed", player_id=getattr(self, 'id', 'unknown'), error=str(e))

    def put_event(self, msg):
        self.q.put(msg)

    @defer.inlineCallbacks
    def upnp_message_worker(self):
        """Traite les événements UPnP de manière 100% asynchrone sans thread."""
        self.is_worker_running = True
        while self.is_worker_running:
            try:
                message = yield self.q.get()
                if not self.is_worker_running:
                    break

                parsed_message = self.upnp_message_parse(message)
                if not parsed_message or self.old_message == parsed_message:
                    continue

                self.old_message = copy(parsed_message)
                self.upnp_message_process(parsed_message)

            except Exception as e:
                self._warning("upnp_message_worker|failed", player_id=getattr(self, 'id', 'unknown'), error=str(e))

    def upnp_message_parse(self, msg):
        """Parses the SOAP eventing response data"""
        if not msg or msg.get("id") != self.id:
            return

        data = msg.get("data", b"").decode('utf-8')
        parser = HTMLParser()
        data = parser.unescape(data)
        if "<LastChange>" in data:
            data = data.split("<LastChange>")[1].split("</LastChange>")[0]
        else:
            return

        root = etree.fromstring(data)
        vals = {}
        for child in root[0]:
            try:
                key = child.tag.split("}")[1]
                if key in self.upnp__keys_to_watch:
                    vals[key] = child.attrib
            except Exception:
                pass
        return vals

    def upnp_message_process(self, parsed_message):
        if parsed_message is None:
            return

        if 'TransportState' in parsed_message:
            if self.upnp_state['TransportState']['val'] != parsed_message['TransportState']['val']:
                self._debug("upnp_message_process|transport_state_changed", player_id=self.id, state=parsed_message['TransportState']['val'])
                state = None
                if parsed_message['TransportState']['val'] == "STOPPED":
                    state = "stopped"
                elif parsed_message['TransportState']['val'] == "PLAYING":
                    state = "playing"
                elif parsed_message['TransportState']['val'] == "PAUSED_PLAYBACK":
                    state = "paused"

                self.upnp_state['TransportState']['val'] = parsed_message['TransportState']['val']
                if state is not None:
                    self.on_state_change(state)

    @defer.inlineCallbacks
    def set_uri(self, dic, position=None):
        if self.state == "paused":
            return

        file_path = dic.get("file", "") or dic.get("uri", "")
        if "file" in file_path:
            uri = file_path.replace("file://", "")
            uri = uri.replace(str(self.app.mediafiles_folder), "")
            uri = urllib.parse.quote(uri)
            uri = self.app.webadr + uri
            player = next((p for p in self.app.players if str(p.get('id')) == str(self.id)), None)
            if player is not None:
                codec = str(player.get('codec', getattr(getattr(self.app, 'player', None), 'transcode_codec', 'mp3'))).lower()
            dic['uri'] = uri
            if self.transcode:
                source_name = os.path.basename(dic.get('file', 'track'))
                source_ext = os.path.splitext(source_name)[1].lstrip('.') or 'mp3'
                player_id = self.id
                dic["uri"] = f"{self.app.webadr}/v1/Transcode/{player_id}/{dic['_id']}.{codec}"
        else:
            self._warning("set_uri|missing_file_or_uri", player_id=self.id, payload=dic)

        meta = set_TrackMetaData(self.app, dic)

        # Arrêt temporaire du sondage
        if self.ask_transport_task.running:
            try:
                self.ask_transport_task.stop()
            except Exception:
                pass

        if position is not None:
            self.queue_position = position
            try:
                self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=dic["uri"], CurrentURIMetaData=meta)
                print('-----------------')
                print("set uri : " +dic['filename'])
                print(dic['uri'])
                print('-----------------')
            except Exception as e:
                self._warning("set_uri|set_avtransporturi_failed", player_id=self.id, uri=dic.get('uri'), error=str(e))

            yield self.sleep_async(self.sleep_time)

            try:
                self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
            except Exception:
                self._debug("set_uri|clear_next_uri_failed", player_id=self.id)

            yield self.sleep_async(0.2)
            self._debug("set_uri|track_ready", player_id=self.id, uri=dic.get('uri'), metadata=meta)
            self.audio_changed(self.id)
            self.next_position = position

        else:
            self.bock_task = True
            self.queue_position = 0
            self.next_position = 0

            try:
                self.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=dic["uri"], CurrentURIMetaData=meta)
                print('-----------------')
                print("set uri : " +dic['filename'])
                print(dic['uri'])
                print('-----------------')
            except Exception as e:
                self._warning("set_uri|set_avtransporturi_failed", player_id=self.id, uri=dic.get('uri'), error=str(e))

            yield self.sleep_async(self.sleep_time)

            try:
                self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI="", NextURIMetaData="")
                self._debug("set_uri|next_uri_cleared", player_id=self.id)
            except Exception:
                self._debug("set_uri|clear_next_uri_failed", player_id=self.id)

            yield self.sleep_async(self.sleep_time)
            self._debug("set_uri|track_loaded", player_id=self.id, uri=dic.get('uri'), metadata=meta)
            self.audio_changed(self.id)
            self.bock_task = False

        # Relance du sondage
        if not self.ask_transport_task.running:
            try:
                self.ask_transport_task.start(10)
            except Exception:
                pass

    @defer.inlineCallbacks
    def set_path(self, dic, position=None):
        uri = dic["file"]
        uri = uri.replace(str(self.app.mediafiles_folder), "")
        uri = urllib.parse.quote(uri)
        uri = self.app.webadr + uri
        player = next((p for p in self.app.players if str(p.get('id')) == str(self.id)), None)
        if player is not None:
            codec = str(player.get('codec', getattr(getattr(self.app, 'player', None), 'transcode_codec', 'mp3'))).lower()
        dic["uri"] = uri
        if self.transcode:
            source_name = os.path.basename(dic.get('file', 'track'))
            source_ext = os.path.splitext(source_name)[1].lstrip('.') or 'mp3'
            #player_id = getattr(self, 'id', getattr(self.app, 'player_id', '0'))
            player_id = self.id
            dic["uri"] = f"{self.app.webadr}/v1/Transcode/{player_id}/{dic['_id']}.{codec}"

        yield self.set_uri(dic, position)

    def get_volume(self):
        try:
            vol = self.RenderingControl.GetVolume(InstanceID=0, Channel="Master")
            return int(vol['CurrentVolume']) / 100
        except Exception:
            self._warning("get_volume|failed", player_id=getattr(self, 'id', 'unknown'))
            return 0

    def set_volume(self, vol):
        try:
            self.RenderingControl.SetVolume(InstanceID=0, Channel="Master", DesiredVolume=int(vol * 100))
        except Exception:
            self._warning("set_volume|failed", player_id=getattr(self, 'id', 'unknown'), volume=vol)
        self.volume_restore = round(vol, 2)

    def get_position(self):
        try:
            position = self.AVTransport.GetPositionInfo(InstanceID=0)
            self.position = HHMMSSToMs(position['RelTime'])
            return int(self.position)
        except Exception:
            self._warning("get_position|failed", player_id=getattr(self, 'id', 'unknown'))
            return 0

    def get_duration(self):
        try:
            self.duration = int(self.queue[int(self.queue_position)]["length"] * 1000)
            return int(self.duration)
        except Exception:
            self._warning("get_duration|failed", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position, queue_length=len(self.queue))
            return 0

    def get_state(self):
        return self.state

    def set_play(self):
        try:
            self.AVTransport.Play(InstanceID=0, Speed="1")
            self._debug("set_play|ok", player_id=self.id)
        except Exception as e:
            self._warning("set_play|failed", player_id=self.id, error=str(e))
        self.state = "playing"
        self._schedule_state_change(0.2, self.state)

    def set_play_uri(self):
        try:
            self.AVTransport.Play(InstanceID=0, Speed="1")
            self._debug("set_play_uri|ok", player_id=self.id)
        except Exception:
            self._warning("set_play_uri|failed", player_id=self.id)
        self._schedule_state_change(0.5, self.state)

    def set_pause(self):
        try:
            self.AVTransport.Pause(InstanceID=0)
            self._debug("set_pause|ok", player_id=self.id)
        except Exception:
            self._warning("set_pause|failed", player_id=self.id)
        self.state = "paused"
        self._schedule_state_change(0.2, self.state)

    def set_stop(self):
        try:
            self.AVTransport.Stop(InstanceID=0)
            self._debug("set_stop|ok", player_id=self.id)
        except Exception as e:
            self._warning("set_stop|failed", player_id=self.id, error=str(e))
        self.state = "stopped"
        self._schedule_state_change(0.5, self.state)

    def set_ready(self):
        pass

    def set_pipeline(self):
        try:
            self.set_volume(self.volume_restore)
        except Exception:
            pass

    def on_state_change(self, state):
        self.state = state
        self.state_changed(self.id, self.state)

    @defer.inlineCallbacks
    def on_AVTransportURI_Has_Next(self, current_uri):
        if self.bock_task or current_uri == "" or not self.queue:
            self._debug("on_AVTransportURI_Has_Next|skipped", player_id=self.id, blocked=self.bock_task, current_uri=current_uri, queue_length=len(self.queue))
            return

        if self.next_position is None:
            self.queue_position = 0
            self.next_position = 0
        else:
            try:
                self.queue_position = copy(self.next_position)
            except Exception:
                pass

        try:
            dic = self.queue[self.queue_position + 1]
            self.audio_changed(self.id)
            self._debug("on_AVTransportURI_Has_Next|preview_next_track", player_id=self.id, next_index=self.queue_position + 1)
        except IndexError:
            return

        if 'file' in dic and self.Has_Next_AVTransport:
            uri = dic['file']
            uri = uri.replace("file://", "")
            uri = uri.replace(str(self.app.mediafiles_folder), "")
            uri = urllib.parse.quote(uri)
            uri = f"{self.app.webadr}{uri}"
            player = next((p for p in self.app.players if str(p.get('id')) == str(self.id)), None)
            if player is not None:
                codec = str(player.get('codec', getattr(getattr(self.app, 'player', None), 'transcode_codec', 'mp3'))).lower()
            dic['uri'] = uri
            if self.transcode:
                source_name = os.path.basename(dic.get('file', 'track'))
                source_ext = os.path.splitext(source_name)[1].lstrip('.') or 'mp3'
                #player_id = getattr(self, 'id', getattr(self.app, 'player_id', '0'))
                player_id = self.id
                dic['uri'] = f"{self.app.webadr}/v1/Transcode/{player_id}/{dic['_id']}.{codec}"

        meta = set_TrackMetaData(self.app, dic)
        try:
            self.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI=dic['uri'], NextURIMetaData=meta)
            yield self.sleep_async(0.8)
            self._debug("on_AVTransportURI_Has_Next|next_uri_set", player_id=self.id, next_uri=dic.get('uri'))
            if self.queue_position == self.next_position:
                self.next_position += 1
        except Exception as e:
            self._warning("on_AVTransportURI_Has_Next|set_next_failed", player_id=self.id, next_uri=dic.get('uri'), error=str(e))

    def set_queue(self, list_items):
        self.queue = list_items.copy()

    def set_queue_position(self, pos):
        self.queue_position = pos

    def append_queue(self, list_items):
        self.queue.append(list_items.copy())

    def get_current(self):
        try:
            return self.queue[int(self.queue_position)]
        except Exception:
            return []

    @defer.inlineCallbacks
    def set_next(self):
        if int(self.queue_position) < int(len(self.queue) - 1):
            self.is_changing_track = True

            if self.ask_transport_task.running:
                self.ask_transport_task.stop()

            self.set_stop()
            yield self.sleep_async(1)

            self.queue_position += 1
            track = self.queue[self.queue_position]

            if 'file' in track:
                yield self.set_path(track, self.queue_position)
            elif 'uri' in track:
                yield self.set_uri(track, self.queue_position)

            yield self.sleep_async(1)

            self.set_play()

            if not self.ask_transport_task.running:
                self.ask_transport_task.start(2)

            self.app.reactor.callLater(1.0, self._release_track_lock)

    def _release_track_lock(self):
        self.is_changing_track = False

    @defer.inlineCallbacks
    def set_previous(self):
        if int(self.queue_position) > 0:
            self.is_changing_track = True

            if self.ask_transport_task.running:
                self.ask_transport_task.stop()

            self.set_stop()
            yield self.sleep_async(1)

            self.queue_position = int(self.queue_position) - 1
            track = self.queue[self.queue_position]

            if 'file' in track:
                yield self.set_path(track, self.queue_position)
            elif 'uri' in track:
                yield self.set_uri(track, self.queue_position)

            yield self.sleep_async(1)

            self.set_play()

            if not self.ask_transport_task.running:
                self.ask_transport_task.start(2)

            self.app.reactor.callLater(1.0, self._release_track_lock)

    def quit(self):
        self.is_worker_running = False
        self.q.put(None)

        try:
            self.set_stop()
            self.old_message = None
        except Exception:
            self._warning("quit|stop_failed", player_id=getattr(self, 'id', 'unknown'))

        if hasattr(self, 'renew_subscriptions_task') and self.renew_subscriptions_task.running:
            self.renew_subscriptions_task.stop()
        if hasattr(self, 'ask_transport_task') and self.ask_transport_task.running:
            self.ask_transport_task.stop()

        try:
            if hasattr(self, 'RenderingControl_sub') and self.RenderingControl_sub:
                self.RenderingControl.unsubscribe(self.subscription_callback)
            if hasattr(self, 'AVTransport_sub') and self.AVTransport_sub:
                self.AVTransport_sub.unsubscribe(self.subscription_callback)
            if hasattr(self, 'ConnectionManager_sub') and self.ConnectionManager_sub:
                self.ConnectionManager_sub.unsubscribe(self.subscription_callback)
        except Exception as e:
            self._warning("quit|unsubscribe_failed", player_id=getattr(self, 'id', 'unknown'), error=str(e))

        self.RenderingControl_sub = None
        self.AVTransport_sub = None
        self.ConnectionManager_sub = None