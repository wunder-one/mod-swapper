import logging

import ui.app
from config.logging_setup import configure_logging
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from customtkinter import set_default_color_theme

logger = logging.getLogger(__name__)


def main():
    configure_logging()
    prof_state = ProfileState.load_config()
    user_settings = UserSettings.load_settings()
    logger.info("Active profile from config: %s", prof_state.active_profile)
    logger.info("Available profiles: %s", list(prof_state.profiles.keys()))
    logger.info("Game folder: %s", user_settings.game_folder)

    set_default_color_theme("ui/theme.json")
    # set_default_color_theme("green")
    app = ui.app.App(prof_state, user_settings)
    app.mainloop()

    logger.info("Saving configuration...")
    prof_state.save_config()
    user_settings.save_settings()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
