"""Wrapper around the vendored Divine.exe from lslib.

This module uses the Divine.exe tool from lslib.
It extracts metadata from BG3 mod packages.

The module is organized into several parts:
- Constants and configuration
- Data classes for metadata
- Helper functions for running Divine.exe
- Functions for reading metadata from mod packages
"""

import subprocess
import xml.etree.ElementTree as ET
import re
from config.mod_metadata import ModMetadata
from pathlib import Path
import tempfile

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
DIVINE_EXE = _PROJECT_ROOT / "tools" / "lslib" / "Divine.exe"
_META_LSX_PATTERN = re.compile(r"^Mods/([^/]+)/meta\.lsx", re.IGNORECASE)


def check_divine() -> None:
    if not DIVINE_EXE.exists():
        raise FileNotFoundError(
            f"Divine.exe not found at: {DIVINE_EXE}\n"
            f"Make sure tools/lslib/ is populated from the lslib release."
        )


def _decode_version64(value: int) -> str:
    major = value >> 55
    minor = (value >> 47) & 0xFF
    revision = (value >> 31) & 0xFFFF
    build = value & 0x7FFFFFFF
    return f"{major}.{minor}.{revision}.{build}"


def _run_divine(*args: str) -> subprocess.CompletedProcess:
    check_divine()
    return subprocess.run(
        [str(DIVINE_EXE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _parse_meta_lsx(xml_string: str) -> ModMetadata:
    root = ET.fromstring(xml_string)
    module_info = root.find(".//node[@id='ModuleInfo']")
    if module_info is None:
        raise ValueError("meta.lsx missing ModuleInfo node")

    def attr(name: str) -> str:
        node = module_info.find(f"./attribute[@id='{name}']")
        if node is None:
            return ""
        return node.get("value", "")

    return ModMetadata(
        name=attr("Name"),
        uuid=attr("UUID"),
        author=attr("Author"),
        description=attr("Description"),
        version=_decode_version64(int(attr("Version64"))),
        version64=int(attr("Version64")),
        tags=list(set(attr("Tags").split(";"))),
    )


def _find_meta_lsx_path(pak_path: Path) -> str | None:
    result = _run_divine(
        "--game",
        "bg3",
        "--action",
        "list-package",
        "--source",
        str(pak_path),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Divine.exe failed listing package (exit {result.returncode}):\n{result.stderr}"
        )
    stdout = result.stdout or ""
    for line in stdout.splitlines():
        path = line.split()[0]
        if _META_LSX_PATTERN.match(path):
            return path
    return None


def read_mod_metadata(pak_path: Path) -> ModMetadata | None:
    """Read metadata from a BG3 mod package. Returns None if unavailable."""
    try:
        meta_path = _find_meta_lsx_path(pak_path)
    except Exception:
        return None
    if meta_path is None:
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "meta.lsx"

        result = _run_divine(
            "--game",
            "bg3",
            "--action",
            "extract-single-file",
            "--source",
            str(pak_path),
            "--packaged-path",
            meta_path,
            "--destination",
            str(temp_path),
        )
        if result.returncode != 0:
            return None
        try:
            return _parse_meta_lsx(temp_path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
