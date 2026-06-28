# Changelog

## [v0.3.3] - 2026-06-28

Protection for files after adding new swap folders in settings.

- Fix: When adding a new swap folder, protects exsisting files when swapping profiles
    - Bump profile manifests to version 3 and record the swap paths used when each profile was saved.
    - When loading a profile, use the manifest's pinned swap paths (for v3+) when deciding which live files to remove, so changing settings later does not delete files outside the original swap scope.
    - When swap paths change in Settings, automatically migrate outdated manifests to v3 with the previous swap paths pinned before applying the new paths.
    - Refactor profile restore helpers to accept a typed manifest and expand test coverage for migration and load behavior.

## [v0.3.2] - 2026-06-20

Improves Update Mods progress reporting and developer test tooling.

- Fix: Issue where cancel button was not avaiable when list of updates is shown
- Centralizes update-scan progress bar ranges in `UpdateScanProgress` for easier progress bar adjustments
- Adjusted progress bar status percents
- Migrates the test suite from unittest to pytest (`uv run pytest`)

## [v0.3.1] - 2026-06-20

Fixed a bug that can sometimes cause the wrong version to be selected when checking for mod updates.

- Adds tests/test_update_mods.py with 18 tests covering update detection (_check_mod_for_update), pak file scanning (_is_excluded, _collect_pak_files), and update application (copy_updates)
- Fixes _check_mod_for_update to select the highest version64 when multiple stored versions of the same mod exist; previously it compared each candidate only against the live version, so manifest iteration order could pick an older update over a newer one

## [v0.3.0] - 2026-06-20

Adds mod version tracking and an update workflow so profiles can pick up newer versions of mods already stored in the blob store.

- Global manifest tracks mod metadata (name, author, UUID, version) keyed by blob hash
- Vendored lslib `Divine.exe` extracts metadata from `.pak` files; metadata is recorded when files are stored
- Scans active profile for available updates by matching mod UUIDs and comparing `Version64` across stored blobs
- New **Update Mods** dialog lists pending updates with version transitions and applies them on confirmation
- Manifest preparation step with progress reporting; can be cancelled before changes are committed
- UI disables controls during long operations (swap, profile load/save, update apply)
- Per-file progress callbacks during profile save; indeterminate progress during profile load
- Moves `BlobStore` from `functions/` to `storage/`

## [v0.2.0] - 2026-05-25

Introduces content-addressed blob storage as v2 of the mod storage layer, replacing the old file-copy approach (v1).

- Adds `BlobStore` with SHA-256 content-addressed deduplication
- Migration system reads existing v1 profiles and re-stores files by hash
- Profile save/load/swap operations using the new blob store
- Hash-based verification on restore (compares live file hash against manifest's expected blob hash)
- Always hashes file bytes on store; size/mtime cache used only for restore verification
- Corresponding test coverage for store, restore, and hash mismatch scenarios

## [v0.1.1] - 2026-04-22

- Added app icon
- Fix: records missing folders in the manifest. After a swap, missing paths are correctly removed

## [v0.1.0] - 2026-04-20

First Release. Windows only.

- Swap mods and mod-related files between two or more profiles
- Create new profiles
- Delete profiles
- Overwrite a profile
- Customize swapped files/folders and protected files/folders
