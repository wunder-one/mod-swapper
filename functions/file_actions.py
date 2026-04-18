import subprocess
import json
from pathlib import Path
from shutil import move, rmtree, copy2

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from constants import PROFILES_SNAPSHOT_DIR, USER_DIR


def mirror_directory(
        source_dir: Path, 
        dest_dir: Path, 
        excluded_files: list[Path] | None = None,
        exclude_dirs: list[Path] | None = None,
    ):
    # print(f"- Mirror Directory {source_dir.name} => {dest_dir.name}")
    command = [
        "robocopy",
        str(source_dir),
        str(dest_dir),
    ]
    if excluded_files:
        command.append("/XF")
        command.extend(str(f) for f in excluded_files)
    if exclude_dirs:
        command.append("/XD")
        command.extend(str(f) for f in exclude_dirs)
    command.extend([
        "/MIR",   # mirror
        "/FFT",   # use FAT file times (2-second tolerance, more reliable)
        "/Z",     # restartable mode in case of interruption
        "/NP",    # no progress percentage in output
    ])
    # print(f"--> {source_dir}(file) --> {dest_dir}")
    result = subprocess.run(command, capture_output=True, text=True)
    # Robocopy exit codes 0-7 are success, 8+ are errors
    if result.returncode >= 8:
        raise RuntimeError(f"Robocopy failed with exit code {result.returncode}\n{result.stderr}\n{result.stdout}")

def copy_file(src_file: Path, dst_file: Path, excluded_files: list[Path] | None):
    # print(f"- Copy File {src_file.name} => {dst_file.name}")
    if excluded_files and dst_file in excluded_files:
        raise ValueError("Specified destination is protected")    
    if excluded_files and src_file in excluded_files:
        raise ValueError("Specified source file is protected")
    # print(f"--> {src_file}(file) --> {dst_file}")
    src_file.copy(dst_file, follow_symlinks=False, preserve_metadata=True)

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

def save_live_to_profile(profile_name: str, user_settings: UserSettings):
    # Create profile folder if needed
    profile_folder = PROFILES_SNAPSHOT_DIR / profile_name
    profile_folder.mkdir(parents=True, exist_ok=True)
    # Move "extra" folders to desktop 
    recovery_folder_created = False
    swap_folder_names = [p.name for p in user_settings.swap_paths]
    for path in profile_folder.iterdir():
        if path.name not in swap_folder_names and path.is_dir():
            if not recovery_folder_created:
                recovery_folder = get_unique_path(USER_DIR / "Desktop" / "BG3 Mod Swapper Recovered Files" / profile_name)
                recovery_folder.mkdir(parents=True, exist_ok=True)
                recovery_folder_created = True
            move(path, recovery_folder)
    # manifest_data = {"name of storage folder": "folder the data came from"}
    manifest_data = {"version": 1, "targets": []}
    # Mirror each swap folder 
    for live_path in user_settings.swap_paths:
        if live_path.exists():
            storage_folder = profile_folder / live_path.name
            storage_folder.mkdir(parents=True, exist_ok=True)
            excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
            if live_path.is_dir():
                mirror_directory(
                    live_path, 
                    storage_folder,
                    excluded_files=excluded_files, 
                    exclude_dirs=excluded_dirs,
                )
                manifest_data["targets"].append({ "source": str(live_path), "storage": str(storage_folder), "type": "directory" })
            if live_path.is_file():
                storage_file_path = storage_folder / live_path.name
                copy_file(live_path, storage_file_path, excluded_files)
                # Need to consider if file source should be parent folder or file path.
                manifest_data["targets"].append({ "source": str(live_path), "storage": str(storage_file_path), "type": "file" })
        
    json_data = json.dumps(manifest_data, indent=4, default=str)
    manifest_file = profile_folder / "manifest.json"
    manifest_file.write_text(json_data, encoding="utf-8")

