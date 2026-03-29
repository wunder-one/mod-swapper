import json
import os
from dataclasses import dataclass, asdict, fields
from pathlib import Path

@dataclass
class Profile:
    name: str
    directory: object
    # add profile fields here as needed.

def get_profile_path(profile_name: str) -> Path:
    return self.directory / f"{profile_name}.json"

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
