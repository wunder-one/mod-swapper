import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from config.manifest import Manifest, ManifestEntry
from config.mod_metadata import ModMetadata
from storage.blob_store import BlobStore
from functions.update_mods import (
    Update,
    _check_mod_for_update,
    _collect_pak_files,
    _is_excluded,
    copy_updates,
)

MOD_UUID = "11111111-2222-3333-4444-555555555555"


def _metadata(
    *,
    name: str = "Test Mod",
    uuid: str = MOD_UUID,
    author: str = "Test Author",
    version: str = "1.0.0.0",
    version64: int = 65536,
) -> ModMetadata:
    return ModMetadata(
        name=name,
        uuid=uuid,
        author=author,
        description="",
        version=version,
        version64=version64,
        tags=[],
    )


def _manifest_entry(
    hash: str,
    *,
    filename: str = "mod.pak",
    mod_metadata: ModMetadata | None = None,
) -> tuple[str, ManifestEntry]:
    return hash, ManifestEntry(
        filename=filename,
        size=100,
        mod_metadata=mod_metadata,
    )


def _global_manifest(*entries: tuple[str, ManifestEntry]) -> Manifest:
    return Manifest(version=1, entries=dict(entries))


def _profile_manifest(
    mod_path: Path, live_hash: str, *, hash_path: str | None = None
) -> dict:
    blob_ref = hash_path if hash_path is not None else live_hash
    return {"version": 2, "targets": {str(mod_path): blob_ref}}


class CheckModForUpdateTests(unittest.TestCase):
    def test_returns_none_when_live_entry_has_no_metadata(self):
        live_hash = "a" * 64
        mod_path = Path("C:/mods/old.pak")
        global_manifest = _global_manifest(
            _manifest_entry(live_hash, mod_metadata=None),
        )
        profile_manifest = _profile_manifest(mod_path, live_hash)

        self.assertIsNone(
            _check_mod_for_update(mod_path, global_manifest, profile_manifest)
        )

    def test_returns_none_when_no_newer_version_with_same_uuid(self):
        live_hash = "a" * 64
        other_hash = "b" * 64
        mod_path = Path("C:/mods/mod.pak")
        metadata = _metadata(version64=200)
        global_manifest = _global_manifest(
            _manifest_entry(live_hash, mod_metadata=metadata),
            _manifest_entry(
                other_hash,
                mod_metadata=_metadata(version64=100, uuid="other-uuid"),
            ),
        )
        profile_manifest = _profile_manifest(mod_path, live_hash)

        self.assertIsNone(
            _check_mod_for_update(mod_path, global_manifest, profile_manifest)
        )

    def test_returns_update_when_newer_version_exists(self):
        live_hash = "a" * 64
        update_hash = "b" * 64
        mod_path = Path("C:/mods/mod_v1.pak")
        live_metadata = _metadata(version="1.0.0.0", version64=65536)
        new_metadata = _metadata(version="2.0.0.0", version64=131072)
        global_manifest = _global_manifest(
            _manifest_entry(
                live_hash, filename="mod_v1.pak", mod_metadata=live_metadata
            ),
            _manifest_entry(
                update_hash,
                filename="mod_v2.pak",
                mod_metadata=new_metadata,
            ),
        )
        profile_manifest = _profile_manifest(mod_path, live_hash)

        update = _check_mod_for_update(mod_path, global_manifest, profile_manifest)

        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["current_path"], mod_path)
        self.assertEqual(update["target_filename"], "mod_v2.pak")
        self.assertEqual(update["update_hash"], update_hash)
        self.assertEqual(
            update["update_storage_path"], Path(update_hash[:2]) / update_hash[2:]
        )
        self.assertEqual(update["prev_version64"], 65536)
        self.assertEqual(update["prev_version"], "1.0.0.0")
        self.assertEqual(update["new_version64"], 131072)
        self.assertEqual(update["new_version"], "2.0.0.0")
        self.assertEqual(update["mod_name"], "Test Mod")
        self.assertEqual(update["mod_author"], "Test Author")
        self.assertEqual(update["mod_uuid"], MOD_UUID)

    def test_picks_highest_version_when_multiple_updates_exist(self):
        live_hash = "a" * 64
        v2_hash = "b" * 64
        v3_hash = "c" * 64
        mod_path = Path("C:/mods/mod.pak")
        live_metadata = _metadata(version64=100)
        global_manifest = _global_manifest(
            _manifest_entry(live_hash, mod_metadata=live_metadata),
            _manifest_entry(
                v3_hash,
                filename="mod_v3.pak",
                mod_metadata=_metadata(version64=300, version="3.0.0.0"),
            ),
            _manifest_entry(
                v2_hash,
                filename="mod_v2.pak",
                mod_metadata=_metadata(version64=200, version="2.0.0.0"),
            ),
        )
        profile_manifest = _profile_manifest(mod_path, live_hash)

        update = _check_mod_for_update(mod_path, global_manifest, profile_manifest)

        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["update_hash"], v3_hash)
        self.assertEqual(update["new_version64"], 300)
        self.assertEqual(update["target_filename"], "mod_v3.pak")

    def test_normalizes_hash_path_from_profile_manifest(self):
        live_hash = "a" * 64
        update_hash = "b" * 64
        mod_path = Path("C:/mods/mod.pak")
        global_manifest = _global_manifest(
            _manifest_entry(live_hash, mod_metadata=_metadata(version64=100)),
            _manifest_entry(
                update_hash,
                filename="mod_v2.pak",
                mod_metadata=_metadata(version64=200, version="2.0.0.0"),
            ),
        )
        hash_path = f"{live_hash[:2]}\\{live_hash[2:]}"
        profile_manifest = _profile_manifest(mod_path, live_hash, hash_path=hash_path)

        update = _check_mod_for_update(mod_path, global_manifest, profile_manifest)

        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["update_hash"], update_hash)

    def test_ignores_newer_entries_without_metadata(self):
        live_hash = "a" * 64
        update_hash = "b" * 64
        mod_path = Path("C:/mods/mod.pak")
        global_manifest = _global_manifest(
            _manifest_entry(live_hash, mod_metadata=_metadata(version64=100)),
            _manifest_entry(update_hash, filename="mod_v2.pak", mod_metadata=None),
        )
        profile_manifest = _profile_manifest(mod_path, live_hash)

        self.assertIsNone(
            _check_mod_for_update(mod_path, global_manifest, profile_manifest)
        )


