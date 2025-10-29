from classification_songs.configorations.logger_setup import logger_classified_process as logger
from typing import Protocol, Dict
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen import File
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.wave import WAVE


class MetadataWriter(Protocol):
    suffixes: tuple[str, ...]
    def write(self, path: Path, genre: str, song_type: str) -> None:...

class WriteRegister:
    def __init__(self):
        self._by_suffix: Dict[str, MetadataWriter] = {}

    def register(self, writer: MetadataWriter):
        for s in writer.suffixes:
            self._by_suffix[s.lower()] = writer
            logger.debug(f"Registered writer for suffix {s}: {writer.__class__.__name__}")

    def get(self, path: Path) -> MetadataWriter | None:
        return self._by_suffix.get(path.suffix.lower())


class Mp3Writer:
    suffixes = ('.mp3',)

    def write(self, path: Path, genre: str, song_type: str) -> None:
        logger.info(f'Writing mp3 tag to {path.name}')
        try:
            try:
                audio = EasyID3(path)
            except Exception:
                audio = File(path, easy=True)
                if not getattr(audio, 'tags', None):
                    audio.add_tags()
            EasyID3.RegisterTextKey('comment', 'COMM')
            audio['genre'] = genre
            audio['comment'] = song_type
            audio.save()
            logger.debug(f"Wrote mp3 tag to file")
        except Exception as e:
            logger.error(f"Failed to write mp3 tag to file: {e}")

class FLACWriter:
    suffixes = ('.flac',)

    def write(self, path: Path, genre: str, song_type: str) -> None:
        logger.info(f'Writing flac tag to {path.name}')
        try:
            audio = FLAC(path)
            audio['genre'] = [genre]
            audio['comment'] = [song_type]
            audio.save()
            logger.debug(f"Wrote flac tag to file")
        except Exception as e:
            logger.error(f"Failed to write flac tag to file: {e}")

class OggWriter:
    suffixes = ('.ogg',)

    def write(self, path: Path, genre: str, song_type: str) -> None:
        logger.info(f'Writing ogg tag to {path.name}')
        try:
            audio = OggVorbis(path)
            audio['genre'] = [genre]
            audio['comment'] = [song_type]
            audio.save()
            logger.debug(f"Wrote ogg tag to file")
        except Exception as e:
            logger.error(f"Failed to write ogg tag to file: {e}")

class Mp4LikeWriter:
    suffixes = ('.m4a', '.aac')

    def write(self, path: Path, genre: str, song_type: str) -> None:
        logger.info(f'Writing mp4 tag to {path.name}')
        try:
            audio = MP4(path)
            audio["\xa9gen"] = [genre]
            audio['desc'] = [song_type]
            audio.save()
            logger.debug(f"Wrote mp4 tag to file")
        except Exception as e:
            logger.error(f"Failed to write mp4 tag to file: {e}")

class WavWriter:
    suffixes = ('.wav',)

    def write(self, path: Path, genre: str, song_type: str) -> None:
        logger.info(f'Writing wav tag to {path.name}')
        try:
            audio = WAVE(path)
            audio["ICMT"] = f'type: {song_type} | genre: {genre}'
            audio.save()
            logger.debug(f"Wrote wav tag to file")
        except Exception as e:
            logger.error(f"Failed to write wav tag to file: {e}")
