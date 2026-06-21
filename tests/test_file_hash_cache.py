import json
import time
from unittest.mock import Mock

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


def test_save_cache_writes_versioned_manifest(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src = tmp_path / "mod.txt"
    src.write_text("content", encoding="utf-8")
    store.get_cached_hash(src)
    store.save_cache()

    cache_manifest = json.loads(store.cache_file.read_text(encoding="utf-8"))
    assert cache_manifest["version"] == 2
    assert cache_manifest["entries"] == store.cache
    assert cache_manifest["entries"][str(src)]["mtime_ns"] == src.stat().st_mtime_ns


def test_load_cache_accepts_legacy_unversioned_cache(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    src = tmp_path / "mod.txt"
    legacy_entry = {
        str(src): {
            "size": 7,
            "mtime": 123.0,
            "hash": "a" * 64,
        }
    }
    (store_dir / "file_store_cache.json").write_text(
        json.dumps(legacy_entry), encoding="utf-8"
    )

    store = BlobStore.load_cache(store_dir=store_dir)

    assert store.cache == legacy_entry


def test_load_cache_accepts_version_1_cache(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    src = tmp_path / "mod.txt"
    version_1_manifest = {
        "version": 1,
        "entries": {
            str(src): {
                "size": 7,
                "mtime": 123.0,
                "hash": "a" * 64,
            }
        },
    }
    (store_dir / "file_store_cache.json").write_text(
        json.dumps(version_1_manifest), encoding="utf-8"
    )

    store = BlobStore.load_cache(store_dir=store_dir)

    assert store.cache == version_1_manifest["entries"]


def test_load_cache_ignores_unsupported_version(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()

    cache_manifest = {
        "version": 999,
        "entries": {
            str(tmp_path / "mod.txt"): {
                "size": 7,
                "mtime": 123.0,
                "hash": "a" * 64,
            }
        },
    }
    (store_dir / "file_store_cache.json").write_text(
        json.dumps(cache_manifest), encoding="utf-8"
    )

    store = BlobStore.load_cache(store_dir=store_dir)

    assert store.cache == {}


def test_store_file_uses_cached_hash_when_metadata_matches_and_blob_exists(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src = tmp_path / "mod.txt"
    src.write_text("content", encoding="utf-8")
    stat = src.stat()
    cached_hash = "a" * 64
    cached_blob = store.store_dir / cached_hash[:2] / cached_hash[2:]
    cached_blob.parent.mkdir(parents=True)
    cached_blob.write_text("content", encoding="utf-8")
    store.cache[str(src)] = {
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "mtime_ns": stat.st_mtime_ns,
        "hash": cached_hash,
    }
    store._hash = Mock(side_effect=AssertionError("cache hit should not hash"))

    dest_rel, copied = store.store_file(src)

    assert not copied
    assert dest_rel == cached_blob.relative_to(store.store_dir)
    store._hash.assert_not_called()


def test_store_file_rehashes_legacy_cache_entry_without_mtime_ns(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src = tmp_path / "mod.txt"
    src.write_text("content", encoding="utf-8")
    stat = src.stat()
    legacy_hash = "a" * 64
    legacy_blob = store.store_dir / legacy_hash[:2] / legacy_hash[2:]
    legacy_blob.parent.mkdir(parents=True)
    legacy_blob.write_text("content", encoding="utf-8")
    store.cache[str(src)] = {
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "hash": legacy_hash,
    }
    new_hash = "b" * 64
    store._hash = Mock(return_value=new_hash)

    dest_rel, copied = store.store_file(src)

    assert copied
    assert dest_rel == store._blob_path(new_hash).relative_to(store.store_dir)
    cache_entry = store.cache[str(src)]
    assert "mtime_ns" in cache_entry
    assert cache_entry["mtime_ns"] == stat.st_mtime_ns
    store._hash.assert_called_once_with(src)


def test_store_file_rehashes_when_cached_blob_is_missing(tmp_path):
    store = BlobStore.load_cache(store_dir=tmp_path / "store")

    src = tmp_path / "mod.txt"
    src.write_text("content", encoding="utf-8")
    stat = src.stat()
    cached_hash = "a" * 64
    store.cache[str(src)] = {
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "mtime_ns": stat.st_mtime_ns,
        "hash": cached_hash,
    }
    store._hash = Mock(return_value=cached_hash)

    dest_rel, copied = store.store_file(src)

    assert copied
    assert dest_rel == store._blob_path(cached_hash).relative_to(store.store_dir)
    assert (store.store_dir / dest_rel).exists()
    store._hash.assert_called_once_with(src)
