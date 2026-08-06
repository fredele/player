import copy
from utils.string import display, to_unicode
from requests.utils import requote_uri
from utils.time import HHMMSSToMs ,MsToMMSS

#NextAVTransportURIMetaData_template ='<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"><item id="%id%" parentID="0" restricted="0"><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:title>%title%</dc:title><dc:creator>%creator%</dc:creator><upnp:album>%album%</upnp:album><upnp:artist>%artist%</upnp:artist><upnp:albumArtURI>%cover_uri%</upnp:albumArtURI><res protocolInfo="http-get:*:%type%:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000" duration="%duration%" size="%size%">%file_uri%</res></item></DIDL-Lite>'

CurrentTrackMetaData_template ='<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"><item id="%id%" parentID="0" restricted="0"><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:title>%title%</dc:title><dc:creator>%creator%</dc:creator><upnp:album>%album%</upnp:album><upnp:artist>%artist%</upnp:artist><upnp:albumArtURI>%cover_uri%</upnp:albumArtURI><res protocolInfo="http-get:*:%type%:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000" duration="%duration%" size="%size%">%file_uri%</res></item></DIDL-Lite>'
audiotype =  {"flac":"audio/x-flac" ,"mp3":"audio/mpeg"}


def set_TrackMetaData(app,dic):
    dic["uri"] = requote_uri(dic["uri"])
    try:  # construct metadata for an eventual display ..
        dic.setdefault("title", "")
        dic.setdefault("artist", "")
        dic.setdefault("album", "")
        dic.setdefault("length", 0)
        dic.setdefault("uri", "")
        dic.setdefault("dirhash", "none")
        coveruri = app.webadr + "/v1/Covers/" + str(dic["dirhash"]) + ".jpg?thumbnail=60"
    except:
        dic["meta"] = "NONE"
        return dic["meta"]

    res = copy.copy(CurrentTrackMetaData_template)

    artist = dic["artist"]
    if isinstance(artist, list):
        if len(artist)>1:
            artist =  to_unicode(artist[0] + " ...")
        else:
            artist = to_unicode(artist[0])
    else:
        artist =  to_unicode(artist)

    res = res.replace("%title%",display(dic["title"]))
    res = res.replace("%artist%", artist)
    res = res.replace("%creator%",artist)
    res = res.replace("%album%",display(dic["album"]))
    res = res.replace("%cover_uri%",coveruri)
    res = res.replace("%id%", str(dic["_id"]))
    ext = dic["uri"].rsplit(".",1)[1]
    t = audiotype.get(ext,"audio/mpeg")
    res = res.replace("%type%", t)
    res = res.replace("%duration%",MsToMMSS(dic["length"] * 1000))
    res = res.replace("%size%","0")
    res = res.replace("%file_uri%",requote_uri(display(dic["uri"])))

    return res



