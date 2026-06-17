import logging
from pathlib import Path
import json
from typing import Any, TypedDict

from config import mod_metadata
import functions.manifest as manifest_ops
from config.user_settings import UserSettings
from storage.blob_store import BlobStore
from config.profile_state import ProfileState
from functions.profile_ops import save_live_to_profile
from config.manifest import Manifest, ManifestEntry
from constants import PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


class Update(TypedDict):
    target_path: Path
    update_hash: str
    update_path: Path
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
            update_path = Path(update_hash[:2]) / Path(update_hash[2:])
            update_entry = global_manifest["entries"][update_hash]
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
                target_path=mod_path,
                update_hash=update_hash,
                update_path=update_path,
                prev_version64=prev_version64,
                prev_version=prev_version,
                new_version64=new_version64,
                new_version=new_version,
                mod_name=mod_name,
                mod_author=mod_author,
                mod_uuid=mod_uuid,
            )
    return None





def list_updates(
    profile_state: ProfileState, blob_store: BlobStore, user_settings: UserSettings
) -> list[Update]:
    """
    List all updates for the current profile.
    """
    logger.info(f"Saving active profile to snapshot: {profile_state.active_profile}")
    save_live_to_profile(profile_state.active_profile, blob_store, user_settings)
    updates: list[Update] = []

    logger.debug("Loading global manifest")
    global_manifest = manifest_ops.load()
    logger.debug("Loading profile manifest")
    profile_manifest_file = (
        PROFILES_SNAPSHOT_DIR / profile_state.active_profile / "manifest.json"
    )
    with profile_manifest_file.open("r", encoding="utf-8") as f:
        profile_manifest = json.load(f)

    logger.debug("Getting excluded files and directories")
    excluded_files, excluded_dirs = user_settings.get_all_protected_paths()
    logger.debug("Getting swap paths")
    for swap_path in user_settings.get_swap_paths():
        if swap_path.is_dir():
            for root, _, files in swap_path.walk():
                for file in files:
                    file_path = root / file
                    if _is_excluded(file_path, set(excluded_files), set(excluded_dirs)):
                        continue
                    if file_path.is_file() and file_path.suffix == ".pak":
                        update_info = _check_mod_for_update(
                            file_path, global_manifest, profile_manifest
                        )
                        if update_info:
                            updates.append(update_info)
                            logger.info(f"Update found for {file_path}: {update_info['update_hash']}")
                        else:
                            logger.info(f"No update found for {file_path}")
    return updates
