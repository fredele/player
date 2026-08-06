#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import os
import logging

class StoreDict():

    def __init__(self, folder,filename):
        self._filepath = os.path.join(folder,filename)
        if not os.path.exists(self._filepath):
            self._initdic = {}
        else:
            with open(self._filepath) as f:
                self._initdic = json.load(f)

    def __str__(self):
        for i in  self._initdic:
            print("{0:10}: {1:0}".format(i,self._initdic[i]))
        return ''

    def get(self):
        return self._initdic

    def update(self,key,val):
        self._initdic.update({key:val})

    def save(self):
        logging.debug("StoreDict|save|file saved!")
        with open(self._filepath, 'w') as fp:
            json.dump(self._initdic, fp)


if __name__ == '__main__':

    i = StoreDict('','ini.json')

    i.update('volume',10)
    i.save()

    i = StoreDict('', 'ini.json')

    i.update('volume', 20)

