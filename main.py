# don't forget to remove json after setting up config class
import json

import ui.app
from constants import PROFILES_SNAPSHOT_DIR, USER_CONFIG_DIR, USER_CONFIG_FILE

def main():
    PROFILES_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    profiles = {}
    for dir in PROFILES_SNAPSHOT_DIR.iterdir():
        if dir.is_dir():
            print(f"Found profile: {dir.name}")
            profiles[dir.name] = dir

    # ----- TESTING ONLY: move this to a class -----
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_CONFIG_FILE.touch(exist_ok=True)
    # with open(USER_CONFIG_FILE, "w") as f:
    #     json.dump({"current_profile": "Profile B"}, f, indent=4)
    with open(USER_CONFIG_FILE, "r") as f:
        app_config = json.load(f)
    print(f"Current profile: {app_config.get('current_profile', None)}")

    app = ui.app.App()
    app.mainloop()

# def get_profiles():


if __name__ == "__main__":
    main()
