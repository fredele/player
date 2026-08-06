import logging

def pprint_debug(app, data):
    for k, v in data.items():
        if k in app.app.upnp__keys_to_watch:
            logging.debug('    ' + str(k) + ' : ' + str(v))

def pprint(app,data):
    for k, v in data.items():
        print('    ' + str(k) + ' : ' + str(v))



