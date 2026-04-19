import logging
import winreg
from pathlib import Path

from constants import BG3_STEAM_ID

logger = logging.getLogger(__name__)


def find_steam_path() -> Path | None:
    # Find steam install location from win registry
    keys_to_check = [r"SOFTWARE\WOW6432Node\Valve\Steam", r"SOFTWARE\Valve\Steam"]
    steam_path = None
    for key_path in keys_to_check:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                steam_path_str, _ = winreg.QueryValueEx(key, "InstallPath")
            steam_path = Path(steam_path_str)
            break
        except FileNotFoundError:
            logger.debug("Steam registry key not found: %s", key_path)
    return steam_path


def parse_vdf_value(line: str) -> str:
    # Extract the value from a VDF key-value line.
    parts = line.strip().split('"')
    # parts = ['', 'key', '\t\t', 'value', '']
    return parts[3] if len(parts) >= 4 else ""


def find_steam_game_install_path() -> Path | None:
    app_id = BG3_STEAM_ID
    # Search all Steam libraries for an installed game by App ID.
    # Returns the full path to the game's install folder, or None if not found.

    steam_path = find_steam_path()
    if not steam_path:
        return None

    library_folders_vdf = steam_path / "steamapps" / "libraryfolders.vdf"
    if not library_folders_vdf.exists():
        return None

    # Collect all library paths from libraryfolders.vdf
    current_path = None
    with open(library_folders_vdf, encoding="utf-8") as f:
        for line in f:
            if '"path"' in line:
                current_path = parse_vdf_value(line)
            if f'"{app_id}"' in line:
                break
    if not current_path:
        return None
    target_steam_folder = Path(current_path)
    logger.debug("Using Steam library folder: %s", current_path)

    manifest_path = target_steam_folder / "steamapps" / f"appmanifest_{app_id}.acf"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                if '"installdir"' in line:
                    install_dir = parse_vdf_value(line)
                    game_path = target_steam_folder / "steamapps" / "common" / install_dir
                    if game_path.exists():
                        return game_path

    return None

