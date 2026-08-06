#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst,GObject
import _thread
import time,urllib
import os
import datetime

class GPlayer():

    def Loop(self):
        mainloop = GObject.MainLoop()
        mainloop.run()

    def func(self,playbin):
        self.audio_changed(self.id)

    def __init__(self,app,state_changed,audio_changed,spectrum):

        self.transcode = False #Set this to use /Transcode URLS's
        self.app = app
        self.manual_paused = False
        logging.info("GPlayer|__init__|Initialize GStreamer Player")
        self.spectrum = spectrum
        self.audio_changed = audio_changed
        self.st = state_changed
        self.queue = []
        self.queue_position = 0
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

        _thread.start_new_thread(self.Loop, ())

        # init volume
        self.default_volume = self.app.defaultvolume
        self.set_volume(self.default_volume)
        self.volume_restore = self.default_volume
        app.volumelevel =self.default_volume

        self.last_changed = 0
        self.old_state = [None, None]

    def handle_message(self,bus, message):
        #print(str(bus.name))
        if message.type == Gst.MessageType.ELEMENT:
            #print(str(message.src))
            struct = Gst.Message.get_structure(message)
            if 'spectrum' == Gst.Structure.get_name(struct):
                magn = struct.get_list('magnitude').array
                values = [magn.get_nth(i) for i in range(0, magn.n_values)]
                self.spectrum('spectrum',self.id,values)
            if 'level' == struct.get_name():
                rms = struct.get_value('rms')
                peak = struct.get_value('peak')
                decay = struct.get_value('decay')

                self.spectrum('level',self.id,rms)

    def temp_loc(self,a,b,c):
        print(b)

    def about_to_finish(self,var):
        if int(self.queue_position) < int(len(self.queue) - 1):
            # play next track
            self.queue_position += 1

            if 'file' in self.queue[self.queue_position]:
                self.set_path(self.queue[self.queue_position])
            if 'uri' in self.queue[self.queue_position]:
                self.set_uri(self.queue[self.queue_position])
        else:
            pass

    def send_eos(self):
        self.playbin.send_event(Gst.Event.new_eos())

    def set_pipeline(self, pipeline=None):
        self.playbin.set_property('volume', 0)

        state = int(self.playbin.get_state(0)[1])
        pos= int(self.playbin.query_position(Gst.Format.TIME)[1])

        try:
            # Hangs on non-valid output !
            self.playbin.set_state(Gst.State.NULL)

        except:
            logging.debug("GPlayer|__set_pipeline__|set_state(Gst.State.NULL)")

        try:
            icon = os.path.join(os.getenv("HOME"), ".Player","config", "player.xpm")
            output = self.app.outputs[self.app.current_output]["gstpipeline"]
            output = output.replace("$icon$", icon)
            logging.info("GPlayer|__set_pipeline__to:|"+output)
            self.audiobin = Gst.parse_bin_from_description(output, True)
        except:
            logging.debug("GPlayer|__set_pipeline__|parse_bin_from_description")

        try:

            self.playbin.set_property('audio-sink', self.audiobin)
            #self.playbin.set_property('video-sink', Gst.parse_bin_from_description("ximagesink name=outputvideosink", True))
            self.playbin.set_state(state)
            time.sleep(2)
            self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, pos)
            self.set_volume(self.volume_restore)
        except:
            logging.debug("GPlayer|__set_pipeline__|set_volume")
        try:
            bus = self.playbin.get_bus()
            bus.add_signal_watch()
            bus.connect("message::tag", self.bus_message_tag)
            bus.connect("message::eos", self.on_eos)
            bus.connect("message::buffering", self.on_buffering)
            bus.connect("message::error", self.on_error)
            bus.connect("message::state-changed", self.on_state_changed)
        except:
            logging.debug("GPlayer|__set_pipeline__|message::state-changed")

    def on_eos(self, bus, msg):
        self.eof()

    def on_buffering(self, bus, msg):
        buffer_percent =Gst.Message.get_structure(msg).get_value("buffer-percent")
        #print(f"buffering done at {buffer_percent} %")
        pass

    def eof(self):
        # Fires only at the end of the queue
        if self.app.restartqueue == True and int(self.queue_position) == int(len(self.queue) - 1):
            # Last file
            self.set_stop()
            time.sleep(.5)
            self.queue_position = 0
            self.set_uri({"uri" :self.get_uri_from_path(self.queue[self.queue_position])})
            self.set_play()
        else:
            msg = {}
            time.sleep(.2)
            msg['message'] = 'end of stream'
            msg['id'] = self.app.player['id']
            if self.app.restartqueue == False:
                self.set_stop()
                self.app.wssp.broadcast_message(msg)

    def on_error(self, bus, msg):
        err, dbg = msg.parse_error()
        logging.debug("GPlayer Error : " + dbg)

    def on_state_changed(self, bus, msg):
        old, new, pending = msg.parse_state_changed()
        if [old,new] != self.old_state and msg.src == self.playbin:
            self.old_state = [old, new]
            self.last_changed = datetime.datetime.now().timestamp()
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
        # Set the value in the pipeline ...
        for el in self.app.pm.pipeline :
            if 'name' in el:
                if el['name'] == name:
                    for p in el['props']:
                        if p['name'] == prop:
                           p['value'] = val

        # Set the value in the pipeline ...
        if el is not None:
            el =self.audiobin.get_by_name(name)
            try:
                el.set_property(prop, val)
            except:
                print('not writable ...')

    def get(self, name, prop):
        el =self.audiobin.get_by_name(name)
        return el.get_property(prop)

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
        path= dic['file']
        os.chdir(self.app.root_path)
        f =urllib.parse.quote(os.path.abspath(path))
        uri = f.replace("file://", "")
        p = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
        h = self.app.http_server_adr
        uri = uri.replace(p, h)
        print(f"set_uri: {uri}")
        self.playbin.set_property("uri", uri)
        if self.transcode == True:
            uri = self.app.webadr + "/v1/Transcode/" + dic["_id"] # A masquer
        self.playbin.set_property("uri", uri)

    def set_uri(self,dic,position = None):
        os.chdir(self.app.root_path)
        uri = dic["uri"].replace("file://", "")
        p = os.path.join(os.getenv("HOME"), '.Player', "mediafiles")
        h = self.app.http_server_adr
        uri = uri.replace(p, h)
        self.playbin.set_property("uri",uri)
        if self.transcode == True:
            uri = self.app.webadr + "/v1/Transcode/" + dic["_id"] # A masquer
        print(f"set_uri: {uri}")
        self.playbin.set_property("uri", uri)

    def set_play_uri(self):
        # if stream only ...
        self.playbin.set_state(Gst.State.PLAYING)

    def set_play(self):
        self.playbin.set_state(Gst.State.PLAYING)
        self.manual_paused = True
        self.app.plugins_action('set_play')

    def set_pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.manual_paused = True
        self.app.plugins_action('set_pause')

    def set_stop(self):
        self.app.plugins_action('set_stop')
        ret= self.playbin.set_state(Gst.State.NULL)
        self.st(self.id,'stopped')
        if ret == Gst.StateChangeReturn.FAILURE:
            pass

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
            self.set_stop()
            self.queue_position = int(self.queue_position) + 1
            if 'file' in self.queue[int(self.queue_position)]:
                # file ='file://' + urllib.parse.quote(os.path.abspath(self.queue[int(self.queue_position)]['file']))
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
            if 'uri' in self.queue[int(self.queue_position)]:
                # file = self.queue[int(self.queue_position)]['uri']       
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
            time.sleep(0.2)
            self.set_play()
            
    def set_previous(self):
        if int(self.queue_position) > 0:
            self.set_stop()
            self.queue_position = int(self.queue_position) - 1
            if 'file' in self.queue[int(self.queue_position)]:
                # file = 'file://' + urllib.parse.quote( os.path.abspath(self.queue[int(self.queue_position)]['file']))
                self.set_path(self.queue[int(self.queue_position)], self.queue_position)
            if 'uri' in self.queue[int(self.queue_position)]:
                # file = self.queue[int(self.queue_position)]['uri']
                self.set_uri(self.queue[int(self.queue_position)], self.queue_position)
            time.sleep(0.2)
            self.set_play()

    def set_queue_position(self,pos):
        self.queue_position = pos
