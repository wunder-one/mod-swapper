import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from constants import FILE_STORE_DIR

logger = logging.getLogger(__name__)


@dataclass
class BlobStore:
    store_dir: Path = FILE_STORE_DIR

    @staticmethod
    def _hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def hash_file(self, path: Path) -> str:
        """Compute the SHA-256 hash of *path* by reading its contents."""
        return self._hash(path)

    def _blob_path(self, file_hash: str) -> Path:
        return self.store_dir / file_hash[:2] / file_hash[2:]

    def store_file(self, source_path: Path) -> tuple[Path, bool]:
        """Store ``source_path`` as a content-addressed blob under ``store_dir``.

        Computes the file hash and ensures a blob exists for that hash.

        Args:
            source_path: File to ingest into the store.

        Returns:
            A tuple of ``(dest_rel, copied_to_store)``. ``dest_rel`` is the blob
            path relative to ``store_dir``. ``copied_to_store`` is True when this
            call wrote a new blob file, or False when the blob already existed.

        Raises:
            RuntimeError: If the blob is still missing after an attempted copy.
        """
        file_hash = self._hash(source_path)
        dest = self._blob_path(file_hash)
        dest_rel = dest.relative_to(self.store_dir)

        if dest.exists():
            logger.debug("File %s already in cache. Skipping copy.", source_path)
            return dest_rel, False

        tmp_path = self.store_dir / f"tmp.{file_hash[:16]}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        source_path.copy(tmp_path)
        tmp_path.rename(dest)
        if not dest.exists():
            raise RuntimeError("Failed to store file %s", source_path)
        logger.debug("Stored file %s as %s", source_path, dest_rel)
        return dest_rel, True

    def has_blob(self, file_hash: str) -> bool:
        return self._blob_path(file_hash).exists()
