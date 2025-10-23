from classification_interface import ClassificationInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.get_song_details_for_comparison import GetSongDetailsForComparison
from classification_songs.configorations.configoration import (main_queue, LOVE_COMMON, LOVE_LESS_COMMON,
                                                               LOVE_MOST_COMMON)
from classification_songs.configorations.logger_setup import logger_info_process as logger
from typing import Optional
import numpy as np

class ClassificationForLoveSong(ClassificationInterface):

    def __init__(self, queue_name):
        self.queue_name = queue_name
        logger.info('Initializing Classification for Love Song')

    @staticmethod
    def get_song_from_queue()->Optional[Types]:
        logger.info('Getting song from queue')
        info_json = main_queue.rpop('love_song')
        if not info_json:
            logger.debug('No song found in "love_song" queue')
            return None
        with_types = Types.from_json(info_json)
        logger.debug(f'Successfully parsed {with_types.song_info.song_name if with_types.song_info else "unknown"}')
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
        logger.info(f'Calculating score words for song {song_info.song_name}')
        song_words = self.get_words(song_info)
        words_score = 0.0
        for word in LOVE_MOST_COMMON:
            num_show = song_words.count(word)
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in LOVE_COMMON:
            num_show = song_words.count(word) * 0.7
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in LOVE_LESS_COMMON:
            num_show = song_words.count(word) * 0.4
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        final_score = min(words_score/3.0, 100.0)
        logger.debug(f'Score words for song {song_info.song_name} : {final_score: .f2}')
        return final_score

    def calculate_score_length(self, song_info: SongInfo)->float:
        logger.info(f'Calculating score length for song {song_info.song_name}')
        length = self.get_length(song_info)
        score_length = 0.0
        if 150 <= length < 280:
            score_length += 100.0
        elif 120 < length < 150:
            score_length += 60.0
        elif 280 <= length < 360:
            score_length += 70.0
        logger.debug(f'Score length for song {song_info.song_name} : {score_length: .f2}')
        return score_length

    def drums_scor(self, song_info: SongInfo)->float:
        logger.debug(f'Drums scoring for song {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        drums = sound['drums']
        tempo = drums['tempo']
        ibi_std = drums['ibi_std'] if np.isfinite(drums['ibi_std']) else 0.5
        onset_density = drums['onset_density']
        dev_anchor = min(abs(tempo - 72), abs(tempo - 96))
        tempo_component = (1 - min(dev_anchor, 28) / 28) * 0.45
        ibi_component = (1 - min(abs(ibi_std - 0.25), 0.25) / 0.25) * 0.30
        density_component = (1 - min(abs(onset_density - 1.3) / 1.3, 1.0)) * 0.25
        drum_score = (tempo_component + ibi_component + density_component) * 100.0
        logger.debug(f'drums score for song {song_info.song_name} : {drum_score: .f2}')
        return max(0.0, min(100, drum_score))

    def bass_scor(self, song_info: SongInfo)->float:
        logger.debug(f'Bass scoring for song {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        bass = sound['bass']
        low_ratio = bass['low_ratio']
        low_component =  (1 - abs(low_ratio - 0.18) / 0.14) * 0.65
        corr = bass['corr']
        corr_component =  max(0.0, min(1.0, (corr + 0.4) / 1.2)) * 0.35
        bass_score = (low_component + corr_component) * 100.0
        logger.debug(f'bass score for song {song_info.song_name} : {bass_score: .f2}')
        return max(0.0, min(100, bass_score))

    def others_scor(self, song_info: SongInfo)->float:
        logger.debug(f'Other scoring for song {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        other = sound['other']
        bright_score = 1 - (min(abs(other['centroid'] - 2300) / 1100, 1.0) * 1.0)
        dr_scor = 1 - (min(abs(other['dr_db'] - 11) / 5, 1.0) * 1.0)
        other_score = 70.0*bright_score + 30.0*dr_scor
        logger.debug(f'other score for song {song_info.song_name} : {other_score: .f2}')
        return other_score

    def calculate_sound_score(self, song_info: SongInfo)->float:
        logger.info(f'Calculating sound score for song {song_info.song_name}')
        sound_score = (0.4 * self.drums_scor(song_info)
                       + 0.3 * self.bass_scor(song_info)
                       + 0.3 * self.others_scor(song_info))
        logger.debug(f'sound score for song {song_info.song_name} : {sound_score: .f2}')
        return sound_score

    def calculate_final_score(self, song_info: SongInfo)->float:
        logger.info(f'Calculating final score for song {song_info.song_name}')
        final_score = (0.35 * self.calculate_sound_score(song_info)
                       + 0.50 * self.calculate_score_words(song_info)
                       + 0.15 * self.calculate_score_length(song_info))
        logger.debug(f'final score for song {song_info.song_name} : {final_score: .f2}')
        return final_score

    def comparison_type(self) -> None:
        logger.debug(f'Comparison type for love song')
        dc_with_types = self.get_song_from_queue()
        song_info = dc_with_types.song_info
        final_score = self.calculate_final_score(song_info)
        love_song = final_score
        dc_with_types.love_song = love_song
        main_queue.lpush(self.queue_name, dc_with_types.to_json())
        logger.debug(f'pushed update Types with rap genre to queue {self.queue_name}')

if __name__ == '__main__':
    _love_song = ClassificationForLoveSong('song_info')
    while True:
        _love_song.comparison_type()