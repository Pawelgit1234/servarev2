import logging
import sys

from common.settings import LOG_DATEFMT, LOG_FORMAT


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATEFMT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
