from classification_interface import ClassificationInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.get_song_details_for_comparison import GetSongDetailsForComparison
from classification_songs.configorations.configoration import (main_queue, RAP_COMMON, RAP_LESS_COMMON, RAP_MOST_COMMON)
from classification_songs.configorations.logger_setup import logger_info_process as logger
import numpy as np

class ClassificationForGenreRap(ClassificationInterface):

    def __init__(self, queue_name):
        self.queue_name = queue_name
        logger.info(f'Initialized ClassificationForGenreRap with queue "{queue_name}"')

    @staticmethod
    def get_song_from_queue():
        logger.info(f'getting song info from queue')
        info_json = main_queue.rpop('rap_genre')
        if not info_json:
            logger.info('No song found in "rap_genre" queue — waiting...')
            return None
        with_types = Types.from_json(info_json)
        logger.debug(f'Successfully parsed {with_types.song_info.song_name}')
        return with_types

    @staticmethod
    def get_sound_details(song_info: SongInfo)->dict:
        _all = GetSongDetailsForComparison(song_info)
        return _all.get_all_sound()

    @staticmethod
    def get_length(song_info: SongInfo)->float:
        _all = GetSongDetailsForComparison(song_info)
        return _all.get_length()

    @staticmethod
    def get_words(song_info: SongInfo)->list:
        _all = GetSongDetailsForComparison(song_info)
        return _all.get_words()

    def calculate_score_words(self, song_info: SongInfo)->float:
        logger.info(f'calculating score words for "{song_info.song_name}"')
        song_words = self.get_words(song_info)
        words_score = 0.0
        for word in RAP_MOST_COMMON:
            num_show = song_words.count(word)
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in RAP_COMMON:
            num_show = song_words.count(word) * 0.7
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in RAP_LESS_COMMON:
            num_show = song_words.count(word) * 0.4
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        final_score = min(words_score/3.0, 100.0)
        logger.debug(f'score words for "{song_info.song_name}" = {final_score: .f2}')
        return final_score

    def calculate_score_length(self, song_info: SongInfo)->float:
        logger.info(f'calculating score length for "{song_info.song_name}"')
        length = self.get_length(song_info)
        score_length = 0.0
        if 150 <= length < 270:
            score_length += 100.0
        elif 110 < length < 150:
            score_length += 55.0
        elif 270 <= length < 360:
            score_length += 70.0
        logger.debug(f'score length for "{song_info.song_name}" = {score_length: .f2}')
        return score_length

    def drums_scor(self, song_info: SongInfo)->float:
        logger.debug(f'drums scor for "{song_info.song_name}"')
        sound = self.get_sound_details(song_info)
        drums = sound['drums']
        tempo = drums['tempo']
        tempo_dev = min(abs(tempo - 90), abs(tempo - 145))
        tempo_component = (1 - min(tempo_dev, 30) / 30) * 0.5
        ibi_std = drums['ibi_std'] if np.isfinite(drums['ibi_std']) else 0.4
        ibi_component = (1 - min(ibi_std, 0.4) / 0.4) * 0.3
        onset_density = drums['onset_density']
        density_component = min(onset_density / 2.5, 1.0) * 0.2
        drum_score = (tempo_component + ibi_component + density_component) * 100.0
        logger.debug(f'drums score for "{song_info.song_name}" = {drum_score: .f2}')
        return max(0.0, min(100, drum_score))

    def bass_scor(self, song_info: SongInfo)->float:
        logger.debug(f'bass scor for "{song_info.song_name}"')
        sound = self.get_sound_details(song_info)
        bass = sound['bass']
        low_ratio = bass['low_ratio']
        low_component = (1 - abs(low_ratio - 0.28) / 0.18) * 0.7
        corr = bass['corr']
        corr_component = max(0.0, min(1.0, (corr + 0.5) / 1.0)) * 0.3
        bass_score = (low_component + corr_component) * 100.0
        logger.debug(f'bass score for "{song_info.song_name}" = {bass_score: .f2}')
        return max(0.0, min(100, bass_score))

    def others_scor(self, song_info: SongInfo)->float:
        logger.debug(f'others scor for "{song_info.song_name}"')
        sound = self.get_sound_details(song_info)
        other = sound['other']
        bright_score = 1 - (min(abs(other['centroid'] - 1800) / 900, 1.0) * 1.0)
        dr_scor = 1 - (min(abs(other['dr_db'] - 8) / 5, 1.0) * 1.0)
        other_score = 70.0*bright_score + 30.0*dr_scor
        logger.debug(f'others score for "{song_info.song_name}" = {other_score: .f2}')
        return other_score

    def calculate_sound_score(self, song_info: SongInfo)->float:
        logger.info(f'calculating sound score for "{song_info.song_name}"')
        sound_score = (0.4 * self.drums_scor(song_info)
                       + 0.3 * self.bass_scor(song_info)
                       + 0.3 * self.others_scor(song_info))
        logger.debug(f'sound score for "{song_info.song_name}" = {sound_score: .f2}')
        return sound_score

    def calculate_final_score(self, song_info: SongInfo)->float:
        logger.info(f'calculating final score for "{song_info.song_name}"')
        final_score = (0.55 * self.calculate_sound_score(song_info)
                       + 0.45 * self.calculate_score_words(song_info)
                       + 0.1 * self.calculate_score_length(song_info))
        logger.debug(f'final score for "{song_info.song_name}" = {final_score: .f2}')
        return final_score

    def comparison_type(self) -> None:
        logger.debug(f'comparison type for rap genre')
        dc_with_types = self.get_song_from_queue()
        song_info = dc_with_types.song_info
        final_score = self.calculate_final_score(song_info)
        rap_genre = final_score
        dc_with_types.rap_genre = rap_genre
        main_queue.lpush(self.queue_name, dc_with_types.to_json())
        logger.debug(f'pushed update Types with rap genre to queue {self.queue_name}')


if __name__ == '__main__':
    _rap = ClassificationForGenreRap('song_info')
    while True:
        _rap.comparison_type()