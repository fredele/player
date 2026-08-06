#!/usr/bin/python
# -*- coding: utf-8 -*-

#https://docs.python.org/2/library/xml.sax.handler.html

import  xml.sax

class ite():
    def __init__(self):
        pass

class swdbHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.flag = 0
        self.path = ''
        self.res = {}
        self.itemlist = []

    def startElement(self, name, attrs):
        self.path += "/%s" % name

        if self.path == '/rss/channel/item':
            self.item = ite()
        if self.path == '/rss/channel/image':
            self.image = dict()
        if self.path == '/rss/channel/item/enclosure':
            self.item.url = attrs.get('url', '')

    def endElement(self, name):
        if self.path == '/rss/channel/item':
            self.itemlist.append(self.item)

        offset = self.path.rfind("/")
        if offset >= 0:
            self.path = self.path[0:offset]

    def characters(self, content):
        #print (self.path)
        if self.path == '/rss/channel/title':
            self.res['title'] = content
        if self.path == '/rss/channel/link':
            self.res['link'] = content
        if self.path == '/rss/channel/description':
            self.res['description'] = content
        if self.path == '/rss/channel/language':
            self.res['language'] = content
        if self.path == '/rss/channel/copyright':
            self.res['copyright'] = content
        if self.path == '/rss/channel/lastBuildDate':
            self.res['lastBuildDate'] = content
        if self.path == '/rss/channel/generator':
            self.res['generator'] = content
        if self.path == '/rss/channel/':
            self.res['lastBuildDate'] = content

        #image
        if self.path == '/rss/channel/image/url':
            self.image_url  = content
        if self.path == '/rss/channel/image/title':
            pass
        if self.path == '/rss/channel/image/link':
            pass
        if self.path == '/rss/channel/media:thumbnail':
            self.image_url  = content

        #item
        if self.path == '/rss/channel/item/title':
            self.item.title = content
        if self.path == '/rss/channel/item/link':
            pass
        if self.path == '/rss/channel/item/description':
            self.item.description= content
        if self.path == '/rss/channel/item/author':
            self.item.author = content
        if self.path == '/rss/channel/item/category':
            self.item.category = content
        if self.path == '/rss/channel/item/enclosure':
            self.item.enclosure = content
        # if self.path == '/rss/channel/item/guid':
        #     self.item.enclosure_url = content
        if self.path == '/rss/channel/item/pubDate':
            self.item.pubDate = content
        if self.path == '/rss/channel/item/podcastRF:businessReference':
            self.item.podcastRF_businessReference = content
        if self.path == '/rss/channel/item/itunes:duration':
            self.item.itunes_duration = content
        if self.path == '/rss/channel/item/podcastRF:magnetothequeID':
            self.item.podcastRF_magnetothequeID= content
        if self.path == '/rss/channel/item/podcastRF:stepID':
            self.item.podcastRF_stepID = content

    def getResult(self):
            self.res['items'] = self.itemlist
            return self.res

class Podcast():
    def __init__(self,xml_str):
        h = swdbHandler()
        xml.sax.parseString(xml_str, h)
        self.items = h.itemlist
        if hasattr(h,'image_url') :
            self.image_url = h.image_url



if __name__ == '__main__':

    with open("rss_12250.xml", "r") as myfile:
        f_list = myfile.readlines()
        xml_str = ''.join(f_list)

    podcast = Podcast(xml_str)

    for it in podcast.items:
        #print(it.title)
        #print(podcast.image_url)
        #print(it.enclosure_url)
        #print(it.itunes_duration)
        pass
