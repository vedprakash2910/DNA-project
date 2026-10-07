import logging
import sys

from config import LOG_LEVEL


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:  # already configured (e.g. under pytest / uvicorn reload)
        root.setLevel(LOG_LEVEL)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(LOG_LEVEL)
