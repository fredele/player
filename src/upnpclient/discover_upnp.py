import  requests
from upnpclient.ssdp import scan
import hashlib
import  threading
from threading import Thread

def get_upnp_renderers(host):
    renderers = []
    urls = list(set([url.location for url in scan(host)]))
    for location in urls:
        try:
            res = requests.get(location)
            content =res.content.decode("utf-8")
            if "MediaRenderer" in content.split("<deviceType>")[1].split("</deviceType>")[0] :
                friendlyname = content.split("<friendlyName>")[1].split("</friendlyName>")[0]
                ip = location.split("://")[1].split("/")[0]
                hashid = ip + '@'+ friendlyname
                hashid = hashlib.sha256(hashid.encode('utf-8')).hexdigest()
                renderers.append({ "id": str(hashid), "address": location, "name" : friendlyname + " on " + ip, "saved" : "no"})
        except:
            pass
    return renderers



if __name__ == '__main__':
    print(get_upnp_renderers())
