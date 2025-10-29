import unittest
from unittest import mock
import hashlib
from get_song_info import GetSongInfo
from pathlib import Path
import pytest

def test_check_path_is_audio():
    GetSongInfo.check_path_is_audio(Path('song.mp3'))

def test_check_path_is_not_audio():
    with pytest.raises(ValueError):
        GetSongInfo.check_path_is_audio(Path('song.txt'))

def test_check_path_not_exist():
    with pytest.raises(FileNotFoundError):
        GetSongInfo.check_path_exist(Path('song.mp3'))

class TestSplitStems(unittest.TestCase):
    @mock.patch('get_song_info.subprocess.run')
    def test_split_stems(self, mock_run):
        tmp = Path('temp_split');  tmp.mkdir(exist_ok=True)
        try:
            audio = tmp / 'track.wav'
            audio.write_bytes(b'fake')
            out_dir = GetSongInfo.split_stems(audio, out_root=tmp, model_name='htdemucs')
            mock_run.assert_called()
            h = hashlib.sha1(str(audio.resolve()).encode()).hexdigest()[:12]
            assert out_dir.is_dir()
            assert out_dir.name == h
            assert out_dir.parent.name == 'htdemucs'
        finally:
            for p in sorted(tmp.rglob('*'), reverse=True):
                try:
                    if p.is_file() or p.is_symlink():
                        p.unlink()
                    elif p.is_dir():
                        p.rmdir()
                except Exception:
                    pass
            try:
                tmp.rmdir()
            except Exception:
                pass

class TestDictOfStems(unittest.TestCase):
    @mock.patch('get_song_info.GetSongInfo.ensure_demucs_installed')
    @mock.patch('get_song_info.GetSongInfo.split_stems')
    def test_dict_of_stems(self, mock_split, mock_demucs):
        tmp = Path('temp_split'); stems_dir = tmp / 'separated_demucs' / 'htdemucs' / '12345rtyuijk'
        stems_dir.mkdir(parents=True,exist_ok=True)
        (stems_dir / 'vocals.wav') . write_bytes(b'f')
        (stems_dir / 'bass.wav') . write_bytes(b'f')
        mock_split.return_value = stems_dir
        try:
            d = GetSongInfo('q').dict_of_stems(Path('some.wav'))
            assert set(d.keys()) == {'vocals', 'bass', 'drums', 'other'}
            assert d['vocals'].is_file()
            assert d['drums'] is None
            assert d['bass'].is_file()
            assert d['other'] is None
        finally:
            for p in sorted(tmp.rglob('*'), reverse=True):
                try:
                    if p.is_file() or p.is_symlink():
                        p.unlink()
                    elif p.is_dir():
                        p.rmdir()
                except Exception:
                    pass
            try:
                tmp.rmdir()
            except Exception:
                pass

class TestGetWords(unittest.TestCase):
    @mock.patch('get_song_info.get_whisper')
    def test_get_words(self,mock_get_whisper):
        tmp = Path('temp_words'); tmp.mkdir(exist_ok=True)
        vocals = tmp / 'vocals.wav'
        vocals.write_bytes(b'f')
        class Dummy:
            def transcribe(self, path, language='en'):
                return {'text': "Love, LOVE! music's beat... Love"}
        dct = {'vocals': vocals}
        mock_get_whisper.return_value = Dummy()
        words = GetSongInfo.receive_song_words(dct)
        try:
            self.assertIn('love', words)
            self.assertIn("music's", words)
            self.assertFalse(vocals.exists())
        finally:
            for p in sorted(tmp.rglob('*'), reverse=True):
                try:
                    if p.is_file() or p.is_symlink():
                        p.unlink()
                    elif p.is_dir():
                        p.rmdir()
                except Exception:
                    pass
            try:
                tmp.rmdir()
            except Exception:
                pass

class TestGetLength(unittest.TestCase):
    @mock.patch('get_song_info.File')
    def test_get_length(self,mock_audio):
        song = 'song.mp3'
        class Info: length = 33.4
        mock_audio.return_value = type('A', (), {'info': Info})()
        length = GetSongInfo.receive_song_length(Path(song))
        self.assertEqual(length, 33.4)


