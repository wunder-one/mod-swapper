import logging
import json
from pathlib import Path

from constants import PROFILES_SNAPSHOT_DIR
from functions.blob_store import BlobStore
from ui.migration_progress import MigrationProgress

logger = logging.getLogger(__name__)


class MigrationCancelledError(Exception):
    """Raised when the user cancels the migration from the progress dialog."""


def migrate_file_store(
    blob_store: BlobStore,
    migration_progress_window: MigrationProgress | None = None,
):
    # Verification
    if not PROFILES_SNAPSHOT_DIR.is_dir():
        logger.info("No profiles directory; nothing to migrate.")
        return
    profiles = []
    try:
        profiles = [p for p in PROFILES_SNAPSHOT_DIR.iterdir() if p.is_dir()]
    except OSError as e:
        logger.warning("Could not list profiles directory: %s", e)
        return
    if not profiles:
        logger.info("No profiles to migrate.")
        return
    logger.info("Migrating file store...")

    # Start Migration
    if migration_progress_window is not None:
        migration_progress_window.set_total_profiles(len(profiles))
    failed = []
    for i, profile in enumerate(profiles):
        if migration_progress_window is not None:
            if migration_progress_window.check_cancelled():
                raise MigrationCancelledError()
            migration_progress_window.update_progress(i)
            migration_progress_window.set_status(
                f"Processing profile {profile.name}..."
            )
        try:
            migrate_profile(profile, blob_store, migration_progress_window)
        except MigrationCancelledError:
            raise
        except Exception as e:
            logger.error("Failed to migrate %s profile: %s", profile.name, e)
            failed.append(profile.name)
    if migration_progress_window is not None:
        migration_progress_window.update_progress(len(profiles))
        migration_progress_window.set_status("Migration complete!")
    if failed:
        raise RuntimeError(
            "Failed to migrate %d profile(s): %s" % (len(failed), ", ".join(failed))
        )


def migrate_profile(
    profile_path: Path,
    blob_store: BlobStore,
    progress_window: MigrationProgress | None = None,
):
    logger.info("Migrating profile %s...", profile_path.name)
    profile_manifest_file = profile_path / "manifest.json"
    legacy_manifest_file = profile_path / "manifest.json.legacy"
    needs_cleanup = False

    try:
        if legacy_manifest_file.exists():
            try:
                with profile_manifest_file.open("r", encoding="utf-8") as f:
                    existing = json.load(f)
                if existing.get("version") == 2:
                    needs_cleanup = True
            except json.JSONDecodeError, OSError:
                pass

        if not needs_cleanup:
            if legacy_manifest_file.exists():
                logger.info(
                    "Restoring legacy manifest for %s and retrying migration.",
                    profile_path.name,
                )
                if profile_manifest_file.exists():
                    profile_manifest_file.unlink()
                legacy_manifest_file.replace(profile_manifest_file)

            if not profile_manifest_file.exists():
                raise ValueError("Profile %s has no manifest file." % profile_path.name)
            with profile_manifest_file.open("r", encoding="utf-8") as f:
                v1_manifest = json.load(f)
            if v1_manifest["version"] > 1:
                logger.info("Profile %s is already migrated.", profile_path.name)
                return
            v2_manifest = {"version": 2, "targets": {}}
            for target in v1_manifest["targets"]:
                if progress_window is not None and progress_window.check_cancelled():
                    raise MigrationCancelledError()
                try:
                    source_path = Path(target["source"])
                    v1_storage_path = Path(target["storage"])
                    target_type = target["type"]
                    if target_type == "file":
                        logger.info("Migrating file %s...", source_path.name)
                        manifest_additions = migrate_file(
                            source_path, v1_storage_path, blob_store, progress_window
                        )
                    elif target_type == "directory":
                        logger.info("Migrating directory %s...", source_path.name)
                        manifest_additions = migrate_directory(
                            source_path, v1_storage_path, blob_store, progress_window
                        )
                    else:
                        logger.warning(
                            "Unknown type %s for file %s.",
                            target_type,
                            source_path.name,
                        )
                        manifest_additions = {}
                    v2_manifest["targets"].update(manifest_additions)
                except MigrationCancelledError:
                    raise
                except Exception as e:
                    logger.warning(
                        "Skipping target %s: %s", target.get("source", "unknown"), e
                    )

            profile_manifest_file.rename(legacy_manifest_file)
            with profile_manifest_file.open("w", encoding="utf-8") as f:
                json.dump(v2_manifest, f, indent=4, default=str)
            needs_cleanup = True
    except MigrationCancelledError:
        raise
    except Exception as e:
        logger.error("Failed to migrate profile %s: %s", profile_path.name, e)
        raise

    if needs_cleanup:
        _cleanup_v1_profile_data(profile_path)


def migrate_file(
    source_path: Path,
    v1_storage_path: Path,
    blob_store: BlobStore,
    progress_window: MigrationProgress | None = None,
) -> dict:
    if progress_window is not None and progress_window.check_cancelled():
        raise MigrationCancelledError()
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
    progress_window: MigrationProgress | None = None,
) -> dict:
    logger.debug("Migrating directory %s...", source_path.name)
    manifest_additions = {}
    skipped_files_count = 0
    copied_files_count = 0
    for root, _, files in v1_storage_path.walk():
        for filename in files:
            if progress_window is not None and progress_window.check_cancelled():
                raise MigrationCancelledError()
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
        "Stored directory %s:\n"
        "     %d copied files\n"
        "     %d already stored files (skipped)",
        source_path,
        copied_files_count,
        skipped_files_count,
    )
    return manifest_additions


def _cleanup_v1_profile_data(profile_path: Path) -> None:
    profile_manifest_file = profile_path / "manifest.json"
    legacy_manifest_file = profile_path / "manifest.json.legacy"
    try:
        with profile_manifest_file.open("r", encoding="utf-8") as f:
            written = json.load(f)
        if written.get("version") != 2:
            logger.error(
                "Manifest verification failed for %s; skipping cleanup",
                profile_path.name,
            )
            return
        for child in profile_path.iterdir():
            if child in (profile_manifest_file, legacy_manifest_file):
                continue
            if not child.is_dir():
                child.unlink(missing_ok=True)
                continue
            for root, dirs, files in child.walk(top_down=False):
                for name in files:
                    (root / name).unlink(missing_ok=True)
                for name in dirs:
                    try:
                        (root / name).rmdir()
                    except FileNotFoundError, OSError:
                        pass
            try:
                child.rmdir()
            except FileNotFoundError, OSError:
                pass
    except Exception:
        logger.error("Failed to cleanup V1 profile data for %s", profile_path.name)
        raise
    legacy_manifest_file.unlink(missing_ok=True)
    logger.info("Cleaned up V1 profile data for %s", profile_path.name)
