from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from functions.file_hash_cache import FileHashCache
from functions.hashed_store_ops import _list_files_to_restore

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: save live mods into a profile snapshot.",
    )
    parser.add_argument(
        "profile_name", type=str, help="Name of the profile folder to write"
    )
    args = parser.parse_args()

    file_hash_cache = FileHashCache.load_cache()
    files_to_restore = _list_files_to_restore(args.profile_name, file_hash_cache)
    logger.info("Files to restore:")
    for file in files_to_restore:
        logger.info("  - %s", file)


if __name__ == "__main__":
    configure_logging()
    scratch()