class IsExcludedTests(unittest.TestCase):
    def test_excluded_when_path_is_in_excluded_files(self):
        file_path = Path("C:/mods/protected.pak")
        self.assertTrue(_is_excluded(file_path, {file_path}, set()))

    def test_excluded_when_parent_is_in_excluded_dirs(self):
        excluded_dir = Path("C:/mods/protected")
        file_path = excluded_dir / "mod.pak"
        self.assertTrue(_is_excluded(file_path, set(), {excluded_dir}))

    def test_excluded_when_nested_under_excluded_dir(self):
        excluded_dir = Path("C:/mods/protected")
        file_path = excluded_dir / "nested" / "mod.pak"
        self.assertTrue(_is_excluded(file_path, set(), {excluded_dir}))

    def test_not_excluded_for_normal_path(self):
        file_path = Path("C:/mods/nested/mod.pak")
        excluded_file = Path("C:/mods/other.pak")
        excluded_dir = Path("C:/mods/other-dir")
        self.assertFalse(_is_excluded(file_path, {excluded_file}, {excluded_dir}))


class CollectPakFilesTests(unittest.TestCase):
    def test_collects_pak_files_from_swap_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mods_dir = root / "mods"
            nested_dir = mods_dir / "sub"
            nested_dir.mkdir(parents=True)
            (mods_dir / "one.pak").write_bytes(b"pak1")
            (nested_dir / "two.pak").write_bytes(b"pak2")
            (mods_dir / "readme.txt").write_text("notes", encoding="utf-8")

            user_settings = Mock()
            user_settings.get_swap_paths.return_value = [mods_dir]

            pak_files = _collect_pak_files(user_settings, set(), set())

            self.assertEqual(
                sorted(pak_files),
                sorted([mods_dir / "one.pak", nested_dir / "two.pak"]),
            )

    def test_skips_non_directory_swap_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            single_file = root / "single.pak"
            single_file.write_bytes(b"pak")

            user_settings = Mock()
            user_settings.get_swap_paths.return_value = [single_file]

            self.assertEqual(_collect_pak_files(user_settings, set(), set()), [])

    def test_respects_excluded_files_and_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            mods_dir = root / "mods"
            protected_dir = mods_dir / "protected"
            protected_dir.mkdir(parents=True)
            allowed = mods_dir / "allowed.pak"
            excluded_file = mods_dir / "skip.pak"
            excluded_nested = protected_dir / "nested.pak"
            allowed.write_bytes(b"allowed")
            excluded_file.write_bytes(b"skip")
            excluded_nested.write_bytes(b"nested")

            user_settings = Mock()
            user_settings.get_swap_paths.return_value = [mods_dir]

            pak_files = _collect_pak_files(
                user_settings,
                {excluded_file},
                {protected_dir},
            )

            self.assertEqual(pak_files, [allowed])


