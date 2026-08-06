#!/usr/bin/python
from lxml import etree

def parseFile(file):
    res = dict()
    res['title'] = etree.parse(file).getroot()[0].text
    res['tracklist'] = [ { child.tag.split("}")[1]: child.text   for child in list(track) }  for  track in list(etree.parse(file).getroot().xpath('//ns:trackList', namespaces={'ns':"http://xspf.org/ns/0/"} )[0] )]
    return res

