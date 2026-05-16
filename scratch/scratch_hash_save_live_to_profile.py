from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from config.user_settings import UserSettings
from functions.file_hash_cache import FileHashCache
from functions.hashed_store_ops import save_live_to_profile

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: save_live_to_profile — snapshot live swap paths into a profile manifest.",
    )
    parser.add_argument(
        "profile_name",
        type=str,
        help="Name of the profile folder under profiles snapshot dir",
    )
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()
    file_hash_cache = FileHashCache.load_cache()
    save_live_to_profile(args.profile_name, file_hash_cache, user_settings)
    file_hash_cache.save_cache()


if __name__ == "__main__":
    configure_logging()
    scratch()
