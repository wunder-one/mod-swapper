import subprocess
import json
from pathlib import Path
from shutil import rmtree
from profile_state import ProfileState
from user_settings import UserSettings
from constants import PROFILES_SNAPSHOT_DIR

    
def mirror_directory(source_dir: Path, dest_dir: Path, files: list[Path] | None = None):
    command = [
        "robocopy",
        source_dir,
        dest_dir,
    ]

    if files:
        command.extend(files)
    
    command.extend([
        "/MIR",   # mirror
        "/FFT",   # use FAT file times (2-second tolerance, more reliable)
        "/Z",     # restartable mode in case of interruption
        "/NP",    # no progress percentage in output
    ])
    result = subprocess.run(command, capture_output=True, text=True)
    # Robocopy exit codes 0-7 are success, 8+ are errors
    if result.returncode >= 8:
        raise RuntimeError(f"Robocopy failed with exit code {result.returncode}\n{result.stdout}")

def get_unique_path(base_path: Path) -> Path:
    # Returns a Path that doesn't exist by appending (n) if necessary.
    if not base_path.exists():
        return base_path
    counter = 1
    # Keep trying new numbers until we find a path that doesn't exist
    while True:
        new_path = base_path.with_name(f"{base_path.name} ({counter})")
        if not new_path.exists():
            return new_path
        counter += 1

def save_live_to_profile(profile_name: str, swap_paths: list):
    profile_folder = PROFILES_SNAPSHOT_DIR / profile_name
    profile_folder.mkdir(parents=True, exist_ok=True)
    for path in profile_folder.iterdir():
        if path.name not in swap_paths and path.is_dir():
            # TODO: Add in error handling for rmtree
            rmtree(path, ignore_errors=True)
    # manifest_data = {"name of storage folder": "folder the data came from"}
    manifest_data = {}
    for live_path in swap_paths:
        live_path_folder = live_path if live_path.is_dir() else live_path.parent
        live_filename_list = [live_path.name] if live_path.is_file() else None
        storage_folder = profile_folder / live_path.name
        mirror_directory(live_path_folder, storage_folder, live_filename_list)
        manifest_data[storage_folder.name] = str(live_path)
    json_data = json.dumps(manifest_data, indent=4, default=str)
    manifest_file = profile_folder / "manifest.json"
    manifest_file.write_text(json_data, encoding="utf-8")

def load_profile_to_live(profile_name: str):
    profile_folder = PROFILES_SNAPSHOT_DIR / profile_name
    manifest_file = profile_folder / "manifest.json"
    if manifest_file.exists():
        with manifest_file.open("r") as f:
            manifest = json.load(f)
        for storage_folder_str, live_path_str in manifest["paths"].items():
            storage_path = Path(storage_folder_str)
            live_path = Path(live_path_str)

    else:   # if we don't have a manifest
        pass    # check if swap_paths exsist in live, or should we throw an error?

    
    # Now move source_path -> target_path
    print(f"Restoring {storage_path.name} to {live_path.name}...")
    mirror_directory(storage_path, live_path)

def swap_profiles(profile_to_load: str, prof_state: ProfileState, user_settings: UserSettings):
    # Validations
    # Check if the selected profile is already active
    if prof_state.active_profile == profile_to_load:
        print(f"'{profile_to_load}' is already the active profile. No changes made.")
        raise ValueError("Selected profile is already active.")
    # Check if the profile to load exists in storage
    profile_to_load_dir = PROFILES_SNAPSHOT_DIR / profile_to_load
    if not profile_to_load_dir.exists():
        print(f"Profile '{profile_to_load}' does not exist in storage. No changes made to live mods.")
        raise FileNotFoundError(f"Profile '{profile_to_load}' does not exist.")
    # --- End of validations ---

    # Saving current profile
    old_profile = prof_state.active_profile
    backup_profile = None
    if not old_profile:
        backup_profile = get_unique_path(PROFILES_SNAPSHOT_DIR / "Backed Up Profile")
        backup_profile.mkdir(parents=True, exist_ok=False)
        print(f"No active profile found. Backing up current live mods to '{backup_profile.name}'...")
        save_live_to_profile(backup_profile.name, user_settings.swap_paths)
    else:
        print(f"Swapping from {prof_state.active_profile} to {profile_to_load}...")
        save_live_to_profile(prof_state.active_profile, user_settings.swap_paths)
        print(f"{prof_state.active_profile} saved to profile storage.")

    # Loading new profile
    try:
        load_profile_to_live(profile_to_load)
        print(f"{profile_to_load} loaded to live mods.")
        prof_state.active_profile = profile_to_load
        prof_state.save_config()
        print(f"Updated active profile to '{profile_to_load}' in config...")
        return prof_state.active_profile   
    except Exception as e:
        try:
            print("Loading failed, rolling back to old profile...")
            rollback_profile = backup_profile.name if backup_profile else old_profile
            load_profile_to_live(rollback_profile)
            prof_state.active_profile = rollback_profile
            prof_state.save_config()
            print(f"Updated active profile to '{rollback_profile}' in config...")
        except Exception as rollback_error:
            print(f"Rollback failed: {rollback_error}")
            raise RuntimeError("Critical error: Failed to load new profile and rollback also failed. Live mods may be in an inconsistent state.") from rollback_error
        raise RuntimeError(f"Failed to load profile '{profile_to_load}'. Rolled back.") from e


def create_new_profile(profile_name: str, prof_state: ProfileState, user_settings: UserSettings):
    unique_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / profile_name)
    unique_dir.mkdir(parents=True, exist_ok=False)
    profile_name = unique_dir.name
    save_live_to_profile(profile_name, user_settings.swap_paths)
    prof_state.active_profile = profile_name
    prof_state.save_config()
