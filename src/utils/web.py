#import urllib2
#import SSL
import socket

def http_file_exists(location):
    request = urllib2.Request(location)
    request.get_method = lambda : 'HEAD'
    try:

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        response = urllib2.urlopen(request, context=ctx)
        return True
    except urllib2.HTTPError:
        return False

def get_adresse_ip_locale():
    """
    Retourne l'adresse IP locale de la machine (IPv4),
    que la connexion soit en Ethernet ou Wi-Fi.
    """
    try:
        # On crée une socket UDP et on "connecte" à une adresse externe publique
        # (8.8.8.8 est un DNS de Google, peu importe si la connexion réussit vraiment)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Erreur : impossible de récupérer l'IP ({e})"