import json
import logging
import subprocess
from collections.abc import Callable
from pathlib import Path
from shutil import move

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from constants import PROFILES_SNAPSHOT_DIR, USER_DIR

logger = logging.getLogger(__name__)


def mirror_directory(
    source_dir: Path,
    dest_dir: Path,
    excluded_files: list[Path] | None = None,
    exclude_dirs: list[Path] | None = None,
):
    logger.debug("Mirroring directory: %s to %s", source_dir, dest_dir)
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
    command.extend(
        [
            "/MIR",  # mirror
            "/FFT",  # use FAT file times (2-second tolerance, more reliable)
            "/Z",  # restartable mode in case of interruption
            "/NP",  # no progress percentage in output
            # Robocopy defaults are /R:1000000 /W:30 — a locked file can look hung for hours.
            "/R:10",  # retry failed copies a bounded number of times
            "/W:2",  # seconds between retries
        ]
    )
    run_kw: dict = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        # Avoid flashing console windows when packaged as a windowed (pythonw) app.
        run_kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(command, capture_output=True, text=True, **run_kw)
    # Robocopy exit codes 0-7 are success, 8+ are errors
    if result.returncode >= 8:
        raise RuntimeError(
            f"Robocopy failed with exit code {result.returncode}\n{result.stderr}\n{result.stdout}"
        )


def copy_file(src_file: Path, dst_file: Path, excluded_files: list[Path] | None):
    logger.debug("Copying file: %s to %s", src_file, dst_file)
    if excluded_files and dst_file in excluded_files:
        raise ValueError("Specified destination is protected")
    if excluded_files and src_file in excluded_files:
        raise ValueError("Specified source file is protected")
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


def create_missing_folders(swap_paths: list[Path]):
    for path in swap_paths:
        if not path.exists() and path.is_dir():
            path.mkdir(parents=True, exist_ok=True)
            logger.debug("Created missing folder: %s", path)


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
                recovery_folder = get_unique_path(
                    USER_DIR
                    / "Desktop"
                    / "BG3 Mod Swapper Recovered Files"
                    / profile_name
                )
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
                manifest_data["targets"].append(
                    {
                        "source": str(live_path),
                        "storage": str(storage_folder),
                        "type": "directory",
                    }
                )
            if live_path.is_file():
                storage_file_path = storage_folder / live_path.name
                copy_file(live_path, storage_file_path, excluded_files)
                # Need to consider if file source should be parent folder or file path.
                manifest_data["targets"].append(
                    {
                        "source": str(live_path),
                        "storage": str(storage_file_path),
                        "type": "file",
                    }
                )
        else:
            manifest_data["targets"].append(
                {"source": str(live_path), "storage": "", "type": "none"}
            )
            logger.warning(
                "Live path does not exist, recording as empty target: %s", live_path
            )

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

    incoming_sources = {
        t["source"] for t in incoming_manifest["targets"] if t["type"] == "file"
    }
    for target in outgoing_manifest.get("targets"):
        if target["type"] == "file" and target["source"] not in incoming_sources:
            p = Path(target["source"])
            logger.debug("Removing outgoing-only file: %s", p)
            p.unlink(missing_ok=True)


def load_profile_to_live(profile_name: str, user_settings: UserSettings):
    logger.info("Loading profile to live mods: %s", profile_name)
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
            mirror_directory(
                storage_path,
                dst_path,
                excluded_files=excluded_files,
                exclude_dirs=excluded_dirs,
            )
        if target["type"] == "file":
            copy_file(storage_path, dst_path, excluded_files)
        if target["type"] == "none":
            logger.debug(
                "Target is recorded as empty, checking if path exists: %s",
                target["source"],
            )
            if dst_path.exists() and dst_path.is_dir():
                logger.debug(
                    "Deleting empty target directory recursively: %s", dst_path
                )
                for root, dirs, files in dst_path.walk(top_down=False):
                    for name in files:
                        (root / name).unlink()
                    for name in dirs:
                        (root / name).rmdir()
                dst_path.rmdir()
            elif dst_path.exists() and dst_path.is_file():
                logger.debug("Removing empty target file: %s", dst_path)
                dst_path.unlink()
            else:
                logger.debug("Path does not exist, skipping: %s", dst_path)


