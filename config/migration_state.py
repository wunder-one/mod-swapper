import json
import logging
from dataclasses import dataclass
from pathlib import Path

from constants import MIGRATION_STATE_FILE, PROFILES_SNAPSHOT_DIR

logger = logging.getLogger(__name__)


@dataclass
class MigrationState:
    migration_state: bool = False
    migration_state_file: Path = MIGRATION_STATE_FILE
    storage_version: int = 1

    def __post_init__(self):
        # If the migration state is false we need to check if this is a new installation.
        if not self.migration_state and not self.migration_state_file.exists():
            has_profiles = False
            try:
                if PROFILES_SNAPSHOT_DIR.is_dir():
                    for child in PROFILES_SNAPSHOT_DIR.iterdir():
                        if child.is_dir():
                            has_profiles = True
                            break
            except OSError:
                has_profiles = False
            if has_profiles:
                try:
                    self.migration_state = True
                    self.storage_version = 2
                    self.save_state()
                except Exception as e:
                    logger.warning(
                        "Failed to migrate file store; using defaults: %s", e
                    )
                    self.migration_state = False
                    self.save_state()
            # If the profiles snapshot directory is missing or empty, we have nothing to migrate.
            else:
                self.migration_state = True
                self.storage_version = 2
                self.save_state()

    @classmethod
    def load_state(cls) -> "MigrationState":
        if not cls.migration_state_file.exists():
            return cls()
        try:
            with cls.migration_state_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(
                    migration_state=data, migration_state_file=cls.migration_state_file
                )
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to load migration state; using defaults: %s", e)
            return cls()

    def save_state(self):
        with self.migration_state_file.open("w", encoding="utf-8") as f:
            json.dump(self.migration_state, f, indent=4, default=str)

    def update_state(self, migrated: bool):
        self.migration_state = migrated
        if migrated:
            self.storage_version = 2
        else:
            self.storage_version = 1
        self.save_state()
