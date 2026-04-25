import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


def _import_hashed_store_ops():
    # CI runs on Linux where winreg is unavailable; stub before importing module.
    sys.modules.setdefault("winreg", Mock())
    # Import after stubbing so module import doesn't fail cross-platform.
    return importlib.import_module("functions.hashed_store_ops")


class SaveLiveToProfileTests(unittest.TestCase):
    def test_save_live_to_profile_writes_manifest(self):
        # Import module under test with winreg safely stubbed for non-Windows CI.
        hashed_store_ops = _import_hashed_store_ops()
        # Use an isolated temporary directory so test has no side effects.
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            profile_name = "test-profile"

            # Directory input that should be processed via store_directory().
            live_dir = temp_root / "live-dir"
            live_dir.mkdir()

            # File input that should be processed via store_file().
            live_file = temp_root / "live-file.txt"
            live_file.write_text("data", encoding="utf-8")

            # Missing path exercises warning path and skip behavior.
            missing_path = temp_root / "does-not-exist"

            # Protected paths should be forwarded to storage helpers.
            excluded_files = [temp_root / "protected-file.txt"]
            excluded_dirs = [temp_root / "protected-dir"]

            # Mock user settings that define what "live" paths to snapshot.
            user_settings = Mock()
            user_settings.swap_paths = [live_dir, live_file, missing_path]
            user_settings.get_all_protected_paths.return_value = (
                excluded_files,
                excluded_dirs,
            )

            # Hash cache is passed through to underlying storage helpers.
            file_hash_cache = Mock()
            # Pretend results returned by directory/file storage helpers.
            dir_manifest = {str(live_dir / "nested.txt"): "hash-store/dir-entry"}
            file_manifest = {str(live_file): "hash-store/file-entry"}

            # Redirect profile output under temp root and mock helper behavior.
            with (
                patch.object(
                    hashed_store_ops, "PROFILES_SNAPSHOT_DIR", temp_root / "profiles"
                ),
                patch.object(
                    hashed_store_ops, "store_directory", return_value=dir_manifest
                ) as store_directory_mock,
                patch.object(
                    hashed_store_ops, "store_file", return_value=file_manifest
                ) as store_file_mock,
                patch.object(hashed_store_ops.logger, "warning") as warning_mock,
            ):
                # Execute function under test: snapshot live paths into manifest.
                hashed_store_ops.save_live_to_profile(
                    profile_name=profile_name,
                    file_hash_cache=file_hash_cache,
                    user_settings=user_settings,
                )

            # Directory inputs should call store_directory with exclusions.
            store_directory_mock.assert_called_once_with(
                live_dir,
                file_hash_cache,
                excluded_files=excluded_files,
                exclude_dirs=excluded_dirs,
            )
            # File inputs should call store_file with the same exclusions.
            store_file_mock.assert_called_once_with(
                live_file,
                file_hash_cache,
                excluded_files=excluded_files,
                exclude_dirs=excluded_dirs,
            )
            # Missing paths should be warned about exactly once.
            warning_mock.assert_called_once_with(
                "Live path does not exist: %s", missing_path
            )

            # Function should create a profile manifest in the expected location.
            manifest_file = temp_root / "profiles" / profile_name / "manifest.json"
            self.assertTrue(manifest_file.exists())

            # Read manifest and verify schema version and merged target entries.
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(
                manifest["targets"],
                {
                    str(live_dir / "nested.txt"): "hash-store/dir-entry",
                    str(live_file): "hash-store/file-entry",
                },
            )


if __name__ == "__main__":
    unittest.main()
