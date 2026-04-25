import os
from pathlib import Path

USER_DIR = Path.home()
LOCAL_APPDATA = Path(os.getenv("LOCALAPPDATA", USER_DIR / "AppData" / "Local"))
PROFILES_SNAPSHOT_DIR = LOCAL_APPDATA / "BG3ProfileSwapper" / "profiles"
FILE_STORE_DIR = LOCAL_APPDATA / "BG3ProfileSwapper" / "file_store"
ROAMING_APPDATA = Path(os.getenv("APPDATA", USER_DIR / "AppData" / "Roaming"))
USER_CONFIG_DIR = ROAMING_APPDATA / "BG3ProfileSwapper"
PROFILE_STATE_FILE = USER_CONFIG_DIR / "profile_state.json"
USER_SETTINGS_FILE = USER_CONFIG_DIR / "user_settings.json"
APP_WINDOW_GEOMETRY_FILE = USER_CONFIG_DIR / "app_window_geometry.json"

BG3_STEAM_ID = "1086940"

CRITICAL_GAME_FOLDER_PATHS = [
    Path("Data/Generated/Public/Engine"),
    Path("Data/Generated/Public/Game"),
    Path("Data/bin/db"),
]

PROTECTED_PATTERNS = [
    "*.exe",
    "*.dmp",
    "*.log",
]
