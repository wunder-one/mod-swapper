import logging
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict
import json

from config.manifest import Manifest
from storage.blob_store import BlobStore
from config.user_settings import UserSettings
from config.profile_state import ProfileState
from constants import PROFILES_SNAPSHOT_DIR
from functions.file_actions import get_unique_path
from functions.manifest import (
    load_global_manifest,
    add_global_manifest_entry,
    save_global_manifest,
)

logger = logging.getLogger(__name__)


class ProfileManifest(TypedDict):
    version: int
    swap_paths: list[Path]
    targets: dict[str, str]


OnStoreFile = Callable[[Path, int, int], None]
# args: file_path, index (1-based), total_files

OnLoadStart = Callable[[], None]


def upgrade_outdated_profile_manifests(swap_paths: list[Path]) -> list[str]:
    """Pin old profile manifests to the current swap paths before settings change."""
    upgraded_profiles: list[str] = []
    if not PROFILES_SNAPSHOT_DIR.exists():
        return upgraded_profiles

    for profile_dir in PROFILES_SNAPSHOT_DIR.iterdir():
        if not profile_dir.is_dir():
            continue

        manifest_file = profile_dir / "manifest.json"
        if not manifest_file.exists():
            continue

        try:
            with manifest_file.open("r", encoding="utf-8") as f:
                profile_manifest = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning(
                "Skipping profile manifest migration for %s: %s",
                profile_dir.name,
                e,
            )
            continue

        try:
            manifest_version = int(profile_manifest.get("version", 1))
        except (TypeError, ValueError) as e:
            logger.warning(
                "Skipping profile manifest migration for %s: invalid version %r (%s)",
                profile_dir.name,
                profile_manifest.get("version"),
                e,
            )
            continue

        if manifest_version >= 3:
            continue

        profile_manifest["version"] = 3
        profile_manifest["swap_paths"] = swap_paths
        with manifest_file.open("w", encoding="utf-8") as f:
            json.dump(profile_manifest, f, indent=4, default=str)
        upgraded_profiles.append(profile_dir.name)

    return upgraded_profiles


def chain_store_file_callbacks(*callbacks: OnStoreFile | None) -> OnStoreFile:
    def combined(file_path: Path, index: int, total: int) -> None:
        for callback in callbacks:
            if callback is not None:
                callback(file_path, index, total)

    return combined


def _is_excluded(
    file_path: Path,
    excluded_files: set[Path],
    excluded_dirs: set[Path],
) -> bool:
    if file_path in excluded_files or file_path.parent in excluded_dirs:
        return True
    for excluded_dir in excluded_dirs:
        if file_path.is_relative_to(excluded_dir):
            return True
    return False


def _count_files_to_store(
    swap_paths: list[Path],
    excluded_files: list[Path],
    excluded_dirs: list[Path],
) -> int:
    excluded_files_set = set(excluded_files)
    excluded_dirs_set = set(excluded_dirs)
    total = 0
    for live_path in swap_paths:
        if not live_path.exists():
            continue
        if live_path.is_file():
            if not _is_excluded(live_path, excluded_files_set, excluded_dirs_set):
                total += 1
        elif live_path.is_dir():
            for root, _, files in live_path.walk():
                for filename in files:
                    file_path = root / filename
                    if not _is_excluded(
                        file_path, excluded_files_set, excluded_dirs_set
                    ):
                        total += 1
    return total


