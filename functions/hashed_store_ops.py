import logging
from pathlib import Path
from functions.file_hash_cache import FileHashCache
from config.user_settings import UserSettings

logger = logging.getLogger(__name__)


def _is_excluded(
    file_path: Path, excluded_files: set[Path], exclude_dirs: set[Path]
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
    excluded_files: set[Path] | None = None,
    exclude_dirs: set[Path] | None = None,
):
    logger.debug("Storing directory: %s", source_dir)
    if excluded_files is None:
        excluded_files = set[Path]()
    if exclude_dirs is None:
        exclude_dirs = set[Path]()
    manifest = {}
    for root, _, files in source_dir.walk():
        for filename in files:
            file_path = root / filename

            if _is_excluded(file_path, excluded_files, exclude_dirs):
                logger.debug(
                    "File %s is excluded. Skipping.", file_path.relative_to(source_dir)
                )
                continue

            dest_rel = file_hash_cache.store_file(file_path)
            logger.debug(
                "Stored file %s as %s", file_path.relative_to(source_dir), dest_rel
            )
            manifest[str(file_path)] = str(dest_rel)
    return manifest

def store_file(
    source_path: Path,
    file_hash_cache: FileHashCache,
    excluded_files: set[Path] | None = None,
    exclude_dirs: set[Path] | None = None,
):
    if excluded_files is None:
        excluded_files = set[Path]()
    if exclude_dirs is None:
        exclude_dirs = set[Path]()
    if _is_excluded(source_path, excluded_files, exclude_dirs):
        return {}
    dest_rel = file_hash_cache.store_file(source_path)
    return {str(source_path): str(dest_rel)}

def save_live_to_profile(
    profile_name: str,
    file_hash_cache: FileHashCache,
    user_settings: UserSettings,
):
    pass

"""
functions to add

restore_directory(...)
build_manifest(...)
apply_manifest(...)


    manifest = {"version": 2, "targets": {}}

"""
