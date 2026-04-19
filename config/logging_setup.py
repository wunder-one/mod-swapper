import logging
import os


def configure_logging() -> None:
    """Configure root logging once (safe to call from main or test entrypoints)."""
    level_name = os.environ.get("MOD_SWAPPER_LOG", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(levelname)s %(name)s: %(message)s",
        )
    else:
        root.setLevel(level)
