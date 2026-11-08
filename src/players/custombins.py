import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst,GObject

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

Gst.init(None)

class GstBs2bCustom(Gst.Bin):
    def do_class_init(klass):
        klass.set_metadata(
            "Bs2b Custom",
            "Filter/Effect/Audio",
            "Filtre de crossfeed",
            "fredele"
        )

    def __init__(self):
        super(GstBs2bCustom, self).__init__()
        
        # a=<1.0,-0.9051> b=<0.0949>  -> 700 Hz ,  amplification=0.5012   ->  -6.0 dB (Chu Moy)
        # a=<1.0,-0.9051> b=<0.0949>  -> 700 Hz ,  amplification=0.5957   ->  -4.5 dB (Default)
        # a=<1.0,-0.9115> b=<0.0885>  -> 650 Hz ,  amplification=0.3350   ->  -9.5 dB (Jan Meier)

        description = """
        ( deinterleave name=d 
          audiomixer name=mix_L audiomixer name=mix_R 
          interleave name=i 
          d.src_0 ! queue ! mix_L.sink_0 
          d.src_0 ! queue ! audioiirfilter name=fl a=<1.0,-0.9051> b=<0.0949> ! audioamplify amplification=0.5012 ! mix_R.sink_1 
          d.src_1 ! queue ! mix_R.sink_0 
          d.src_1 ! queue ! audioiirfilter name=fr a=<1.0,-0.9051> b=<0.0949> ! audioamplify amplification=0.5012 ! mix_L.sink_1 
          mix_L. ! i.sink_0 
          mix_R. ! i.sink_1 )
        """
        inner_bin = Gst.parse_launch(description)
        self.add(inner_bin)

        # Récupération des éléments pour les Ghost Pads
        inner_d = inner_bin.get_by_name("d")
        inner_i = inner_bin.get_by_name("i")

        # Raccordement des entrées/sorties aux parois extérieures
        sink_pad = inner_d.get_static_pad("sink")
        self.add_pad(Gst.GhostPad.new("sink", sink_pad))

        src_pad = inner_i.get_static_pad("src")
        self.add_pad(Gst.GhostPad.new("src", src_pad))




class GstLoudnessCustom(Gst.Bin):
    def do_class_init(klass):
        klass.set_metadata(
            "Loudness Custom",
            "Filter/Effect/Audio",
            "Filtre de loudness",
            "fredele"
        ) 

    def __init__(self):
        super(GstLoudnessCustom, self).__init__()

        # CORRECTION : On donne un nom au premier et au dernier élément 
        # pour pouvoir attraper leurs pads respectifs directement
        description = "audioconvert name=first_conv ! equalizer-3bands name=eq ! audioconvert name=last_conv"
        inner_bin = Gst.parse_launch(description)
        self.add(inner_bin)
        self.eq = inner_bin.get_by_name("eq")

        # 1. On récupère les éléments de l'extrême entrée et de l'extrême sortie
        first_conv = inner_bin.get_by_name("first_conv")
        last_conv = inner_bin.get_by_name("last_conv")

        # 2. On va chercher leurs vrais pads statiques (qui ne seront plus 'None')
        sink_pad = first_conv.get_static_pad("sink")
        src_pad = last_conv.get_static_pad("src")

        # 3. On crée et connecte les Ghost Pads aux parois de notre classe
        self.add_pad(Gst.GhostPad.new("sink", sink_pad))
        self.add_pad(Gst.GhostPad.new("src", src_pad))

    def set_loudness_compensation(self, current_volume):
        inverse_vol = 1.0 - current_volume
        bass_gain = inverse_vol * 12.0
        treble_gain = inverse_vol * 6.0
        self.eq.set_property("band0", bass_gain)
        self.eq.set_property("band1", 0.0)
        self.eq.set_property("band2", treble_gain)

class GstLoudnessCustomAdaptive(Gst.Bin):
    def do_class_init(klass):
        klass.set_metadata("Loudness Adaptive", "Filter/Audio", "Loudness dynamique", "fredele") 

    def __init__(self):
        super(GstLoudnessCustomAdaptive, self).__init__()

        # On insère l'élément 'level' avant l'égaliseur pour mesurer le signal entrant
        description = "audioconvert name=first ! level name=detecteur ! equalizer-3bands name=eq ! audioconvert name=last"
        inner_bin = Gst.parse_launch(description)
        self.add(inner_bin)
        
        self.eq = inner_bin.get_by_name("eq")
        self.detecteur = inner_bin.get_by_name("detecteur")
        
        # On configure l'élément level pour envoyer des rapports très fréquemment (ex: toutes les 50ms)
        self.detecteur.set_property("interval", 50000000) # en nanosecondes

        # Connecteurs Ghost Pads
        self.add_pad(Gst.GhostPad.new("sink", inner_bin.get_by_name("first").get_static_pad("sink")))
        self.add_pad(Gst.GhostPad.new("src", inner_bin.get_by_name("last").get_static_pad("src")))

    # Cette méthode devra être appelée par le bus de votre pipeline principal
    # dès qu'un message provenant de l'élément "detecteur" est intercepté.
    def analyser_message_bus(self, message):
        if message.src == self.detecteur and message.has_name("level"):
            structure = message.get_structure()
            # Récupération de la valeur RMS moyenne des canaux (en dB)
            rms_list = structure.get_value("rms")
            rms_moyen = sum(rms_list) / len(rms_list) # Valeur typique entre -60dB (silence) et 0dB (max)
            
            # Application de la formule adaptative basée sur le VRAI niveau du signal
            # Si le signal est fort (proche de 0 dB), pas de boost. 
            # S'il est faible (ex: -30 dB), on compense.
            seuil_confort = -15.0 # Niveau cible
            if rms_moyen < seuil_confort:
                manque = seuil_confort - rms_moyen # Ecart positif
                # On limite le boost max pour éviter la distorsion
                boost_basses = min(manque * 0.4, 12.0) 
                boost_aigus = min(manque * 0.2, 6.0)
            else:
                boost_basses = 0.0
                boost_aigus = 0.0

            self.eq.set_property("band0", boost_basses)
            self.eq.set_property("band2", boost_aigus)
