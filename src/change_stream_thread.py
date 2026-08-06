import pymongo
from threading import Thread
import logging

class ChangeStream(Thread):

    def __init__(self, owner):
        Thread.__init__(self)
        self.owner = owner
        self.MongoConnection = pymongo.MongoClient(self.owner.mongo_addr)
        self.db = self.MongoConnection.player
        logging.info("Change stream is active")

    def run(self):
        # change_stream = self.db.mediafiles.watch()
        # for change in change_stream:
        #     id = str(change['documentKey']['_id'])
        #
        #     if change['operationType'] == 'update':
        #         self.owner.send_message("mediafile_updated",id)
        #         print(f"mediafile_updated : {id}")
        #     elif change['operationType'] == 'delete':
        #         self.owner.send_message("mediafile_deleted",id)
        #         print(f"mediafile_deleted : {id}")
        #     elif change['operationType'] == 'insert':
        #         self.owner.send_message("mediafile_inserted",id)
        #         print(f"mediafile_inserted : {id}")
        #     else:
        pass
