from classification_interface import ClassificationInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.get_song_details_for_comparison import GetSongDetailsForComparison
from classification_songs.configorations.configoration import (main_queue, CLASSICAL_COMMON, CLASSICAL_LESS_COMMON,
                                                               CLASSICAL_MOST_COMMON)
from classification_songs.configorations.logger_setup import logger_info_process as logger
import numpy as np

class ClassificationForGenreClassical(ClassificationInterface):

    def __init__(self, queue_name):
        self.queue_name = queue_name

    @staticmethod
    def get_song_from_queue():
        logger.info('Getting song info from queue "classical_genre" for classification classical genre')
        info_json = main_queue.rpop('classical_genre')
        if not info_json:
            logger.info('No classical genre info available in queue')
            return None
        with_types = Types.from_json(info_json)
        logger.debug(f'With types ')
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
        logger.info('Calculating score words for classical genre')
        song_words = self.get_words(song_info)
        words_score = 0.0
        for word in CLASSICAL_MOST_COMMON:
            num_show = song_words.count(word)
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in CLASSICAL_COMMON:
            num_show = song_words.count(word) * 0.7
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        for word in CLASSICAL_LESS_COMMON:
            num_show = song_words.count(word) * 0.4
            if num_show > 0:
                words_score += (len(song_words)/num_show)
        final_score = min(words_score/3.0, 100.0)
        logger.debug(f'Final score for words: {final_score}')
        return final_score

    def calculate_score_length(self, song_info: SongInfo)->float:
        logger.info('Calculating score length for classical genre')
        length = self.get_length(song_info)
        score_length = 0.0
        if 240 <= length < 600:
            score_length += 100.0
        elif 120 < length < 240:
            score_length += 60.0
        elif 600 <= length < 1200:
            score_length += 80.0
        logger.debug(f'final score length: {score_length}')
        return score_length

    def drums_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        drums = sound['drums']
        tempo = drums['tempo']
        ibi_std = drums['ibi_std'] if np.isfinite(drums['ibi_std']) else 0.5
        onset_density = drums['onset_density']
        density_component = (1 - min(onset_density / 1.5, 1.0)) * 0.5  # משקל מרכזי
        ibi_component = min(ibi_std, 0.8) / 0.8 * 0.3
        tempo_dev = min(abs(tempo - 60), abs(tempo - 120))
        tempo_component = (1 - min(tempo_dev, 60) / 60) * 0.2
        drum_score = (density_component + ibi_component + tempo_component) * 100.0
        return max(0.0, min(100, drum_score))

    def bass_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        bass = sound['bass']
        low_ratio = bass['low_ratio']
        low_component = (1 - abs(low_ratio - 0.12) / 0.10) * 0.7  # יעד ~0.12, חלון ±0.10
        corr = bass['corr']
        corr_component = max(0.0, min(1.0, (corr + 0.4) / 1.2)) * 0.3
        bass_score = (low_component + corr_component) * 100.0
        return max(0.0, min(100, bass_score))

    def others_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        other = sound['other']
        bright_score = 1 - (min(abs(other['centroid'] - 2600) / 1200, 1.0) * 1.0)
        dr_scor = 1 - (min(abs(other['dr_db'] - 14) / 6, 1.0) * 1.0)
        other_score = 70.0 * bright_score + 30.0 * dr_scor
        return other_score

    def calculate_sound_score(self, song_info: SongInfo)->float:
        logger.info('Calculating sound score for classical genre')
        sound_score = (0.4 * self.drums_scor(song_info)
                       + 0.3 * self.bass_scor(song_info)
                       + 0.3 * self.others_scor(song_info))
        logger.debug(f'sound score: {sound_score}')
        return sound_score

    def calculate_final_score(self, song_info: SongInfo)->float:
        logger.info('Calculating final score for classical genre')
        final_score = (0.65 * self.calculate_sound_score(song_info)
                       + 0.05 * self.calculate_score_words(song_info)
                       + 0.30 * self.calculate_score_length(song_info))
        logger.debug(f'final score: {final_score}')
        return final_score

    def comparison_type(self) ->None:
        logger.info('Comparing classical genre')
        dc_with_types = self.get_song_from_queue()
        song_info = dc_with_types.song_info
        final_score = self.calculate_final_score(song_info)
        classical = final_score
        dc_with_types.classical_genre = classical
        l
        main_queue.lpush(self.queue_name, dc_with_types.to_json())


_classical = ClassificationForGenreClassical('song_info')
while True:
    _classical.comparison_type()



