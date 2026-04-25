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
class FileHashCache:
    cache: dict[str, FileMeta]
    store_dir: Path = FILE_STORE_DIR

    @property
    def cache_file(self) -> Path:
        return self.store_dir / "file_store_cache.json"

    @classmethod
    def load_cache(cls, store_dir: Path = FILE_STORE_DIR) -> "FileHashCache":
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
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_hash(self, path: Path) -> str:
        stat = path.stat()
        entry = self.cache.get(str(path))
        logger.debug("Getting hash for %s from cache", path)
        if entry and entry["size"] == stat.st_size and entry["mtime"] == stat.st_mtime:
            return entry["hash"]
        file_hash = self._hash_file(path)
        self.cache[str(path)] = FileMeta(
            size=stat.st_size, mtime=stat.st_mtime, hash=file_hash
        )
        return file_hash

    def _blob_path(self, file_hash: str) -> Path:
        return self.store_dir / file_hash[:2] / file_hash[2:]

    def store_file(self, source_path: Path) -> Path:
        file_hash = self.get_hash(source_path)
        dest = self._blob_path(file_hash)
        dest_rel = dest.relative_to(self.store_dir)

        if dest.exists():
            logger.debug("File %s already in cache. Skipping copy.", source_path)
            return dest_rel

        tmp_path = self.store_dir / "tmp"
        dest.parent.mkdir(parents=True, exist_ok=True)
        source_path.copy(tmp_path)
        tmp_path.rename(dest)
        if not dest.exists():
            raise RuntimeError("Failed to store file %s", source_path)
        dest_stat = dest.stat()
        self.cache[str(source_path)] = FileMeta(
            size=dest_stat.st_size, mtime=dest_stat.st_mtime, hash=file_hash
        )
        return dest_rel

    def has_blob(self, file_hash: str) -> bool:
        return self._blob_path(file_hash).exists()
