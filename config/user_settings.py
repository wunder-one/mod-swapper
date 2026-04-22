import json
import logging
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Literal
from itertools import chain

from constants import (
    USER_CONFIG_DIR,
    USER_SETTINGS_FILE,
    CRITICAL_GAME_FOLDER_PATHS,
    LOCAL_APPDATA,
)
from functions.discover_steam import find_steam_game_install_path

logger = logging.getLogger(__name__)

InstallType = Literal["steam", "gog", "custom"]


def guess_install_type_and_folder() -> tuple[InstallType, Path | None]:
    steam_path = find_steam_game_install_path()
    if steam_path:
        return "steam", steam_path
    # TODO: logic for GOG install
    return "custom", None


@dataclass
class UserSettings:
    install_type: InstallType
    game_folder: Path | None
    swap_paths: list[Path]
    user_protected_paths: list[Path]
    critical_game_paths: list[Path]

    @staticmethod
    def _get_default_swap_paths(game_folder: Path | None) -> list[Path]:
        app_data_paths = [
            LOCAL_APPDATA
            / "Larian Studios"
            / "Baldur's Gate 3"
            / "Mods",  # C:\Users\wes\AppData\Local\Larian Studios\Baldur's Gate 3\Mods
            LOCAL_APPDATA
            / "Larian Studios"
            / "Baldur's Gate 3"
            / "PlayerProfiles"
            / "Public"
            / "modsettings.lsx",
        ]
        if not game_folder:
            return app_data_paths
        else:
            game_folder_paths = [
                game_folder / "bin" / "NativeMods",
                game_folder / "Data" / "Generated",
            ]
            app_data_paths.extend(game_folder_paths)
            return app_data_paths

    @staticmethod
    def _get_default_protected_paths(game_folder: Path | None) -> list[Path]:
        if not game_folder:
            return []
        return [
            game_folder / "DigitalDeluxe",
            game_folder / "DotNetCore",
            game_folder / "Launcher",
            game_folder / "Data" / "Localization",
        ]

    @staticmethod
    def _getcritical_game_paths(game_folder: Path | None) -> list[Path]:
        result = []
        if not game_folder:
            return result
        for path in CRITICAL_GAME_FOLDER_PATHS:
            path = game_folder / path
            result.append(path)
        return result

    def reset_to_defaults(self):
        # Wipes current settings and re-detects the game paths.
        install_type, game_folder = guess_install_type_and_folder()
        self.install_type = install_type
        self.game_folder = game_folder
        self.swap_paths = self._get_default_swap_paths(game_folder)
        self.user_protected_paths = self._get_default_protected_paths(game_folder)
        self.critical_game_paths = self._getcritical_game_paths(game_folder)
        # Save to disk again
        self.save_settings()

    @classmethod
    def create_with_defaults(cls) -> "UserSettings":
        """Build default settings and write them to disk (bootstrap / corrupt-config recovery)."""
        install_type, game_folder = guess_install_type_and_folder()
        settings = cls(
            install_type=install_type,
            game_folder=game_folder,
            swap_paths=cls._get_default_swap_paths(game_folder),
            user_protected_paths=cls._get_default_protected_paths(game_folder),
            critical_game_paths=cls._getcritical_game_paths(game_folder),
        )
        settings.save_settings()
        return settings

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
            allowed_keys = {f.name: f.type for f in fields(cls) if f.init}
            del allowed_keys["critical_game_paths"]
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}

            # Convert the list of strings back into a list of Paths
            converted_data = {}
            default_install_type, default_game_folder = guess_install_type_and_folder()
            install_type = filtered_data.get("install_type", default_install_type)
            game_folder = Path(filtered_data.get("game_folder", default_game_folder))
            # TODO: add logic to ask for game folder if not found
            for field_name, field_type in allowed_keys.items():
                if field_name in filtered_data:
                    value = filtered_data[field_name]
                    if field_type == Path:
                        converted_data[field_name] = Path(value)
                    elif field_type == list[Path]:
                        converted_data[field_name] = [Path(p) for p in value]
                    else:
                        converted_data[field_name] = value
                else:
                    match field_name:
                        case "install_type":
                            converted_data[field_name] = install_type
                        case "game_folder":
                            converted_data[field_name] = game_folder
                        case "swap_paths":
                            converted_data[field_name] = cls._get_default_swap_paths(
                                game_folder
                            )
                        case "user_protected_paths":
                            converted_data[field_name] = (
                                cls._get_default_protected_paths(game_folder)
                            )

            return cls(
                critical_game_paths=cls._getcritical_game_paths(game_folder),
                **converted_data,
            )

        except (json.JSONDecodeError, TypeError) as e:
            # If the file is garbled or missing required fields,
            # fall back to a fresh default config.
            logger.warning("Failed to load user settings; using defaults: %s", e)
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
        for protected_path in chain(
            self.user_protected_paths, self.critical_game_paths
        ):
            if protected_path.is_file():
                excluded_files.append(protected_path)
            elif protected_path.is_dir():
                excluded_dirs.append(protected_path)
        return excluded_files, excluded_dirs
