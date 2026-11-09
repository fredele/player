import gi
import signal
import sys

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib, GObject


Gst.init(None)


class GstBs2bCustom(Gst.Bin):

    PRESETS = {
        "chu-moy": {"cutoff": 700, "volume": 0.5, "type": 1, "poles": 4},
        "jan-meier": {"cutoff": 650, "volume": 0.335, "type": 1, "poles": 4},
        "light": {"cutoff": 700, "volume": 0.707, "type": 1, "poles": 4},
    }

    __gproperties__ = {
        "preset": (
            str, "Preset", "Preset de crossfeed", "chu-moy",
            GObject.ParamFlags.READWRITE
        ),
        "bypass": (
            bool, "Bypass", "Désactive le crossfeed", False,
            GObject.ParamFlags.READWRITE
        ),
    }

    def do_class_init(klass):
        klass.set_metadata(
            "Bs2b Custom",
            "Filter/Effect/Audio",
            "Filtre de crossfeed linéaire",
            "fredele"
        )

    def do_get_property(self, prop):
        if prop.name == "preset":
            return self._preset
        if prop.name == "bypass":
            return self._bypass
        raise AttributeError(f"Unknown property: {prop.name}")

    def do_set_property(self, prop, value):
        if prop.name == "preset":
            if value not in self.PRESETS:
                raise ValueError(f"Preset inconnu : {value}")
            self._preset = value
            self._apply_preset()
        elif prop.name == "bypass":
            self._bypass = value
            self._apply_preset()
        else:
            raise AttributeError(f"Unknown property: {prop.name}")

    def _create_element(self, factory, name):
        element = Gst.ElementFactory.make(factory, name)
        if element is None:
            raise RuntimeError(f"Impossible de créer {factory} ({name})")
        self.add(element)
        return element

    # Diagnostic automatique : chaque pad est instrumenté une seule fois.
    # Pour éviter un flot de logs, seuls les 3 premiers buffers de chaque pad
    # sont affichés. Les événements de négociation sont tous affichés.
    def _trace_pad(self, pad):
        if not hasattr(self, "_traced_pads"):
            self._traced_pads = set()

        key = (pad.get_parent_element().get_name(), pad.get_name())
        if key in self._traced_pads:
            return
        self._traced_pads.add(key)
        self._pad_buffer_counts = getattr(self, "_pad_buffer_counts", {})
        self._pad_buffer_counts[key] = 0

        def probe(_pad, info):
            parent = _pad.get_parent_element()
            element_name = parent.get_name() if parent else "?"
            label = f"{element_name}:{_pad.get_name()}"

            if info.type & Gst.PadProbeType.EVENT_DOWNSTREAM:
                event = info.get_event()
                if event is not None:
                    if event.type == Gst.EventType.CAPS:
                        print(f"[CAPS] {label}: {event.parse_caps().to_string()}")
                    elif event.type == Gst.EventType.STREAM_START:
                        print(f"[STREAM_START] {label}")
                    elif event.type == Gst.EventType.SEGMENT:
                        print(f"[SEGMENT] {label}")

            if info.type & Gst.PadProbeType.BUFFER:
                count = self._pad_buffer_counts[key]
                if count < 3:
                    buffer = info.get_buffer()
                    if buffer is not None:
                        print(f"[BUFFER {count + 1}] {label}: {buffer.get_size()} bytes")
                    self._pad_buffer_counts[key] = count + 1

            return Gst.PadProbeReturn.OK

        pad.add_probe(
            Gst.PadProbeType.EVENT_DOWNSTREAM | Gst.PadProbeType.BUFFER,
            probe
        )

    def _link(self, source, destination):
        if not source.link(destination):
            raise RuntimeError(
                f"Link impossible : {source.get_name()} -> "
                f"{destination.get_name()}"
            )
        self._trace_pad(source.get_static_pad("src"))
        self._trace_pad(destination.get_static_pad("sink"))

    def _request_link(self, source, destination, template):
        request_pad = destination.request_pad_simple(template)
        if request_pad is None:
            raise RuntimeError(
                f"Impossible de réserver {template} sur {destination.get_name()}"
            )

        src_pad = source.get_static_pad("src")
        if src_pad is None:
            raise RuntimeError(f"Pad src absent sur {source.get_name()}")

        result = src_pad.link(request_pad)
        if result != Gst.PadLinkReturn.OK:
            destination.release_request_pad(request_pad)
            raise RuntimeError(
                f"Link impossible : {source.get_name()} -> "
                f"{destination.get_name()} : {result.value_nick}"
            )

        self.request_pads.append((destination, request_pad))
        self._trace_pad(src_pad)
        self._trace_pad(request_pad)

    def _link_tee_branch(self, tee, queue):
        tee_pad = tee.request_pad_simple("src_%u")
        if tee_pad is None:
            raise RuntimeError(f"Impossible de réserver un pad sur {tee.get_name()}")

        sink_pad = queue.get_static_pad("sink")
        result = tee_pad.link(sink_pad)
        if result != Gst.PadLinkReturn.OK:
            tee.release_request_pad(tee_pad)
            raise RuntimeError(f"Link tee -> queue impossible : {result.value_nick}")

        self.request_pads.append((tee, tee_pad))
        self._trace_pad(tee_pad)
        self._trace_pad(sink_pad)

    def __init__(self):
        super().__init__()

        self._preset = "chu-moy"
        self._bypass = False
        self.request_pads = []
        self.tees = []
        self.filters = []
        self.volumes = []

        # ---------- Entrée ----------
        self.input_convert = self._create_element("audioconvert", "input_convert")

        # Tee principal (stéréo)
        self.main_tee = self._create_element("tee", "main_tee")

        self._link(self.input_convert, self.main_tee)

        # ---------- Mixers + interleave ----------
        self.interleave = self._create_element("interleave", "i")
        self.output_convert = self._create_element("audioconvert", "output_convert")
        self._link(self.interleave, self.output_convert)

        self.mixers = [
            self._create_element("audiomixer", "mix_l"),
            self._create_element("audiomixer", "mix_r"),
        ]

        self.mix_converts = []
        for index, mixer in enumerate(self.mixers):
            convert = self._create_element("audioconvert", f"mix_convert_{index}")
            caps = self._create_element("capsfilter", f"mix_caps_{index}")
            # On force un format stable pour l'interleave
            caps.set_property(
                "caps",
                Gst.Caps.from_string(
                    "audio/x-raw,format=F32LE,channels=1,layout=interleaved"
                )
            )
            self._link(mixer, convert)
            self._link(convert, caps)
            self._request_link(caps, self.interleave, "sink_%u")
            self.mix_converts.append(convert)

        # ---------- Extraction des deux canaux ----------
        self.channel_tees = []
        self.direct_queues = []
        self.cross_queues = []

        channel_masks = [
            "(bitmask)0x1",   # Left
            "(bitmask)0x2",   # Right
        ]

        for channel in range(2):
            # Branche depuis le tee principal
            queue = self._create_element("queue", f"extract_queue_{channel}")
            convert = self._create_element("audioconvert", f"extract_convert_{channel}")
            caps = self._create_element("capsfilter", f"extract_caps_{channel}")
            caps.set_property(
                "caps",
                Gst.Caps.from_string(
                    f"audio/x-raw,channels=1,channel-mask={channel_masks[channel]},layout=interleaved"
                )
            )

            self._link_tee_branch(self.main_tee, queue)
            self._link(queue, convert)
            self._link(convert, caps)

            # Tee par canal (direct + cross)
            tee = self._create_element("tee", f"tee_{channel}")
            self._link(caps, tee)
            self.channel_tees.append(tee)

            # Chemins direct et cross
            direct_queue = self._create_element("queue", f"direct_queue_{channel}")
            cross_queue = self._create_element("queue", f"cross_queue_{channel}")
            cross_convert = self._create_element("audioconvert", f"cross_convert_{channel}")
            filt = self._create_element("audiocheblimit", f"filter_{channel}")
            volume = self._create_element("volume", f"volume_{channel}")

            self._link_tee_branch(tee, direct_queue)
            self._link_tee_branch(tee, cross_queue)

            # Direct → mixer du même côté
            self._request_link(direct_queue, self.mixers[channel], "sink_%u")

            # Cross → filtre → volume → mixer de l'autre côté
            self._link(cross_queue, cross_convert)
            self._link(cross_convert, filt)
            self._link(filt, volume)
            self._request_link(volume, self.mixers[1 - channel], "sink_%u")

            self.direct_queues.append(direct_queue)
            self.cross_queues.append(cross_queue)
            self.filters.append(filt)
            self.volumes.append(volume)

        # ---------- Ghost pads ----------
        self._trace_pad(self.input_convert.get_static_pad("sink"))
        self._trace_pad(self.output_convert.get_static_pad("src"))

        sink_ghost = Gst.GhostPad.new("sink", self.input_convert.get_static_pad("sink"))
        src_ghost = Gst.GhostPad.new("src", self.output_convert.get_static_pad("src"))

        if sink_ghost is None or not self.add_pad(sink_ghost):
            raise RuntimeError("Impossible de créer le pad sink")
        if src_ghost is None or not self.add_pad(src_ghost):
            raise RuntimeError("Impossible de créer le pad src")

        self._apply_preset()
      
    def _on_deinterleave_pad_added(self, element, pad):
        name = pad.get_name()
        print(f"[PAD ADDED] deinterleave:{name}")
        self._trace_pad(pad)

        if name == "src_0":
            channel = 0
        elif name == "src_1":
            channel = 1
        else:
            print(f"[WARNING] Pad inattendu de deinterleave : {name}")
            return

        tee = self.tees[channel]
        sink_pad = tee.get_static_pad("sink")
        result = pad.link(sink_pad)
        print(f"[LINK] deinterleave:{name} -> {tee.get_name()}: {result.value_nick}")

        if result != Gst.PadLinkReturn.OK:
            print(f"[ERROR] Échec de liaison de {name}: {result.value_nick}")
        else:
            self._trace_pad(sink_pad)

    def _apply_preset(self):
        preset = self.PRESETS[self._preset]

        for filt in self.filters:
            filt.set_property("cutoff", preset["cutoff"])
            filt.set_property("type", preset["type"])
            filt.set_property("poles", preset["poles"])

        volume = 0.0 if self._bypass else preset["volume"]
        for vol in self.volumes:
            vol.set_property("volume", volume)




