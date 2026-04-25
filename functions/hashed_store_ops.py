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
    exclude_dirs: set[Path],
) -> bool:
    if file_path in excluded_files or file_path.parent in exclude_dirs:
        return True
    for excluded_dir in exclude_dirs:
        if file_path.is_relative_to(excluded_dir):
            return True
    return False


def store_directory(
    source_dir: Path,
    file_hash_cache: FileHashCache,
    excluded_files: list[Path] | None = None,
    exclude_dirs: list[Path] | None = None,
) -> dict[str, str]:
    logger.debug("Storing directory: %s", source_dir)
    if excluded_files is None:
        excluded_files = list[Path]()
    if exclude_dirs is None:
        exclude_dirs = list[Path]()
    manifest = {}
    for root, _, files in source_dir.walk():
        for filename in files:
            file_path = root / filename
            # skip protected files and directories
            if _is_excluded(file_path, set(excluded_files), set(exclude_dirs)):
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
    exclude_dirs: list[Path] | None = None,
) -> dict[str, str]:
    if excluded_files is None:
        excluded_files = list[Path]()
    if exclude_dirs is None:
        exclude_dirs = list[Path]()
    if _is_excluded(source_path, set(excluded_files), set(exclude_dirs)):
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
                    exclude_dirs=excluded_dirs,
                )
            if live_path.is_file():
                manifest_additions = store_file(
                    live_path,
                    file_hash_cache,
                    excluded_files=excluded_files,
                    exclude_dirs=excluded_dirs,
                )
            manifest["targets"].update(manifest_additions)
        else:
            logger.warning("Live path does not exist: %s", live_path)

    json_data = json.dumps(manifest, indent=4, default=str)
    manifest_file = PROFILES_SNAPSHOT_DIR / profile_name / "manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json_data, encoding="utf-8")


"""
functions to add

restore_directory(...)
build_manifest(...)
apply_manifest(...)


    manifest = {"version": 2, "targets": {}}

"""
