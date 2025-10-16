from classification_interface import ClassificationInterface
from logger_setup import logger2
from _dataclasses import SongInfo, Types
import numpy as np
from get_song_details_for_comparison import GetSongDetailsForComparison
from configoration import (info_queue, types_queue, POP_COMMON, POP_LESS_COMMON, POP_MOST_COMMON)

class ClassificationForGenrePop(ClassificationInterface):

    def __init__(self, info_queue_name, types_queue_name):
        self.info_queue_name = info_queue_name
        self.types_queue_name = types_queue_name

    def get_song_from_queue(self):
        info_json = info_queue.rpop(self.info_queue_name)
        as_dataclass = SongInfo.from_json(info_json)
        info_queue.lpush(self.info_queue_name, info_json)
        return as_dataclass

    def get_sound_details(self)->dict:
        _all = GetSongDetailsForComparison(self.get_song_from_queue())
        return _all.get_all_sound()

    def get_length(self)->float:
        _all = GetSongDetailsForComparison(self.get_song_from_queue())
        return _all.get_length()

    def get_words(self)->list:
        _all = GetSongDetailsForComparison(self.get_song_from_queue())
        return _all.get_words()

    def calculate_score_words(self)->float:
        song_words = self.get_words()
        words_score = 0.0
        for word in POP_MOST_COMMON:
            num_show = word.count(song_words)
            words_score += (len(song_words)/num_show)
        for word in POP_COMMON:
            num_show = word.count(song_words) * 0.7
            words_score += (len(song_words)/num_show)
        for word in POP_LESS_COMMON:
            num_show = word.count(song_words) * 0.4
            words_score += (len(song_words)/num_show)
        final_score = min(words_score/3.0, 100.0)
        return final_score

    def calculate_score_length(self)->float:
        length = self.get_length()
        score_length = 0.0
        if 165 <= length < 225:
            score_length += 100.0
        elif 120 < length < 165:
            score_length += 45.0
        elif 225 <= length < 300:
            score_length += 75.0
        return score_length

    def drums_scor(self)->float:
        sound = self.get_sound_details()
        drums = sound['drums']
        drum_score = (
            (100 - min(abs(drums['temp']-110), 40)/40) * 50.0 +
            (100 - min(drums['ibi_std'] if np.isfinite(drums['ibi_std']) else 0.5)/0.5) * 30.0 +
            min(drums['onset_density']/2.0, 1.0) * 20.0
        )
        return max(0.0, min(100, drum_score))

    def bass_scor(self)->float:
        sound = self.get_sound_details()
        bass = sound['bass']
        bass_score = (
            (100 - abs(bass['low_ratio']-0.20)/0.20) * 60.0 +
            max(0.0, min(1.0, (bass['corr']+0.5)/1.0)) *40.0
        )
        return max(0.0, min(100, bass_score))

    def others_scor(self)->float:
        sound = self.get_sound_details()
        other = sound['other']
        bright_score = 100 - ((min(abs(other['centroid']-2200)/1200, 1.0))*100.0)
        dr_scor = 100 - (min(abs(other['dr_db']-12)/6, 1.0)*100.0)
        other_score = 70.0*bright_score + 30.0*dr_scor
        return other_score

    def calculate_sound_score(self)->float:
        sound_score = 0.4*self.drums_scor() + 0.3*self.bass_scor() + 0.3*self.others_scor()
        return sound_score

    def calculate_final_score(self)->float:
        final_score = 0.50*self.calculate_sound_score() + 0.35*self.calculate_score_words() + 0.15*self.calculate_score_length()
        return final_score

    def comparison_type(self):
        pop = self.calculate_final_score() > 50
        types = Types(song_name=SongInfo.song_name, pop_genre=pop)
        types_queue.lpush(types)
        return pop





