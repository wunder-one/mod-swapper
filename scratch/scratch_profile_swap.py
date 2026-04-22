from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from functions.file_actions import swap_profiles

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: swap profiles (loads named profile to live mods).",
    )
    parser.add_argument(
        "profile_to_load",
        type=str,
        help="Profile folder name to activate",
    )
    args = parser.parse_args()

    prof_state = ProfileState.load_config()
    user_settings = UserSettings.load_settings()
    swap_profiles(args.profile_to_load, prof_state, user_settings)
    logger.info(
        "Scratch swap finished; active profile is %r.", prof_state.active_profile
    )


if __name__ == "__main__":
    configure_logging()
    scratch()
