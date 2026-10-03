#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import queue
import time
from threading import Thread
from typing import Callable, Optional, Any
import subprocess
import threading
from pymongo import MongoClient
from pymongo.database import Database
import copy
import hashlib
import re
import os
import time
import urllib.parse
from typing import Any, Dict, Optional, Callable
from pymongo.database import Database
from threading import Thread
from bson import ObjectId  # only if you need it later
from requestfind import Requestfind
from pathlib import Path
from paths import config_folder
import subprocess
import threading



scan_lock = threading.Lock()

scan_requested = False
scanprocess = None

# single-flight
# updates at first and last request_querybuilder

def request_querybuilder():
    global scan_requested, scanprocess
    with scan_lock:
        scan_requested = True
        
        if scanprocess is not None:
            return

        threading.Thread(
            target=querybuilder_worker,
            daemon=True
        ).start()


def querybuilder_worker():
    global scan_requested, scanprocess
    while True:
        with scan_lock:
            if not scan_requested:
                scanprocess = None
                return

            scan_requested = False

            scanprocess = subprocess.Popen(
                ["/bin/bash", "querybuilder"],
                cwd=None
            )

        scanprocess.wait()
        
        
class Update_Queries(Thread):
    def __init__(
        self,
        mongo_uri,
        db,
        notifier: Optional[Callable] = None,
        max_workers: int = 4,
    ):
        super().__init__(daemon=True)
        print("Update_Queries initialized")

        self.mongo_client = MongoClient(mongo_uri)
        self.owner = self.mongo_client.player
        


        if self.owner is None:
            raise ValueError("A MongoDB database or mongo_uri must be provided.")
        

        self.func = Requestfind        
        self.notifier = notifier
        self.max_workers = max_workers
        self.stop = False
        self.enpause = False
        self._q: queue.Queue = queue.Queue()

    def run(self) -> None:
        # snapshot
        
        try:
            # track only 100 most representative requests ..
            self.savedqueries = list(
                self.owner.savedqueries.aggregate([
                    {"$addFields": {"_query_length": {"$strLenCP": "$query"}}},
                    {"$sort": {"_query_length": 1}},
                    {"$limit": 100}
                ])
            )

            self.owner.savedqueries.delete_many({
                "_id": {"$nin": [doc["_id"] for doc in self.savedqueries]}
            })

            self.owner.savedqueries.update_many({}, {"$set": {"valid": "false"}})
            
            
        except Exception as e:
            print(f"Failed to drop savedqueries collection: {e}")
            

        def recalculate_music_views() -> None:
            views_path = config_folder / "views.json"

            try:
                with views_path.open("r", encoding="utf-8") as f:
                    views = json.load(f)

                music_views = views.get("music", [])
                print(f"Recalculating {len(music_views)} music views")

                for view in music_views:
                    levels = view.get("levels", [])
                    if not levels or len(levels[0]) < 3:
                        print(f"Invalid first level for view {view.get('name')}")
                        continue

                    field_spec, sort_spec, display = levels[0]

                    field_parts = field_spec.split("$", 1)
                    field = field_parts[0]
                    full = "true" if len(field_parts) > 1 and field_parts[1] == "full" else "false"

                    sort_parts = sort_spec.split("$", 1)
                    sorttag = sort_parts[0]
                    sort = sort_parts[1] if len(sort_parts) > 1 else "ASCENDING"

                    request = {
                        "query": str(view["query"]),
                        "field": field,
                        "sort": sort,
                        "sorttag": sorttag,
                        "display": display,
                        "page_nbr": 0,
                        "full": full,
                    }

                    print(f"recalculate view: {view.get('name')}")
                    self.func(request, self.owner, None)

            except Exception as exc:
                print(f"Error processing music views: {exc}")
                if self.notifier:
                    self.notifier(f"Update_Queries error: {exc}")

        #recalculate_music_views()

        # DO NOT REMOVE: wait until the IMPORT process has finished
        #time.sleep(10)

        def worker() -> None:
            while True:
                if self.stop:
                    # drain the queue so other threads can also exit
                    with self._q.mutex:
                        self._q.queue.clear()
                    break

                if self.enpause:
                    time.sleep(0.5)
                    continue

                try:
                    query = self._q.get(timeout=1.0)
                except queue.Empty:
                    continue

                if query is None:          # sentinel
                    self._q.task_done()
                    break

                try:
                    ha = query["hashquery"]
                    print(f"query hash to update: {ha}")

                    request = {
                        "query": query["query"],
                        "field": query["field"],
                        "sort": "ASCENDING" if int(query["sort"]) == 1 else "DESCENDING",
                        "sorttag": query["sorttag"],
                        "display": query["display"],
                        "page_nbr": query["page_nbr"],
                        "full": "false" if query.get("full") is None else query["full"],
                    }

                    print(f"recalculate hash: {ha}")
                    self.func(request, self.owner, ha)

                except Exception as exc:
                    print(f"Error processing query {query.get('hashquery')}: {exc}")
                    if self.notifier:
                        self.notifier(f"Update_Queries error: {exc}")
                finally:
                    self._q.task_done()

        # start workers
        threads = []
        try:
            for _ in range(self.max_workers):
                t = Thread(target=worker, daemon=True)
                t.start()
                threads.append(t)
        except Exception as e:
            print(f"Failed to start worker threads: {e}")
            if self.notifier:
                self.notifier(f"Update_Queries error: {e}")
            return
        
        # feed the queue
        for query in self.savedqueries:
            self._q.put(query)

        # send sentinels so workers can exit cleanly
        for _ in range(self.max_workers):
            self._q.put(None)

        # wait until everything is processed
        self._q.join()

        for t in threads:
            t.join(timeout=5)

        print("Update_Queries finished")

    def pause(self) -> None:
        self.enpause = True

    def reprise(self) -> None:
        self.enpause = False

    def do_stop(self) -> None:
        self.stop = True


def build_parser():
    parser = argparse.ArgumentParser(description="Query Builder service")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="MongoDB URI")
    return parser
        
if __name__ == "__main__":
    args = build_parser().parse_args()
    mongo_uri = args.mongo_uri
    p = config_folder / "config.ini"


    if not mongo_uri and os.path.isfile(p):
        config = configparser.ConfigParser()
        config.read(p)

        mongo = config["MongoDB"]

        address = mongo.get("address", "localhost")
        port = mongo.getint("port", 27017)
        user = mongo.get("user", "")
        password = mongo.get("password", "")

        if user:
            mongo_uri = (
                f"mongodb://{quote_plus(user)}:{quote_plus(password)}"
                f"@{address}:{port}"
            )
        else:
            mongo_uri = f"mongodb://{address}:{port}"
            

    u = Update_Queries(
        mongo_uri=mongo_uri,
        db="player"
    )
    u.start()
    u.join()
