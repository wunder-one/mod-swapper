import logging
import json
from pathlib import Path

from constants import PROFILES_SNAPSHOT_DIR
from functions.blob_store import BlobStore

logger = logging.getLogger(__name__)


def migrate_file_store(blob_store: BlobStore):
    try:
        if PROFILES_SNAPSHOT_DIR.is_dir() and any(
            child.is_dir() for child in PROFILES_SNAPSHOT_DIR.iterdir()
        ):
            pass
    except Exception:
        logger.info("No profiles to migrate.")
        return
    logger.info("Migrating file store...")
    for child in PROFILES_SNAPSHOT_DIR.iterdir():
        if child.is_dir():
            try:
                migrate_profile(child, blob_store)
            except Exception as e:
                logger.error("Failed to migrate %s profile: %s", child.name, e)
                raise


def migrate_profile(profile_path: Path, blob_store: BlobStore):
    logger.info("Migrating profile %s...", profile_path.name)
    try:
        profile_manifest_file = profile_path / "manifest.json"
        if not profile_manifest_file.exists():
            logger.error("Profile %s has no manifest file.", profile_path.name)
            return
        with profile_manifest_file.open("r", encoding="utf-8") as f:
            v1_manifest = json.load(f)
        if v1_manifest["version"] > 1:
            logger.info("Profile %s is already migrated.", profile_path.name)
            return
        v2_manifest = {"version": 2, "targets": {}}
        for source_path_str, v1_storage_path_str, type in v1_manifest[
            "targets"
        ].items():
            source_path = Path(source_path_str)
            v1_storage_path = Path(v1_storage_path_str)
            if type == "file":
                logger.info("Migrating file %s...", source_path.name)
                manifest_additions = migrate_file(
                    source_path, v1_storage_path, blob_store
                )
            elif type == "directory":
                logger.info("Migrating directory %s...", source_path.name)
                manifest_additions = migrate_directory(
                    source_path, v1_storage_path, blob_store
                )
            else:
                logger.warning("Unknown type %s for file %s.", type, source_path.name)
            v2_manifest["targets"].update(manifest_additions)
        with profile_manifest_file.open("w", encoding="utf-8") as f:
            json.dump(v2_manifest, f, indent=4, default=str)
    except Exception as e:
        logger.error("Failed to migrate profile %s: %s", profile_path.name, e)
        raise


def migrate_file(
    source_path: Path,
    v1_storage_path: Path,
    blob_store: BlobStore,
) -> dict:
    manifest_additions = {}
    dest_rel, copied_to_store = blob_store.store_file(v1_storage_path)
    if copied_to_store:
        logger.info("Copied file %s to store", v1_storage_path)
    else:
        logger.info("File %s already in store", v1_storage_path)
    manifest_additions[str(source_path)] = str(dest_rel)
    return manifest_additions


def migrate_directory(
    source_path: Path,
    v1_storage_path: Path,
    blob_store: BlobStore,
) -> dict:
    logger.debug("Migrating directory %s...", source_path.name)
    manifest_additions = {}
    skipped_files_count = 0
    copied_files_count = 0
    for root, _, files in v1_storage_path.walk():
        for filename in files:
            v1_storage_file_path = root / filename
            source_file_path = source_path / v1_storage_file_path.relative_to(
                v1_storage_path
            )

            # store file in hashed store
            blob_store_rel, copied_to_store = blob_store.store_file(
                v1_storage_file_path
            )
            logger.debug(
                "Stored file %s as %s",
                v1_storage_file_path.relative_to(v1_storage_path),
                blob_store_rel,
            )
            if copied_to_store:
                copied_files_count += 1
            else:
                skipped_files_count += 1
            # add file to manifest
            manifest_additions[str(source_file_path)] = str(blob_store_rel)
    logger.info(
        " - Stored directory %s:\n"
        "     %d copied files\n"
        "     %d already stored files (skipped)",
        v1_storage_path,
        copied_files_count,
        skipped_files_count,
    )
    return manifest_additions

def _cleanup_v1_profile_data(profile_path: Path) -> None:
    # Verify manifest is valid V2 before cleanup
    try:
        profile_manifest_file = profile_path / "manifest.json"
        with profile_manifest_file.open("r", encoding="utf-8") as f:
            written = json.load(f)
        if written.get("version") != 2:
            logger.error("Manifest verification failed for %s; skipping cleanup", profile_path.name)
            return
        # delete all files and directories in profile except manifest
        for child in profile_path.iterdir():  
            if child == profile_manifest_file:
                continue
            child.unlink()
    except Exception:
        logger.error("Failed to cleanup V1 profile data for %s", profile_path.name)
        raise
    logger.info("Cleaned up V1 profile data for %s", profile_path.name)