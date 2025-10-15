from typing import List, Union, Optional
from get_info_interface import GetInfoInterface
from dataclasses import dataclass
from time import time
import redis

@dataclass
class SongInfo:
    song_name: str
    song_words: Optional[List[str]]
    song_length: Optional[time]
    song_sound: Optional[bytes]

r = redis.Redis(host='localhost', port=6379, db=0)

class GetSongInfo(GetInfoInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    def check_path_is_audio(self, path: str) -> bool:
        pass

    def receive_song_words(self, path: str) -> list[str]:
        pass

    def receive_song_length(self, path: str) -> float:
        pass

    def receive_song_sound(self, path: str) -> bytes:
        pass

    def get_info(self, path: str) ->FileInfo:
        pass

