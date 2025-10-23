import redis
from .logger_setup import logger_info_process
from classification_songs.configorations._dataclasses import CategoryFilter, FieldFilter

_WHISPER_MODEL = None
_WHISPER_NAME = None
_WHISPER_DEVICE = None

def get_whisper(model_name='medium', device='cpu'):
    global _WHISPER_MODEL, _WHISPER_NAME, _WHISPER_DEVICE
    if not _WHISPER_MODEL is None:
        logger_info_process.info(f'returning caches whisper model: {_WHISPER_MODEL}')
        return _WHISPER_MODEL
    import whisper
    logger_info_process.info(f"loading whisper model:'{model_name}' on device: '{device}'")
    _WHISPER_MODEL = whisper.load_model(model_name, device=device)
    _WHISPER_NAME = model_name
    _WHISPER_DEVICE = device
    return _WHISPER_MODEL

try:
    main_queue = redis.Redis(host='localhost', port=6379, db=0)
    main_queue.ping()
    logger_info_process.info(f'connected to redis for main queue')
except redis.ConnectionError:
    logger_info_process.error(f'failed to connect to redis for main queue')
    main_queue = None



AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg")
STEM_NAMES = ['vocals', 'bass', 'drums', 'other']

LIST_OF_TYPES = ['pop_genre', 'rap_genre', 'classical_genre', 'love_song']

MIN_POP_REGULAR_LENGTH = 165.0
MAX_POP_REGULAR_LENGTH = 225.0

POP_MOST_COMMON = [
    "baby", "love", "heart", "kiss", "forever", "together", "tonight", "dance", "party",
    "feel", "touch", "hold", "shine", "light", "fun", "beautiful", "happy", "magic",
    "smile", "sweet", "dream", "believe"
]

POP_COMMON = [
    "darling", "honey", "crazy", "fly", "sky", "angel", "amazing", "wonderful", "perfect",
    "free", "alive", "sing", "move", "groove", "everybody", "strong", "hope", "sweetheart"
]

POP_LESS_COMMON = [
    "rainbow", "fantasy", "paradise", "wonder", "glow", "vibe", "bright", "pretty"
]


RAP_MOST_COMMON = [
    "flow","bars","beat","rhythm","mic","verse","hook","chorus","rap","rhyme",
    "freestyle","spit","drop","track","studio","bass","808","kick","snare","hi-hat",
    "trap","boom-bap","crew","street","hustle","grind","real","fire","dope","ill",
    "flex","vibe","wave","drip","boss","king","queen","game","respect","legend"
]

RAP_COMMON = [
    "line","punchline","scheme","metaphor","wordplay","slang","flowing","sample",
    "loop","mix","master","producer","DJ","label","record","gig","stage","crowd",
    "shoutout","represent","city","block","hood","downtown","uptown","club","party",
    "ride","whip","night","money","cash","stack","paper","gold","ice","chain","bling",
    "crewlove","dayone","homie","bro","squad"
]

RAP_LESS_COMMON = [
    "miccheck","cipher","cypher","diss","beef","comeback","mixtape","EP","LP",
    "OG","GOAT","bars-heavy","doubletime","pocket","offbeat","onbeat","bridge",
    "outro","intro","adlib","tag","skit","remix","feature","verse2","chorus2",
    "autotune","punch-in","one-take","mastering","stems","acapella","instrumental",
    "backspin","scratch","turntable","breakbeat","boombox","streetwear","sneakers",
    "graffiti","cipher-circle"
]

CLASSICAL_MOST_COMMON = [
    "symphony","concerto","sonata","orchestra","string","quartet","piano",
    "violin","cello","viola","flute","oboe","clarinet","bassoon","horn","trumpet",
    "trombone","timpani","conductor","maestro","movement","allegro","andante",
    "adagio","presto","overture","aria","chorale","fugue","suite","opus","no.",
    "oratorio","harmonic","counterpoint","cadence","crescendo","diminuendo"
]

CLASSICAL_COMMON = [
    "harp","doublebass","piccolo","english horn","bass clarinet","contrabassoon",
    "percussion","tutti","solo","duet","trio","ensemble","chamber","tuning",
    "score","manuscript","edition","baroque","classical","romantic","modern",
    "themes","motif","variation","cadenza","development","recapitulation",
    "scherzo","minuet","waltz","gavotte","rondo","aria da capo","da capo",
    "rubato","legato","staccato","pizzicato","arpeggio","glissando"
]

CLASSICAL_LESS_COMMON = [
    "largo","moderato","vivace","grave","lento","meno mosso","piu mosso",
    "sostenuto","sfz","sforzato","forte","piano","fortissimo","pianissimo",
    "subito","fermata","attacca","da segno","dal segno","coda","codetta",
    "through-composed","through composed","binary form","ternary form",
    "ground bass","basso continuo","figured bass","twelve-tone","serial",
    "aleatoric","programmatic","absolute music","leitmotif","tessitura",
    "coloratura","cantabile","bel canto","lieder","lied","recitativo","recitative"
]

LOVE_MOST_COMMON = [
    "love", "heart", "baby", "darling", "sweetheart", "kiss", "miss",
    "need", "want", "hold", "together", "forever", "always", "yours",
    "mine", "feel", "hug", "touch", "romance", "belong", "desire", "dear"
]

LOVE_COMMON = [
    "alone", "lonely", "memory", "promise", "hurt", "pain", "tear", "cry",
    "sorry", "forgive", "back", "stay", "leave", "apart", "tonight",
    "morning", "tomorrow", "dream", "soul", "beautiful", "smile", "eye",
    "arm", "close", "near", "far"
]

LOVE_LESS_COMMON = [
    "heartbeat", "butterfly", "valentine", "someday", "destiny", "fate",
    "rain", "storm", "sunrise", "sunset", "candle", "letter", "poem",
    "melody", "serenade"
]

def make_genre_decider()->CategoryFilter:
    return CategoryFilter(
        filters=[
            FieldFilter(name='pop', field='pop_genre', weight=1.0),
            FieldFilter(name='rap', field='rap_genre', weight=1.0),
            FieldFilter(name='classical', field='classical_genre', weight=1.0)
        ],
        _unknown=45.0
    )


def make_song_type_decider()->CategoryFilter:
    return CategoryFilter(
        filters=[
            FieldFilter(name='love_song', field='love_song', weight=1.0),
        ],
        _unknown=50.0
    )