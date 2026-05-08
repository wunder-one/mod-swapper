import logging
from pathlib import Path
from functions.file_hash_cache import FileHashCache
from config.user_settings import UserSettings
import json

from constants import PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


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


def store_directory(
    source_dir: Path,
    file_hash_cache: FileHashCache,
    excluded_files: list[Path] | None = None,
    excluded_dirs: list[Path] | None = None,
) -> dict[str, str]:
    logger.debug("Storing directory: %s", source_dir)
    if excluded_files is None:
        excluded_files = list[Path]()
    if excluded_dirs is None:
        excluded_dirs = list[Path]()
    manifest = {}
    for root, _, files in source_dir.walk():
        for filename in files:
            file_path = root / filename
            # skip protected files and directories
            if _is_excluded(file_path, set(excluded_files), set(excluded_dirs)):
                logger.debug(
                    "File %s is excluded. Skipping.", file_path.relative_to(source_dir)
                )
                continue
            # store file in hashed store
            dest_rel = file_hash_cache.store_file(file_path)
            logger.debug(
                "Stored file %s as %s", file_path.relative_to(source_dir), dest_rel
            )
            # add file to manifest
            manifest[str(file_path)] = str(dest_rel)
    return manifest


def store_file(
    source_path: Path,
    file_hash_cache: FileHashCache,
    excluded_files: list[Path] | None = None,
    excluded_dirs: list[Path] | None = None,
) -> dict[str, str]:
    if excluded_files is None:
        excluded_files = list[Path]()
    if excluded_dirs is None:
        excluded_dirs = list[Path]()
    if _is_excluded(source_path, set(excluded_files), set(excluded_dirs)):
        return {}
    dest_rel = file_hash_cache.store_file(source_path)
    return {str(source_path): str(dest_rel)}


def save_live_to_profile(
    profile_name: str,
    file_hash_cache: FileHashCache,
    user_settings: UserSettings,
):
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    manifest = {"version": 2, "targets": {}}
    for live_path in user_settings.swap_paths:
        if live_path.exists():
            if live_path.is_dir():
                manifest_additions = store_directory(
                    live_path,
                    file_hash_cache,
                    excluded_files=excluded_files,
                    excluded_dirs=excluded_dirs,
                )
            if live_path.is_file():
                manifest_additions = store_file(
                    live_path,
                    file_hash_cache,
                    excluded_files=excluded_files,
                    excluded_dirs=excluded_dirs,
                )
            manifest["targets"].update(manifest_additions)
        else:
            logger.warning("Live path does not exist: %s", live_path)

    json_data = json.dumps(manifest, indent=4, default=str)
    manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json_data, encoding="utf-8")


def _list_files_to_restore(
    profile_name: str,
    file_hash_cache: FileHashCache,
) -> list[tuple[Path, Path]]:
    
    manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    with manifest_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    files_to_restore: list[tuple[Path, Path]] = []
    for live_path_str, storage_rel_str in manifest["targets"].items():
        live_path = Path(live_path_str)
        storage_path = file_hash_cache.store_dir / storage_rel_str
        if not live_path.exists():
            logger.debug("File %s does not exist. Adding to restore list.", live_path)
            files_to_restore.append((live_path, storage_path))
        else:
            live_file_meta = file_hash_cache.get_file_meta(live_path)
            if live_file_meta:
                stat = live_path.stat()
                if (
                    live_file_meta["size"] != stat.st_size
                    or live_file_meta["mtime"] != stat.st_mtime
                ):
                    logger.debug(
                        "File %s has changed. Adding to restore list.", live_path
                    )
                    files_to_restore.append((live_path, storage_path))
                else:
                    logger.debug("File %s is already live. Skipping.", live_path)
            else:
                logger.debug(
                    "File %s is not in cache. Adding to restore list.", live_path
                )
                files_to_restore.append((live_path, storage_path))
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
    for swap_path in swap_paths:
        if (
            swap_path.exists()
            and swap_path.is_file()
            and not _is_excluded(swap_path, set(excluded_files), set(excluded_dirs))
            and swap_path not in target_paths
        ):
            logger.debug("Adding singlefile %s to remove list", swap_path)
            files_to_remove.append(swap_path)
        elif (
            swap_path.exists()
            and swap_path.is_dir()
            and not _is_excluded(swap_path, set(excluded_files), set(excluded_dirs))
        ):
            for root, _, files in swap_path.walk():
                for filename in files:
                    file_path = root / filename
                    # skip protected files and directories
                    if (
                        not _is_excluded(file_path, set(excluded_files), set(excluded_dirs))
                        and file_path not in target_paths
                    ):
                        files_to_remove.append(file_path)
    return files_to_remove


def load_profile_to_live(
    profile_name: str,
    file_hash_cache: FileHashCache,
    user_settings: UserSettings,
):
    # get files to restore and remove
    files_to_restore = _list_files_to_restore(profile_name, file_hash_cache)
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    files_to_remove = _list_files_to_remove(
        profile_name,
        user_settings.swap_paths,
        excluded_files=excluded_files,
        excluded_dirs=excluded_dirs,
    )
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

"""
functions to add

restore_directory(...)
build_manifest(...)
apply_manifest(...)


    manifest = {"version": 2, "targets": {}}

"""
