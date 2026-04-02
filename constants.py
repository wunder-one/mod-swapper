import os
from pathlib import Path

USER_DIR = Path.home()
LOCAL_APPDATA = Path(os.getenv("LOCALAPPDATA", USER_DIR / "AppData" / "Local"))
PROFILES_SNAPSHOT_DIR = LOCAL_APPDATA / "BG3ProfileSwapper" / "profiles"
ROAMING_APPDATA = Path(os.getenv("APPDATA", USER_DIR / "AppData" / "Roaming"))
USER_CONFIG_DIR = ROAMING_APPDATA / "BG3ProfileSwapper"
PROFILE_STATE_FILE = USER_CONFIG_DIR / "profile_state.json"
USER_SETTINGS_FILE = USER_CONFIG_DIR / "user_settings.json"

# For Testing. Need to remove later.
TEST_LIVE_MODS_DIR = USER_DIR / "Desktop" / "live-mods-test"