icon = "/usr/share/icons/hicolor/256x256/apps/player.png"

output = (
  
    'audioconvert ! '
    'audioresample ! '
    'audio/x-raw,channels=2,channel-mask=(bitmask)0x3,layout=interleaved ! '
    'bs2b_custom ! '
    'pulsesink '
    'client-name="Player" '
    f'stream-properties="props,application.icon_name={icon}"'
)

audiobin = Gst.parse_bin_from_description(output, True)

uri = "file:///home/fredele/MyPlayer/player/audio_test/tones/right_200Hz.wav"  
playbin = Gst.ElementFactory.make("playbin", "player")
playbin.set_property("uri", uri)
playbin.set_property("audio-sink", audiobin)


loop = GLib.MainLoop()
bus = playbin.get_bus()
bus.add_signal_watch()


def on_message(bus, message):
    if message.type == Gst.MessageType.ERROR:
        error, debug = message.parse_error()
        print("GSTREAMER ERROR:", error)
        print("DEBUG:", debug)
        loop.quit()
    elif message.type == Gst.MessageType.EOS:
        print("Fin du flux")
        loop.quit()


bus.connect("message", on_message)


def stop_pipeline(*args):
    loop.quit()


signal.signal(signal.SIGINT, stop_pipeline)
signal.signal(signal.SIGTERM, stop_pipeline)

result = playbin.set_state(Gst.State.PLAYING)

if result == Gst.StateChangeReturn.FAILURE:
    print("Impossible de démarrer le pipeline")
    sys.exit(1)

print("Lecture du signal 440 Hz. Ctrl+C pour arrêter.")
print("Diagnostic automatique actif : CAPS, événements et 3 premiers buffers par pad.")

try:
    loop.run()
finally:
    playbin.set_state(Gst.State.NULL)
