from time import sleep
from classification_interface import ClassificationInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.get_song_details_for_comparison import GetSongDetailsForComparison
from classification_songs.configorations.configoration import (main_queue, POP_COMMON, POP_LESS_COMMON, POP_MOST_COMMON,
                                                               as_scalar)
from classification_songs.configorations.logger_setup import logger_info_process as logger
import numpy as np


class ClassificationForGenrePop(ClassificationInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        logger.info(f'Initialized ClassificationForGenrePop with queue "{queue_name}"')

    @staticmethod
    def get_song_from_queue(timeout: int = 5):
        if main_queue is None:
            logger.error('Redis connection is None')
            return None
        try:
            res = main_queue.brpop('pop_genre', timeout=timeout)
            if not res:
                logger.debug('No song found in "pop_genre" (timeout)')
                return None
            _q, info_json = res
            if isinstance(info_json, bytes):
                info_json = info_json.decode('utf-8', errors='ignore')
            with_types = Types.from_json(info_json)
            logger.debug(f'Successfully parsed {with_types.song_info.song_name if with_types.song_info else "unknown"}')
            return with_types
        except Exception as e:
            logger.error(f'Failed to fetch/parse from "pop_genre": {e}')
            return None

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
        logger.info(f'Calculating score words for {song_info.song_name}')
        song_words = self.get_words(song_info)
        words_score = 0.0
        for word in POP_MOST_COMMON:
            num_show = song_words.count(word)
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in POP_COMMON:
            num_show = song_words.count(word) * 0.7
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in POP_LESS_COMMON:
            num_show = song_words.count(word) * 0.4
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        final_score = min(words_score/3.0, 100.0)
        logger.debug(f'Score words for {song_info.song_name} : {final_score}')
        return final_score

    def calculate_score_length(self, song_info: SongInfo)->float:
        logger.info(f'Calculating score length for {song_info.song_name}')
        length = self.get_length(song_info)
        score_length = 0.0
        if 165 <= length < 225:
            score_length += 100.0
        elif 120 < length < 165:
            score_length += 45.0
        elif 225 <= length < 300:
            score_length += 75.0
        logger.debug(f'Score length for {song_info.song_name} : {score_length}')
        return score_length

    def drums_scor(self, song_info: SongInfo) -> float:
        logger.debug(f'Drums scor for {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        drums = sound['drums']
        tempo = as_scalar(drums.get('tempo', 110.0) or 110.0)
        ibi_std = as_scalar(drums.get('ibi_std', 0.5) or 0.5)
        onset_density = as_scalar(drums.get('onset_density', 0.0) or 0.0)
        drum_score = (
                ((1 - min(abs(tempo - 110), 40) / 40) * 0.5) * 100
                + ((1 - min(ibi_std if np.isfinite(ibi_std) else 0.5, 0.5) / 0.5) * 0.3) * 100
                + (min(onset_density / 2.0, 1.0) * 0.2) * 100
        )
        drum_score = as_scalar(drum_score)
        logger.debug(f'drums scor for {song_info.song_name} : {drum_score}')
        return max(0.0, min(100.0, drum_score))

    def bass_scor(self, song_info: SongInfo) -> float:
        logger.debug(f'Bass scor for {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        bass = sound['bass']
        low_ratio = as_scalar(bass.get('low_ratio', 0.0) or 0.0)
        corr = as_scalar(bass.get('corr', 0.0) or 0.0)
        bass_score = (
                ((1 - abs(low_ratio - 0.20) / 0.20) * 0.6) * 100
                + max(0.0, min(1.0, (corr + 0.5) / 1.0)) * 40.0
        )
        bass_score = as_scalar(bass_score)
        logger.debug(f'bass scor for {song_info.song_name} : {bass_score}')
        return max(0.0, min(100.0, bass_score))

    def others_scor(self, song_info: SongInfo) -> float:
        logger.debug(f'Other scor for {song_info.song_name}')
        sound = self.get_sound_details(song_info)
        other = sound['other']
        centroid = as_scalar(other.get('centroid', 0.0) or 0.0)
        dr_db = as_scalar(other.get('dr_db', 0.0) or 0.0)
        bright_score = 1 - (min(abs(centroid - 2200) / 1200, 1.0) * 1.0)
        dr_scor = 1 - (min(abs(dr_db - 12) / 6, 1.0) * 1.0)
        other_score = 70.0 * bright_score + 30.0 * dr_scor
        other_score = as_scalar(other_score)
        logger.debug(f'other scor for {song_info.song_name} : {other_score}')
        return other_score

    def calculate_sound_score(self, song_info: SongInfo) -> float:
        logger.info(f'Calculating sound score for {song_info.song_name}')
        d = as_scalar(self.drums_scor(song_info))
        b = as_scalar(self.bass_scor(song_info))
        o = as_scalar(self.others_scor(song_info))
        sound_score = as_scalar(0.4 * d + 0.3 * b + 0.3 * o)
        logger.debug(f'calculating sound score for {song_info.song_name} : {sound_score}')
        return sound_score

    def calculate_final_score(self, song_info: SongInfo)->float:
        logger.info(f'Calculating final score for {song_info.song_name}')
        final_score = (0.50 * as_scalar(self.calculate_sound_score(song_info))
                       + 0.35 * self.calculate_score_words(song_info)
                       + 0.15 * self.calculate_score_length(song_info))
        logger.debug(f'final score for {song_info.song_name} : {final_score}')
        return final_score

    def comparison_type(self) -> None:
        logger.debug('Comparison type for pop genre')
        dc_with_types = self.get_song_from_queue(timeout=5)
        if dc_with_types is None:
            return
        try:
            song_info = dc_with_types.song_info
            final_score = self.calculate_final_score(song_info)
            dc_with_types.pop_genre = final_score
            main_queue.lpush(self.queue_name, dc_with_types.to_json())
            logger.info(f'pushed update Types with pop score={final_score} to queue {self.queue_name}')
        except Exception as e:
            logger.error(f'pop worker failed: {e}')

if __name__ == '__main__':
    _pop = ClassificationForGenrePop('song_info')
    while True:
        try:
            _pop.comparison_type()
            sleep(0.02)
        except Exception as e:
            logger.error(f'pop crash-loop guard: {e}')
            sleep(1)






