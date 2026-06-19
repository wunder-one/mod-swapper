from typing import TypedDict
from config.mod_metadata import ModMetadata


class ManifestEntry(TypedDict):
    filename: str | None
    size: int
    mod_metadata: ModMetadata | None


class Manifest(TypedDict):
    version: int
    entries: dict[str, ManifestEntry]  # hash -> entry
