import urllib.parse
import sys
import tkinter
from tkinter import messagebox
import requests
import  os
# Message Box



if __name__ == "__main__":
    #root = tkinter.Tk()
    #root.withdraw()
    folder = sys.argv[1:][0]
    print(folder)
    folders = [x[0] for x in os.walk(folder)]
    folders = ['Music' + f.split('/Music')[1] for f in folders]
    folder = 'Music'+folder.split('/Music')[1]
    folders.append(folder)
    folders = list(set(folders))
    folders = ";".join(folders)
    web_addr = "http://192.168.1.15:8000"
    req = web_addr + "/v1/Library/Import?folder=" + urllib.parse.quote(folders)
    print(req)
    #messagebox.showinfo("Import",req)
    r = requests.get(req)