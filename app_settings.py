import json
import os
from dataclasses import dataclass, asdict, fields
from pathlib import Path

@dataclass
class AppConfig:
    active_profile: str = ""
    mods_directory: str = ""
    storage_directory: str = ""

def get_config_path() -> Path:
    roaming = os.getenv("APPDATA")
    return Path(roaming) / "BGProfileSwapper" / "config.json"

def load_config() -> AppConfig:
    path = get_config_path()
    if not path.exists():
        return AppConfig()  # return defaults if no file yet
    with open(path, "r") as f:
        data = json.load(f)
    return AppConfig(**data)

def save_config(config: AppConfig):
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)  # create folders if needed
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=2)

@dataclass
class Profile:
    name: str
    description: str = ""
    # add profile fields here as needed.

def get_profile_path(profile_name: str) -> Path:
    roaming = os.getenv("APPDATA")
    return Path(roaming) / "BGProfileSwapper" / "profiles" / f"{profile_name}.json"

def load_profile(profile_name: str) -> Profile:
    path = get_profile_path(profile_name)
    with open(path, "r") as f:
        data = json.load(f)
    known = {f.name for f in fields(Profile)}
    filtered = {k: v for k, v in data.items() if k in known}
    return Profile(**filtered)

def save_profile(profile: Profile):
    path = get_profile_path(profile.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(profile), f, indent=2)

def list_profiles() -> list[str]:
    roaming = os.getenv("APPDATA")
    profiles_dir = Path(roaming) / "BGProfileSwapper" / "profiles"
    if not profiles_dir.exists():
        return []
    return [p.stem for p in profiles_dir.glob("*.json")]