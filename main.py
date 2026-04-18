import ui.app
from profile_state import ProfileState
from user_settings import UserSettings
from customtkinter import set_default_color_theme
from watchpoints import watch

def main():
    prof_state = ProfileState.load_config()
    watch(prof_state)
    user_settings = UserSettings.load_settings()
    watch(user_settings)
    print(f"Active profile from config: {prof_state.active_profile}")
    print(f"Available profiles: {list(prof_state.profiles.keys())}")
    print(f"Game Folder: {user_settings.game_folder}")

    set_default_color_theme("ui/theme.json")
    # set_default_color_theme("green")
    app = ui.app.App(prof_state, user_settings)
    app.mainloop()

    print("Saving configuration...")
    prof_state.save_config()
    user_settings.save_settings()
    print("Shutdown complete.")


if __name__ == "__main__":
    main()
