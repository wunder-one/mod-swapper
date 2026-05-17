import logging
import sys
from pathlib import Path

import ui.app
import ui.migration_progress
from config.logging_setup import configure_logging
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from functions.blob_store import BlobStore
from functions.migrate import migrate_file_store
from config.migration_state import MigrationState
from customtkinter import set_default_color_theme

logger = logging.getLogger(__name__)


def _meipass_path(relative_path: str) -> str:
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass is not None:
        return str(Path(meipass) / relative_path)
    return relative_path


def _run_migration(app, blob_store, migration_state):
    progress = ui.migration_progress.MigrationProgress(app)
    try:
        migrate_file_store(blob_store, progress)
        migration_state.update_state(True)
    except Exception as e:
        logger.error("Migration failed: %s", e)
    finally:
        progress.destroy()
    app.deiconify()


def main():
    configure_logging()

    prof_state = ProfileState.load_config()
    logger.info("Active profile from config: %s", prof_state.active_profile)
    logger.info("Available profiles: %s", list(prof_state.profiles.keys()))

    user_settings = UserSettings.load_settings()
    logger.info("Game folder: %s", user_settings.game_folder)

    blob_store = BlobStore.load_cache()
    migration_state = MigrationState.load_state()

    set_default_color_theme(_meipass_path("ui/theme.json"))
    # set_default_color_theme("green")
    app = ui.app.App(prof_state, user_settings, blob_store)
    app.iconbitmap(_meipass_path("assets/icons/magic_icon.ico"))

    if not migration_state.migration_state:
        app.withdraw()
        app.after(100, _run_migration, app, blob_store, migration_state)

    app.mainloop()

    logger.info("Saving configuration...")
    prof_state.save_config()
    user_settings.save_settings()
    blob_store.save_cache()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
