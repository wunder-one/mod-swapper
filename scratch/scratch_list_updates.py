from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import logging

from config.logging_setup import configure_logging
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from storage.blob_store import BlobStore
from functions.update_mods import list_updates

logger = logging.getLogger(__name__)


def scratch():
    profile_state = ProfileState.load_config()
    if not profile_state.active_profile:
        raise SystemExit("No active profile in profile state config.")

    user_settings = UserSettings.load_settings()
    blob_store = BlobStore.load_cache()
    updates = list_updates(profile_state, blob_store, user_settings)
    blob_store.save_cache()

    if not updates:
        logger.info("No updates found for profile %r.", profile_state.active_profile)
        return

    logger.info(
        "Found %d update(s) for profile %r:",
        len(updates),
        profile_state.active_profile,
    )
    for update in updates:
        logger.info(
            "  - %s (%s): %s -> %s",
            update["mod_name"],
            update["mod_author"],
            update["prev_version"],
            update["new_version"],
        )
        logger.info("      target: %s", update["target_path"])
        logger.info("      blob:   %s", update["update_path"])


if __name__ == "__main__":
    configure_logging()
    scratch()
