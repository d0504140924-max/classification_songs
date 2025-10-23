import sys

from classification_songs.information.get_info_interface import GetInfoInterface
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.configorations.configoration import get_whisper, AUDIO_EXTENSIONS, STEM_NAMES, main_queue
from classification_songs.configorations.logger_setup import logger_info_process
from typing import Optional
import subprocess
from pathlib import Path
import hashlib
from mutagen import File
import re

class GetSongInfo(GetInfoInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        logger_info_process.info(f'initialized GetSongInfo with queue: {queue_name}')

    @staticmethod
    def check_path_is_audio(path: Path) ->None:
        logger_info_process.debug(f'Checking file audio or not {path}')
        if not path.suffix.lower() in AUDIO_EXTENSIONS:
            logger_info_process.error(f'{path} is not an audio file')
            raise ValueError(f"{path} is not an audio file")

    @staticmethod
    def check_path_exist(path: Path) -> None:
        logger_info_process.debug(f'Checking path existing {path}')
        if not path.is_file():
            logger_info_process.error(f'{path} is not exist')
            raise FileNotFoundError(f"{path} is not a file")

    @staticmethod
    def get_song_id(path: Path) -> str:
        st = path.stat()
        payload = f'{path.resolve()}|{st.st_size}|{int(st.st_mtime)}'
        return hashlib.sha1(payload.encode()).hexdigest()[:16]

    @staticmethod
    def ensure_demucs_installed() -> None:
        from shutil import which
        logger_info_process.debug(f'Ensuring demucs is installed')
        if which("demucs") is None:
            logger_info_process.error(f'demucs is not installed')
            raise EnvironmentError("demucs CLI not found in PATH. Install via pipx/pip.")

    @staticmethod
    def split_stems(path: Path, out_root: None|Path = None, model_name: str='htdemucs') -> Path:
        logger_info_process.debug(f'Splitting stems for {path}')
        if out_root is None:
            out_root = path.parent / "separated_demucs"
        out_root.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:12]
        out_dir = out_root / model_name / h
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["demucs", "-n", model_name, "-d", 'cpu', "-o", str(out_dir), str(path)]
        subprocess.run(cmd, capture_output=True, text=True, check=False)
        produced_dir = out_dir / model_name / path.stem
        logger_info_process.debug(f'Demucs output directory {out_dir}')
        return produced_dir

    def dict_of_stems(self, path: Path) -> dict[str, Path]:
        logger_info_process.debug(f'Creating dictionary of stems for {path}')
        self.ensure_demucs_installed()
        stems_dir = self.split_stems(path)
        stems = {}
        for name in STEM_NAMES:
            stem = stems_dir / f'{name}.wav'
            if stem.is_file():
                stems[name] = stem
            else:
                stems[name] = None
        missing = [name for name, p in stems.items() if p is None]
        if missing:
            logger_info_process.error(f'Missing stems {missing} in {stems_dir}')
            raise FileNotFoundError(f"Missing stems {missing} in {stems_dir}")
        logger_info_process.debug(f'Stems: {stems}')
        return stems

    @staticmethod
    def receive_song_words(separated_stems: dict[str, Path]) -> list[str]:
        vocals = separated_stems.get('vocals')
        if not vocals or not vocals.is_file():
            logger_info_process.error('No vocals stem available to transcribe')
            return []
        logger_info_process.info(f'Transcribing vocal from {vocals}')
        model = get_whisper()
        result  = model.transcribe(str(vocals), language='en')
        try:
            vocals.unlink()
            logger_info_process.debug(f'Removed temporary vocal file {vocals}')
        except Exception as e:
            logger_info_process.warning(f'Failed to remove vocal file {vocals}: {e}')
        text = result.get('text', '') if isinstance(result, dict) else ''
        words = re.findall(r"[A-Za-z']+", text)
        logger_info_process.debug(f'Extracted words: {words}')
        return [w.lower() for w in words]

    @staticmethod
    def receive_song_length(path: Path) -> float:
        logger_info_process.info(f'Receiving song length for {path}')
        audio = File(path)
        if audio is None or not hasattr(audio, 'info') or not hasattr(audio.info, 'length'):
            logger_info_process.error(f'Mutagen failed to get length from {path}')
            raise ValueError(f"Mutagen didn't recognize length of {path}")
        length_seconds = audio.info.length
        return length_seconds

    @staticmethod
    def receive_song_sound(separated_stems: dict[str, Path]) -> dict:
        logger_info_process.debug(f'Collecting sound stems')
        bass_path = separated_stems['bass']
        drums_path = separated_stems['drums']
        other_path = separated_stems['other']
        return {'bass_path': bass_path, 'drums_path': drums_path, 'other_path': other_path}

    def get_info(self, path: str) ->None:
        logger_info_process.debug(f'Getting info for {path}')
        _pathlib = Path(path)
        self.check_path_exist(_pathlib)
        self.check_path_is_audio(_pathlib)
        separated_stems = self.dict_of_stems(_pathlib)
        words = self.receive_song_words(separated_stems)
        length = self.receive_song_length(_pathlib)
        sound = self.receive_song_sound(separated_stems)
        song_info = SongInfo(song_name=_pathlib.stem,song_path=_pathlib, song_words=words, song_length=length, song_sound=sound)
        types = Types(song_info=song_info)
        main_queue.lpush(self.queue_name, types.to_json())
        logger_info_process.info(f'Pushed song {song_info.song_name} to queue{self.queue_name}')

def main(path: str) -> None:
    get_info = GetSongInfo('song_info')
    while True:
        get_info.get_info(path)
if __name__ == '__main__':
    main(sys.argv[1])
