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
# pak = Path(r"C:\Users\wes\AppData\Local\Larian Studios\Baldur's Gate 3\Mods\AahzLib.pak")
# pak = Path(r"C:\Users\wes\AppData\Local\BG3ProfileSwapper\file_store\00\7a66e778512e57df442b3ccf92ed0e57924ebac1d70167d88e9b52469b67a8")
pak = Path(
    r"C:\Users\wes\AppData\Local\BG3ProfileSwapper\file_store\00\3e10515bbaef6fef0f0b3df953a2145b87e894f3708f349dd435680609f305"
)
result = divine.read_mod_metadata(pak)
if result is None:
    print("No metadata found")
else:
    print(result["name"])
    print(result["uuid"])
    print(result["author"])
    print(result["description"])
    print(result["version"])
