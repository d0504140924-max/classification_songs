from classification_songs.configorations.configoration import main_queue, LIST_OF_TYPES
from classification_songs.configorations._dataclasses import Types
from typing import Optional
from classification_songs.configorations.logger_setup import logger_info_process as logger
from time import sleep


class SendToClasiffier:

    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        logger.info('init SendToClasiffier')

    def get_song_from_queue(self, block: bool = True, timeout: int = 5) -> Optional[Types]:
        if main_queue is None:
            logger.error('Redis connection is None')
            sleep(1)
            return None

        try:
            if block:
                res = main_queue.brpop(self.queue_name, timeout=timeout)
                if not res:
                    logger.debug('no song found in queue (timeout)')
                    return None
                _q, info_json = res
            else:
                info_json = main_queue.rpop(self.queue_name)
                if not info_json:
                    logger.debug('no song found in queue (empty)')
                    return None

            logger.debug('Successfully fetched JSON from queue')
            return Types.from_json(info_json)
        except Exception as e:
            logger.error(f'failed to fetch/parse from queue: {e}')
            sleep(1)
            return None

    @staticmethod
    def make_and_send_queue(queue_name: str, info_json: str):
        try:
            main_queue.lpush(queue_name, info_json)
            logger.debug(f'Successfully sent to {queue_name}')
        except Exception as e:
            logger.error(f'failed to push to {queue_name}: {e}')

    def queues(self) -> None:
        info = self.get_song_from_queue(block=True, timeout=5)
        if info is None:
            return

        try:
            info_dict = info.to_dict()
            for _type in LIST_OF_TYPES:
                if not info_dict.get(_type):
                    self.make_and_send_queue(_type, info.to_json())
                    logger.debug(f'Successfully sent to {_type}')
                    return
            self.make_and_send_queue('all_filed', info.to_json())
            logger.debug('Successfully sent to all_filed')
        except Exception as e:
            logger.error(f'error in routing logic: {e}')
            sleep(0.1)

if __name__ == '__main__':
    send = SendToClasiffier('song_info')
    while True:
        try:
            send.queues()
            sleep(0.02)
        except Exception as e:
            logger.error(f'router crash-loop guard: {e}')
            sleep(1)

