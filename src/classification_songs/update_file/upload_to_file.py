from classification_songs.configorations.configoration import main_queue
from classification_songs.configorations._dataclasses import Types, SongInfo
from classification_songs.configorations.logger_setup import logger_classified_process
from classification_songs.configorations.logger_setup import logger_info_process as logger
from mutagen.mp3 import MP3
from update_file_interface import UpdateFileInterface
from pathlib import Path
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.wave import WAVE


class UpLoadToFile(UpdateFileInterface):

    @staticmethod
    def get_song_from_queue():
        info_json = main_queue.rpop('all_filed')
        with_types = Types.from_json(info_json)
        return with_types

    @staticmethod
    def calculate_final_genre(types: Types)->str:
        scors_dict = {}
        scors_dict[types.pop_genre] = 'pop'
        scors_dict[types.rap_genre] = 'rap'
        scors_dict[types.classical_genre] = 'classical'
        high = max(types.pop_genre, types.rap_genre, types.classical_genre)
        if high > 45:
            return scors_dict[high]
        return 'Unknown'

    @staticmethod
    def check_song_type(types: Types)->str:
        if types.love_song:
            return 'love_song'
        else:
            return 'Unknown'

    @staticmethod
    def song_format(types: Types)->str:
        path = types.song_info.song_path
        return (path, path.suffix)

    @staticmethod
    def saperate_to_formats(path:Path, format: str, genre: str, _type: str)->None:
        try:
            if format == '.mp3':
                try:
                    audio = EasyID3(path)
                except Exception:
                    audio = File(path, easy=True)
                    audio.add_tags()
                EasyID3.RegisterTextKey("comment", "COMM")
                audio['comment'] = _type
                audio['genre'] = genre
                audio.save()

            elif format == '.flac':
                audio = FLAC(path)
                audio['genre'] = [genre]
                audio['comment'] = [_type]
                audio.save()

            elif format == '.ogg':
                audio = OggVorbis(path)
                audio['genre'] = [genre]
                audio['comment'] = [_type]
                audio.save()

            elif format in ('.m4a', '.aac'):
                audio = MP4(path)
                audio["\xa9gen"] = [genre]
                audio["desc"] = [_type]
                audio.save()

            elif format == '.wav':
                audio = WAVE(path)
                audio["ICMT"] = f'type: {_type} genre: {genre}' or ""
                audio.save()

        except Exception as e:
            print(f"Error updating metadata for {path.name}: {e}")

    def upload_to_file(self) ->None:
        song_info = self.get_song_from_queue()
        final_genre = self.calculate_final_genre(song_info)
        final_type = self.check_song_type(song_info)
        path, format = self.song_format(song_info)
        self.saperate_to_formats(path, format, final_genre, final_type)

up_load = UpLoadToFile()
while True:
    up_load.upload_to_file()











