import logging
from pathlib import Path

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / 'song_info.log'

LOG_FILE2 = LOG_DIR / 'classified_process.log'


formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)

running_handler = logging.StreamHandler()
running_handler.setFormatter(formatter)

logger_info_process = logging.getLogger('song_logger')
logger_info_process.setLevel(logging.DEBUG)
logger_info_process.addHandler(file_handler)
logger_info_process.addHandler(running_handler)

file_handler2 = logging.FileHandler(LOG_FILE2)
file_handler2.setFormatter(formatter)

running_handler2 = logging.StreamHandler()
running_handler2.setFormatter(formatter)

logger_classified_process = logging.getLogger('classification_logger')
logger_classified_process.setLevel(logging.DEBUG)
logger_classified_process.addHandler(file_handler2)
logger_classified_process.addHandler(running_handler2)

