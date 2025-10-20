from dataclasses import dataclass, asdict
from typing import Optional
import json
from .logger_setup import logger_info_process, logger_classified_process
from pathlib import Path

@dataclass
class SongInfo:
    song_name: str
    song_path: Path
    song_words: Optional[list[str]]
    song_length: Optional[float]
    song_sound: Optional[dict[str, Path]]

    def to_dict(self)->dict:
        logger_info_process.debug(f'Converting SongInfo of {self.song_name} to dict')
        _dict = asdict(self)
        _dict['song_path'] = str(self.song_path)
        if _dict['song_sound'] is not None:
            _dict['song_sound'] = {k: str(v) for k, v in _dict['song_sound'].items()}
        return _dict

    @classmethod
    def from_dict(cls, _dict: dict):
        if _dict is None:
            return None
        logger_info_process.debug(f"Converting SongInfo from dict: {_dict.get('song_name')}")
        song_path = Path(_dict['song_path']) if isinstance(_dict.get('song_path'), str) else _dict.get('song_path')
        sound = _dict.get('song_sound')
        if sound is not None:
            sound = {k: Path(v) for k, v in sound.items()}
        return cls(
            song_name=_dict.get('song_name'),
            song_path=song_path,
            song_words=_dict.get('song_words'),
            song_length=_dict.get('song_length'),
            song_sound=sound
        )

    def to_json(self)->str:
        logger_info_process.debug(f'Converting {self.song_name} to json')
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str):
        logger_info_process.debug(f'Converting SongInfo from json')
        return cls.from_dict(json.loads(json_str))

@dataclass
class Types:
    song_info: Optional[SongInfo] = None
    love_song: Optional[float] = None
    pop_genre: Optional[float] = None
    rap_genre: Optional[float] = None
    classical_genre: Optional[float] = None

    def to_dict(self)->dict:
        logger_classified_process.debug(f'Converting Types of to dict')
        _dict = asdict(self)
        if _dict['song_info'] is not None:
            _dict['song_info'] = self.song_info.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, _dict: dict):
        logger_classified_process.debug(f"Converting Types from dict: {_dict.get('song_name')}")
        si = SongInfo.from_dict(_dict.get('song_info')) if _dict and _dict.get('song_info') else None
        return cls(
            song_info=si,
            love_song=_dict.get('love_song'),
            pop_genre=_dict.get('pop_genre'),
            rap_genre=_dict.get('rap_genre'),
            classical_genre=_dict.get('classical_genre')
        )

    def to_json(self)->str:
        logger_classified_process.debug(f'Converting to json')
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str):
        logger_classified_process.debug(f'Converting Types from json')
        return cls.from_dict(json.loads(json_str))
