import time
import hashlib
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from functions.divine import read_mod_metadata

MODS_DIR = Path(r"C:\Users\wes\AppData\Local\Larian Studios\Baldur's Gate 3\Mods")
paks = sorted(MODS_DIR.glob("*.pak"))

results = []
total = len(paks)
failed = 0

for pak in paks:
    size = pak.stat().st_size

    t1 = time.perf_counter()
    meta = read_mod_metadata(pak)
    divine_time = time.perf_counter() - t1

    if meta is None:
        failed += 1
        print(f"{pak.name:60s} {size // 1024:>8}KB  divine=FAIL (no metadata)")
        continue

    t2 = time.perf_counter()
    hashlib.sha256(pak.read_bytes()).hexdigest()
    hash_time = time.perf_counter() - t2

    faster = "divine" if divine_time < hash_time else "hash"
    results.append((size, divine_time, hash_time, faster, pak.name))
    print(
        f"{pak.name:60s} {size // 1024:>8}KB  divine={divine_time:.3f}s  hash={hash_time:.3f}s  [{faster}]"
    )

print()
print(f"=== Summary ({len(results)}/{total} succeeded, {failed} failed) ===")

print()
print("=== Speed by file size ===")
results.sort(key=lambda r: r[0])
for label, cond in [
    ("Divine faster", lambda r: r[3] == "divine"),
    ("Hash faster", lambda r: r[3] == "hash"),
]:
    subset = [r for r in results if cond(r)]
    if subset:
        sizes = [r[0] for r in subset]
        print(
            f"  {label}: {len(subset)} files, sizes {min(sizes) // 1024}KB – {max(sizes) // 1024}KB"
        )
    else:
        print(f"  {label}: none")
