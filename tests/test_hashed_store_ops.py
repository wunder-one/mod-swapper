import json
from unittest.mock import Mock, patch

from storage.blob_store import BlobStore
from functions.profile_ops import (
    ProfileManifest,
    save_live_to_profile,
    _list_files_to_restore,
)


def test_save_live_to_profile_writes_manifest(tmp_path):
    profile_name = "test-profile"

    live_dir = tmp_path / "live-dir"
    live_dir.mkdir()

    live_file = tmp_path / "live-file.txt"
    live_file.write_text("data", encoding="utf-8")

    missing_path = tmp_path / "does-not-exist"

    excluded_files = [tmp_path / "protected-file.txt"]
    excluded_dirs = [tmp_path / "protected-dir"]

    user_settings = Mock()
    user_settings.swap_paths = [live_dir, live_file, missing_path]
    user_settings.get_all_protected_paths.return_value = (
        excluded_files,
        excluded_dirs,
    )

    blob_store = Mock()
    dir_manifest = {str(live_dir / "nested.txt"): "hash-store/dir-entry"}
    file_manifest = {str(live_file): "hash-store/file-entry"}
    global_manifest = {"version": 1, "entries": {}}

    with (
        patch(
            "functions.profile_ops.PROFILES_SNAPSHOT_DIR",
            tmp_path / "profiles",
        ),
        patch(
            "functions.profile_ops.load_global_manifest",
            return_value=global_manifest,
        ),
        patch(
            "functions.profile_ops.save_global_manifest"
        ) as save_global_manifest_mock,
        patch(
            "functions.profile_ops.store_directory",
            return_value=(dir_manifest, 0, global_manifest),
        ) as store_directory_mock,
        patch(
            "functions.profile_ops.store_file",
            return_value=(file_manifest, 1, global_manifest),
        ) as store_file_mock,
        patch("functions.profile_ops.logger.warning") as warning_mock,
    ):
        save_live_to_profile(
            profile_name=profile_name,
            blob_store=blob_store,
            user_settings=user_settings,
        )

    store_directory_mock.assert_called_once_with(
        live_dir,
        blob_store,
        global_manifest,
        excluded_files=excluded_files,
        excluded_dirs=excluded_dirs,
        on_file=None,
        file_index=0,
        total_files=1,
    )
    store_file_mock.assert_called_once_with(
        live_file,
        blob_store,
        global_manifest,
        excluded_files=excluded_files,
        excluded_dirs=excluded_dirs,
        on_file=None,
        file_index=0,
        total_files=1,
    )
    save_global_manifest_mock.assert_called_once_with(global_manifest)
    warning_mock.assert_called_once_with("Live path does not exist: %s", missing_path)

    manifest_file = tmp_path / "profiles" / profile_name / "manifest.json"
    assert manifest_file.exists()

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["version"] == 3
    assert manifest["swap_paths"] == [str(live_dir), str(live_file), str(missing_path)]
    assert manifest["targets"] == {
        str(live_dir / "nested.txt"): "hash-store/dir-entry",
        str(live_file): "hash-store/file-entry",
    }


def test_hash_mismatch_triggers_restore(tmp_path):
    store_dir = tmp_path / "store"
    store = BlobStore.load_cache(store_dir=store_dir)

    blob_src = tmp_path / "v1.txt"
    blob_src.write_text("v1 content", encoding="utf-8")
    dest_rel, _ = store.store_file(blob_src)

    live_file = tmp_path / "live.txt"
    live_file.write_text("v2 content", encoding="utf-8")

    manifest: ProfileManifest = {
        "version": 3,
        "swap_paths": [live_file],
        "targets": {str(live_file): str(dest_rel)},
    }

    files_to_restore = _list_files_to_restore("test-profile", store, manifest)

    assert len(files_to_restore) == 1
    assert files_to_restore[0][0] == live_file


def test_hash_match_skips_restore(tmp_path):
    store_dir = tmp_path / "store"
    store = BlobStore.load_cache(store_dir=store_dir)

    live_file = tmp_path / "live.txt"
    live_file.write_text("same content", encoding="utf-8")
    dest_rel, _ = store.store_file(live_file)

    manifest: ProfileManifest = {
        "version": 3,
        "swap_paths": [live_file],
        "targets": {str(live_file): str(dest_rel)},
    }

    files_to_restore = _list_files_to_restore("test-profile", store, manifest)

    assert len(files_to_restore) == 0


def test_missing_file_triggers_restore(tmp_path):
    store_dir = tmp_path / "store"
    store = BlobStore.load_cache(store_dir=store_dir)

    blob_src = tmp_path / "blob.txt"
    blob_src.write_text("content", encoding="utf-8")
    dest_rel, _ = store.store_file(blob_src)

    live_file = tmp_path / "missing.txt"

    manifest: ProfileManifest = {
        "version": 3,
        "swap_paths": [live_file],
        "targets": {str(live_file): str(dest_rel)},
    }

    files_to_restore = _list_files_to_restore("test-profile", store, manifest)

    assert len(files_to_restore) == 1
    assert files_to_restore[0][0] == live_file
