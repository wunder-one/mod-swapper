import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from functions.file_hash_cache import FileHashCache


class FileHashCacheMtimeTests(unittest.TestCase):
    def test_get_hash_uses_cache_when_file_is_unchanged(self):
        # Create an isolated temporary filesystem for the test.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # This file stands in for a mod file whose hash we cache.
            source_file = root / "mod.txt"
            source_file.write_text("v1", encoding="utf-8")

            # Load a cache instance backed by a temporary store directory.
            cache = FileHashCache.load_cache(store_dir=root / "store")

            # Wrap _hash_file so we can count real hash computations.
            with patch.object(
                FileHashCache, "_hash_file", wraps=FileHashCache._hash_file
            ) as hash_mock:
                # First call computes and caches the hash.
                first_hash = cache.get_hash(source_file)
                # Second call should reuse cached value because file is unchanged.
                second_hash = cache.get_hash(source_file)

            # Cached value should match the original computed hash.
            self.assertEqual(first_hash, second_hash)
            # Only one underlying hash computation should have happened.
            self.assertEqual(hash_mock.call_count, 1)

    def test_get_hash_recomputes_when_file_mtime_changes(self):
        # Create an isolated temporary filesystem for the test.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Initial file contents represent the first file state.
            source_file = root / "mod.txt"
            source_file.write_text("v1", encoding="utf-8")

            # Prime the cache with the file's initial hash and mtime.
            cache = FileHashCache.load_cache(store_dir=root / "store")
            first_hash = cache.get_hash(source_file)

            # Ensure the next write gets a distinct mtime on Windows filesystems.
            time.sleep(0.02)
            # Change file contents so the hash should become different.
            source_file.write_text("v2", encoding="utf-8")

            # Wrap _hash_file so we can confirm recomputation occurs.
            with patch.object(
                FileHashCache, "_hash_file", wraps=FileHashCache._hash_file
            ) as hash_mock:
                # Cache should detect mtime change and re-hash the file.
                second_hash = cache.get_hash(source_file)

            # Exactly one hash call during this second get_hash invocation.
            self.assertEqual(hash_mock.call_count, 1)
            # New content should produce a different hash value.
            self.assertNotEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()