def store_directory(
    source_dir: Path,
    blob_store: BlobStore,
    global_manifest: Manifest,
    excluded_files: list[Path] | None = None,
    excluded_dirs: list[Path] | None = None,
    on_file: OnStoreFile | None = None,
    *,
    file_index: int = 0,
    total_files: int = 0,
) -> tuple[dict[str, str], int, Manifest]:
    """Store a directory in the blob store and add the file to the global manifest

    Args:
        source_dir: The directory to store
        blob_store: The blob store to use
        global_manifest: The global manifest to use
        excluded_files: A list of files to exclude from the store
        excluded_dirs: A list of directories to exclude from the store
        on_file: A callback to call when a file is stored
        file_index: The index of the current file
        total_files: The total number of files to store

    Returns:
        A tuple of (profile_manifest_additions, file_index, file_hash)
        profile_manifest_additions: A dictionary of the files that were stored
        file_index: The index of the current file
        global_manifest: The global manifest with the new entries
    """
    logger.debug("Storing directory: %s", source_dir)
    if excluded_files is None:
        excluded_files = list[Path]()
    if excluded_dirs is None:
        excluded_dirs = list[Path]()
    profile_manifest_additions = {}
    excluded_files_count = 0
    skipped_files_count = 0
    copied_files_count = 0
    excluded_files_set = set(excluded_files)
    excluded_dirs_set = set(excluded_dirs)
    for root, _, files in source_dir.walk():
        for filename in files:
            file_path = root / filename
            # skip protected files and directories
            if _is_excluded(file_path, excluded_files_set, excluded_dirs_set):
                logger.debug(
                    "File %s is excluded. Skipping.", file_path.relative_to(source_dir)
                )
                excluded_files_count += 1
                continue
            # store file in hashed store
            dest_rel, copied_to_store = blob_store.store_file(file_path)
            file_hash = str(dest_rel).replace("\\", "").replace("/", "")
            logger.debug(
                "Stored file %s as %s",
                file_path.relative_to(source_dir),
                dest_rel,
            )
            if copied_to_store:
                copied_files_count += 1
            else:
                skipped_files_count += 1
            file_index += 1
            if on_file is not None:
                on_file(file_path, file_index, total_files)
            # add file to manifest
            profile_manifest_additions[str(file_path)] = str(dest_rel)
            global_manifest = add_global_manifest_entry(
                global_manifest, file_hash, file_path
            )

    logger.info(
        " - Stored directory %s:\n"
        "     %d copied files\n"
        "     %d already stored files (skipped)\n"
        "     %d protected files (skipped)",
        source_dir,
        copied_files_count,
        skipped_files_count,
        excluded_files_count,
    )
    return profile_manifest_additions, file_index, global_manifest


def store_file(
    source_path: Path,
    blob_store: BlobStore,
    global_manifest: Manifest,
    excluded_files: list[Path] | None = None,
    excluded_dirs: list[Path] | None = None,
    on_file: OnStoreFile | None = None,
    *,
    file_index: int = 0,
    total_files: int = 0,
) -> tuple[dict[str, str], int, Manifest]:
    """Store a file in the blob store and add the file to the global manifest

    Args:
        source_path: The file to store
        blob_store: The blob store to use
        global_manifest: The global manifest to use
        excluded_files: A list of files to exclude from the store
        excluded_dirs: A list of directories to exclude from the store
        on_file: A callback to call when a file is stored
        file_index: The index of the current file
        total_files: The total number of files to store

    Returns:
        A tuple of (profile_manifest_additions, file_index, file_hash)
        profile_manifest_additions: A dictionary of the files that were stored
        file_index: The index of the current file
        global_manifest: The global manifest with the new entries
    """
    if excluded_files is None:
        excluded_files = list[Path]()
    if excluded_dirs is None:
        excluded_dirs = list[Path]()
    excluded_files_set = set(excluded_files)
    excluded_dirs_set = set(excluded_dirs)
    if _is_excluded(source_path, excluded_files_set, excluded_dirs_set):
        return {}, file_index, global_manifest
    dest_rel, copied_to_store = blob_store.store_file(source_path)
    if copied_to_store:
        file_hash = str(dest_rel).replace("\\", "").replace("/", "")
        global_manifest = add_global_manifest_entry(
            global_manifest, file_hash, source_path
        )
        logger.info("Copied file %s to store", source_path)
    else:
        logger.info("File %s already in store", source_path)
    file_index += 1
    if on_file is not None:
        on_file(source_path, file_index, total_files)
    return {str(source_path): str(dest_rel)}, file_index, global_manifest


def save_live_to_profile(
    profile_name: str,
    blob_store: BlobStore,
    user_settings: UserSettings,
    on_file: OnStoreFile | None = None,
):
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    total_files = _count_files_to_store(
        user_settings.swap_paths, excluded_files, excluded_dirs
    )
    file_index = 0
    profile_manifest = {
        "version": 3,
        "swap_paths": user_settings.swap_paths,
        "targets": {},
    }
    global_manifest = load_global_manifest()

    for live_path in user_settings.swap_paths:
        if live_path.exists():
            profile_manifest_additions = {}
            if live_path.is_dir():
                profile_manifest_additions, file_index, global_manifest = (
                    store_directory(
                        live_path,
                        blob_store,
                        global_manifest,
                        excluded_files=excluded_files,
                        excluded_dirs=excluded_dirs,
                        on_file=on_file,
                        file_index=file_index,
                        total_files=total_files,
                    )
                )
            if live_path.is_file():
                profile_manifest_additions, file_index, global_manifest = store_file(
                    live_path,
                    blob_store,
                    global_manifest,
                    excluded_files=excluded_files,
                    excluded_dirs=excluded_dirs,
                    on_file=on_file,
                    file_index=file_index,
                    total_files=total_files,
                )
            profile_manifest["targets"].update(profile_manifest_additions)
        else:
            logger.warning("Live path does not exist: %s", live_path)

    profile_manifest_json = json.dumps(profile_manifest, indent=4, default=str)
    profile_manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    profile_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    profile_manifest_file.write_text(profile_manifest_json, encoding="utf-8")

    save_global_manifest(global_manifest)


