from classification_songs.configorations.configoration import main_queue, LIST_OF_TYPES
from classification_songs.configorations._dataclasses import Types
from typing import Optional
from classification_songs.configorations.logger_setup import logger_info_process as logger


class SendToClasiffier:

    def __init__(self, queue_name):
        self.queue_name = queue_name

    def get_song_from_queue(self)->Optional[Types]:
        info_json = main_queue.rpop(self.queue_name)
        if not info_json:
            return None
        return Types.from_json(info_json)

    @staticmethod
    def make_and_send_queue(queue_name: str, info_json: str):
        main_queue.lpush(queue_name, info_json)

    def queues(self)->None:
        info = self.get_song_from_queue()
        info_dict = info.to_dict()
        for _type in LIST_OF_TYPES:
            if not info_dict.get(_type):
                self.make_and_send_queue(_type, info.to_json())
                return
        self.make_and_send_queue('all_filed', info.to_json())

send = SendToClasiffier('song_info')
while True:
    send.queues()