def remove_single_files(outgoing_profile: str, incoming_profile: str):
    outgoing_manifest_file = PROFILES_SNAPSHOT_DIR / outgoing_profile / "manifest.json"
    with outgoing_manifest_file.open("r", encoding="utf-8") as f:
        outgoing_manifest = json.load(f)
    incoming_manifest_file = PROFILES_SNAPSHOT_DIR / incoming_profile / "manifest.json"
    with incoming_manifest_file.open("r", encoding="utf-8") as f:
        incoming_manifest = json.load(f)

    incoming_sources = {t["source"] for t in incoming_manifest["targets"] if t["type"] == "file"}
    for target in outgoing_manifest.get("targets"):
        if target["type"] == "file" and target["source"] not in incoming_sources:
            # print("Converting to Path")
            p = Path(target["source"])
            # print(f"Deleting {p.name}")
            p.unlink(missing_ok=True)

def load_profile_to_live(profile_name: str, user_settings: UserSettings):
    # print(f"Running load_profile_to_live for {profile_name}")
    profile_folder = PROFILES_SNAPSHOT_DIR / profile_name
    if not profile_folder.exists():
        raise FileNotFoundError(f"No profile folder found for '{profile_name}'")
    manifest_file = profile_folder / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found for profile '{profile_name}'")

    with manifest_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    for target in manifest.get("targets", []):
        storage_path = Path(target["storage"])
        dst_path = Path(target["source"])
        if target["type"] == "directory":
            # print(f"Restoring {storage_path.name} directory to {dst_path.name}...")
            mirror_directory(
                storage_path,
                dst_path,
                excluded_files=excluded_files,
                exclude_dirs=excluded_dirs,
            )
        if target["type"] == "file":
            # print(f"Restoring {storage_path.name} file to {dst_path.name}...")
            copy_file(storage_path, dst_path, excluded_files)

def create_new_profile(profile_name: str, prof_state: ProfileState, user_settings: UserSettings) -> str:
    unique_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / profile_name)
    unique_dir.mkdir(parents=True, exist_ok=False)
    profile_name = unique_dir.name
    save_live_to_profile(profile_name, user_settings)
    prof_state.active_profile = profile_name
    prof_state.save_config()
    return profile_name

def overwrite_profile(profile_to_overwrite: str, prof_state: ProfileState, user_settings: UserSettings):
    profile_to_overwrite_dir = PROFILES_SNAPSHOT_DIR / profile_to_overwrite
    if not profile_to_overwrite_dir.exists():
        raise FileNotFoundError(f"Profile '{profile_to_overwrite}' does not exist.")
    save_live_to_profile(profile_to_overwrite_dir.name, user_settings)
    prof_state.active_profile = profile_to_overwrite_dir.name
    prof_state.save_config()
    return profile_to_overwrite_dir.name

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
        print("No active profile found. Backing up current live mods...")
        backup_profile = create_new_profile("Backup Profile", prof_state, user_settings)
        print(f"New backup profile: {backup_profile}")
        old_profile = backup_profile
    else:
        # print(f"Swapping from {prof_state.active_profile} to {profile_to_load}...")
        save_live_to_profile(prof_state.active_profile, user_settings)
        # print(f"{prof_state.active_profile} saved to profile storage.")

    remove_single_files(old_profile, profile_to_load)

    # Loading new profile
    try:
        load_profile_to_live(profile_to_load, user_settings)
        # print(f"{profile_to_load} loaded to live mods.")
        prof_state.active_profile = profile_to_load
        prof_state.save_config()
        print(f"[SUCCESS] Updated active profile to '{profile_to_load}'")
        print("------ END OF SWAP ------")
        return prof_state.active_profile   
    except Exception as e:
        try:
            print("Loading failed, rolling back to old profile...")
            rollback_profile = backup_profile or old_profile
            print(f"Loading {rollback_profile} to Live")
            load_profile_to_live(rollback_profile, user_settings)
            print("Profile loaded. Updating active profile in memory...")
            prof_state.active_profile = rollback_profile
            print("Active Profiles Saved. Saving updated state to disk...")
            prof_state.save_config()
            print(f"[RESTORE] Updated active profile to '{rollback_profile}' in config...")
        except Exception as rollback_error:
            print(f"Rollback failed: {rollback_error}")
            raise RuntimeError("Critical error: Failed to load new profile and rollback also failed. Live mods may be in an inconsistent state.") from rollback_error
        raise RuntimeError(f"Failed to load profile '{profile_to_load}'. Rolled back.") from e



