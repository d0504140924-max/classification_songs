from get_info_interface import GetInfoInterface
from typing import Optional
import subprocess
from pathlib import Path
import hashlib
from mutagen import File
from _dataclasses import SongInfo
import re
from configoration import get_whisper, AUDIO_EXTENSIONS, STEM_NAMES, info_queue
from logger_setup import logger

class GetSongInfo(GetInfoInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        logger.info(f'initialized GetSongInfo with queue: {queue_name}')

    @staticmethod
    def check_path_is_audio(path: Path) ->None:
        logger.debug(f'Checking file audio or not {path}')
        if not path.suffix.lower() in AUDIO_EXTENSIONS:
            logger.error(f'{path} is not an audio file')
            raise ValueError(f"{path} is not an audio file")

    @staticmethod
    def check_path_exist(path: Path) -> None:
        logger.debug(f'Checking path existing {path}')
        if not path.is_file():
            logger.error(f'{path} is not exist')
            raise FileNotFoundError(f"{path} is not a file")

    @staticmethod
    def ensure_demucs_installed() -> None:
        from shutil import which
        logger.debug(f'Ensuring demucs is installed')
        if which("demucs") is None:
            logger.error(f'demucs is not installed')
            raise EnvironmentError("demucs CLI not found in PATH. Install via pipx/pip.")

    @staticmethod
    def split_stems(path: Path, out_root: None|Path = None, model_name: str='htdemucs') -> Path:
        logger.debug(f'Splitting stems for {path}')
        if out_root is None:
            out_root = path.parent / "separated_demucs"
        out_root.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:12]
        out_dir = out_root / model_name / h
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["demucs", "-n", model_name, "-d", 'cpu', "-o", str(out_root), str(path)]
        subprocess.run(cmd, capture_output=True, text=True, check=False)
        logger.debug(f'Demucs output directory {out_dir}')
        return out_dir

    def dict_of_stems(self, path: Path) -> dict[str, Path]:
        logger.debug(f'Creating dictionary of stems for {path}')
        self.ensure_demucs_installed()
        stems_dir = self.split_stems(path)
        stems = {}
        for name in STEM_NAMES:
            stem = stems_dir / f'{name}.wav'
            if stem.is_file():
                stems[name] = stem
            else:
                stems[name] = None
        if not stems:
            logger.error(f'No stems found in {stems_dir}')
            raise FileNotFoundError(f"{stems_dir} is not a file")
        logger.debug(f'Stems: {stems}')
        return stems

    @staticmethod
    def receive_song_words(separated_stems: dict[str, Path]) -> list[str]:
        logger.debug(f'Receiving song words for {separated_stems['vocals']}')
        vocal_path = separated_stems['vocals']
        logger.info(f'Transcribing vocal from {vocal_path}')
        model = get_whisper()
        result  = model.transcribe(str(vocal_path), language='en')
        vocal_path.unlink()
        text = result.get('text', '')
        words = re.findall(r"[A-Za-z']+", text)
        logger.debug(f'Extracted words: {words}')
        return [w.lower() for w in words]

    @staticmethod
    def receive_song_length(path: Path) -> float:
        logger.info(f'Receiving song length for {path}')
        audio = File(path)
        if audio is None or not hasattr(audio, 'info') or not hasattr(audio.info, 'length'):
            logger.error(f'Mutagen failed to get length from {path}')
            raise ValueError(f"Mutagen didn't recognize length of {path}")
        length_seconds = audio.info.length
        return length_seconds

    @staticmethod
    def receive_song_sound(separated_stems: dict[str, Path]) -> list[Optional[Path]]:
        logger.debug(f'Collecting sound stems')
        bass_path = separated_stems['bass']
        drums_path = separated_stems['drums']
        other_path = separated_stems['other']
        return [bass_path, drums_path, other_path]

    def get_info(self, path: str) ->SongInfo:
        logger.debug(f'Getting info for {path}')
        _pathlib = Path(path)
        self.check_path_exist(_pathlib)
        self.check_path_is_audio(_pathlib)
        separated_stems = self.dict_of_stems(_pathlib)
        words = self.receive_song_words(separated_stems)
        length = self.receive_song_length(_pathlib)
        sound = self.receive_song_sound(separated_stems)
        song_info = SongInfo(song_name=path, song_words=words, song_length=length, song_sound=sound)
        info_queue.lpush(self.queue_name, song_info.to_json())
        logger.info(f'Pushed song {song_info} to queue {self.queue_name}')
        return song_info

