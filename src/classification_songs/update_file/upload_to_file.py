from classification_songs.configorations.configoration import main_queue, make_genre_decider, make_song_type_decider
from classification_songs.configorations._dataclasses import Types
from classification_songs.configorations.logger_setup import logger_classified_process as logger
from classification_songs.update_file.formats import WriteRegister, Mp3Writer, FLACWriter, OggWriter, Mp4LikeWriter, WavWriter
from mutagen.mp3 import MP3
from update_file_interface import UpdateFileInterface
from pathlib import Path




class UpLoadToFile(UpdateFileInterface):

    def __init__(self, genre_decider: GenreFilters, type_decider: TypeFilters, registry: WriteRegister):
        self.type_decider = type_decider
        self.genre_deciders = genre_decider
        self.registry = registry


    @staticmethod
    def get_song_from_queue():
        info_json = main_queue.rpop('all_filed')
        if not info_json:
            logger.info('Queue "all_filed" is empty.')
            return None
        try:
            with_types = Types.from_json(info_json)
            logger.debug('Parsed Types from JSON successfully.')
            return with_types
        except Exception as e:
            logger.error(f'Failed to parse Types JSON from queue: {e}')
            return None


    def calculate_final_genre(self, types: Types)->str:
        label, score = self.genre_decider.decide(types)
        logger.info(f'final genre: {label} ({score:.2f})')
        return label

    def check_song_type(self, types: Types)->str:
        label, score = self.type_decider.decide(types)
        logger.info(f'final song type: {label} ({score:.2f})')
        return label

    @staticmethod
    def detect_path(types: Types) -> Path | None:
        try:
            p = types.song_info.song_path
            return p if p.exists() else None
        except Exception:
            return None

    def write_metadata(self, path: Path, genre: str, song_type: str):
        writer = self.registry.get(path)
        if writer is None:
            logger.warning(f'No writer registered for suffix "{path.suffix}". Skipping.')
            return
        writer.write(path, genre, song_type)

    def upload_to_file(self) ->None:
        song_info = self.get_song_from_queue()
        if song_info is None:
            return
        try:
            final_genre = self.calculate_final_genre(song_info)
            final_type = self.check_song_type(song_info)
            path = self.detect_path(song_info)
            if path is None:
                logger.error('invalid path')
                return
            self.write_metadata(path, final_genre, final_type)
        except Exception as e:
            logger.error(f'Failed to write metadata to file: {e}')


if __name__ == '__main__':
    ilogger.info('Starting file upload process...')
    registry = WriteRegister()
    registry.register(Mp3Writer())
    registry.register(FLACWriter())
    registry.register(OggWriter())
    registry.register(Mp4LikeWriter())
    registry.register(WavWriter())

    genre_decider = make_genre_decider()
    type_decider  = make_song_type_decider()

    up_load = UpLoadToFile(genre_decider=genre_decider, type_decider=type_decider, registry=registry)
    while True:
        up_load.upload_to_file()










