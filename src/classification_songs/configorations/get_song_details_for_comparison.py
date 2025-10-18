import librosa
import librosa.display
import numpy as np
from classification_songs.configorations._dataclasses import SongInfo
from nltk.stem import WordNetLemmatizer

sr = 22050
class GetSongDetailsForComparison:
    def __init__(self, song_info: SongInfo):
        self.song_info = song_info
        self.sound_files = self.song_info.song_sound
        self.length = self.song_info.song_length
        self.words = self.song_info.song_words

    def get_drums(self) -> dict:
        drums_path = self.sound_files['drums_path']
        y, _sr = librosa.load(drums_path, sr=sr, mono=True)
        y = y - y.mean()
        y = y / (np.max(np.abs(y)) or 1.0)
        on = librosa.onset.onset_strength(y=y, sr=_sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=on, sr=_sr)
        ibi_std = np.std(np.diff(librosa.frames_to_time(beats, sr=sr))) if len(beats) > 2 else np.nan
        on_times = librosa.onset.onset_detect(onset_envelope=on, sr=_sr, units='time')
        onset_density = len(on_times) / (len(y) / _sr)
        return {'tempo': tempo, 'ibi_std': ibi_std, 'onset_density': onset_density}

    @staticmethod
    def low_envelope(y):
        S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)) ** 2
        f = librosa.fft_frequencies(sr=sr, n_fft=1024)
        low = S[f < 200].mean(axis=0)
        low = (low - low.mean()) / (low.std() + 1e-6)
        return low

    def get_bass(self) -> dict:
        bass_path = self.sound_files['bass_path']
        b, _ = librosa.load(bass_path, sr=sr, mono=True)
        s = np.abs(librosa.stft(b, n_fft=2048, hop_length=512)) ** 2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        total = s.sum() + 1e-12
        low_ratio = s[(freqs >= 20) & (freqs < 200), :].sum() / total
        drums_path = self.sound_files['drums_path']
        d, _ = librosa.load(drums_path, sr=sr, mono=True)
        la, lb = self.low_envelope(b), self.low_envelope(d)
        n = min(len(la), len(lb))
        corr = float(np.dot(la[:n], lb[:n]) / (n)) if n > 8 else 0
        return {'low_ratio': low_ratio, 'corr': corr}


    def get_other(self) -> dict:
        other_path = self.sound_files['other_path']
        o, _ = librosa.load(other_path, sr=sr, mono=True)
        centroid = librosa.feature.spectral_centroid(y=o, sr=sr).mean()
        rms = librosa.feature.rms(y=o).flatten()
        dr_db = 10 * np.log10((np.percentile(rms, 95) + 1e-9) / (np.percentile(rms, 10) + 1e-9))
        return {'centroid': centroid, 'dr_db': dr_db}

    def get_all_sound(self)->dict[str, dict]:
        drums = self.get_drums()
        bass = self.get_bass()
        other = self.get_other()
        return {
            'drums': drums,
            'bass': bass,
            'other': other
        }

    def get_length(self):
        return self.length

    def _lemmatizer(self):
        song_words = self.words
        lemmatizer = WordNetLemmatizer()
        lemmatized_words = []
        for word in song_words:
            lemmatized_words.append(lemmatizer.lemmatize(word, pos='v'))
            if lemmatized_words[-1] == word:
                lemmatized_words[-1] = lemmatizer.lemmatize(word, pos='n')
            if lemmatized_words[-1] == word:
                lemmatized_words[-1] = lemmatizer.lemmatize(word, pos='a')
        return lemmatized_words

    def get_words(self):
        return self._lemmatizer()




