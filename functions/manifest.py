from collections.abc import Callable
from typing import Any
from config.manifest import Manifest, ManifestEntry
from functions.divine import read_mod_metadata
from pathlib import Path
import json
import logging

from constants import FILE_STORE_DIR, PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


class UpdateCancelled(Exception):
    """Raised when a cancellable manifest update is aborted by the user."""


def load_global_manifest() -> Manifest:
    manifest_path = FILE_STORE_DIR / "manifest.json"
    if not manifest_path.exists():
        return Manifest(version=1, entries={})
    with manifest_path.open("r") as f:
        return Manifest(**json.load(f))


def load_profile_manifest(profile_path: Path) -> dict[str, Any]:
    manifest_path = profile_path / "manifest.json"
    with manifest_path.open("r") as f:
        return json.load(f)


def create_filename_hash_dict() -> dict[str, str]:  # [hash: filename]
    filename_hash_dict = {}
    for profile_dir in PROFILES_SNAPSHOT_DIR.iterdir():
        if not profile_dir.is_dir():
            continue
        manifest_dict = load_profile_manifest(profile_dir)
        for path_str, blob_path_str in manifest_dict["targets"].items():
            filename = Path(path_str).name
            hash = blob_path_str.replace("\\", "").replace("/", "")
            if hash not in filename_hash_dict:
                filename_hash_dict[hash] = filename
    return filename_hash_dict


def save_global_manifest(manifest: Manifest) -> None:
    manifest_path = FILE_STORE_DIR / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=4)


def add_global_manifest_entry(
    global_manifest: Manifest,
    hash: str,
    source_path: Path,
    size: int | None = None,
) -> Manifest:
    if hash not in global_manifest["entries"]:
        mod_metadata = read_mod_metadata(source_path)
        if size is None:
            size = source_path.stat().st_size
        global_manifest["entries"][hash] = {
            "filename": source_path.name,
            "size": size,
            "mod_metadata": mod_metadata if mod_metadata else None,
        }
    return global_manifest


def update_manifest(
    on_progress: Callable[..., None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    on_commit: Callable[[], None] | None = None,
) -> Manifest:
    def report(message: str, *, progress: float) -> None:
        if on_progress is not None:
            on_progress(message, progress=progress)

    def check_cancelled() -> None:
        if should_cancel is not None and should_cancel():
            raise UpdateCancelled()

    def commit_and_save() -> None:
        check_cancelled()
        if on_commit is not None:
            on_commit()
        save_global_manifest(manifest)

    manifest = load_global_manifest()

    all_files = [
        file
        for dir in FILE_STORE_DIR.iterdir()
        if dir.is_dir()
        for file in dir.iterdir()
        if file.is_file()
    ]
    total = len(all_files)
    filename_hash_dict = create_filename_hash_dict()

    if total == 0:
        report("Manifest is already up to date.", progress=1.0)
        check_cancelled()
        commit_and_save()
        return manifest

    for index, file in enumerate(all_files, start=1):
        check_cancelled()
        hash = file.parent.name + file.name
        progress = index / total

        if hash in manifest["entries"]:
            mod_metadata = manifest["entries"][hash].get("mod_metadata", {})
            if mod_metadata:
                mod_name = mod_metadata.get("name")
            else:
                mod_name = file.parent.name + file.name
            report(f"Checking {mod_name}...", progress=progress)
        else:
            filename = filename_hash_dict.get(hash)
            mod_metadata = read_mod_metadata(file)
            if mod_metadata:
                mod_name = mod_metadata.get("name")
                report(f"Adding {mod_name}...", progress=progress)
            else:
                report(f"Adding {filename}...", progress=progress)

            manifest_entry: ManifestEntry = {
                "filename": filename,
                "size": file.stat().st_size,
                "mod_metadata": mod_metadata if mod_metadata else None,
            }

            manifest["entries"][hash] = manifest_entry

    commit_and_save()
    return manifest
