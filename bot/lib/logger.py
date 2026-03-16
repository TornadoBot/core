from logging import Logger, getLogger, DEBUG, Formatter, StreamHandler, INFO
from logging.handlers import RotatingFileHandler
from pathlib import Path
from sys import stdout

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> Logger:
    logger = getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(DEBUG)

    formatter = Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = StreamHandler(stdout)
    console_handler.setLevel(INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_DIR / "tornadobot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
