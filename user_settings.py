import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from constants import USER_CONFIG_DIR, USER_SETTINGS_FILE, LOCAL_APPDATA, USER_DIR


'''
# Future factory fuction for defaults file paths
def get_bg3_defaults() -> dict[str, Path]:
    """Logic to detect the game and return the recommended folders."""
    # Using expanduser() handles 'C:/Users/Username' automatically
    appdata = Path("~/AppData/Local/Larian Studios/Baldur's Gate 3").expanduser()
    
    # Common install locations
    steam_data = Path("C:/Program Files (x86)/Steam/steamapps/common/Baldurs Gate 3/Data")
    gog_data = Path("C:/GOG Games/Baldurs Gate 3/Data")

    # Real Paths:
    bg3_mods_folder: Path = LOCAL_APPDATA / "Larian Studios" / "Baldur's Gate 3" / "Mods"
    bg3_mods_lsx: Path = LOCAL_APPDATA / "Larian Studios" / "Baldur's Gate 3" / "PlayerProfiles" / "Public" / "modsettings.lsx"


    # Detect which one exists
    game_data = steam_data if steam_data.exists() else gog_data
    
    return {
        "Mods": appdata / "Mods",
        "LocalMods": appdata / "LocalMods",
        "GameData": game_data
    }
'''

def get_test_folders() -> dict[str, Path]:
    return {
        "Test Mod Folder": USER_DIR / "Desktop" / "Mod Swapper Test Folder" / "Test Mod Folder",
        "Test Generated Folder": USER_DIR / "Desktop" / "Mod Swapper Test Folder" / "Test Generated Folder",
        "modsettings.lsx": USER_DIR / "Desktop" / "Mod Swapper Test Folder" / "modsettings.lsx",
    }

@dataclass
class UserSettings:
    swap_paths: dict[str, Path] = field(default_factory=get_test_folders)

    def reset_to_defaults(self):
        # Wipes current settings and re-detects the game paths.
        self.swap_paths = get_test_folders()
        # You might want to auto-save after a reset
        self.save_settings()

    def save_settings(self):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        json_data = json.dumps(data, indent=4, default=str)
        USER_SETTINGS_FILE.write_text(json_data, encoding="utf-8")

    @classmethod
    def load_settings(cls) -> "UserSettings":
        if not USER_SETTINGS_FILE.exists():
            return cls()
        try:
            with USER_SETTINGS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Avoid breaking if config file contains unknown fields
            allowed_keys = {f.name for f in cls.__dataclass_fields__.values() if f.init}
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}

            # Convert the dictionary of strings back into a dictionary of Paths
            if "swap_paths" in filtered_data:
                filtered_data["swap_paths"] = {
                    name: Path(p) for name, p in filtered_data["swap_paths"].items()
                }

            return cls(**filtered_data)
        
        except (json.JSONDecodeError, TypeError) as e:
            # If the file is garbled or missing required fields, 
            # fall back to a fresh default config.
            print(f"Warning: Failed to load config, using defaults. Error: {e}")
            return cls()