def create_new_profile(
    profile_name: str,
    prof_state: ProfileState,
    user_settings: UserSettings,
    refresh_profiles: Callable[[], None] | None = None,
) -> str:
    unique_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / profile_name)
    unique_dir.mkdir(parents=True, exist_ok=False)
    profile_name = unique_dir.name
    save_live_to_profile(profile_name, user_settings)
    prof_state.active_profile = profile_name
    prof_state.save_config()
    if refresh_profiles is not None:
        refresh_profiles()
    return profile_name


def delete_profile(profile_to_delete: str, prof_state: ProfileState):
    # Delete current profile folder recursively
    profile_to_delete_dir = PROFILES_SNAPSHOT_DIR / profile_to_delete
    logger.info("Deleting profile folder recursively: %s", profile_to_delete_dir)
    for root, dirs, files in profile_to_delete_dir.walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            (root / name).rmdir()
    profile_to_delete_dir.rmdir()

    prof_state.remove_profile(profile_to_delete)


def overwrite_profile(
    profile_to_overwrite: str, prof_state: ProfileState, user_settings: UserSettings
):
    # Delete current profile folder recursively
    profile_to_delete_dir = PROFILES_SNAPSHOT_DIR / profile_to_overwrite
    logger.info("Deleting profile folder recursively: %s", profile_to_delete_dir)
    for root, dirs, files in profile_to_delete_dir.walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            (root / name).rmdir()
    profile_to_delete_dir.rmdir()

    save_live_to_profile(profile_to_overwrite, user_settings)
    prof_state.active_profile = profile_to_overwrite
    prof_state.save_config()
    return profile_to_overwrite


def swap_profiles(
    profile_to_load: str, prof_state: ProfileState, user_settings: UserSettings
):
    # Validations
    # Check if the selected profile is already active
    if prof_state.active_profile == profile_to_load:
        logger.info("Profile %r is already active; no swap performed.", profile_to_load)
        raise ValueError("Selected profile is already active.")
    # Check if the profile to load exists in storage
    profile_to_load_dir = PROFILES_SNAPSHOT_DIR / profile_to_load
    if not profile_to_load_dir.exists():
        logger.warning("Profile %r not found in storage.", profile_to_load)
        raise FileNotFoundError(f"Profile '{profile_to_load}' does not exist.")
    # --- End of validations ---

    # Saving current profile
    old_profile = prof_state.active_profile
    backup_profile = None
    if not old_profile:
        logger.info("No active profile; creating backup from current live mods.")
        backup_profile = create_new_profile("Backup Profile", prof_state, user_settings)
        logger.info("New backup profile: %s", backup_profile)
        old_profile = backup_profile
    else:
        logger.info(
            "Saving current profile %r before swap to %r.",
            prof_state.active_profile,
            profile_to_load,
        )
        save_live_to_profile(prof_state.active_profile, user_settings)

    remove_single_files(old_profile, profile_to_load)

    # Loading new profile
    try:
        load_profile_to_live(profile_to_load, user_settings)
        prof_state.active_profile = profile_to_load
        prof_state.save_config()
        logger.info("Swap complete; active profile is now %r.", profile_to_load)
        return prof_state.active_profile
    except Exception as e:
        try:
            logger.error(
                "Loading profile %r failed; rolling back.",
                profile_to_load,
                exc_info=True,
            )
            rollback_profile = backup_profile or old_profile
            logger.info("Restoring live mods from profile %r.", rollback_profile)
            load_profile_to_live(rollback_profile, user_settings)
            prof_state.active_profile = rollback_profile
            prof_state.save_config()
            logger.warning("Rolled back; active profile is now %r.", rollback_profile)
        except Exception as rollback_error:
            logger.critical("Rollback after failed swap also failed.", exc_info=True)
            raise RuntimeError(
                "Critical error: Failed to load new profile and rollback also failed. Live mods may be in an inconsistent state."
            ) from rollback_error
        raise RuntimeError(
            f"Failed to load profile '{profile_to_load}'. Rolled back."
        ) from e
