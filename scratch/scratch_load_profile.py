from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from config.user_settings import UserSettings
from functions.file_actions import load_profile_to_live

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: load a profile snapshot into live mod paths.",
    )
    parser.add_argument("profile_name", type=str, help="Profile folder name to load")
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()
    load_profile_to_live(args.profile_name, user_settings)
    logger.info("Loaded profile %r to live paths:", args.profile_name)
    for p in user_settings.swap_paths:
        logger.info("  - %s", p)


if __name__ == "__main__":
    configure_logging()
    scratch()
