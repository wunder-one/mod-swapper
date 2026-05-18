from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import logging

from config.logging_setup import configure_logging
from functions.blob_store import BlobStore
from functions.profile_ops import _list_files_to_restore

logger = logging.getLogger(__name__)


def scratch():
    parser = argparse.ArgumentParser(
        description="Scratch: _list_files_to_restore — log (live_path, storage_path) pairs that load_profile_to_live would restore.",
    )
    parser.add_argument(
        "profile_name",
        type=str,
        help="Name of the profile folder under profiles snapshot dir",
    )
    args = parser.parse_args()

    blob_store = BlobStore()
    files_to_restore = _list_files_to_restore(args.profile_name, blob_store)
    logger.info("Files to restore:")
    for file in files_to_restore:
        logger.info("  - %s", file)


if __name__ == "__main__":
    configure_logging()
    scratch()
