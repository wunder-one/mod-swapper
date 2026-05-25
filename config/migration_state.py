import json
import logging
from dataclasses import dataclass
from pathlib import Path

from constants import MIGRATION_STATE_FILE

logger = logging.getLogger(__name__)


@dataclass
class MigrationState:
    migration_state: bool = False
    migration_state_file: Path = MIGRATION_STATE_FILE
    storage_version: int = 1

    def __post_init__(self):
        pass

    @classmethod
    def load_state(cls) -> "MigrationState":
        if not cls.migration_state_file.exists():
            return cls()
        try:
            with cls.migration_state_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, bool):
                    return cls(
                        migration_state=data,
                        migration_state_file=cls.migration_state_file,
                    )
                return cls(
                    migration_state=data.get("migrated", False),
                    storage_version=data.get("storage_version", 1),
                    migration_state_file=cls.migration_state_file,
                )
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to load migration state; using defaults: %s", e)
            return cls()

    def save_state(self):
        data = {
            "migrated": self.migration_state,
            "storage_version": self.storage_version,
        }
        with self.migration_state_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

    def update_state(self, migrated: bool):
        self.migration_state = migrated
        if migrated:
            self.storage_version = 2
        else:
            self.storage_version = 1
        self.save_state()
