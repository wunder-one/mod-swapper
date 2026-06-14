from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import functions.divine as divine

print(f"Project root guess: {divine.DIVINE_EXE.parent.parent.parent}")
print(f"Divine.exe path:    {divine.DIVINE_EXE}")
print(f"Exists:             {divine.DIVINE_EXE.exists()}")

dest = _REPO_ROOT / "scratch" / "meta_test.lsx"
pak = Path(r"C:\Users\wes\AppData\Local\Larian Studios\Baldur's Gate 3\Mods\AahzLib.pak")
result = divine.read_mod_metadata(pak)
print(result.name)
print(result.uuid)
print(result.author)
print(result.description)
print(result.version)
print(result.tags)

