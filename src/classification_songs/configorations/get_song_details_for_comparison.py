import librosa
import librosa.display
import numpy as np
from classification_songs.configorations._dataclasses import SongInfo
from classification_songs.configorations.logger_setup import logger_info_process as logger
from nltk.stem import WordNetLemmatizer

sr = 22050
class GetSongDetailsForComparison:
    def __init__(self, song_info: SongInfo):
        self.song_info = song_info
        self.sound_files = self.song_info.song_sound
        self.length = self.song_info.song_length
        self.words = self.song_info.song_words
        logger.info(f'Initialized GetSongDetailsForComparison for {song_info.song_name}')


    def get_drums(self) -> dict:
        try:
            drums_path = self.sound_files['drums_path']
            logger.debug(f'Loading drums from {drums_path}')
            y, _sr = librosa.load(drums_path, sr=sr, mono=True)
            y = y - y.mean()
            y = y / (np.max(np.abs(y)) or 1.0)
            on = librosa.onset.onset_strength(y=y, sr=_sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=on, sr=_sr)
            ibi_std = np.std(np.diff(librosa.frames_to_time(beats, sr=sr))) if len(beats) > 2 else np.nan
            on_times = librosa.onset.onset_detect(onset_envelope=on, sr=_sr, units='time')
            onset_density = len(on_times) / (len(y) / _sr)
            logger.debug(f'Drums analyzed: tempo={tempo}, onset_density={onset_density}')
            return {'tempo': tempo, 'ibi_std': ibi_std, 'onset_density': onset_density}
        except Exception as e:
            logger.error(f'Failed to analyze drums: {e}')
            return {'tempo': 0, 'ibi_std': np.nan, 'onset_density': 0}

    @staticmethod
    def low_envelope(y):
        S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)) ** 2
        f = librosa.fft_frequencies(sr=sr, n_fft=1024)
        low = S[f < 200].mean(axis=0)
        low = (low - low.mean()) / (low.std() + 1e-6)
        return low

    def get_bass(self) -> dict:
        try:
            bass_path = self.sound_files['bass_path']
            logger.debug(f'Loading bass from {bass_path}')
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
            logger.debug(f'Bass analyzed: low_ratio={low_ratio}, corr={corr}')
            return {'low_ratio': low_ratio, 'corr': corr}
        except Exception as e:
            logger.error(f'Failed to analyze bass: {e}')
            return {'low_ratio': 0, 'corr': 0}


    def get_other(self) -> dict:
        try:
            other_path = self.sound_files['other_path']
            logger.debug(f'Loading other from {other_path}')
            o, _ = librosa.load(other_path, sr=sr, mono=True)
            centroid = librosa.feature.spectral_centroid(y=o, sr=sr).mean()
            rms = librosa.feature.rms(y=o).flatten()
            dr_db = 10 * np.log10((np.percentile(rms, 95) + 1e-9) / (np.percentile(rms, 10) + 1e-9))
            logger.debug(f'Other analyzed: centroid={centroid:.2f}, dr_db={dr_db}')
            return {'centroid': centroid, 'dr_db': dr_db}
        except Exception as e:
            logger.error(f'Failed to analyze other: {e}')
            return {'centroid': 0, 'dr_db': 0}

    def get_all_sound(self)->dict[str, dict]:
        logger.info(f'Getting all sound details for {self.song_info.song_name}')
        drums = self.get_drums()
        bass = self.get_bass()
        other = self.get_other()
        return {
            'drums': drums,
            'bass': bass,
            'other': other
        }

    def get_length(self):
        logger.debug(f'Length for {self.song_info.song_name}: {self.length}')
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
        logger.debug(f'Lemmatized words: {lemmatized_words[:10]} ...')
        return lemmatized_words

    def get_words(self):
        logger.info(f'Getting lemmatized words for {self.song_info.song_name}')
        return self._lemmatizer()

if __name__ == "__main__":
    logger.info("Running GetSongDetailsForComparison test mode")


