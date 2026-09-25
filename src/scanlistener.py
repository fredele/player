import os
import socket
import json
import threading


SOCKET_PATH = os.path.join(
    os.getenv("HOME"),
    ".Player",
    "run",
    "scan.sock"
)


class ScanSocketListener:

    EVENTS = {
        "library_scan_started",
        "library_scan_stopped",
        "library_scan_finished",
        "library_file_importing",
    }

    def __init__(
        self,
        library_scan_started=None,
        library_scan_stopped=None,
        library_scan_finished=None,
        library_file_importing=None,
    ):
        self.callbacks = {
            "library_scan_started": library_scan_started,
            "library_scan_stopped": library_scan_stopped,
            "library_scan_finished": library_scan_finished,
            "library_file_importing": library_file_importing,
        }

        self.server = None
        self.running = False
        self.thread = None

    def set_callback(self, event, callback):
        if event not in self.EVENTS:
            raise ValueError(f"Événement inconnu : {event}")

        if callback is not None and not callable(callback):
            raise TypeError(
                "Le callback doit être callable ou None"
            )

        self.callbacks[event] = callback

    def _emit(self, event, *args):
        callback = self.callbacks.get(event)

        if callback is not None:
            try:
                callback(*args)
            except Exception as e:
                print(
                    f"Erreur dans le callback {event}: {e}",
                    flush=True
                )

    def start(self):
        """Démarre le listener dans un thread daemon."""
        if self.thread is not None and self.thread.is_alive():
            return

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

    def _run(self):
        """Thread principal du socket listener."""

        try:
            # Supprimer un ancien socket
            try:
                os.unlink(SOCKET_PATH)
            except FileNotFoundError:
                pass

            self.server = socket.socket(
                socket.AF_UNIX,
                socket.SOCK_STREAM
            )

            self.server.bind(SOCKET_PATH)
            self.server.listen(5)

            self.running = True

            print(
                "Scan socket listening:",
                SOCKET_PATH,
                flush=True
            )

            while self.running:
                conn, _ = self.server.accept()

                with conn:
                    self._handle_connection(conn)

        except OSError as e:
            if self.running:
                print(
                    f"Erreur socket listener: {e}",
                    flush=True
                )

        finally:
            self.running = False

            if self.server is not None:
                self.server.close()
                self.server = None

            try:
                os.unlink(SOCKET_PATH)
            except FileNotFoundError:
                pass

    def _handle_connection(self, conn):
        buffer = b""

        while self.running:
            data = conn.recv(4096)

            if not data:
                break

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if not line:
                    continue

                self._handle_message(line)

    def _handle_message(self, line):
        try:
            message = json.loads(
                line.decode("utf-8")
            )

            print(
                "SCAN EVENT:",
                message,
                flush=True
            )

            event = message.get("event")

            if event not in self.EVENTS:
                return

            if event == "library_file_importing":
                self._emit(
                    event,
                    message.get("path")
                )
            else:
                self._emit(event)

        except Exception as e:
            print(
                f"Erreur scan socket: {e}",
                flush=True
            )

    def stop(self):
        """Arrête le listener."""

        self.running = False

        if self.server is not None:
            self.server.close()
            self.server = None

        # Le socket peut être bloqué sur accept().
        # La fermeture du socket permet normalement de le débloquer.
        if self.thread is not None:
            self.thread.join(timeout=2)

            if not self.thread.is_alive():
                self.thread = None