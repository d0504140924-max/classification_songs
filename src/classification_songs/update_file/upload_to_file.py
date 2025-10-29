from time import sleep
from pathlib import Path
from classification_songs.configorations.configoration import main_queue, make_genre_decider, make_song_type_decider
from classification_songs.configorations._dataclasses import Types, CategoryFilter
from classification_songs.configorations.logger_setup import logger_classified_process as logger
from classification_songs.update_file.formats import (
    WriteRegister, Mp3Writer, FLACWriter, OggWriter, Mp4LikeWriter, WavWriter
)

class UpLoadToFile:
    def __init__(self, genre_decider: CategoryFilter, type_decider: CategoryFilter, registry: WriteRegister):
        self.genre_decider = genre_decider   # תיקון שם השדה (לא לוגיקה)
        self.type_decider  = type_decider
        self.registry = registry

    @staticmethod
    def get_song_from_queue(timeout: int = 5):
        if main_queue is None:
            logger.error('Redis connection is None')
            sleep(1)
            return None
        try:
            res = main_queue.brpop('all_filed', timeout=timeout)
            if not res:
                logger.debug('Queue "all_filed" empty (timeout)')
                return None
            _q, info_json = res
            if isinstance(info_json, bytes):
                info_json = info_json.decode('utf-8', errors='ignore')
            types = Types.from_json(info_json)
            logger.debug('Parsed Types from JSON successfully.')
            return types
        except Exception as e:
            logger.error(f'Failed to fetch/parse from "all_filed": {e}')
            sleep(1)
            return None

    def calculate_final_genre(self, types: Types) -> str:
        label, score = self.genre_decider.decide(types)
        logger.info(f'final genre: {label} ({score:.2f})')
        return label

    def check_song_type(self, types: Types) -> str:
        label, score = self.type_decider.decide(types)
        logger.info(f'final song type: {label} ({score:.2f})')
        return label

    @staticmethod
    def detect_path(types: Types) -> Path | None:
        try:
            p = types.song_info.song_path if types and types.song_info else None
            p = Path(p) if p is not None else None
            return p if (p and p.exists()) else None
        except Exception:
            return None

    def write_metadata(self, path: Path, genre: str, song_type: str):
        writer = self.registry.get(path)
        if writer is None:
            logger.warning(f'No writer registered for suffix "{path.suffix}". Skipping.')
            return
        writer.write(path, genre, song_type)

    def upload_to_file_once(self) -> None:
        types = self.get_song_from_queue(timeout=5)
        if types is None:
            return
        try:
            final_genre = self.calculate_final_genre(types)
            final_type  = self.check_song_type(types)
            path = self.detect_path(types)
            if path is None:
                logger.error('invalid path for writing metadata')
                return
            self.write_metadata(path, final_genre, final_type)
        except Exception as e:
            logger.error(f'Failed to write metadata to file: {e}')

if __name__ == '__main__':
    logger.info('Starting file upload process...')
    registry = WriteRegister()
    registry.register(Mp3Writer())
    registry.register(FLACWriter())
    registry.register(OggWriter())
    registry.register(Mp4LikeWriter())
    registry.register(WavWriter())

    up_load = UpLoadToFile(
        genre_decider=make_genre_decider(),
        type_decider=make_song_type_decider(),
        registry=registry
    )
    while True:
        try:
            up_load.upload_to_file_once()
            sleep(0.1)
        except Exception as e:
            logger.error(f'uploader crash-loop guard: {e}')
            sleep(1)
