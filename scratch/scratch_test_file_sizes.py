from collections import defaultdict
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import logging

from config.logging_setup import configure_logging
from constants import FILE_STORE_DIR

logger = logging.getLogger(__name__)

_SKIP_NAMES = {"file_store_cache.json"}


def find_duplicate_file_sizes() -> dict[int, list[Path]]:
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in FILE_STORE_DIR.rglob("*"):
        if (
            not path.is_file()
            or path.name in _SKIP_NAMES
            or path.name.startswith("tmp.")
        ):
            continue
        by_size[path.stat().st_size].append(path)
    return {size: paths for size, paths in by_size.items() if len(paths) > 1}


if __name__ == "__main__":
    configure_logging()
    duplicates = find_duplicate_file_sizes()
    if not duplicates:
        logger.info("No files with matching sizes in %s", FILE_STORE_DIR)
    else:
        logger.info("Found %d shared size(s) in %s:", len(duplicates), FILE_STORE_DIR)
        for size, paths in sorted(duplicates.items()):
            logger.info("  %d bytes (%d files):", size, len(paths))
            for path in sorted(paths):
                logger.info("    %s", path.relative_to(FILE_STORE_DIR))
