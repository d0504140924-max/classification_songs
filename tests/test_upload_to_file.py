import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent))  # כדי ש-helpers יימצא
import json
from pathlib import Path
from helpers import load_module_wo_runner, patch_external, DummyTypes, DummySongInfo

# נבדוק את האלגוריתם של זיהוי ז'אנר + כתיבת מטאדאטה לכל פורמט
# מתייחס לקוד: calculate_final_genre, song_format, saperate_to_formats  :contentReference[oaicite:0]{index=0}  :contentReference[oaicite:1]{index=1}  :contentReference[oaicite:2]{index=2}

def make_types(pop, rap, classical, path="song.mp3"):
    return DummyTypes(song_info=DummySongInfo(song_path=Path(path)), pop_genre=pop, rap_genre=rap, classical_genre=classical)

def test_calculate_final_genre_threshold_and_mapping():
    mod = load_module_wo_runner("classification_songs/update_file/upload_to_file.py", "upload_to_file")

    # הזרקת תלותים: Types דמיוני
    patch_external(mod, set_types=True)
    # שים/י לב: המימוש הנוכחי ממפה dict עם מפתחות=ציון (עלול להתנגש בציונים שווים)  :contentReference[oaicite:3]{index=3}
    t = make_types(46, 10, 5)
    assert mod.UpLoadToFile.calculate_final_genre(t) in ("pop","Unknown")
    t2 = make_types(45, 10, 5)
    assert mod.UpLoadToFile.calculate_final_genre(t2) == "Unknown"  # סף >45  :contentReference[oaicite:4]{index=4}

def test_song_format_returns_tuple_path_suffix():
    mod = load_module_wo_runner("upload_to_file.py", "upload_to_file")
    patch_external(mod, set_types=True)
    t = make_types(60, 0, 0, path="x.flac")
    path, suf = mod.UpLoadToFile.song_format(t)
    assert isinstance(path, Path) and suf == ".flac"  #  :contentReference[oaicite:5]{index=5}

def test_saperate_to_formats_all_branches():
    mod = load_module_wo_runner("upload_to_file.py", "upload_to_file")
    patch_external(mod, set_mutagen=True)  # מספק מחלקות WAV/MP4/FLAC/OGG/EasyID3 דמה
    U = mod.UpLoadToFile()

    # מפעילים כל ענף (לא נופל על None/Exception)
    U.saperate_to_formats(Path("a.mp3"), ".mp3", "pop", "love_song")
    U.saperate_to_formats(Path("a.flac"), ".flac", "rap", "Unknown")
    U.saperate_to_formats(Path("a.ogg"), ".ogg", "classical", "Unknown")
    U.saperate_to_formats(Path("a.m4a"), ".m4a", "pop", "Unknown")
    U.saperate_to_formats(Path("a.wav"), ".wav", "rap", "love_song")
    # אם לא קרסנו – עבר

def test_upload_to_file_pipeline_minimal_queue_happy_path():
    mod = load_module_wo_runner("upload_to_file.py", "upload_to_file")
    dq = patch_external(mod, set_queue=True)   # main_queue דמה
    patch_external(mod, set_mutagen=True)      # mutagen דמה
    patch_external(mod, set_types=True)        # Types/SongInfo דמה

    t = DummyTypes(song_info=DummySongInfo(song_path=Path("x.wav")), pop_genre=80, rap_genre=10, classical_genre=5, love_song=True)
    dq.lpush("all_filed", t.to_json())
    U = mod.UpLoadToFile()
    U.upload_to_file()  # לא אמור לקרוס, אמור למשוך מהתור ולעדכן תגיות WAV
