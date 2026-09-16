#! /usr/bin/env python
#sudo apt install libdiscid0
#pip3 install musicbrainzngs
#pip install python-slugify

import time
from os import system
from slugify import slugify
import subprocess
import sys
import argparse
import musicbrainzngs
import os
import glob
import mutagen
import requests
import libdiscid
import urllib.request
import shutil
import fcntl
import os

CDROM_DRIVE = '/dev/cdrom'


def launch_rip(app,temp,dest):
    if app.ripping == True :
        return

    if detect_tray() == 4:
        rip_cd(app,temp,dest)
    else:
        os.system("eject ")
        while (detect_tray() != 4):
            time.sleep(2)
        rip_cd(app,temp,dest)

def detect_tray():
    """detect_tray reads status of the CDROM_DRIVE.
    Statuses:
    1 = no disk in tray
    2 = tray open
    3 = reading tray
    4 = disk in tray
    """
    fd = os.open(CDROM_DRIVE, os.O_RDONLY | os.O_NONBLOCK)
    rv = fcntl.ioctl(fd, 0x5326)
    os.close(fd)
    return(rv)

def rip_cd(app,tmp,dest):
    importdest = dest
    dest = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles') +"/" +dest
    app.ripping = True
    tracks = None
    this_disc = libdiscid.read(libdiscid.default_device())
    musicbrainzngs.set_useragent("Audacious", "0.1", "https://github.com/jonnybarnes/audacious")
    try:
        result = musicbrainzngs.get_releases_by_discid(this_disc.id, includes=["artists", "recordings"])
    except musicbrainzngs.ResponseError:
        print("disc not found or bad response")
        system("eject cdrom")
        app.ripping = False
        return False
    else:
        if result.get("disc"):
            release = result["disc"]["release-list"][0]
            id = release['id']
            print(f"artist:{release['artist-credit-phrase']}")
            print(f"title:{release['title']}")
            print(f"date:{release['date']}")

            for medium in release['medium-list']:
                for disc in medium['disc-list']:
                    if disc['id'] == this_disc.id:
                        trackslist = medium['track-list']
                        trackslist = [{"position": r["position"], "title": r["recording"]["title"]} for r in trackslist]
                        discnumber = medium["position"]
                        break
                else:
                    continue
                break
            print(trackslist)

    if(trackslist == None):
        print("No CD found")
        system("eject cdrom")
        app.ripping = False
        return False

    # Check if Disc already exists ..
    cdpath = dest+"/" + slugify(release['artist-credit-phrase']) + '''/''' + str(discnumber) + "-"+slugify(release['title'])
    if os.path.exists(cdpath):
        print("CD exists !")
        system("eject cdrom")
        app.ripping = False
        return False

    folder = tmp + '/disc/'
    os.chdir(tmp)
    try:
        shutil.rmtree("disc")
    except:
        pass
    os.mkdir("disc")
    os.chdir(folder)
    os.system(''' cd "'''+ folder +'''" && cdparanoia -XB ''')
    os.system(''' cd "'''+ folder + '''" && find . -type f -iname "*.wav" -exec flac -8 {} +''')
    files_in_directory = os.listdir(folder)
    filtered_files = [file for file in files_in_directory if file.endswith(".wav")]
    for file in filtered_files:
        path_to_file = os.path.join(folder, file)
        os.remove(path_to_file)

    tracks = glob.glob(folder+'*.flac')
    tracks = sorted(tracks)
    i =0
    try:
        for track in tracks:
            tags = mutagen.File(track)
            tags["artist"] = release['artist-credit-phrase']
            tags["album"] = release['title']
            tags["date"] = release['date']
            tags["title"] = trackslist[i]["title"]
            tags["source"]="CD ripped with cd paranoia"
            tags["tracknumber"] = trackslist[i]["position"]
            tags["discnumber"] = discnumber
            tags.save()
            os.rename(track, folder + slugify(str(i+1) + "-" + trackslist[i]["title"])+".flac")
            i += 1
    except:
        pass

    cover_archive = "http://coverartarchive.org/release/" + str(id) +"/"
    r = requests.get(url = cover_archive)
    try:
        data = r.json()
        images = data["images"]
    except:
        pass
    try:
        front_images = [image  for image in images if image["front"] == True ]
        front_addr = front_images[0]["image"]
        urllib.request.urlretrieve(front_addr, folder+"cover.jpg")
    except:
        pass

    try:
        back_images = [image  for image in images if image["back"] == True ]
        back_addr = back_images[0]["image"]
        os.mkdir("artwork")
        os.chdir(folder + "/artwork")
        urllib.request.urlretrieve(back_addr, folder+"/artwork/"+"back.jpg")
    except:
        pass
    try:
        os.mkdir(dest +"/" +slugify(release['artist-credit-phrase']))
    except:
        pass
    # rename disc folder
    os.rename(folder, folder.replace("disc/","")  + slugify(release['title']))
    # copy files to dest disc folder
    cmd = '''rsync -r "''' + folder.replace("disc/","")  + slugify(release['title'])  +'''/"  ''' +'''"'''+ cdpath + '''"'''
    try:
        os.system(cmd)
    except:
        pass
    #remove temp folder

    os.chdir(tmp)
    try:
        shutil.rmtree(slugify(release['title']))
    except:
        pass
    system("eject")

    worker = app.Update_Music_Lib(app.mongo_addr, None, app, False, False, importdest, False)
    worker.start()
    app.ripping = False


