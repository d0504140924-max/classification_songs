import logging
from pathlib import Path

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / 'song_info.log'

LOG_FILE2 = LOG_DIR / 'song_info.log'


formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)

running_handler = logging.StreamHandler()
running_handler.setFormatter(formatter)

logger = logging.getLogger('song_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(running_handler)

file_handler2 = logging.FileHandler(LOG_FILE2)
file_handler2.setFormatter(formatter)

running_handler2 = logging.StreamHandler()
running_handler2.setFormatter(formatter)

logger2 = logging.getLogger('classification_logger')
logger2.setLevel(logging.DEBUG)
logger2.addHandler(file_handler2)
logger2.addHandler(running_handler2)

