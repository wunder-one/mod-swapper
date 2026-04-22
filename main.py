import logging
import sys
from pathlib import Path

import ui.app
from config.logging_setup import configure_logging
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from customtkinter import set_default_color_theme

logger = logging.getLogger(__name__)


def _meipass_path(relative_path: str) -> str:
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass is not None:
        return str(Path(meipass) / relative_path)
    return relative_path


def main():
    configure_logging()
    prof_state = ProfileState.load_config()
    user_settings = UserSettings.load_settings()
    logger.info("Active profile from config: %s", prof_state.active_profile)
    logger.info("Available profiles: %s", list(prof_state.profiles.keys()))
    logger.info("Game folder: %s", user_settings.game_folder)

    set_default_color_theme(_meipass_path("ui/theme.json"))
    # set_default_color_theme("green")
    app = ui.app.App(prof_state, user_settings)
    app.iconbitmap(_meipass_path("assets/icons/magic_icon.ico"))
    app.mainloop()

    logger.info("Saving configuration...")
    prof_state.save_config()
    user_settings.save_settings()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
