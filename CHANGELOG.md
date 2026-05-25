# Changelog

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
