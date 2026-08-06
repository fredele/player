#!/usr/bin/python3
#-*- coding: utf-8 -*-
from threading import Thread
import queue
from utils.string import to_unicode
import time

class Update_Queries(Thread):

    def __init__(self, owner,func):
        Thread.__init__(self)
        self.owner = owner
        self.func = func
        self.enpause = False
        self.stop = False

    def run(self):

        savedqueries =  [x for x in  self.owner.db.savedqueries.find()]
        self.owner.savedqueries.extend(savedqueries)
        self.owner.savedqueries = [[d for d in self.owner.savedqueries if d['hashquery'] == h][0] for h in list(set([q['hashquery'] for q in self.owner.savedqueries]))]
        #delete duplicated queries ...
        self.savedqueries = [e for e in reversed(sorted(self.owner.savedqueries, key=lambda i: (i.get('lasttime', 0))))]#[:100]

        # Drop Queries ONLY here ...
        self.owner.db.savedqueries.drop()

        time.sleep(60) # DO NOT REMOVE :  wait till IMPORT has finished, then recalculate the queries ...
        num_worker_threads = 2

        def worker():
            while True:
                if self.stop == True:
                    self.stop = False
                    with q.mutex:
                        q.queue.clear()
                    break
                query = q.get()
                if query is None:
                    break
                time.sleep(1)
                ha = query["hashquery"]
                print(f"query hash to update: {ha}")
                request = {}
                request["query"] = query["query"]
                request["field"]  = query["field"]
                request["sort"] = "ASCENDING" if int(query["sort"]) == 1 else "DESCENDING"
                request["sorttag"] = query["sorttag"]
                request["display"] = query["display"]
                request["page_nbr"] = query["page_nbr"]
                request["full"] =  "false" if query["full"] == None else query["full"]
                print(f"recalculate hash : {ha}")
                self.func(request, self.owner.db,ha)

                q.task_done()
                self.savedqueries = [x for x in self.owner.db.savedqueries.find()]

        q = queue.Queue()

        for i in range(num_worker_threads):
            t = Thread(target=worker)
            t.start()

        for query in self.savedqueries:
            q.put(query)

    def pause(self):
        self.enpause = True

    def reprise(self):
        self.enpause = False

    def do_stop(self):
        self.stop = True