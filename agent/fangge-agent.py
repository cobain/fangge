#!/usr/bin/python

# add the next line to /etc/rc.local
# cd /home/pi/;./fangge-agent.py

import logging
import traceback
import time
import subprocess
import urllib
import urllib2
import re
import argparse
from os import listdir
from os.path import isdir, isfile, join



JB_ID = "test"
DELAY = 70
DELAY_SHORT = 7
URL_PREFIX = "http://www.bookxclub.com/";
PLAYLIST = "test.m3u"
song_list = []
TOKEN = "testtoken"

def init():
    print "init..."

def check_usb():
    folders = ['/media/usb0', '/media/usb1', '/media/usb2', '/media/usb3',
        '/media/usb4', '/media/usb5', '/media/usb6', '/media/usb7']
    for folder in folders:
        if isdir(folder):
            files = listdir(folder)
            if files and len(files)>0:
                return folder
    return None


def play_song(song):
    uname = subprocess.check_output(['uname', '-a'])
    if re.search("Darwin", uname):
        return subprocess.call("/Applications/VLC.app/Contents/MacOS/VLC --play-and-exit -I dummy \"%s\"" % song, shell=True)
    elif re.search("raspberrypi", uname):
        return subprocess.call(["cvlc", "--play-and-exit", "-I", "dummy", song])
    else:
        print "unknow system, don't know how to play"
        return -1

def get_jb_info():
    ip = ""
    try:
        ip = args.info+"-"+subprocess.check_output(["hostname", "-I"])
    except:
        ip = args.info
    return ip

def register_music(music_folder):
    global song_list
    song_list = sorted([f for f in listdir(music_folder) if isfile(join(music_folder, f))])
    onlyfiles = ["%d %s" % (i+1, f) for i, f in enumerate(song_list)]
    print("%s" % onlyfiles)
    url = URL_PREFIX + 'musiclist'
    values = {
            'jukebox' : JB_ID,
            'info': get_jb_info(),
            'songs': '\n'.join(song_list),
            'token': TOKEN
            }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    rtn = response.read()
    print("register %s" % rtn)

def job(music_folder):
    print("%s play music..." % time.strftime("%Y/%m/%d-%H:%M:%S"))

    song = urllib2.urlopen(URL_PREFIX+'playlist/current?jukebox='+JB_ID).read()
    if song:
        print("...play song: "+song)
        p = re.compile(r'^#STOP')
        if p.match(song):
            print("...received: %s" % song)
            time.sleep(DELAY)
        else:
            try:
                p = re.compile(r'^\d+')
                if p.match(song):
                    song_name = song_list[int(song)-1]
                song_name = music_folder+"/"+song_name
                rtn = play_song(song_name)
                print ("song play returned: %s" % rtn)
            except Exception as e:
                print("play error: %s %s" % (song, e))
            # delete song from the server whatever
            values = {
                'jukebox': JB_ID,
                'token': TOKEN
            }
            data = urllib.urlencode(values)
            req = urllib2.Request(URL_PREFIX+"playlist/delete", data)
            response = urllib2.urlopen(req)
            song_deleted = response.read()
            if song != song_deleted:
                print("...inconsistent songs: %s - %s" % (song, song_deleted))
            time.sleep(DELAY_SHORT)
    else:
        print("no song received.")
        time.sleep(DELAY)


# main
parser = argparse.ArgumentParser(description='play songs under a folder')
parser.add_argument('--id', dest='id', required='true',
                   help='id of this agent')
parser.add_argument('--path', dest='path', default='Music',
                   help='path to music')
parser.add_argument('--url', dest='url', default='http://www.bookxclub.com/', help='server url')
parser.add_argument('--info', dest='info', default="", help='server url')
parser.add_argument('--token', dest='token', required='true', help='token to connect to the server')
parser.add_argument('--usb', dest='usb', default=False, action='store_true')

args = parser.parse_args()
JB_ID = args.id
URL_PREFIX = args.url
TOKEN=args.token
current_path = args.path
print "ID: %s, Music folder: %s" % (JB_ID, current_path)

time.sleep(DELAY_SHORT)    # without this rc.local will fail!
init()
register_music(current_path)
while True:
    try:
        job(current_path)
        if args.usb:
            usb_path = check_usb()
            if usb_path:
                current_path = usb_path
                register_music(current_path)
    except KeyboardInterrupt:
        print("Bye!")
        import sys;sys.exit(0)
    except Exception as e:
        logging.error(traceback.format_exc())