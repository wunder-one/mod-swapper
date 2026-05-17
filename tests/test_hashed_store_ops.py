import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from functions.profile_ops import save_live_to_profile


class SaveLiveToProfileTests(unittest.TestCase):
    def test_save_live_to_profile_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            profile_name = "test-profile"

            live_dir = temp_root / "live-dir"
            live_dir.mkdir()

            live_file = temp_root / "live-file.txt"
            live_file.write_text("data", encoding="utf-8")

            missing_path = temp_root / "does-not-exist"

            excluded_files = [temp_root / "protected-file.txt"]
            excluded_dirs = [temp_root / "protected-dir"]

            user_settings = Mock()
            user_settings.swap_paths = [live_dir, live_file, missing_path]
            user_settings.get_all_protected_paths.return_value = (
                excluded_files,
                excluded_dirs,
            )

            blob_store = Mock()
            dir_manifest = {str(live_dir / "nested.txt"): "hash-store/dir-entry"}
            file_manifest = {str(live_file): "hash-store/file-entry"}

            with (
                patch(
                    "functions.profile_ops.PROFILES_SNAPSHOT_DIR",
                    temp_root / "profiles",
                ),
                patch(
                    "functions.profile_ops.store_directory",
                    return_value=dir_manifest,
                ) as store_directory_mock,
                patch(
                    "functions.profile_ops.store_file",
                    return_value=file_manifest,
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
                excluded_files=excluded_files,
                excluded_dirs=excluded_dirs,
            )
            store_file_mock.assert_called_once_with(
                live_file,
                blob_store,
                excluded_files=excluded_files,
                excluded_dirs=excluded_dirs,
            )
            warning_mock.assert_called_once_with(
                "Live path does not exist: %s", missing_path
            )

            manifest_file = temp_root / "profiles" / profile_name / "manifest.json"
            self.assertTrue(manifest_file.exists())

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
