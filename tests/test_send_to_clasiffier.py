import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent))  # כדי ש-helpers יימצא
import json
from helpers import load_module_wo_runner, patch_external, DummyTypes, DummySongInfo

# מכסה: get_song_from_queue(), queues() שמפזר ל-LIST_OF_TYPES או ל-'all_filed'  :contentReference[oaicite:18]{index=18}  :contentReference[oaicite:19]{index=19}

def make_module():
    mod = load_module_wo_runner("classification_songs/classifications/send_to_clasiffier.py", "routermod")

    dq = patch_external(mod, set_queue=True)
    patch_external(mod, set_types=True)

    # נגדיר LIST_OF_TYPES דמה עם שלושה ייעדים
    mod.LIST_OF_TYPES = ["pop_genre", "rap_genre", "classical_genre"]
    return mod, dq

def test_get_song_from_queue_empty_and_nonempty():
    mod, dq = make_module()
    S = mod.SendToClasiffier("song_info")

    assert S.get_song_from_queue() is None  # ריק

    t = DummyTypes(song_info=DummySongInfo())
    dq.lpush("song_info", t.to_json())
    got = S.get_song_from_queue()
    assert isinstance(got, DummyTypes)

def test_queues_routes_first_missing_type_then_all_filed():
    mod, dq = make_module()
    S = mod.SendToClasiffier("song_info")

    # מקרה 1: חסר pop_genre => מפזר לשם וחוזר  :contentReference[oaicite:20]{index=20}
    t1 = DummyTypes(song_info=DummySongInfo(), pop_genre=None, rap_genre=10, classical_genre=20)
    dq.lpush("song_info", t1.to_json())
    S.queues()
    assert "pop_genre" in dq.store and dq.store["pop_genre"]

    # מקרה 2: שלושתם קיימים => 'all_filed'  :contentReference[oaicite:21]{index=21}
    t2 = DummyTypes(song_info=DummySongInfo(), pop_genre=1, rap_genre=2, classical_genre=3)
    dq.lpush("song_info", t2.to_json())
    S.queues()
    assert "all_filed" in dq.store and dq.store["all_filed"]
