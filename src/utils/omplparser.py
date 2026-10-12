import os
import opml
from flask import request
import configparser
import urllib.parse
from utils.web import get_adresse_ip_locale
from paths import mediafiles_folder, config_folder 





def read_opml(file, levels):
    
    _config = configparser.ConfigParser()
    inifile = os.path.join(config_folder, 'config.ini')
    if os.path.isfile(inifile):
        _config.read(inifile)
        port = _config['Server']['httpport']
        host = get_adresse_ip_locale()
     
     
    f = file
    file = os.path.join(mediafiles_folder,'Podcasts', file)
    items = []
    if os.path.isfile(file):
        o = opml.parse(file)
        for i in list(map(int, levels.split(';')))[1:]:
            o = o[i]
        j = 0
        for oe in o._outlines:
            dic = {}
            attrib = (oe._root.attrib)
            dic['dirhashs']=None
            myaddr = 'http://' + host + ':' + port + '/'
            dic['covers']= [myaddr +urllib.parse.quote('v1/Mediafile/Podcasts/'+ attrib.get('image',''))]
            dic['display']= attrib.get('text','')
            dic['keyval'] = j
            dic['query'] = 'file=' + str(f) + '&levels='+levels
            if attrib.get('type')=='rss':
                dic['query'] = attrib.get('xmlUrl')
            dic['url'] = attrib.get('xmlUrl', '')
            items.append(dic)
            #outlines = (o._outlines)
            j +=1

    return items



if __name__ == '__main__':
    file = '/home/fredele/Player/player/src/snippets/ompl/opml.xml'
    res = read_opml(file,'0')




