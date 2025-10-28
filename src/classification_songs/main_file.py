# main_redis.py
import os
import json
import threading
import time
from pathlib import Path
from typing import Optional, Dict

import redis

# ==== קונפיג תורים (שמור עקבי בכל הפרויקט) ====
QUEUE_SONG_INFO       = "song_info"          # SongInfo JSON
QUEUE_GENRE_POP       = "pop_genre"          # Types JSON → worker pop
QUEUE_GENRE_RAP       = "rap_genre"          # Types JSON → worker rap
QUEUE_GENRE_CLASSICAL = "classical_genre"    # Types JSON → worker classical
QUEUE_MERGED_RESULTS  = "all_filed"          # Types JSON עם שדות מעודכנים

# ==== ייבוא מהפרויקט שלך ====
from classification_songs.configorations.configoration import AUDIO_EXTENSIONS
from classification_songs.configorations._dataclasses import SongInfo, Types
from classification_songs.information.get_song_info import GetSongInfo
from classification_songs.classifications.classificatio_for_genre_classical import ClassificationForGenreClassical
from classification_songs.classifications.classification_for_genre_pop import ClassificationForGenrePop
from classification_songs.classifications.classification_for_genre_rap import ClassificationForGenreRap

# Deciders + Writers
from classification_songs.configorations.configoration import make_genre_decider, make_song_type_decider
from classification_songs.update_file.formats import WriteRegister, Mp3Writer, FLACWriter, OggWriter, Mp4LikeWriter, WavWriter

# לוגרים
from classification_songs.configorations.logger_setup import logger as log


def r() -> redis.Redis:
    # חיבור יחיד — אפשר להתאים host/port/db
    return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# ---------- Producer: מפיק SongInfo ודוחף Types לשלושת התורים ----------
def produce_song_info(audio_path: Path) -> None:
    gi = GetSongInfo(queue_name=QUEUE_SONG_INFO)  # המתודה שלו גם דוחפת ל-QUEUE_SONG_INFO אוטומטית
    si: SongInfo = gi.get_info(str(audio_path))
    log.info(f"Produced SongInfo for {audio_path.name}")

    # עוטפים באובייקט Types (כלי אחד מסונקרן לכל ה-workers)
    types = Types(
        song_info=si,
        love_song=False,             # אם הסוג מספרי אצלך, עדכן לטיפוס מתאים
        pop_genre=0.0,
        rap_genre=0.0,
        classical_genre=0.0,
    )
    # נצרף את ה-SongInfo פנימה אם הדאטה-קלאס שלך תומך בזה (יש אצלך שדה כזה בפרויקטים קודמים)
    types.song_info = si  # אם אין שדה כזה אצלך, הסר את השורה הזו והתאם את ה-Types

    payload = types.to_json()
    # דוחפים עותק של אותו Types לכל תור ז'אנר
    r().lpush(QUEUE_GENRE_POP, payload)
    r().lpush(QUEUE_GENRE_RAP, payload)
    r().lpush(QUEUE_GENRE_CLASSICAL, payload)
    log.info("Seeded Types to pop/rap/classical queues.")


# ---------- Worker בסיסי: תבנית ל-pop/rap/classical ----------
def genre_worker_loop(label: str, queue_in: str, setter, calculator) -> None:
    """
    label: "pop"/"rap"/"classical"
    queue_in: שם התור ממנו לוקחים Types לעיבוד
    setter: פונקציה שקובעת את השדה המתאים בתוך Types (לדוגמה: lambda t,v: setattr(t,'classical_genre',v))
    calculator: מתודה שמקבלת SongInfo ומחזירה ציון סופי (מתוך המחלקה שבנית)
    """
    log.info(f"[{label}] worker started, listening on {queue_in}")
    while True:
        item = r().brpop(queue_in, timeout=5)  # חוסם עד 5 שניות
        if item is None:
            continue
        _, json_str = item
        try:
            t: Types = Types.from_json(json_str)
            si: SongInfo = t.song_info if hasattr(t, "song_info") else SongInfo.from_json(r().lindex(QUEUE_SONG_INFO, 0))
            score = float(calculator(si))
            setter(t, score)
            r().lpush(QUEUE_MERGED_RESULTS, t.to_json())
            log.info(f"[{label}] score={score:.2f} -> pushed to {QUEUE_MERGED_RESULTS}")
        except Exception as e:
            log.error(f"[{label}] worker error: {e}")