class CopyUpdatesTests(unittest.TestCase):
    def _store_blob(self, store: BlobStore, content: bytes) -> tuple[str, Path]:
        src = store.store_dir.parent / "source.bin"
        src.write_bytes(content)
        dest_rel, _ = store.store_file(src)
        file_hash = store.get_cached_hash(src)
        storage_path = store.store_dir / dest_rel
        return file_hash, storage_path

    def test_copy_updates_writes_blob_content_to_live_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore.load_cache(store_dir=root / "store")
            live_dir = root / "live"
            live_dir.mkdir()
            live_path = live_dir / "mod.pak"
            live_path.write_bytes(b"old content")

            file_hash, _ = self._store_blob(store, b"new content")
            updates: list[Update] = [
                {
                    "current_path": live_path,
                    "target_filename": "mod.pak",
                    "update_hash": file_hash,
                    "update_storage_path": Path(file_hash[:2]) / file_hash[2:],
                    "prev_version64": 100,
                    "prev_version": "1.0.0.0",
                    "new_version64": 200,
                    "new_version": "2.0.0.0",
                    "mod_name": "Test Mod",
                    "mod_author": "Author",
                    "mod_uuid": MOD_UUID,
                }
            ]

            copy_updates(updates, store)

            self.assertEqual(live_path.read_bytes(), b"new content")

    def test_copy_updates_renames_when_target_filename_differs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore.load_cache(store_dir=root / "store")
            live_dir = root / "live"
            live_dir.mkdir()
            current_path = live_dir / "mod_v1.pak"
            current_path.write_bytes(b"old content")

            file_hash, _ = self._store_blob(store, b"new content")
            updates: list[Update] = [
                {
                    "current_path": current_path,
                    "target_filename": "mod_v2.pak",
                    "update_hash": file_hash,
                    "update_storage_path": Path(file_hash[:2]) / file_hash[2:],
                    "prev_version64": 100,
                    "prev_version": "1.0.0.0",
                    "new_version64": 200,
                    "new_version": "2.0.0.0",
                    "mod_name": "Test Mod",
                    "mod_author": "Author",
                    "mod_uuid": MOD_UUID,
                }
            ]

            copy_updates(updates, store)

            target_path = live_dir / "mod_v2.pak"
            self.assertTrue(target_path.exists())
            self.assertEqual(target_path.read_bytes(), b"new content")
            self.assertFalse(current_path.exists())

    def test_copy_updates_raises_when_blob_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore.load_cache(store_dir=root / "store")
            live_path = root / "live" / "mod.pak"
            live_path.parent.mkdir()
            live_path.write_bytes(b"old")
            missing_hash = "d" * 64
            updates: list[Update] = [
                {
                    "current_path": live_path,
                    "target_filename": "mod.pak",
                    "update_hash": missing_hash,
                    "update_storage_path": Path(missing_hash[:2]) / missing_hash[2:],
                    "prev_version64": 100,
                    "prev_version": "1.0.0.0",
                    "new_version64": 200,
                    "new_version": "2.0.0.0",
                    "mod_name": "Test Mod",
                    "mod_author": "Author",
                    "mod_uuid": MOD_UUID,
                }
            ]

            with self.assertRaises(FileNotFoundError):
                copy_updates(updates, store)

    def test_copy_updates_empty_list_completes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BlobStore.load_cache(store_dir=Path(tmpdir) / "store")
            progress_calls: list[tuple[str, float | None]] = []

            def on_progress(message: str, *, progress: float | None = None) -> None:
                progress_calls.append((message, progress))

            copy_updates([], store, on_progress=on_progress)

            self.assertEqual(progress_calls, [("Done.", 1.0)])

    def test_copy_updates_reports_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            store = BlobStore.load_cache(store_dir=root / "store")
            live_dir = root / "live"
            live_dir.mkdir()
            first_path = live_dir / "one.pak"
            second_path = live_dir / "two.pak"
            first_path.write_bytes(b"old1")
            second_path.write_bytes(b"old2")

            first_hash, _ = self._store_blob(store, b"new1")
            second_hash, _ = self._store_blob(store, b"new2")
            updates: list[Update] = [
                {
                    "current_path": first_path,
                    "target_filename": "one.pak",
                    "update_hash": first_hash,
                    "update_storage_path": Path(first_hash[:2]) / first_hash[2:],
                    "prev_version64": 100,
                    "prev_version": "1.0.0.0",
                    "new_version64": 200,
                    "new_version": "2.0.0.0",
                    "mod_name": "One",
                    "mod_author": "Author",
                    "mod_uuid": MOD_UUID,
                },
                {
                    "current_path": second_path,
                    "target_filename": "two.pak",
                    "update_hash": second_hash,
                    "update_storage_path": Path(second_hash[:2]) / second_hash[2:],
                    "prev_version64": 100,
                    "prev_version": "1.0.0.0",
                    "new_version64": 200,
                    "new_version": "2.0.0.0",
                    "mod_name": "Two",
                    "mod_author": "Author",
                    "mod_uuid": MOD_UUID,
                },
            ]
            progress_calls: list[tuple[str, float | None]] = []

            def on_progress(message: str, *, progress: float | None = None) -> None:
                progress_calls.append((message, progress))

            copy_updates(updates, store, on_progress=on_progress)

            self.assertEqual(
                progress_calls,
                [
                    ("Updating one.pak...", 0.5),
                    ("Updating two.pak...", 1.0),
                    ("Done.", 1.0),
                ],
            )


if __name__ == "__main__":
    unittest.main()
