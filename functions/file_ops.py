import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_unique_path(base_path: Path) -> Path:
    # Returns a Path that doesn't exist by appending (n) if necessary.
    if not base_path.exists():
        return base_path
    counter = 1
    # Keep trying new numbers until we find a path that doesn't exist
    while True:
        new_path = base_path.with_name(f"{base_path.name} ({counter})")
        if not new_path.exists():
            return new_path
        counter += 1
