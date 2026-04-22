from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def scratch():
    bg3_folder = Path(
        r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data\Mods"
    )
    print(f"Parts => {bg3_folder.parts}")
    print(f"bin filder exsists == {bg3_folder.exists()}")
    for f in bg3_folder.iterdir():
        print(f)


if __name__ == "__main__":
    scratch()
