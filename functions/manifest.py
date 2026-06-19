from typing import Any
from config.manifest import Manifest, ManifestEntry
from functions.divine import read_mod_metadata
from pathlib import Path
import json
import logging

from constants import FILE_STORE_DIR, PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


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


def save(manifest: Manifest) -> None:
    manifest_path = FILE_STORE_DIR / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=4)


def add_manifest_entry(hash: str, source_path: Path, size: int) -> None:
    mod_metadata = read_mod_metadata(source_path)
    manifest = load_global_manifest()
    manifest["entries"][hash] = {
        "filename": source_path.name,
        "size": size,
        "mod_metadata": mod_metadata if mod_metadata else None,
    }
    save(manifest)


def update_manifest() -> Manifest:
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
    processed = 0

    for i, file in enumerate(all_files, 1):
        hash = file.parent.name + file.name
        processed += 1

        if hash in manifest["entries"]:
            continue

        
        mod_metadata = read_mod_metadata(file)
        if mod_metadata:
            print(f"[{processed}/{total}] Adding {mod_metadata['name']}...")
        else:
            logger.debug("Failed to read mod metadata for %s, skipping...", file)
            print(
                f"[{processed}/{total}] No metadata for {file.parent.name}/{file.name}"
            )
        filename = filename_hash_dict.get(hash)
        manifest_entry: ManifestEntry = {
            "filename": filename,
            "size": file.stat().st_size,
            "mod_metadata": mod_metadata if mod_metadata else None,
        }

        manifest["entries"][hash] = manifest_entry

    if processed == 0:
        print("Manifest is already up to date.")
    save(manifest)
    return manifest
