import inspect
import logging


def log_debug(prefix, action, **details):
    frame = inspect.currentframe().f_back
    caller_file = frame.f_code.co_filename if frame is not None else "unknown"
    caller_line = frame.f_lineno if frame is not None else 0
    caller_name = frame.f_code.co_name if frame is not None else "unknown"

    parts = [f"{key}={value}" for key, value in details.items() if value is not None]
    message = f"{prefix}|{action}|caller={caller_name}:{caller_file.rsplit('/')[-1]}:{caller_line}|{' | '.join(parts)}" if parts else f"{prefix}|{action}|caller={caller_name}:{caller_file}:{caller_line}"
    logging.debug(message)


def log_warning(prefix, action, **details):
    frame = inspect.currentframe().f_back
    caller_file = frame.f_code.co_filename if frame is not None else "unknown"
    caller_line = frame.f_lineno if frame is not None else 0
    caller_name = frame.f_code.co_name if frame is not None else "unknown"

    parts = [f"{key}={value}" for key, value in details.items() if value is not None]
    message = f"{prefix}|{action}|caller={caller_name}:{caller_file.rsplit('/')[-1]}:{caller_line}|{' | '.join(parts)}" if parts else f"{prefix}|{action}|caller={caller_name}:{caller_file}:{caller_line}"
    logging.warning(message)
