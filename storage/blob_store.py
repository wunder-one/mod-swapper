import hashlib
import logging
import json
from dataclasses import dataclass
from pathlib import Path
from os import stat_result
from typing import NotRequired, TypedDict

from constants import FILE_STORE_DIR

logger = logging.getLogger(__name__)


class FileMeta(TypedDict):
    size: int
    mtime: float
    mtime_ns: NotRequired[int]
    hash: str


class CacheManifest(TypedDict):
    version: int
    entries: dict[str, FileMeta]


CACHE_VERSION = 2
SUPPORTED_CACHE_VERSIONS = {1, CACHE_VERSION}


@dataclass
class BlobStore:
    cache: dict[str, FileMeta]
    store_dir: Path = FILE_STORE_DIR

    @property
    def cache_file(self) -> Path:
        return self.store_dir / "file_store_cache.json"

    @classmethod
    def load_cache(cls, store_dir: Path = FILE_STORE_DIR) -> "BlobStore":
        cache = cls(cache={}, store_dir=store_dir)
        cache.store_dir.mkdir(parents=True, exist_ok=True)
        if not cache.cache_file.exists():
            return cache
        with cache.cache_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("version") in SUPPORTED_CACHE_VERSIONS and "entries" in data:
                entries = data["entries"]
            elif "version" in data and "entries" in data:
                logger.warning(
                    "Unsupported file store cache version %s. Rebuilding cache.",
                    data["version"],
                )
                return cache
            else:
                entries = data
            cache.cache = {k: FileMeta(**v) for k, v in entries.items()}
            return cache

    def save_cache(self):
        self.store_dir.mkdir(parents=True, exist_ok=True)
        manifest: CacheManifest = {"version": CACHE_VERSION, "entries": self.cache}
        with self.cache_file.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4, default=str)

    @staticmethod
    def _hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _file_meta(stat: stat_result, file_hash: str) -> FileMeta:
        return FileMeta(
            size=stat.st_size,
            mtime=stat.st_mtime,
            mtime_ns=stat.st_mtime_ns,
            hash=file_hash,
        )

    @staticmethod
    def _matches_stat(entry: FileMeta, stat: stat_result) -> bool:
        return (
            entry["size"] == stat.st_size
            and "mtime_ns" in entry
            and entry["mtime_ns"] == stat.st_mtime_ns
        )

    def get_cached_hash(self, path: Path) -> str:
        """Compute the SHA-256 hash of *path*, using the cache for performance.

        Returns the cached hash if the file's size and mtime_ns match the
        cache entry; otherwise hashes the file and stores it in the cache.
        """
        stat = path.stat()
        entry = self.cache.get(str(path))
        if entry and self._matches_stat(entry, stat):
            logger.debug("Cache hit for %s", path)
            return entry["hash"]
        file_hash = self._hash(path)
        self.cache[str(path)] = self._file_meta(stat, file_hash)
        return file_hash

    def get_file_meta(self, path: Path) -> FileMeta | None:
        entry = self.cache.get(str(path))
        if entry:
            return FileMeta(**entry)
        else:
            return None

    def _blob_path(self, file_hash: str) -> Path:
        return self.store_dir / file_hash[:2] / file_hash[2:]

    def store_file(self, source_path: Path) -> tuple[Path, bool]:
        """Store ``source_path`` as a content-addressed blob under ``store_dir``.

        Reuses cached hashes only when the file's size and mtime_ns match and
        the referenced blob already exists; otherwise hashes the source bytes.

        Args:
            source_path: File to ingest into the store.

        Returns:
            A tuple of ``(dest_rel, copied_to_store)``. ``dest_rel`` is the blob
            path relative to ``store_dir``. ``copied_to_store`` is True when this
            call wrote a new blob file, or False when the blob already existed.

        Raises:
            RuntimeError: If the blob is still missing after an attempted copy.
        """
        stat = source_path.stat()
        entry = self.cache.get(str(source_path))
        if entry and self._matches_stat(entry, stat) and self.has_blob(entry["hash"]):
            dest = self._blob_path(entry["hash"])
            logger.debug("Cache hit for %s. Skipping hash and copy.", source_path)
            return dest.relative_to(self.store_dir), False

        file_hash = self._hash(source_path)
        self.cache[str(source_path)] = self._file_meta(stat, file_hash)
        dest = self._blob_path(file_hash)
        dest_rel = dest.relative_to(self.store_dir)

        if dest.exists():
            logger.debug("File %s already in store. Skipping copy.", source_path)
            return dest_rel, False

        tmp_path = self.store_dir / f"tmp.{file_hash[:16]}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        source_path.copy(tmp_path)
        tmp_path.rename(dest)
        if not dest.exists():
            raise RuntimeError("Failed to store file %s", source_path)
        logger.debug("Stored file %s as %s", source_path, dest_rel)
        logger.debug("Added file %s to manifest", source_path)
        return dest_rel, True

    def has_blob(self, file_hash: str) -> bool:
        return self._blob_path(file_hash).exists()
