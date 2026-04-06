import ui.app
from profile_state import ProfileState
from user_settings import UserSettings

def main():
    prof_state = ProfileState.load_config()
    user_settings = UserSettings.load_settings()
    print(f"Active profile from config: {prof_state.active_profile}")
    print(f"Available profiles: {list(prof_state.profiles.keys())}")
    # print(f"Swap Paths: {user_settings.swap_paths}")
    # print(f"Protected Paths: {user_settings.protected_paths}")
    # print(f"Critical Game Paths: {user_settings.critical_game_paths}")
    print(f"Game Folder: {user_settings.game_folder}")

    app = ui.app.App(prof_state, user_settings)
    app.mainloop()

    print("Saving configuration...")
    prof_state.save_config()
    user_settings.save_settings()
    print("Shutdown complete.")


if __name__ == "__main__":
    main()
