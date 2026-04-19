import json
from constants import USER_CONFIG_DIR

def load_window_geometry(window_name: str) -> dict[str, int] | None:
    window_geometry_file = USER_CONFIG_DIR / f"{window_name}_window_geometry.json"
    if not window_geometry_file.exists():
        return None
    with window_geometry_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def save_window_geometry(window_name: str, **kwargs: int) -> None:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    window_geometry_file = USER_CONFIG_DIR / f"{window_name}_window_geometry.json"
    data = {
        **kwargs,
    }
    with window_geometry_file.open("w", encoding="utf-8") as f:
        json.dump(data, f)