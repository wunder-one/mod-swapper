import hashlib
import json
import datetime
import os
from pathlib import Path

ROAMING_APPDATA = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
USER_CONFIG_DIR = ROAMING_APPDATA / "BG3ProfileSwapper"
PROFILE_STATE_FILE = USER_CONFIG_DIR / "profile_state.json"
USER_SETTINGS_FILE = USER_CONFIG_DIR / "user_settings.json"

SCRIPT_DIR = Path(__file__).parent
SNAPSHOT_DIR = SCRIPT_DIR.parent / "logs" / "snapshots"


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_paths(live_paths: list[Path]) -> list[tuple[str, str, int, str]]:
    rows = []
    for root in live_paths:
        if not root.exists():
            print(f"WARNING: {root} does not exist, skipping")
            continue
        print(f"Scanning {root}")
        if root.is_file():
            rel_path = root.relative_to(root.parent)
            rows.append((str(rel_path), hash_file(root), root.stat().st_size, str(root)))
        else:
            for i, file in enumerate(sorted(root.rglob("*")), start=1):
                if file.is_file():
                    rel_path = file.relative_to(root.parent)
                    rows.append((str(rel_path), hash_file(file), file.stat().st_size, str(file)))
                    print(f"\r  {i} files scanned...", end="", flush=True)
        print()
    return rows


def main():
    profile_state = json.loads(PROFILE_STATE_FILE.read_text(encoding="utf-8"))
    profile_name = profile_state["active_profile"]

    user_settings = json.loads(USER_SETTINGS_FILE.read_text(encoding="utf-8"))
    live_paths = [Path(p) for p in user_settings["swap_paths"]]

    rows = scan_paths(live_paths)

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = SNAPSHOT_DIR / f"snapshot_{profile_name}_{ts}.tsv"

    with out.open("w", encoding="utf-8") as f:
        f.write(f"profile_name\t{profile_name}\n")
        f.write(f"timestamp\t{ts}\n")
        f.write("path\tsha256\tsize_bytes\tfull_path\n")
        for rel_path, digest, size, full_path in rows:
            f.write(f"{rel_path}\t{digest}\t{size}\t{full_path}\n")

    print(f"Wrote {len(rows)} files to {out}")


if __name__ == "__main__":
    main()