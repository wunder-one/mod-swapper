import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from constants import USER_CONFIG_DIR, USER_SETTINGS_FILE, LOCAL_APPDATA, USER_DIR, CRITICAL_GAME_FOLDER_PATHS


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
#     "Data" / "Mods" / "Shared",
#     "Data" / "Mods" / "SharedDev",

def get_game_folder():
    # TODO: Logic for getting the game folder
    # TODO: fetch real game folder
    return Path(r"C:\Users\wes\Desktop\Mod Swapper Test Folder\Baldurs Gate 3")

def get_protected_paths() -> list[Path]:
    game_folder = get_game_folder()
    return [
        game_folder / "Data" / "Mods" / "Shared",
        game_folder / "Data" / "Mods" / "SharedDev",
    ]

def get_critical_game_paths() -> list[Path]:
    game_folder = get_game_folder()
    result = []
    for path in CRITICAL_GAME_FOLDER_PATHS:
        path = game_folder / path
        result.append(path)
    return result

def get_test_folders() -> list[Path]:
    test_folder_root = USER_DIR / "Desktop" / "Mod Swapper Test Folder"
    return [
        test_folder_root / "Data" / "Generated",
        test_folder_root / "Data" / "Generated" / "Public" / "Shared" / "Assets" / "unique_tav",
        test_folder_root / "Test Generated Folder",
        test_folder_root / "modsettings.lsx",
    ]

@dataclass
class UserSettings:
    swap_paths: list[Path] = field(default_factory=get_test_folders)
    protected_paths: list[Path] = field(default_factory=get_protected_paths)
    critical_game_paths: list[Path] = field(default_factory=get_critical_game_paths)
    game_folder: Path = field(default_factory=get_game_folder)

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

            # Convert the list of strings back into a list of Paths
            for field in cls.__dataclass_fields__.values():
                if field.init and field.name in filtered_data:
                    filtered_data[field.name] = [
                        Path(p) for p in filtered_data["swap_paths"].items()
                    ]
            return cls(**filtered_data)
        
        except (json.JSONDecodeError, TypeError) as e:
            # If the file is garbled or missing required fields, 
            # fall back to a fresh default config.
            print(f"Warning: Failed to load config, using defaults. Error: {e}")
            return cls()
        
    def is_allowed_path(self, path: Path) -> bool:
        return (
            path in self.protected_paths or
            path in self.critical_game_paths
        )