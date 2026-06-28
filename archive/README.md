# Archive

Frozen snapshots of code that has been removed from the active application. This folder exists for reference and record keeping only.

## Why this folder exists

Mod Swapper ships as a PyInstaller bundle built from `main.py`. PyInstaller includes every module reachable through the import graph—not everything in the repo. Code kept here stays in git for history and comparison, but must **not** be imported by anything under `main.py`, `functions/`, `config/`, `ui/`, or `storage/`.

## What belongs here

- Replaced implementations (for example, the pre–blob-store robocopy profile swap)
- Retired modules that are no longer safe or desirable to run in production
- One-off migrations or experiments worth preserving with context

## What does not belong here

- Active application code (use `functions/`, `config/`, etc.)
- Throwaway dev scripts (use `scratch/`)
- Generated or build output (use `dist/`, already gitignored)

