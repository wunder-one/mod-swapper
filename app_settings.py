import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from constants import PROFILES_SNAPSHOT_DIR, TEST_LIVE_MODS_DIR, USER_CONFIG_DIR, USER_CONFIG_FILE

@dataclass
class AppConfig:
    active_profile: str = ""
    profiles: dict = field(init=False)

    def __post_init__(self):
        self.profiles = self.get_profiles()

    @staticmethod
    def get_profiles() -> dict:
        if not PROFILES_SNAPSHOT_DIR.exists():
            PROFILES_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            return {}
        profiles = {}
        for dir in PROFILES_SNAPSHOT_DIR.iterdir():
            if dir.is_dir():
                print(f"Found profile: {dir.name}")
                profiles[dir.name] = dir
        return profiles

    @classmethod
    def load_config(cls) -> "AppConfig":
        if not USER_CONFIG_FILE.exists():
            return cls()
        with USER_CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Avoid breaking if config file contains unknown fields
        allowed_keys = {f.name for f in cls.__dataclass_fields__.values() if f.init}
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}

        return cls(**filtered_data)

    def save_config(self):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        USER_CONFIG_FILE.write_text(json.dumps(asdict(self), indent=4), encoding="utf-8")

