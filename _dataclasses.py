from dataclasses import dataclass, asdict
from typing import Optional
import json
from logger_setup import logger
from pathlib import Path

@dataclass
class SongInfo:
    song_name: str
    song_words: Optional[list[str]]
    song_length: Optional[float]
    song_sound: Optional[list[Path]]

    def to_dict(self)->dict:
        logger.debug(f'Converting SongInfo of {self.song_name} to dict')
        _dict = asdict(self)
        if _dict['song_sound'] is not None:
            _dict["song_sound"] = [str(p) for p in _dict['song_sound']]
        return _dict

    @classmethod
    def from_dict(cls, _dict: dict):
        logger.debug(f'Converting SongInfo from dict: {_dict.get('song_name')}')
        sound = _dict.get('song_sound')
        if sound is not None:
            sound = [Path(s) for s in sound]
        return cls(
            song_name=_dict.get('song_name'),
            song_words=_dict.get('song_words'),
            song_length=_dict.get('song_length'),
            song_sound=sound
        )

    def to_json(self)->str:
        logger.debug(f'Converting {self.song_name} to json')
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str):
        logger.debug(f'Converting SongInfo from json')
        return cls.from_dict(json.loads(json_str))

@dataclass
class Types:
    song_name: str
    love_song: Optional[bool] = None
    pop_genre: Optional[bool] = None
    rap_genre: Optional[bool] = None
    classical_genre: Optional[bool] = None

    def to_dict(self)->dict:
        logger2.debug(f'Converting Types of {self.song_name} to dict')
        _dict = asdict(self)
        return _dict

    @classmethod
    def from_dict(cls, _dict: dict):
        logger2.debug(f'Converting Types from dict: {_dict.get('song_name')}')
        return cls(
            song_name=_dict.get('song_name'),
            love_song=_dict.get('love_song'),
            pop_genre=_dict.get('pop_genre'),
            rap_genre=_dict.get('rap_genre'),
            classical_genre=_dict.get('classical_genre')
        )

    def to_json(self)->str:
        logger2.debug(f'Converting {self.song_name} to json')
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str):
        logger2.debug(f'Converting Types from json')
        return cls.from_dict(json.loads(json_str))
