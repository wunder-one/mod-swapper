import hashlib
import logging
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from constants import FILE_STORE_DIR

logger = logging.getLogger(__name__)


class FileMeta(TypedDict):
    size: int
    mtime: float
    hash: str


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
            cache.cache = {k: FileMeta(**v) for k, v in data.items()}
            return cache

    def save_cache(self):
        self.store_dir.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=4, default=str)

    @staticmethod
    def _hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hash_and_cache(self, path: Path) -> str:
        stat = path.stat()
        entry = self.cache.get(str(path))
        if entry and entry["size"] == stat.st_size and entry["mtime"] == stat.st_mtime:
            logger.debug("Cache hit for %s", path)
            return entry["hash"]
        file_hash = self._hash(path)
        self.cache[str(path)] = FileMeta(
            size=stat.st_size, mtime=stat.st_mtime, hash=file_hash
        )
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

        Computes the file hash, ensures a blob exists for that hash, and updates
        the path metadata cache when a new blob file is written.

        Args:
            source_path: File to ingest into the store.

        Returns:
            A tuple of ``(dest_rel, copied_to_store)``. ``dest_rel`` is the blob
            path relative to ``store_dir``. ``copied_to_store`` is True when this
            call wrote a new blob file, or False when the blob already existed.

        Raises:
            RuntimeError: If the blob is still missing after an attempted copy.
        """
        file_hash = self._hash_and_cache(source_path)
        dest = self._blob_path(file_hash)
        dest_rel = dest.relative_to(self.store_dir)

        if dest.exists():
            logger.debug("File %s already in cache. Skipping copy.", source_path)
            return dest_rel, False

        tmp_path = self.store_dir / "tmp"
        dest.parent.mkdir(parents=True, exist_ok=True)
        source_path.copy(tmp_path)
        tmp_path.rename(dest)
        if not dest.exists():
            raise RuntimeError("Failed to store file %s", source_path)
        logger.debug("Stored file %s as %s", source_path, dest_rel)
        return dest_rel, True

    def has_blob(self, file_hash: str) -> bool:
        return self._blob_path(file_hash).exists()
