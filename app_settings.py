import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from constants import PROFILES_SNAPSHOT_DIR, TEST_LIVE_MODS_DIR, USER_CONFIG_FILE

@dataclass
class AppConfig:
    active_profile: str = ""
    profiles: dict = field(init=False)  # Don't initialize in __init__

    def __post_init__(self):
        self.profiles = self.get_profiles()

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

    def load_config() -> AppConfig:
        if not USER_CONFIG_FILE.exists():
            return AppConfig()  # return defaults if no file yet
        with open(USER_CONFIG_FILE, "r") as f:
            data = json.load(f)
        return AppConfig(**data)

    def save_config(config: AppConfig):
        USER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)  # create folders if needed
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(asdict(config), f, indent=2)

