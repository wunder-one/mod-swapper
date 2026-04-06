import os
from pathlib import Path

USER_DIR = Path.home()
LOCAL_APPDATA = Path(os.getenv("LOCALAPPDATA", USER_DIR / "AppData" / "Local"))
PROFILES_SNAPSHOT_DIR = LOCAL_APPDATA / "BG3ProfileSwapper" / "profiles"
ROAMING_APPDATA = Path(os.getenv("APPDATA", USER_DIR / "AppData" / "Roaming"))
USER_CONFIG_DIR = ROAMING_APPDATA / "BG3ProfileSwapper"
PROFILE_STATE_FILE = USER_CONFIG_DIR / "profile_state.json"
USER_SETTINGS_FILE = USER_CONFIG_DIR / "user_settings.json"
# TODO: update to real steam default and real GOG default
BG3_STEAM_ID = "1086940"
DEFAULT_STEAM_GAME_FOLDER = Path(r"C:\Users\wes\Desktop\Mod Swapper Test Folder\Baldurs Gate 3")
DEFAULT_GOG_GAME_FOLDER = Path("")

# TODO: map to real files. 
CRITICAL_GAME_FOLDER_PATHS = [
    Path("Data/Generated/Public/Engine"),
    Path("Data/Generated/Public/Game"),
    Path("Data/bin/db")
]

PROTECTED_PATTERNS = [
    "*.exe",
    "*.dmp",
    "*.log",
]