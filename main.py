# don't forget to remove json after setting up config class
import json

import ui.app
from constants import PROFILES_SNAPSHOT_DIR, USER_CONFIG_DIR, USER_CONFIG_FILE

active_profile = None

def main():


    # ----- TESTING ONLY: move this to a class -----
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_CONFIG_FILE.touch(exist_ok=True)
    # with open(USER_CONFIG_FILE, "w") as f:
    #     json.dump({"active_profile": "Profile B"}, f, indent=4)
    with open(USER_CONFIG_FILE, "r") as f:
        app_config = json.load(f)
    global active_profile
    active_profile = app_config.get("active_profile", None)
    print(f"Current profile: {active_profile}")

    app = ui.app.App(active_profile=active_profile, profiles=list(profiles.keys()))
    app.mainloop()


if __name__ == "__main__":
    main()
