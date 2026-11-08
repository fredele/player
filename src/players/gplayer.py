#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst,GObject
import _thread
import time,urllib
import os
import datetime

from utils.player_logging import log_debug, log_warning
from players.custombins import GstBs2bCustom, GstLoudnessCustom , GstLoudnessCustomAdaptive

class GPlayer():

    def _debug(self, action, **details):
        log_debug("GPlayer", action, **details)

    def _warning(self, action, **details):
        log_warning("GPlayer", action, **details)

    def Loop(self):
        mainloop = GObject.MainLoop()
        mainloop.run()

    def func(self,playbin):
        self.audio_changed(self.id)

    def __init__(self,app,state_changed,audio_changed,spectrum):

        self.transcode = False #Set this to use /Transcode URLS's
        self.app = app
        self.manual_paused = False
        log_debug("GPlayer", "__init__", player_id=getattr(self, 'id', 'unknown'))
        self.spectrum = spectrum
        self.audio_changed = audio_changed
        self.st = state_changed
        self.queue = []
        self.queue_position = 0
        self._debug("__init__|starting gst", player_id=getattr(self, 'id', 'unknown'))
        Gst.init(None)
        GObject.threads_init()
        self.playbin = Gst.ElementFactory.make("playbin", "player")

        # DO NOT REMOVE ...utile pour le stream ...
        self.playbin.set_property("buffer-size", 50 << 20)  # 50MB
        self.playbin.set_property("buffer-duration", 60*1 * Gst.SECOND)
        self.playbin.connect("about-to-finish",  self.about_to_finish)
        self.playbin.connect("audio-changed", self.func)
        self.playbin.connect("deep-notify::temp-location", self.temp_loc)

        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message::tag", self.bus_message_tag)
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        bus.connect("message::buffering", self.on_buffering)
        bus.connect("message::state-changed", self.on_state_changed)
        bus.connect("message", self.handle_message)
        
      
        # Enregistrement du type de la classe dans PyGObject
        bs2b_custom_type = GObject.type_register(GstBs2bCustom)
        Gst.Element.register(None, "bs2b_custom", Gst.Rank.NONE, bs2b_custom_type)

        loudness_custom_type = GObject.type_register(GstLoudnessCustom)
        Gst.Element.register(None, "loudness_custom", Gst.Rank.NONE, loudness_custom_type)  

        loudness_adapative_custom_type = GObject.type_register(GstLoudnessCustomAdaptive)
        Gst.Element.register(None, "loudness_adaptative_custom", Gst.Rank.NONE, loudness_adapative_custom_type) 
        
        _thread.start_new_thread(self.Loop, ())

        # init volume
        self.default_volume = self.app.defaultvolume
        self.set_volume(self.default_volume)
        self.volume_restore = self.default_volume
        app.volumelevel =self.default_volume

        self.last_changed = 0
        self.old_state = [None, None]

    def handle_message(self,bus, message):
        if message.type == Gst.MessageType.ELEMENT:
            struct = Gst.Message.get_structure(message)
            if struct is None:
                self._debug("handle_message|element_without_structure", message_type=message.type)
                return

            name = Gst.Structure.get_name(struct)
            if 'spectrum' == name:
                try:
                    magn = struct.get_list('magnitude').array
                    values = [magn.get_nth(i) for i in range(0, magn.n_values)]
                    self.spectrum('spectrum', self.id, values)
                except Exception:
                    self._warning("handle_message|spectrum_parse_error", player_id=self.id)
            if 'level' == name:
                try:
                    rms = struct.get_value('rms')
                    peak = struct.get_value('peak')
                    decay = struct.get_value('decay')
                    self.spectrum('level', self.id, rms)
                except Exception:
                    self._warning("handle_message|level_parse_error", player_id=self.id)

    def temp_loc(self,a,b,c):
        self._debug("temp_loc", temp_location=b)

    def about_to_finish(self,var):
        if int(self.queue_position) < int(len(self.queue) - 1):
            self._debug("about_to_finish|advance_queue", player_id=self.id, queue_position=self.queue_position, queue_length=len(self.queue))
            self.queue_position += 1

            if self.queue_position >= len(self.queue):
                self._warning("about_to_finish|queue_index_out_of_range", player_id=self.id, queue_position=self.queue_position, queue_length=len(self.queue))
                return

            if 'file' in self.queue[self.queue_position]:
                self.set_path(self.queue[self.queue_position])
            if 'uri' in self.queue[self.queue_position]:
                self.set_uri(self.queue[self.queue_position])
        else:
            self._debug("about_to_finish|queue_end_reached", player_id=self.id, queue_position=self.queue_position, queue_length=len(self.queue))

    def send_eos(self):
        self.playbin.send_event(Gst.Event.new_eos())

    def set_pipeline(self, pipeline=None):
        self.playbin.set_property('volume', 0)

        try:
            state = int(self.playbin.get_state(0)[1])
            pos = int(self.playbin.query_position(Gst.Format.TIME)[1])
        except Exception:
            state = Gst.State.NULL
            pos = 0
            self._warning("set_pipeline|state_query_failed", player_id=getattr(self, 'id', 'unknown'))

        try:
            self.playbin.set_state(Gst.State.NULL)
            self._debug("set_pipeline|reset_pipeline", player_id=getattr(self, 'id', 'unknown'))
        except Exception:
            self._warning("set_pipeline|reset_pipeline_failed", player_id=getattr(self, 'id', 'unknown'))

        try:
            icon = os.path.join(os.getenv("HOME"), ".config", "Player", "player.xpm")
            output = self.app.outputs[self.app.current_output]["gstpipeline"]
            output = output.replace("$icon$", icon)
            self._debug("set_pipeline|building_bin", output=output[:180], player_id=getattr(self, 'id', 'unknown'))
            self.audiobin = Gst.parse_bin_from_description(output, True)
        except Exception:
            self._warning("set_pipeline|parse_bin_failed", player_id=getattr(self, 'id', 'unknown'))

        try:
            self.playbin.set_property('audio-sink', self.audiobin)
            self.playbin.set_state(state)
            time.sleep(2)
            self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, pos)
            self.set_volume(self.volume_restore)
            self._debug("set_pipeline|pipeline_restored", player_id=getattr(self, 'id', 'unknown'), state=state, position=pos)
        except Exception:
            self._warning("set_pipeline|restore_pipeline_failed", player_id=getattr(self, 'id', 'unknown'))
        try:
            bus = self.playbin.get_bus()
            bus.add_signal_watch()
            bus.connect("message::tag", self.bus_message_tag)
            bus.connect("message::eos", self.on_eos)
            bus.connect("message::buffering", self.on_buffering)
            bus.connect("message::error", self.on_error)
            bus.connect("message::state-changed", self.on_state_changed)
            bus.connect("message::element", self.on_element_message)
        except Exception:
            self._warning("set_pipeline|bus_connections_failed", player_id=getattr(self, 'id', 'unknown'))
        try:
            self.loudness = self.playbin.get_by_name("mon_loudness")
        except Exception:
            pass
            
    def on_element_message(self, bus, message):
        if message.has_name("level"):
            if hasattr(self, 'loudness') and self.loudness is not None:
                self.loudness.analyser_message_bus(message)


    def on_eos(self, bus, msg):
        self._debug("on_eos|end_of_stream", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position)
        self.eof()

    def on_buffering(self, bus, msg):
        pass
        '''
        try:
            buffer_percent = Gst.Message.get_structure(msg).get_value("buffer-percent")
            self._debug("on_buffering", player_id=getattr(self, 'id', 'unknown'), buffer_percent=buffer_percent)
        except Exception:
            self._debug("on_buffering|no_buffer_info", player_id=getattr(self, 'id', 'unknown'))
        '''

    def eof(self):
        if self.app.restartqueue == True and int(self.queue_position) == int(len(self.queue) - 1):
            self._debug("eof|restart_queue", player_id=getattr(self, 'id', 'unknown'))
            self.set_stop()
            time.sleep(.5)
            self.queue_position = 0
            self.set_uri({"uri": self.get_uri_from_path(self.queue[self.queue_position])})
            self.set_play()
        else:
            msg = {}
            time.sleep(.2)
            msg['message'] = 'end of stream'
            msg['id'] = self.app.player['id']
            if self.app.restartqueue == False:
                self._debug("eof|stream_finished", player_id=getattr(self, 'id', 'unknown'))
                self.set_stop()
                self.app.wssp.broadcast_message(msg)

    def on_error(self, bus, msg):
        try:
            err, dbg = msg.parse_error()
            self._warning("on_error|gst_error", player_id=getattr(self, 'id', 'unknown'), error=str(err), debug=str(dbg))
        except Exception:
            self._warning("on_error|gst_error_unparsed", player_id=getattr(self, 'id', 'unknown'))

    def on_state_changed(self, bus, msg):
        old, new, pending = msg.parse_state_changed()
        if [old,new] != self.old_state and msg.src == self.playbin:
            self.old_state = [old, new]
            self.last_changed = datetime.datetime.now().timestamp()
            self._debug("on_state_changed", player_id=getattr(self, 'id', 'unknown'), old_state=str(old), new_state=str(new))
            if new == Gst.State.PLAYING:
                self.st(self.id,'playing')
                self.app.plugins_action('state_playing')
            elif new == Gst.State.PAUSED:
                self.st(self.id,'paused')
                self.app.plugins_action('state_paused')
            elif new == Gst.State.NULL:
                self.st(self.id,'stopped')
                self.app.plugins_action('state_stopped')

    def bus_message_tag(self,bus, message):
        #we received a tag message
        try:
            if (self.queue[self.queue_position]['uri']).startswith('http'):
                taglist = message.parse_tag()
                for x in range(taglist.n_tags()):
                    name = taglist.nth_tag_name(x)
                    if name == 'title':
                        if str(self.queue[self.queue_position]['artist'][0]) != str(taglist.get_string(name)[1]):
                            self.queue[self.queue_position]['title'] = taglist.get_string(name)[1]
        except:
            pass

    def set(self, name, prop,val):
        target = None
        for el in self.app.pm.pipeline :
            if 'name' in el:
                if el['name'] == name:
                    for p in el['props']:
                        if p['name'] == prop:
                           p['value'] = val
                           target = el

        if target is not None:
            self._debug("set|pipeline_prop_updated", player_id=getattr(self, 'id', 'unknown'), element=name, property=prop, value=val)

        if target is not None:
            el = self.audiobin.get_by_name(name)
            try:
                el.set_property(prop, val)
            except Exception:
                self._warning("set|property_not_writable", player_id=getattr(self, 'id', 'unknown'), element=name, property=prop, value=val)

    def get(self, name, prop):
        try:
            el = self.audiobin.get_by_name(name)
            return el.get_property(prop)
        except Exception:
            self._warning("get|property_not_found", player_id=getattr(self, 'id', 'unknown'), element=name, property=prop)
            return None

    def get_volume(self):
        return round(float(self.playbin.get_property('volume')),2)

    def get_position(self):
        pos =  self.playbin.query_position(Gst.Format.TIME)
        int(pos[1] / 1000000)
        return int(pos[1] / 1000000)

    def get_duration(self):
        dur = self.playbin.query_duration(Gst.Format.TIME)

        return int(dur[1] / 1000000)

    def get_state(self):
        if int(self.playbin.get_state(0)[1]) == 1:
            return 'stopped'
        if int(self.playbin.get_state(0)[1]) == 4:
            return 'playing'
        if int(self.playbin.get_state(0)[1]) == 3:
            return 'paused'

    def set_path(self,dic,position = None):
        path = dic.get('file')
        if not path:
            self._warning("set_path|missing_file", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position)
            return

        if not os.path.exists(path):
            self._warning("set_path|file_not_found", player_id=getattr(self, 'id', 'unknown'), path=path)
            return

        self._debug("set_path|prepare_uri", player_id=getattr(self, 'id', 'unknown'), path=path)
        os.chdir(self.app.root_path)
        f = urllib.parse.quote(os.path.abspath(path))
        uri = f.replace("file://", "")
        p = str(self.app.mediafiles_folder)
        h = self.app.http_server_adr
        uri = uri.replace(p, h)
        self.playbin.set_property("uri", uri)
        if self.transcode == True:
            source_path = str(dic.get('file', 'track'))
            player = next((p for p in self.app.players if str(p.get('id')) == str(self.id)), None)
            if player is not None:
                codec = str(player.get('codec', getattr(getattr(self.app, 'player', None), 'transcode_codec', 'mp3'))).lower()
            uri = f"{self.app.webadr}/v1/Transcode/{self.id}/{dic['_id']}.{codec}"
        self.playbin.set_property("uri", uri)

    def set_uri(self,dic,position = None):
        uri = dic.get('uri')
        if not uri:
            self._warning("set_uri|missing_uri", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position)
            return

        self._debug("set_uri|prepare_uri", player_id=getattr(self, 'id', 'unknown'), uri=uri)
        os.chdir(self.app.root_path)
        uri = uri.replace("file://", "")
        p = self.app.mediafiles_folder
        h = self.app.http_server_adr
        uri = uri.replace(p, h)
        self.playbin.set_property("uri", uri)
        if self.transcode == True:
            source_path = str(dic.get('file', 'track'))
            player = next((p for p in self.app.players if str(p.get('id')) == str(self.id)), None)
            if player is not None:
                codec = str(player.get('codec', getattr(getattr(self.app, 'player', None), 'transcode_codec', 'mp3'))).lower()
            uri = f"{self.app.webadr}/v1/Transcode/{self.id}/{dic['_id']}.{codec}"
        self.playbin.set_property("uri", uri)

    def set_play_uri(self):
        # if stream only ...
        self.playbin.set_state(Gst.State.PLAYING)

    def set_play(self):
        self._debug("set_play|request", player_id=getattr(self, 'id', 'unknown'))
        try:
            self.playbin.set_state(Gst.State.PLAYING)
            self.manual_paused = True
            self.app.plugins_action('set_play')
        except Exception:
            self._warning("set_play|failed", player_id=getattr(self, 'id', 'unknown'))

    def set_pause(self):
        self._debug("set_pause|request", player_id=getattr(self, 'id', 'unknown'))
        try:
            self.playbin.set_state(Gst.State.PAUSED)
            self.manual_paused = True
            self.app.plugins_action('set_pause')
        except Exception:
            self._warning("set_pause|failed", player_id=getattr(self, 'id', 'unknown'))

    def set_stop(self):
        self._debug("set_stop|request", player_id=getattr(self, 'id', 'unknown'))
        self.app.plugins_action('set_stop')
        try:
            ret = self.playbin.set_state(Gst.State.NULL)
            self.st(self.id,'stopped')
            if ret == Gst.StateChangeReturn.FAILURE:
                self._warning("set_stop|state_change_failure", player_id=getattr(self, 'id', 'unknown'))
        except Exception:
            self._warning("set_stop|failed", player_id=getattr(self, 'id', 'unknown'))

    def set_ready(self):
        self.playbin.set_state(Gst.State.READY)

    def set_volume(self,val):
        self.playbin.set_property('volume',round(val,2))
        self.volume_restore = round(val,2)

    def set_device(self,id,a,b,c):
        pass



    def quit(self):
        try:
            self.set_stop()
        except:
            pass


    def set_queue(self,list):
        self.queue = list

    def append_queue(self,list):
        self.queue.append(list)

    def get_current(self):

        return self.queue[int(self.queue_position)]

    
    def set_next(self):
        if int(self.queue_position) < int(len(self.queue) - 1):
            self._debug("set_next|request", player_id=getattr(self, 'id', 'unknown'), current_position=self.queue_position, queue_length=len(self.queue))
            self.set_stop()
            self.queue_position = int(self.queue_position) + 1
            if 'file' in self.queue[int(self.queue_position)]:
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
            if 'uri' in self.queue[int(self.queue_position)]:
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
            time.sleep(0.2)
            self.set_play()
        else:
            self._debug("set_next|already_last_track", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position, queue_length=len(self.queue))

    def set_previous(self):
        if int(self.queue_position) > 0:
            self._debug("set_previous|request", player_id=getattr(self, 'id', 'unknown'), current_position=self.queue_position)
            self.set_stop()
            self.queue_position = int(self.queue_position) - 1
            if 'file' in self.queue[int(self.queue_position)]:
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
            if 'uri' in self.queue[int(self.queue_position)]:
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
            time.sleep(0.2)
            self.set_play()
        else:
            self._debug("set_previous|already_first_track", player_id=getattr(self, 'id', 'unknown'), queue_position=self.queue_position)

    def set_queue_position(self,pos):
        self.queue_position = pos