def _list_files_to_restore(
    profile_name: str,
    blob_store: BlobStore,
    manifest: ProfileManifest,
) -> list[tuple[Path, Path]]:

    files_to_restore: list[tuple[Path, Path]] = []
    skipped_files_count = 0
    restored_files_count = 0
    for live_path_str, storage_rel_str in manifest["targets"].items():
        live_path = Path(live_path_str)
        storage_path = blob_store.store_dir / storage_rel_str
        if not live_path.exists():
            logger.debug("File %s does not exist. Adding to restore list.", live_path)
            restored_files_count += 1
            files_to_restore.append((live_path, storage_path))
            continue

        # The blob path is content-addressed: <hash[:2]>/<hash[2:]>
        expected_hash = str(storage_rel_str).replace("\\", "").replace("/", "")
        actual_hash = blob_store.get_cached_hash(live_path)

        if actual_hash != expected_hash:
            logger.debug(
                "File %s hash mismatch (expected %s, got %s). Adding to restore list.",
                live_path,
                expected_hash[:16],
                actual_hash[:16],
            )
            restored_files_count += 1
            files_to_restore.append((live_path, storage_path))
        else:
            logger.debug("File %s matches expected hash. Skipping.", live_path)
            skipped_files_count += 1
    logger.info(
        "Copying files for '%s' from snapshot:\n"
        "     %d files copied\n"
        "     %d files already in live (skipped)",
        profile_name,
        restored_files_count,
        skipped_files_count,
    )
    return files_to_restore


def _list_files_to_remove(
    profile_name: str,
    swap_paths: list[Path],
    excluded_files: list[Path] | None = None,
    excluded_dirs: list[Path] | None = None,
) -> list[Path]:
    if excluded_files is None:
        excluded_files = list[Path]()
    if excluded_dirs is None:
        excluded_dirs = list[Path]()
    manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    with manifest_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    target_paths = {Path(path).resolve() for path in manifest["targets"].keys()}
    files_to_remove = list[Path]()
    excluded_files_set = set(excluded_files)
    excluded_dirs_set = set(excluded_dirs)
    for swap_path in swap_paths:
        if (
            swap_path.exists()
            and swap_path.is_file()
            and not _is_excluded(swap_path, excluded_files_set, excluded_dirs_set)
            and swap_path.resolve() not in target_paths
        ):
            logger.debug("Adding singlefile %s to remove list", swap_path)
            files_to_remove.append(swap_path)
        elif (
            swap_path.exists()
            and swap_path.is_dir()
            and not _is_excluded(swap_path, excluded_files_set, excluded_dirs_set)
        ):
            for root, _, files in swap_path.walk():
                for filename in files:
                    file_path = root / filename
                    # skip protected files and directories
                    if (
                        not _is_excluded(
                            file_path, excluded_files_set, excluded_dirs_set
                        )
                        and file_path.resolve() not in target_paths
                    ):
                        files_to_remove.append(file_path)
    logger.info(
        "Removing extra files not used in '%s' from live:\n     %d files removed",
        profile_name,
        len(files_to_remove),
    )
    return files_to_remove


def load_profile_to_live(
    profile_name: str,
    blob_store: BlobStore,
    user_settings: UserSettings,
    on_load_start: OnLoadStart | None = None,
):
    manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    with manifest_file.open("r", encoding="utf-8") as f:
        manifest: ProfileManifest = json.load(f)
    # get files to restore and remove
    files_to_restore = _list_files_to_restore(profile_name, blob_store, manifest)
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    swap_paths = (
        [Path(path) for path in manifest["swap_paths"]]
        if manifest["version"] >= 3
        else user_settings.swap_paths
    )
    files_to_remove = _list_files_to_remove(
        profile_name,
        swap_paths,
        excluded_files=excluded_files,
        excluded_dirs=excluded_dirs,
    )
    if on_load_start is not None:
        on_load_start()
    # restore files from list of files to restore
    for live_path, storage_path in files_to_restore:
        if not storage_path.exists():
            raise FileNotFoundError(
                f"Snapshot blob missing for {live_path}: {storage_path}"
            )
        tmp_path = live_path.parent / f"{live_path.name}.tmp-restore"
        live_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.copy(tmp_path, follow_symlinks=False, preserve_metadata=True)
        tmp_path.replace(live_path)
        if not live_path.exists():
            raise RuntimeError("Failed to restore file %s", live_path)
    # remove files from list of files to remove
    for file in files_to_remove:
        file.unlink(missing_ok=True)