# ---------- Merger+Uploader: מאחד תוצאות וכותב תגיות ----------
def merger_and_uploader(audio_path: Path) -> None:
    """
    אוסף שלושה עדכונים (pop/rap/classical) עבור אותו song_name, מאחד, מחליט ז'אנר/סוג, כותב תגיות.
    זיהוי לפי song_name. אפשר לשפר עם מזהה ייחודי אם תרצה.
    """
    pending: Dict[str, Dict[str, float]] = {}
    writers = WriteRegister()
    writers.register(Mp3Writer()); writers.register(FLACWriter()); writers.register(OggWriter())
    writers.register(Mp4LikeWriter()); writers.register(WavWriter())

    genre_decider = make_genre_decider()
    type_decider  = make_song_type_decider()

    log.info("[merge] waiting for results...")
    target_song = str(audio_path)

    while True:
        item = r().brpop(QUEUE_MERGED_RESULTS, timeout=5)
        if item is None:
            continue
        _, json_str = item
        try:
            t: Types = Types.from_json(json_str)
            if t.song_name != target_song:
                # אם יש תורים מקבילים לשירים אחרים—אפשר לשמור ב-pending לפי song_name
                continue

            d = pending.setdefault(t.song_name, {})
            # נשמור מה שקיבלנו
            if t.pop_genre is not None:
                d["pop"] = float(t.pop_genre)
            if t.rap_genre is not None:
                d["rap"] = float(t.rap_genre)
            if t.classical_genre is not None:
                d["classical"] = float(t.classical_genre)

            # אם קיבלנו את שלושתם—מתקדמים
            if all(k in d for k in ("pop", "rap", "classical")):
                # מחליטים קטגוריות
                class _T:
                    def __init__(self, pop, rap, classical, love):
                        self.pop_genre = pop
                        self.rap_genre = rap
                        self.classical_genre = classical
                        self.love_song = love  # אם זה בוליאני/מספרי—התאם

                # love: כרגע נשתמש בהיגיון מינימלי—אפשר להחליף למסווג האמיתי שלך
                love_score = 100.0 if "love" in (t.song_info.song_words or []) else 0.0

                tt = _T(d["pop"], d["rap"], d["classical"], love_score)
                genre_label, _ = genre_decider.decide(tt)
                type_label,  _ = type_decider.decide(tt)

                # כתיבת תגיות
                writer = writers.get(audio_path)
                if writer is None:
                    log.warning(f'No writer for suffix {audio_path.suffix}')
                else:
                    writer.write(audio_path, genre=genre_label, song_type=type_label)
                    log.info(f'Wrote tags to {audio_path.name}: genre="{genre_label}", type="{type_label}"')
                break
        except Exception as e:
            log.error(f"[merge] error: {e}")


# ---------- main ----------
def main():
    import argparse
    ap = argparse.ArgumentParser(description="Run full pipeline via Redis queues")
    ap.add_argument("audio", help="Path to audio file (.mp3/.flac/.wav/.m4a/.aac/.ogg)")
    args = ap.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.is_file():
        log.error(f"File not found: {audio_path}")
        return
    if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
        log.error(f"Unsupported suffix {audio_path.suffix}")
        return

    # Producer: יוצרים SongInfo + דוחפים Types לתורים
    produce_song_info(audio_path)

    # Workers: classical עובד; פופ/ראפ תפעיל אם קיימים אצלך (בטל הערות למטה)
    classical = ClassificationForGenreClassical(queue_name=QUEUE_MERGED_RESULTS)
    t1 = threading.Thread(
        target=genre_worker_loop,
        args=("classical", QUEUE_GENRE_CLASSICAL,
              lambda t, v: setattr(t, "classical_genre", v),
              classical.calculate_final_score),
        daemon=True
    )

    # אם יש לך מחלקות Pop/Rap, בטל סימון:
    pop = ClassificationForGenrePop(queue_name=QUEUE_MERGED_RESULTS)
    rap = ClassificationForGenreRap(queue_name=QUEUE_MERGED_RESULTS)
    t2 = threading.Thread(target=genre_worker_loop,
             args=("pop", QUEUE_GENRE_POP, lambda t,v: setattr(t, "pop_genre", v), pop.calculate_final_score),
             daemon=True)
    t3 = threading.Thread(target=genre_worker_loop,
            args=("rap", QUEUE_GENRE_RAP, lambda t,v: setattr(t, "rap_genre", v), rap.calculate_final_score),
            daemon=True)

    t1.start()
    t2.start(); t3.start()


    merger_and_uploader(audio_path)


if __name__ == "__main__":
    main()


