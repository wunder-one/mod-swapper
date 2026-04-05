import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

from constants import USER_CONFIG_DIR, USER_SETTINGS_FILE, LOCAL_APPDATA, USER_DIR, CRITICAL_GAME_FOLDER_PATHS, DEFAULT_STEAM_GAME_FOLDER, DEFAULT_GOG_GAME_FOLDER
from functions.discover_steam import find_game_install_path

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

# determine if the game is from Steam or GOG
InstallType = Literal["steam", "gog", "custom"]

def get_game_install_type() -> InstallType:
    # TODO: logic that determines install type goes here
    # Setting game type to steam for testing
    return "steam"

def get_default_game_folder() -> Path:
    install_type = get_game_install_type()
    if install_type == "steam":
        game_folder = DEFAULT_STEAM_GAME_FOLDER
    if install_type == "gog":
        game_folder = DEFAULT_GOG_GAME_FOLDER
    else:
        raise ValueError(f"Cannot provide default folder path without install type")
    if not game_folder.exists():
        raise FileNotFoundError(f"Game folder not found at {game_folder}. Please check the path and try again.")
    return game_folder

def get_swap_folder_defaults(game_folder: Path) -> list[Path]:
    if not game_folder:
        return []
    test_folder_root = USER_DIR / "Desktop" / "Mod Swapper Test Folder"
    return [
        game_folder / "Data" / "Generated",
        game_folder / "Data" / "Generated" / "Public" / "Shared" / "Assets" / "unique_tav",
        test_folder_root / "Test Generated Folder",
        test_folder_root / "modsettings.lsx",
    ]

def get_protected_path_defaults(game_folder: Path) -> list[Path]:
    if not game_folder:
        return []
    return [
        game_folder / "Data" / "Mods" / "Shared",
        game_folder / "Data" / "Mods" / "SharedDev",
    ]

def get_critical_game_paths(game_folder: Path) -> list[Path]:
    result = []
    if not game_folder:
        return result
    for path in CRITICAL_GAME_FOLDER_PATHS:
        path = game_folder / path
        result.append(path)
    return result

@dataclass
class UserSettings():
    game_folder: Path
    swap_paths: list[Path]
    protected_paths: list[Path]
    critical_game_paths: list[Path]

    def reset_to_defaults(self):
        # Wipes current settings and re-detects the game paths.
        game_folder = get_default_game_folder()
        self.game_folder = game_folder
        self.swap_paths = get_swap_folder_defaults(game_folder)
        self.protected_paths = get_protected_path_defaults(game_folder)
        self.critical_game_paths = get_critical_game_paths(game_folder)
        # Save to disk again
        self.save_settings()

    @classmethod
    def create_with_defaults(cls) -> "UserSettings":
        game_folder = get_default_game_folder()
        return cls(
            game_folder=game_folder,
            swap_paths=get_swap_folder_defaults(game_folder),
            protected_paths=get_protected_path_defaults(game_folder),
            critical_game_paths=get_critical_game_paths(game_folder),
        )

    @classmethod
    def load_settings(cls) -> "UserSettings":
        # If no user settings file, load defaults
        if not USER_SETTINGS_FILE.exists():
            return cls.create_with_defaults()
        # If there is a user settings file, load it 
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
            return cls.create_with_defaults()
        
    def save_settings(self):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        json_data = json.dumps(data, indent=4, default=str)
        USER_SETTINGS_FILE.write_text(json_data, encoding="utf-8")     
        
    def is_allowed_path(self, path: Path) -> bool:
        return (
            path in self.protected_paths or
            path in self.critical_game_paths
        )