def swap_profile(
    profile_name: str,
    profile_state: ProfileState,
    blob_store: BlobStore,
    user_settings: UserSettings,
    on_file: OnStoreFile | None = None,
    on_load_start: OnLoadStart | None = None,
):
    old_profile = profile_state.active_profile
    backup_profile = None
    if not old_profile:
        logger.info("No active profile; creating backup from current live mods.")
        backup_profile = create_new_profile(
            "Backup Profile",
            profile_state,
            blob_store,
            user_settings,
            on_file=on_file,
        )
        old_profile = backup_profile
    else:
        logger.info(
            "Saving current profile %r before swap to %r.",
            old_profile,
            profile_name,
        )
        save_live_to_profile(old_profile, blob_store, user_settings, on_file=on_file)
    blob_store.save_cache()

    try:
        load_profile_to_live(
            profile_name, blob_store, user_settings, on_load_start=on_load_start
        )
        profile_state.active_profile = profile_name
        profile_state.save_config()
        logger.info("Swap complete; active profile is now %r.", profile_name)
    except Exception as e:
        rollback_profile = backup_profile or old_profile
        logger.error(
            "Loading profile %r failed; rolling back to %r.",
            profile_name,
            rollback_profile,
        )
        try:
            load_profile_to_live(rollback_profile, blob_store, user_settings)
            profile_state.active_profile = rollback_profile
            profile_state.save_config()
            logger.warning("Rolled back; active profile is now %r.", rollback_profile)
        except Exception as rollback_error:
            logger.critical("Rollback after failed swap also failed.", exc_info=True)
            raise RuntimeError(
                "Critical error: Failed to load new profile and rollback also failed. "
                "Live mods may be in an inconsistent state."
            ) from rollback_error
        raise RuntimeError(
            f"Failed to load profile '{profile_name}'. Rolled back."
        ) from e


def create_new_profile(
    profile_name: str,
    profile_state: ProfileState,
    blob_store: BlobStore,
    user_settings: UserSettings,
    refresh_profiles: Callable[[], None] | None = None,
    on_file: OnStoreFile | None = None,
) -> str:
    unique_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / profile_name)
    unique_dir.mkdir(parents=True, exist_ok=False)
    profile_name = unique_dir.name
    save_live_to_profile(profile_name, blob_store, user_settings, on_file=on_file)
    profile_state.active_profile = profile_name
    profile_state.save_config()
    if refresh_profiles is not None:
        refresh_profiles()
    return profile_name


def delete_profile(profile_to_delete: str, profile_state: ProfileState):
    profile_to_delete_dir = PROFILES_SNAPSHOT_DIR / profile_to_delete
    logger.info("Deleting profile folder recursively: %s", profile_to_delete_dir)
    for root, dirs, files in profile_to_delete_dir.walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            (root / name).rmdir()
    profile_to_delete_dir.rmdir()
    profile_state.remove_profile(profile_to_delete)


def _rmtree(path: Path):
    for root, dirs, files in path.walk(top_down=False):
        for name in files:
            (root / name).unlink()
        for name in dirs:
            (root / name).rmdir()
    path.rmdir()


def overwrite_profile(
    profile_to_overwrite: str,
    profile_state: ProfileState,
    blob_store: BlobStore,
    user_settings: UserSettings,
    on_file: OnStoreFile | None = None,
):
    profile_dir = PROFILES_SNAPSHOT_DIR / profile_to_overwrite
    if not profile_dir.exists():
        raise FileNotFoundError(f"Profile {profile_to_overwrite} does not exist.")
    logger.info("Overwriting profile: %s", profile_dir)
    backup_dir = PROFILES_SNAPSHOT_DIR / f"{profile_to_overwrite}.tmp-rollback"
    profile_dir.rename(backup_dir)
    try:
        save_live_to_profile(
            profile_to_overwrite, blob_store, user_settings, on_file=on_file
        )
    except Exception:
        if (PROFILES_SNAPSHOT_DIR / profile_to_overwrite).exists():
            _rmtree(PROFILES_SNAPSHOT_DIR / profile_to_overwrite)
        backup_dir.rename(profile_dir)
        raise
    _rmtree(backup_dir)
    blob_store.save_cache()
    profile_state.active_profile = profile_to_overwrite
    profile_state.save_config()
