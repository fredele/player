# ram_search.py

import threading
import time
from typing import Dict, List

from rapidfuzz import fuzz, process


class RamSearch:

    def __init__(self, mongo_db):
        self.db = mongo_db

        self._index = {}
        self._albums = {}
        self._available = False

        self._thread = None
        self._lock = threading.Lock()

        self.refresh()

    @property
    def available(self) -> bool:
        return self._available

    @property
    def index(self):
        return self._index

    def refresh(self):
        """
        Reconstruit l'index en arrière-plan.

        Si un index existe déjà, il continue à être utilisé
        pendant toute la durée de la reconstruction.
        """
        with self._lock:
            # Évite de lancer plusieurs reconstructions simultanément
            if self._thread is not None and self._thread.is_alive():
                return False

            self._thread = threading.Thread(
                target=self._build_index,
                daemon=True
            )

            self._thread.start()

        return True

    def _build_search_text(self, album: Dict) -> str:
        artists = album.get("artist", "")

        if isinstance(artists, list):
            artists = " ".join(artists)

        album_name = album.get("album", "")
        year = str(album.get("year", "")) if album.get("year") else ""

        return f"{artists} {album_name} {year}".strip().lower()

    def _build_index(self):
        start_time = time.time()

        cursor = self.db.mediafiles.find(
            {},
            {
                "dirhash": 1,
                "artist": 1,
                "album": 1,
                "year": 1,
                "_id": 0
            }
        )

        unique_albums = {}

        for doc in cursor:
            dirhash = doc.get("dirhash")

            if dirhash and dirhash not in unique_albums:
                unique_albums[dirhash] = doc

        albums = list(unique_albums.values())

        # Nouvel index construit entièrement en dehors
        # de l'index actuellement utilisé.
        new_albums = {
            album["dirhash"]: album
            for album in albums
        }

        new_index = {
            album["dirhash"]: self._build_search_text(album)
            for album in albums
        }

        # Remplacement atomique des deux structures.
        self._albums = new_albums
        self._index = new_index
        self._available = True

        elapsed = time.time() - start_time

        print(
            f"RamSearch : index construit en {elapsed:.3f} secondes "
            f"({len(new_index)} albums)"
        )

    def search(
        self,
        query: str,
        limit: int = 15,
        score_threshold: int = 55
    ) -> List[Dict]:

        start_time = time.time()

        if not self._available:
            return []

        if not query:
            return []

        results = process.extract(
            query.lower(),
            self._index,
            scorer=fuzz.token_set_ratio,
            limit=limit
        )

        final_results = []

        for match_text, score, dirhash in results:
            if score >= score_threshold:
                album = self._albums[dirhash].copy()
                album["score"] = score
                final_results.append(album)

        elapsed = time.time() - start_time

        print(
            f"Recherche terminée en {elapsed:.3f} secondes"
        )

        return final_results