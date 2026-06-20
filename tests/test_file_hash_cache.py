import time

from storage.blob_store import BlobStore


def test_store_file_dedup_reuses_existing_blob(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src1 = tmp_path / "src.txt"
    src1.write_text("same content", encoding="utf-8")

    dest_rel1, copied1 = store.store_file(src1)
    assert copied1, "first store should copy"

    src2 = tmp_path / "src-dup.txt"
    src2.write_text("same content", encoding="utf-8")

    dest_rel2, copied2 = store.store_file(src2)
    assert not copied2, "duplicate content should not copy"
    assert dest_rel1 == dest_rel2, "blob path should match"


def test_modified_content_produces_different_hash(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src = tmp_path / "mod.txt"
    src.write_text("v1", encoding="utf-8")

    dest_rel1, copied1 = store.store_file(src)
    assert copied1

    time.sleep(0.02)
    src.write_text("v2", encoding="utf-8")

    dest_rel2, copied2 = store.store_file(src)
    assert copied2
    assert dest_rel1 != dest_rel2
