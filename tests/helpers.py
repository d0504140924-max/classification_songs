# כלי עזר משותפים לכל הטסטים
import importlib.util, types, re, pathlib, json
import builtins
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # תקן אם צריך

def load_module_wo_runner(filename: str, module_name: str):
    """
    טוען מודול מקובץ, אך מסיר ממנו את בלוק ה-'while True' האחרון כדי שלא ירוץ לופ אינסופי בזמן import.
    """
    path = ROOT / filename
    src = path.read_text(encoding="utf-8")
    # חתוך מה-while True האחרון עד סוף הקובץ (כולל)
    cut = re.sub(r"(?:\n|\r\n?)while\s+True\s*:\s*(?:.|\n|\r\n)*\Z", "\n", src, count=1, flags=re.MULTILINE)
    mod = types.ModuleType(module_name)
    mod.__file__ = str(path)
    exec(compile(cut, filename, "exec"), mod.__dict__)
    return mod

# דמי Types/SongInfo תואמים לממשק שמופיע בקוד שלכם
@dataclass
class DummySongInfo:
    song_name: str = "x"
    song_path: Path = Path("dummy.mp3")
    song_words: list[str] = None
    song_length: float = 0.0
    song_sound: dict | None = None

@dataclass
class DummyTypes:
    song_info: DummySongInfo
    pop_genre: float | None = None
    rap_genre: float | None = None
    classical_genre: float | None = None
    love_song: bool = False

    def to_json(self) -> str:
        return json.dumps({
            "song_info": {
                "song_name": self.song_info.song_name,
                "song_path": str(self.song_info.song_path),
                "song_words": self.song_info.song_words,
                "song_length": self.song_info.song_length,
                "song_sound": self.song_info.song_sound,
            },
            "pop_genre": self.pop_genre,
            "rap_genre": self.rap_genre,
            "classical_genre": self.classical_genre,
            "love_song": self.love_song,
        })

    @classmethod
    def from_json(cls, s: str):
        d = json.loads(s)
        si = d["song_info"]
        return cls(
            song_info=DummySongInfo(
                song_name=si["song_name"],
                song_path=Path(si["song_path"]),
                song_words=si["song_words"],
                song_length=si["song_length"],
                song_sound=si["song_sound"],
            ),
            pop_genre=d.get("pop_genre"),
            rap_genre=d.get("rap_genre"),
            classical_genre=d.get("classical_genre"),
            love_song=d.get("love_song", False),
        )

class DummyQueue:
    def __init__(self): self.store = {}
    def lpush(self, key, val): self.store.setdefault(key, []).insert(0, val)
    def rpop(self, key):
        arr = self.store.get(key) or []
        return arr.pop() if arr else None

class DummyLibrosa:
    """ מחליף פונקציות librosa בשימוש אצלכם. """
    class feature:
        @staticmethod
        def spectral_centroid(y, sr): import numpy as np; return np.array([[2200.0]])
        @staticmethod
        def rms(y): import numpy as np; return np.array([[0.1, 0.2, 0.3, 0.4]])
    class onset:
        @staticmethod
        def onset_strength(y, sr): import numpy as np; return np.ones(10)
        @staticmethod
        def onset_detect(onset_envelope, sr, units='time'): return [0.1,0.2,0.4,0.8]
    class beat:
        @staticmethod
        def beat_track(onset_envelope, sr): return (110.0, [1,2,3,4,5])
    @staticmethod
    def load(path, sr=22050, mono=True): import numpy as np; return (np.ones(44100), sr)
    @staticmethod
    def stft(y, n_fft=1024, hop_length=256): import numpy as np; return np.ones((n_fft//2+1, 50))
    @staticmethod
    def fft_frequencies(sr, n_fft): import numpy as np; return np.linspace(0, sr/2, n_fft//2+1)
    @staticmethod
    def frames_to_time(beats, sr): import numpy as np; return np.array(beats)/float(sr)

def patch_external(mod, *, set_types=False, set_queue=False, set_librosa=False, set_wordnet=False, set_mutagen=False):
    """ הזרקת תלותים מדומים למודול שטעינו. """
    if set_types:
        mod.Types = DummyTypes
        # במודולים שמייבאים SongInfo, ניתן להציב DummySongInfo:
        mod.SongInfo = DummySongInfo
    if set_queue:
        dq = DummyQueue()
        mod.main_queue = dq
        return dq
    if set_librosa:
        mod.librosa = DummyLibrosa
    if set_wordnet:
        class DummyLem:
            def lemmatize(self, w, pos='n'): return w.lower()
        class DummyStem:
            def WordNetLemmatizer(self): return DummyLem()
        # אם הייבוא הוא "from nltk.stem import WordNetLemmatizer" – נאלץ לגשר:
        mod.WordNetLemmatizer = DummyStem().WordNetLemmatizer
    if set_mutagen:
        class W:
            def __init__(self, p): self.tags={}
            def __setitem__(self,k,v): self.tags[k]=v
            def save(self): pass
        class MP4(W): pass
        class FLAC(W): pass
        class OggVorbis(W): pass
        class EasyID3(dict):
            @staticmethod
            def RegisterTextKey(a,b): pass
            def save(self): pass
        class File(dict):
            def add_tags(self): pass
        class MP3: pass
        mod.MP3 = MP3; mod.MP4 = MP4; mod.FLAC = FLAC; mod.OggVorbis = OggVorbis
        mod.EasyID3 = EasyID3; mod.File = File
        # WAV מיובא כ: from mutagen.wave import WAVE – לכן נציב גם:
        mod.WAVE = W
