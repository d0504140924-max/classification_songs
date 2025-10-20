from classification_interface import ClassificationInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.get_song_details_for_comparison import GetSongDetailsForComparison
from classification_songs.configorations.configoration import (main_queue, POP_COMMON, POP_LESS_COMMON, POP_MOST_COMMON)
from classification_songs.configorations.logger_setup import logger_info_process as logger
import numpy as np

GROUP_NAME = 'pop'
CONSUMER_NAME = 'POP-1'

class ClassificationForGenrePop(ClassificationInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    @staticmethod
    def get_song_from_queue():
        info_json = main_queue.rpop('pop_genre')
        if not info_json:
            return None
        with_types = Types.from_json(info_json)
        return with_types

    @staticmethod
    def check_double_processing(_type)->bool:
        pop = getattr(_type, 'pop_genre', None)
        return pop in (None, '', [], {})

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
        return final_score

    def calculate_score_length(self, song_info: SongInfo)->float:
        length = self.get_length(song_info)
        score_length = 0.0
        if 165 <= length < 225:
            score_length += 100.0
        elif 120 < length < 165:
            score_length += 45.0
        elif 225 <= length < 300:
            score_length += 75.0
        return score_length

    def drums_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        drums = sound['drums']
        drum_score = (
            ((1 - min(abs(drums['tempo']-110), 40)/40) * 0.5)*100 +
            ((1 - min(drums['ibi_std'] if np.isfinite(drums['ibi_std']) else 0.5)/0.5) * 0.3)*100 +
            (min(drums['onset_density']/2.0, 1.0) * 0.2)*100
        )
        return max(0.0, min(100, drum_score))

    def bass_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        bass = sound['bass']
        bass_score = (
            ((1 - abs(bass['low_ratio']-0.20)/0.20) * 0.6)*100 +
            max(0.0, min(1.0, (bass['corr']+0.5)/1.0)) *40.0
        )
        return max(0.0, min(100, bass_score))

    def others_scor(self, song_info: SongInfo)->float:
        sound = self.get_sound_details(song_info)
        other = sound['other']
        bright_score = 1 - ((min(abs(other['centroid']-2200)/1200, 1.0))*1.0)
        dr_scor = 1 - (min(abs(other['dr_db']-12)/6, 1.0)*1.0)
        other_score = 70.0*bright_score + 30.0*dr_scor
        return other_score

    def calculate_sound_score(self, song_info: SongInfo)->float:
        sound_score = 0.4*self.drums_scor(song_info) + 0.3*self.bass_scor(song_info) + 0.3*self.others_scor(song_info)
        return sound_score

    def calculate_final_score(self, song_info: SongInfo)->float:
        final_score = (0.50 * self.calculate_sound_score(song_info)
                       + 0.35 * self.calculate_score_words(song_info)
                       + 0.15 * self.calculate_score_length(song_info))
        return final_score

    def comparison_type(self) -> None:
        dc_with_types = self.get_song_from_queue()
        song_info = dc_with_types.song_info
        final_score = self.calculate_final_score(song_info)
        pop = final_score
        dc_with_types.pop_genre = pop
        main_queue.lpush(self.queue_name, dc_with_types.to_json())


_pop = ClassificationForGenrePop('song_info')
while True:
    _pop.comparison_type()






