import logging
from pathlib import Path
import json
from collections.abc import Callable
from typing import Any, TypedDict

import functions.manifest as manifest_ops
from config.user_settings import UserSettings
from storage.blob_store import BlobStore
from config.profile_state import ProfileState
from functions.profile_ops import OnStoreFile, save_live_to_profile
from config.manifest import Manifest
from constants import PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


class Update(TypedDict):
    current_path: Path
    target_filename: str | None
    update_hash: str
    update_storage_path: Path
    prev_version64: int
    prev_version: str
    new_version64: int
    new_version: str
    mod_name: str
    mod_author: str
    mod_uuid: str


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


def _check_mod_for_update(
    mod_path: Path, global_manifest: Manifest, profile_manifest: dict[str, Any]
) -> Update | None:
    """
    Check if the mod has an update.
    """
    profile_targets = profile_manifest["targets"]
    live_hash = profile_targets.get(str(mod_path)).replace("\\", "").replace("/", "")
    mod_metadata = global_manifest["entries"][live_hash]["mod_metadata"]
    if mod_metadata:
        mod_uuid = mod_metadata.get("uuid")
        newest_so_far = live_hash
        for entry_hash, entry in global_manifest.get("entries").items():
            if entry_hash == live_hash:
                continue
            entry_mod_metadata = entry.get("mod_metadata")
            if not entry_mod_metadata:
                continue
            if entry_mod_metadata.get("uuid") == mod_uuid:
                if entry_mod_metadata.get("version64") > mod_metadata.get("version64"):
                    newest_so_far = entry_hash
        if newest_so_far != live_hash:
            update_hash = newest_so_far
            update_storage_path = Path(update_hash[:2]) / Path(update_hash[2:])
            update_entry = global_manifest["entries"][update_hash]
            update_filename = update_entry.get("filename")
            update_mod_metadata = update_entry.get("mod_metadata")
            if update_mod_metadata:
                mod_name = update_mod_metadata.get("name")
                mod_author = update_mod_metadata.get("author")
                mod_uuid = update_mod_metadata.get("uuid")
                prev_version64 = mod_metadata.get("version64")
                prev_version = mod_metadata.get("version")
                new_version64 = update_mod_metadata.get("version64")
                new_version = update_mod_metadata.get("version")
            else:
                mod_name = mod_metadata.get("name")
                mod_author = mod_metadata.get("author")
                mod_uuid = mod_metadata.get("uuid")
                prev_version64 = mod_metadata.get("version64")
                prev_version = mod_metadata.get("version")
                new_version64 = 0
                new_version = ""
                logger.error(f"Mod metadata not found for {mod_path}")
            return Update(
                current_path=mod_path,
                target_filename=update_filename,
                update_hash=update_hash,
                update_storage_path=update_storage_path,
                prev_version64=prev_version64,
                prev_version=prev_version,
                new_version64=new_version64,
                new_version=new_version,
                mod_name=mod_name,
                mod_author=mod_author,
                mod_uuid=mod_uuid,
            )
    return None


def _collect_pak_files(
    user_settings: UserSettings,
    excluded_files: set[Path],
    excluded_dirs: set[Path],
) -> list[Path]:
    pak_files: list[Path] = []
    for swap_path in user_settings.get_swap_paths():
        if not swap_path.is_dir():
            continue
        for root, _, files in swap_path.walk():
            for file in files:
                file_path = root / file
                if _is_excluded(file_path, excluded_files, excluded_dirs):
                    continue
                if file_path.is_file() and file_path.suffix == ".pak":
                    pak_files.append(file_path)
    return pak_files


def list_updates(
    profile_state: ProfileState,
    blob_store: BlobStore,
    user_settings: UserSettings,
    on_progress: Callable[..., None] | None = None,
    on_file: OnStoreFile | None = None,
) -> list[Update]:
    """
    List all updates for the current profile.
    """

    def report(
        message: str,
        *,
        progress: float | None = None,
        update: Update | None = None,
    ) -> None:
        if on_progress is not None:
            on_progress(message, progress=progress, update=update)

    logger.info(f"Saving active profile to snapshot: {profile_state.active_profile}")
    report("Saving current mods to profile...", progress=0.0)
    save_live_to_profile(
        profile_state.active_profile,
        blob_store,
        user_settings,
        on_file=on_file,
    )
    updates: list[Update] = []

    report("Preparing update scan...", progress=0.05)
    logger.debug("Loading global manifest")
    global_manifest = manifest_ops.load_global_manifest()
    logger.debug("Loading profile manifest")
    profile_manifest_file = (
        PROFILES_SNAPSHOT_DIR / profile_state.active_profile / "manifest.json"
    )
    with profile_manifest_file.open("r", encoding="utf-8") as f:
        profile_manifest = json.load(f)

    logger.debug("Getting excluded files and directories")
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    pak_files = _collect_pak_files(
        user_settings, set(excluded_files), set(excluded_dirs)
    )
    total_paks = len(pak_files)

    if total_paks == 0:
        report("No mod files to check.", progress=1.0)
        return updates

    report(f"Scanning {total_paks} mod file(s)...", progress=0.1)
    for index, file_path in enumerate(pak_files, start=1):
        progress = 0.1 + (0.9 * index / total_paks)
        report(f"Checking {file_path.name}...", progress=progress)
        update_info = _check_mod_for_update(
            file_path, global_manifest, profile_manifest
        )
        if update_info:
            updates.append(update_info)
            logger.info(f"Update found for {file_path}: {update_info['update_hash']}")
            report(
                f"Update found: {update_info['mod_name']} "
                f"({update_info['prev_version']} -> {update_info['new_version']})",
                progress=progress,
                update=update_info,
            )
        else:
            logger.info(f"No update found for {file_path}")

    report(f"Done — {len(updates)} update(s) found.", progress=1.0)
    return updates


def copy_updates(
    updates: list[Update],
    blob_store: BlobStore,
    on_progress: Callable[..., None] | None = None,
) -> None:
    """
    Copy the updates to live mod paths.
    """
    total = len(updates)

    def report(message: str, *, progress: float | None = None) -> None:
        if on_progress is not None:
            on_progress(message, progress=progress)

    for index, update in enumerate(updates, start=1):
        current_path = update["current_path"]
        target_name = update["target_filename"] or current_path.name
        target_path = current_path.parent / target_name
        storage_path = blob_store.store_dir / update["update_storage_path"]

        if not storage_path.exists():
            raise FileNotFoundError(
                f"Update blob missing for {current_path}: {storage_path}"
            )

        progress = index / total if total else 1.0
        report(f"Updating {target_name}...", progress=progress)

        tmp_path = target_path.parent / f"{target_name}.tmp-update"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.copy(tmp_path, follow_symlinks=False, preserve_metadata=True)
        tmp_path.replace(target_path)

        if target_path != current_path:
            current_path.unlink(missing_ok=True)

    report("Done.", progress=1.0)
