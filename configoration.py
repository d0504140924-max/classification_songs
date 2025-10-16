import redis
from logger_setup import logger

_WHISPER_MODEL = None
_WHISPER_NAME = None
_WHISPER_DEVICE = None

def get_whisper(model_name='medium', device='cpu'):
    global _WHISPER_MODEL, _WHISPER_NAME, _WHISPER_DEVICE
    if not _WHISPER_MODEL is None:
        logger.info(f'returning caches whisper model: {_WHISPER_MODEL}')
        return _WHISPER_MODEL
    import whisper
    logger.info(f"loading whisper model:'{model_name}' on device: '{device}'")
    _WHISPER_MODEL = whisper.load_model(model_name, device=device)
    _WHISPER_NAME = model_name
    _WHISPER_DEVICE = device
    return _WHISPER_MODEL

try:
    info_queue = redis.Redis(host='localhost', port=6379, db=0)
    info_queue.ping()
    logger.info(f'connected to redis for info queue')
except redis.ConnectionError:
    logger.info(f'failed to connect to redis for info queue')

try:
    types_queue = redis.Redis(host='localhost', port=6379, db=1)
    types_queue.ping()
    logger.info(f'connected to redis for types queue')
except redis.ConnectionError:
    logger.info(f'failed to connect to redis for types queue')



AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg")
STEM_NAMES = ['vocals', 'bass', 'drums', 'other']

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


