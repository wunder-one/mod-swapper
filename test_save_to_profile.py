import argparse
import logging

from config.logging_setup import configure_logging
from config.user_settings import UserSettings
from functions.file_actions import save_live_to_profile

logger = logging.getLogger(__name__)


def test():
    parser = argparse.ArgumentParser(description="Test saving live mods into a profile snapshot.")
    parser.add_argument("profile_name", type=str, help="Name of the profile folder to write")
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()
    save_live_to_profile(args.profile_name, user_settings)
    logger.info("Saved live mods from:")
    for p in user_settings.swap_paths:
        logger.info("  - %s", p)
    logger.info("  --> profile %r", args.profile_name)


if __name__ == "__main__":
    configure_logging()
    test()
