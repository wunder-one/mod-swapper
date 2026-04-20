from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import logging

from config.logging_setup import configure_logging
from functions.discover_steam import find_steam_game_install_path

logger = logging.getLogger(__name__)


def scratch():
    result = find_steam_game_install_path()
    if result:
        logger.info("Found game folder: %s", result)
    else:
        logger.info("Steam game path discovery returned None.")


if __name__ == "__main__":
    configure_logging()
    scratch()
