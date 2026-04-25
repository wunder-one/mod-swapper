import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from functions.file_hash_cache import FileHashCache


class FileHashCacheMtimeTests(unittest.TestCase):
    def test_get_hash_uses_cache_when_file_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "mod.txt"
            source_file.write_text("v1", encoding="utf-8")

            cache = FileHashCache.load_cache(store_dir=root / "store")

            with patch.object(
                FileHashCache, "_hash_file", wraps=FileHashCache._hash_file
            ) as hash_mock:
                first_hash = cache.get_hash(source_file)
                second_hash = cache.get_hash(source_file)

            self.assertEqual(first_hash, second_hash)
            self.assertEqual(hash_mock.call_count, 1)

    def test_get_hash_recomputes_when_file_mtime_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "mod.txt"
            source_file.write_text("v1", encoding="utf-8")

            cache = FileHashCache.load_cache(store_dir=root / "store")
            first_hash = cache.get_hash(source_file)

            # Ensure the next write gets a distinct mtime on Windows filesystems.
            time.sleep(0.02)
            source_file.write_text("v2", encoding="utf-8")

            with patch.object(
                FileHashCache, "_hash_file", wraps=FileHashCache._hash_file
            ) as hash_mock:
                second_hash = cache.get_hash(source_file)

            self.assertEqual(hash_mock.call_count, 1)
            self.assertNotEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()
