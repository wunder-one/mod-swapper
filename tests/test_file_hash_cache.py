import tempfile
import time
import unittest
from pathlib import Path

from functions.blob_store import BlobStore


class BlobStoreCacheTests(unittest.TestCase):
    def test_store_file_dedup_reuses_existing_blob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore(store_dir=root / "store")

            src1 = root / "src.txt"
            src1.write_text("same content", encoding="utf-8")

            dest_rel1, copied1 = store.store_file(src1)
            self.assertTrue(copied1, "first store should copy")

            src2 = root / "src-dup.txt"
            src2.write_text("same content", encoding="utf-8")

            dest_rel2, copied2 = store.store_file(src2)
            self.assertFalse(copied2, "duplicate content should not copy")
            self.assertEqual(dest_rel1, dest_rel2, "blob path should match")

    def test_modified_content_produces_different_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore(store_dir=root / "store")

            src = root / "mod.txt"
            src.write_text("v1", encoding="utf-8")

            dest_rel1, copied1 = store.store_file(src)
            self.assertTrue(copied1)

            time.sleep(0.02)
            src.write_text("v2", encoding="utf-8")

            dest_rel2, copied2 = store.store_file(src)
            self.assertTrue(copied2)
            self.assertNotEqual(dest_rel1, dest_rel2)


if __name__ == "__main__":
    unittest.main()
