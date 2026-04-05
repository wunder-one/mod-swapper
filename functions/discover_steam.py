import winreg
import json
from pathlib import Path

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
            print(f"No key at {key_path}")
            # pass needed for when print() is removed.
            pass    # key not present, try next path
    return steam_path


def parse_vdf_value(line: str) -> str:
    # Extract the value from a VDF key-value line.
    parts = line.strip().split('"')
    # parts = ['', 'key', '\t\t', 'value', '']
    return parts[3] if len(parts) >= 4 else ""


def find_game_install_path(app_id: str) -> Path | None:

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
    print(f"Target steam library folder is {current_path}")

    manifest_path = target_steam_folder / "steamapps" / f"appmanifest_{app_id}.acf"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                if '"installdir"' in line:
                    install_dir = parse_vdf_value(line)
                    return target_steam_folder / "steamapps" / "common" / install_dir

    return None

