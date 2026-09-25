import json
import socket


class ScanNotifier:
    def __init__(self, socket_path):
        self.socket_path = socket_path

    def __call__(self, event, **payload):
        message = {
            "event": event,
            **payload,
        }

        print(f"[{event}] {payload}", flush=True)

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(self.socket_path)

                data = json.dumps(message) + "\n"
                sock.sendall(data.encode("utf-8"))

        except (FileNotFoundError, ConnectionRefusedError):
            # Flask n'est éventuellement pas à l'écoute.
            # Le scan doit pouvoir continuer malgré cela.
            pass
