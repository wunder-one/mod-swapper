from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from config.user_settings import UserSettings
from functions.profile_ops import _list_files_to_remove

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: _list_files_to_remove — log swap-path files not in the manifest (excluding protected paths).",
    )
    parser.add_argument(
        "profile_name",
        type=str,
        help="Name of the profile folder under profiles snapshot dir",
    )
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    files_to_remove = _list_files_to_remove(
        args.profile_name,
        user_settings.swap_paths,
        excluded_files=excluded_files,
        excluded_dirs=excluded_dirs,
    )
    logger.info("Files to remove: %d", len(files_to_remove))
    for file in files_to_remove:
        logger.info("  - %s", file)


if __name__ == "__main__":
    configure_logging()
    scratch()
