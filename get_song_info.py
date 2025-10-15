from get_info_interface import GetInfoInterface
from typing import Optional
import redis
import subprocess
from pathlib import Path
import hashlib
from mutagen import File
from _dataclasses import SongInfo
import re

_WHISPER_MODEL = None
_WHISPER_NAME = None
_WHISPER_DEVICE = None

def get_wisper(model_name='medium', device='cpu'):
    global _WHISPER_MODEL, _WHISPER_NAME, _WHISPER_DEVICE
    if not _WHISPER_MODEL is None:
        return _WHISPER_MODEL
    import whisper
    _WHISPER_MODEL = whisper.load_model(model_name, device=device)
    _WHISPER_NAME = model_name
    _WHISPER_DEVICE = device
    return _WHISPER_MODEL



r = redis.Redis(host='localhost', port=6379, db=0)

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg")

class GetSongInfo(GetInfoInterface):

    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    @staticmethod
    def check_path_is_audio(path: Path) ->None:
        if not path.suffix.lower() in AUDIO_EXTENSIONS:
            raise ValueError(f"{path} is not an audio file")

    @staticmethod
    def check_path_exist(path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"{path} is not a file")

    @staticmethod
    def split_stems(path: Path, out_root: None|Path = None, model_name: str='htdemucs') -> dict[str, Path]:
        def ensure_demucs_installed() -> None:
            from shutil import which
            if which("demucs") is None:
                raise EnvironmentError("demucs CLI not found in PATH. Install via pipx/pip.")
        ensure_demucs_installed()
        if out_root is None:
            out_root = path.parent / "separated_demucs"
        out_root.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:12]
        out_dir = out_root / model_name / h
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["demucs", "-n", model_name, "-d", 'cpu', "-o", str(out_root), str(path)]
        subprocess.run(cmd, capture_output=True, text=True, check=False)
        stems_dir = out_dir
        stem_names = ['vocals', 'bass', 'drums', 'other']
        stems = {}
        for name in stem_names:
            stem = stems_dir / f'{name}.wav'
            if stem.is_file():
                stems[name] = stem
            else:
                stems[name] = None
        if not stems:
            raise FileNotFoundError(f"{stems_dir} is not a file")
        return stems

    @staticmethod
    def receive_song_words(separated_stems: dict[str, Path]) -> list[str]:
        vocal_path = separated_stems['vocals']
        model = get_wisper()
        result  = model.transcribe(str(vocal_path), language='en')
        text = result.get('text', '')
        words = re.findall(r"[A-Za-z']+", text)
        return list(set(w.lower() for w in words))

    @staticmethod
    def receive_song_length(path: Path) -> float:
        audio = File(path)
        if audio is None or not hasattr(audio, 'info') or not hasattr(audio.info, 'length'):
            raise ValueError(f"Mutagen didn't recognize length of {path}")
        length_seconds = audio.info.length
        return length_seconds

    @staticmethod
    def receive_song_sound(separated_stems: dict[str, Path]) -> list[Optional[Path]]:
        bass_path = separated_stems['bass']
        drums_path = separated_stems['drums']
        other_path = separated_stems['other']
        return [bass_path, drums_path, other_path]

    def get_info(self, path: str) ->FileInfo:
        _pathlib = Path(path)
        self.check_path_exist(_pathlib)
        self.check_path_is_audio(_pathlib)
        separated_stems = self.split_stems(_pathlib)
        words = self.receive_song_words(separated_stems)
        length = self.receive_song_length(_pathlib)
        sound = self.receive_song_sound(separated_stems)
        song_info = SongInfo(song_name=path, song_words=words, song_length=length, song_sound=sound)
        song_info= song_info.to_json()
        r.blpush(self.queue_name, song_info)
