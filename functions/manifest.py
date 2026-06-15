from config.manifest import Manifest, ManifestEntry
from functions.divine import read_mod_metadata
from pathlib import Path
import json
import logging

from constants import FILE_STORE_DIR

logger = logging.getLogger(__name__)

def load() -> Manifest:
    manifest_path = FILE_STORE_DIR / "manifest.json"
    if not manifest_path.exists():
        return Manifest(version=1, entries={})
    with manifest_path.open("r") as f:
        return Manifest(**json.load(f))
            
def save(manifest: Manifest) -> None:
    manifest_path = FILE_STORE_DIR / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=4)

def add_entry(hash: str, entry: ManifestEntry, manifest: Manifest) -> None:
    manifest["entries"][hash] = entry

def update_manifest() -> Manifest:
    manifest = load()

    all_files = [file for dir in FILE_STORE_DIR.iterdir() if dir.is_dir() for file in dir.iterdir() if file.is_file()]
    total = len(all_files)
    processed = 0

    for i, file in enumerate(all_files, 1):
        hash = file.parent.name + file.name
        processed += 1

        if hash in manifest["entries"]:
            # entry = manifest["entries"][hash]
            # meta = entry.get("mod_metadata")
            # label = meta["name"] if meta else file.name
            # print(f"[{processed}/{total}] Skipping {label}")
            continue
        
        mod_metadata = read_mod_metadata(file)
        if mod_metadata:
            print(f"[{processed}/{total}] Adding {mod_metadata['name']}...")
        else:
            logger.debug("Failed to read mod metadata for %s, skipping...", file)
            print(f"[{processed}/{total}] No metadata for {file.parent.name}/{file.name}")
        manifest_entry: ManifestEntry = {
            "size": file.stat().st_size,
            "mod_metadata": mod_metadata if mod_metadata else None,
        }
        
        add_entry(hash, manifest_entry, manifest)

    if processed == 0:
        print("Manifest is already up to date.")
    save(manifest)
    return manifest