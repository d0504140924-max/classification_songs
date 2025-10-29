import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent))  # כדי ש-helpers יימצא
import numpy as np
from helpers import load_module_wo_runner, patch_external, DummySongInfo, DummyLibrosa

# מכסה: get_drums/get_bass/get_other/get_all_sound/_lemmatizer  :contentReference[oaicite:6]{index=6}

def _make_mod_with_fakes():
    # librosa נטען בשורה הראשונה במודול – צריך להזריק לפני ה-load:
    sys.modules['librosa'] = DummyLibrosa  # <- חשוב!
    mod = load_module_wo_runner("classification_songs/configorations/get_song_details_for_comparison.py", "gsdfc")
    # השאר פאטצ'ים אחרי הטעינה:
    patch_external(mod, set_wordnet=True)   # לממטייזר דמה
    return mod

def test_get_drums_bass_other_and_all_sound():
    mod = _make_mod_with_fakes()
    si = DummySongInfo(
        song_sound={
            "drums_path": "drums.wav",
            "bass_path": "bass.wav",
            "other_path": "other.wav",
        },
        song_length=180.0,
        song_words=["Love","MUSIC","Beat"],
    )
    g = mod.GetSongDetailsForComparison(si)
    d = g.get_drums()      # tempo/ibi_std/onset_density  :contentReference[oaicite:7]{index=7}
    b = g.get_bass()       # low_ratio/corr              :contentReference[oaicite:8]{index=8}
    o = g.get_other()      # centroid/dr_db             :contentReference[oaicite:9]{index=9}
    all_ = g.get_all_sound()

    assert {"tempo","ibi_std","onset_density"} <= d.keys()
    assert {"low_ratio","corr"} <= b.keys()
    assert {"centroid","dr_db"} <= o.keys()
    assert set(all_.keys()) == {"drums","bass","other"}

def test_length_and_words_lemmatizer():
    mod = _make_mod_with_fakes()
    si = DummySongInfo(song_sound={"drums_path":"d.wav","bass_path":"b.wav","other_path":"o.wav"},
                       song_length=200.0,
                       song_words=["LOVING","Songs"])
    g = mod.GetSongDetailsForComparison(si)
    assert g.get_length() == 200.0
    words = g.get_words()  # מפעיל _lemmatizer עם WordNet דמה  :contentReference[oaicite:10]{index=10}
    assert [w.lower() for w in words] == ["loving","songs"]
