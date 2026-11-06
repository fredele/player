from utils.player_logging import log_debug

def pprint_debug(app, data):
    for k, v in data.items():
        if k in app.app.upnp__keys_to_watch:
            log_debug('pprint', 'debug', key=str(k), value=str(v))

def pprint(app,data):
    for k, v in data.items():
        print('    ' + str(k) + ' : ' + str(v))



