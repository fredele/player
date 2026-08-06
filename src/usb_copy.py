#!/usr/bin/env python3

import os
import subprocess
import time
import getpass
import threading
import urllib.parse
from gi.repository import Gio, GLib
import requests

class USBCopyMonitor(threading.Thread):
    def __init__(self,owner):
        super().__init__(daemon=True)  # daemon pour que le thread s'arrête avec le programme principal
        self.owner = owner
        self.user = getpass.getuser()
        self.media_path = f"/media/{self.user}/"
        self.destination_music = f"/home/{self.user}/.Player/mediafiles"

    def extract_copied_files(self, lines):
        """
        Extrait la liste des fichiers audio copiés à partir de la sortie rsync verbose.
        Extensions prises en charge : .mp3, .flac, .ogg, .wav, .m4a
        """
        audio_extensions = self.owner.audioextension
        copied_audio = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # On cherche une ligne avec un nom de fichier/dossier
            if line and not line.startswith(' ') and line != './' and not line.endswith('/'):
                # Vérifie si c'est un fichier avec une extension audio
                if any(line.lower().endswith(ext) for ext in audio_extensions):
                    # On regarde les lignes suivantes pour voir s'il y a un transfert réel
                    # (présence d'une ligne de progression ou "(xfr#")
                    has_transfer = False
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith(' ') or lines[j] == ''):
                        if "(xfr#" in lines[j]:
                            has_transfer = True
                            break
                        j += 1

                    if has_transfer:
                        copied_audio.append(line)

            i += 1

        return copied_audio

    def extract_directories(self, audio_files):

        album_dirs = set()

        for file_path in audio_files:
            # Normalise le chemin
            normalized_path = os.path.normpath(file_path)

            # Le dossier parent direct du fichier = dossier de l'album
            album_dir = os.path.dirname(normalized_path)

            # Vérifie qu'il y a bien au moins un fichier audio dedans (redondant mais sûr)
            if any(normalized_path.lower().endswith(ext) for ext in ['.mp3', '.flac', '.ogg', '.wav', '.m4a']):
                album_dirs.add(album_dir)

        # Retourne trié pour un affichage propre (optionnel)
        return sorted(album_dirs)

    def copy_and_unmount(self, mount_path):
        source_music = os.path.join(mount_path, "mediafiles")
        if not os.path.exists(source_music):
            print(f"Pas de dossier mediafiles sur {mount_path}")
            return

        print(f"Copie mediafiles de {source_music} vers {self.destination_music}")
        print("Copie en cours...")

        try:
            result = subprocess.run([
                "rsync", "-rlDK", "--progress", "--no-perms",
                source_music + "/",
                self.destination_music + "/"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("Copie terminée avec succès !\n")

                # Affichage des éléments réellement copiés
                lines = result.stdout.strip().split("\n")
                copied_items = self.extract_copied_files(lines)

                if copied_items:
                    folders = self.extract_directories(copied_items)
                    folders = list(set(folders))
                    folders = ";".join(folders)
                    web_addr = self.owner.webadr
                    req = web_addr + "/v1/Library/Import?folder=" + urllib.parse.quote(folders)
                    print(req)
                    r = requests.get(req)
                else:
                    print("Aucun nouvel élément copié (tout était déjà à jour).")

                if self.owner._config['USB']['eject'] == "True":
                    # Démonter la clé
                    device = subprocess.check_output(
                        ["findmnt", "-n", "-o", "SOURCE", mount_path]
                    ).decode().strip()
                    subprocess.call(["demontclef"])

                    print("\nClé démontée automatiquement.")
            else:
                print(f"Erreur rsync : {result.stderr}")

        except Exception as e:
            print(f"Erreur : {e}")

    def on_mount_changed(self, monitor, file, other_file, event_type):
        mount_path = file.get_path()

        if event_type == Gio.FileMonitorEvent.CREATED:
            if mount_path.startswith(self.media_path) and os.path.isdir(mount_path):
                print(f"Nouvelle clé montée sur {mount_path}")
                time.sleep(1)  # Petit délai pour laisser le montage se stabiliser
                self.copy_and_unmount(mount_path)

        elif event_type == Gio.FileMonitorEvent.DELETED:
            if mount_path.startswith(self.media_path):
                print(f"Clé démontée : {mount_path}")

    def run(self):
        """Méthode exécutée dans le thread"""
        print(f"Surveillance de {self.media_path} démarrée (thread {threading.current_thread().name})")

        media_file = Gio.File.new_for_path(self.media_path)
        monitor = media_file.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        monitor.connect("changed", self.on_mount_changed)

        # Boucle GLib (bloquante, mais dans un thread séparé → OK)
        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            print("\nArrêt du moniteur USB.")
            loop.quit()


# =============================================================================
# Utilisation
# =============================================================================
if __name__ == "__main__":
    monitor = USBCopyMonitor()
    monitor.start()  # Démarre le thread

    print("Moniteur lancé en arrière-plan. Appuyez sur Ctrl+C pour arrêter.")
    try:
        # Garde le programme principal vivant
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du programme.")
