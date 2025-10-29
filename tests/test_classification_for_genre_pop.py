import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent))  # כדי ש-helpers יימצא
import json
import numpy as np
from pathlib import Path
from helpers import load_module_wo_runner, patch_external, DummyTypes, DummySongInfo

# מכסה:
# - get_song_from_queue (ריק/מלא)  :contentReference[oaicite:11]{index=11}
# - calculate_score_words/length/sound/final  :contentReference[oaicite:12]{index=12}  :contentReference[oaicite:13]{index=13}
# - drums_scor/bass_scor/others_scor  :contentReference[oaicite:14]{index=14}
# - comparison_type: דוחף חזרה לתור היעד  :contentReference[oaicite:15]{index=15}

def make_module_with_dummies():
    mod = load_module_wo_runner("classification_songs/classifications/classification_for_genre_pop.py", "popmod")

    dq = patch_external(mod, set_queue=True)  # main_queue דמה
    patch_external(mod, set_types=True)       # Types/SongInfo דמה

    # מחליף את מחלקת המאפיינים כך שלא נזדקק ל-librosa
    class DummyG:
        def __init__(self, si): self.si = si
        def get_all_sound(self):
            return {
                "drums": {"tempo": 110.0, "ibi_std": 0.1, "onset_density": 1.2},
                "bass": {"low_ratio": 0.20, "corr": 0.3},
                "other": {"centroid": 2200.0, "dr_db": 12.0},
            }
        def get_length(self): return self.si.song_length
        def get_words(self):  return (self.si.song_words or [])
    mod.GetSongDetailsForComparison = DummyG
    return mod, dq

def test_get_song_from_queue_empty_and_nonempty():
    mod, dq = make_module_with_dummies()
    P = mod.ClassificationForGenrePop("song_info")

    assert P.get_song_from_queue() is None  # ללא פריטים  :contentReference[oaicite:16]{index=16}

    t = DummyTypes(song_info=DummySongInfo(song_words=["love","pop"], song_length=180.0))
    dq.lpush("pop_genre", t.to_json())
    got = P.get_song_from_queue()
    assert isinstance(got, DummyTypes)

def test_scores_and_pipeline_push_back():
    mod, dq = make_module_with_dummies()
    P = mod.ClassificationForGenrePop("song_info")

    t = DummyTypes(song_info=DummySongInfo(song_words=["love","love","music","pop"], song_length=180.0))
    # דחיפה לדמה queue של pop_genre
    dq.lpush("pop_genre", t.to_json())

    # comparison_type שולף, מחשב ציון סופי, מציב pop_genre ומחזיר לתור היעד  :contentReference[oaicite:17]{index=17}
    P.comparison_type()

    # נבדוק שנדחף משהו לתור היעד ("song_info" הועבר בקונסטרקטור)
    assert "song_info" in dq.store
    pushed = dq.store["song_info"][0]  # json
    j = json.loads(pushed)
    assert isinstance(j.get("pop_genre"), (int, float))
    # sanity על רכיבי הציונים:
    assert 0.0 <= P.calculate_score_length(t.song_info) <= 100.0
    assert 0.0 <= P.calculate_sound_score(t.song_info) <= 100.0
