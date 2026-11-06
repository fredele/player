from utils.player_logging import log_debug


def _getLogger(name):
    """
    Retrieve a logger instance. Checks if a handler is defined so we avoid the
    'No handlers could be found' message.
    """
    log_debug("upnpclient.util", "_getLogger", logger_name=name)
    import logging
    logger = logging.getLogger(name)
    return logger
