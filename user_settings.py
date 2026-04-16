import json
import os
import typing
from dataclasses import dataclass, field, fields, asdict
from pathlib import Path
from typing import Literal
from itertools import chain

from constants import USER_CONFIG_DIR, USER_SETTINGS_FILE, LOCAL_APPDATA, USER_DIR, CRITICAL_GAME_FOLDER_PATHS, DEFAULT_STEAM_GAME_FOLDER, DEFAULT_GOG_GAME_FOLDER
from functions.discover_steam import find_game_install_path

# determine if the game is from Steam or GOG
InstallType = Literal["steam", "gog", "custom"]

def get_game_install_type() -> InstallType:
    # TODO: logic that determines install type goes here
    # Setting game type to steam for testing
    return "steam"

def get_default_game_folder() -> Path:
    install_type = get_game_install_type()
    print(f"install_type == {install_type}")
    if install_type == "steam":
        game_folder = DEFAULT_STEAM_GAME_FOLDER
    elif install_type == "gog":
        game_folder = DEFAULT_GOG_GAME_FOLDER
    else:
        raise ValueError(f"Cannot provide default folder path without install type")
    if not game_folder.exists():
        raise FileNotFoundError(f"Game folder not found at {game_folder}. Please check the path and try again.")
    return game_folder

@dataclass
class UserSettings():
    game_folder: Path
    swap_paths: list[Path]
    user_protected_paths: list[Path]
    critical_game_paths: list[Path]

    @staticmethod
    def _get_default_swap_paths(game_folder: Path) -> list[Path]:
        if not game_folder:
            return []
        test_folder_root = USER_DIR / "Desktop" / "Mod Swapper Test Folder"
        return [
            game_folder / "bin" / "NativeMods",
            game_folder / "Data" / "Generated",
            test_folder_root / "Mods",
            test_folder_root / "modsettings.lsx",
        ]

    @staticmethod
    def _get_default_protected_paths(game_folder: Path) -> list[Path]:
        if not game_folder:
            return []
        return [
            game_folder / "DigitalDeluxe",
            game_folder / "DotNetCore",
            game_folder / "Launcher",
            game_folder / "Data" / "Localization",
        ]

    @staticmethod
    def _getcritical_game_paths(game_folder: Path) -> list[Path]:
        result = []
        if not game_folder:
            return result
        for path in CRITICAL_GAME_FOLDER_PATHS:
            path = game_folder / path
            result.append(path)
        return result

    def __post_init__(self):
        self.save_settings()

    def reset_to_defaults(self):
        # Wipes current settings and re-detects the game paths.
        game_folder = get_default_game_folder()
        self.game_folder = game_folder
        self.swap_paths = self._get_default_swap_paths(game_folder)
        self.protected_paths = self._get_default_protected_paths(game_folder)
        self.critical_game_paths = self._getcritical_game_paths(game_folder)
        # Save to disk again
        self.save_settings()

    @classmethod
    def create_with_defaults(cls) -> "UserSettings":
        game_folder = get_default_game_folder()
        return cls(
            game_folder=game_folder,
            swap_paths=cls._get_default_swap_paths(game_folder),
            user_protected_paths=cls._get_default_protected_paths(game_folder),
            critical_game_paths=cls._getcritical_game_paths(game_folder),
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
            allowed_keys = {f.name for f in fields(cls) if f.init}
            allowed_keys.discard("critical_game_paths")
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}

            # print(f"Dataclass Values => {cls.__dataclass_fields__.values()}")
            # Convert the list of strings back into a list of Paths
            # print(f"Filtered Data before converting => {filtered_data}")
            hints = typing.get_type_hints(cls)
            converted_data = {}
            for field_name, value in filtered_data.items():
                hint = hints[field_name]
                if hint == Path:
                    converted_data[field_name] = Path(value)
                elif hint == list[Path]:
                    converted_data[field_name] = [Path(p) for p in value]
                else:
                    converted_data[field_name] = value
            game_folder = converted_data.get("game_folder") or get_default_game_folder()
            return cls(critical_game_paths=cls._getcritical_game_paths(game_folder), **converted_data)
        
        except (json.JSONDecodeError, TypeError) as e:
            # If the file is garbled or missing required fields, 
            # fall back to a fresh default config.
            print(f"Warning: Failed to load config, using defaults. Error: {e}")
            return cls.create_with_defaults()
        

    def save_settings(self):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        del data["critical_game_paths"]
        json_data = json.dumps(data, indent=4, default=str)
        USER_SETTINGS_FILE.write_text(json_data, encoding="utf-8")

    def get_swap_paths(self) -> list[Path]:
        return self.swap_paths

    def get_user_protected_paths(self) -> list[Path]:
        return self.user_protected_paths

    def get_all_protected_paths(self) -> tuple[list[Path], list[Path]]:
        excluded_files = []
        excluded_dirs = []
        for protected_path in chain[Path](self.user_protected_paths, self.critical_game_paths):
            if protected_path.is_file():
                excluded_files.append(protected_path)
            if protected_path.is_dir():
                excluded_dirs.append(protected_path)
        return excluded_files, excluded_dirs