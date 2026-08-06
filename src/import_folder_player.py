import urllib.parse
import sys
import requests
import  os

if __name__ == "__main__":

    folder = sys.argv[1:][0]
    folder = 'Music'+folder.split('/music')[1]
    print(folder)
    web_addr = "http://192.168.1.14:8001"
    req = web_addr + "/v1/Library/Import?folder=" + urllib.parse.quote(folder)
    print(req)
    #messagebox.showinfo("Import",req)
    #r = requests.get(req)
