import json
import logging
from dataclasses import dataclass
from pathlib import Path
from constants import PROFILES_SNAPSHOT_DIR, USER_CONFIG_DIR, PROFILE_STATE_FILE

logger = logging.getLogger(__name__)


@dataclass
class ProfileState:
    active_profile: str = ""

    @property
    def profiles(self) -> dict[str, Path]:
        # Returns a live mapping of folder names to their Path objects.
        if not PROFILES_SNAPSHOT_DIR.exists():
            PROFILES_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            return {}
        # This list comprehension runs every time you access 'config.profiles'
        return {d.name: d for d in PROFILES_SNAPSHOT_DIR.iterdir() if d.is_dir()}

    def save_config(self):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        data = {"active_profile": self.active_profile}
        # The default=str handles Path objects automatically.
        json_data = json.dumps(data, indent=4, default=str)
        PROFILE_STATE_FILE.write_text(json_data, encoding="utf-8")

    @classmethod
    def load_config(cls) -> "ProfileState":
        if not PROFILE_STATE_FILE.exists():
            return cls()
        try:
            with PROFILE_STATE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Avoid breaking if config file contains unknown fields
            allowed_keys = {f.name for f in cls.__dataclass_fields__.values() if f.init}
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}

            return cls(**filtered_data)
            # Need to handle case where active profile in config doesn't exist on disk?        

        except (json.JSONDecodeError, TypeError) as e:
            # If the file is garbled or missing required fields, 
            # fall back to a fresh default config.
            logger.warning("Failed to load profile state; using defaults: %s", e)
            return cls()
