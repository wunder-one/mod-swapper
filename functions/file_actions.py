import subprocess
from pathlib import Path
from constants import PROFILES_SNAPSHOT_DIR, TEST_LIVE_MODS_DIR
from app_settings import AppConfig

def mirror_directory(source_dir, dest_dir):
    result = subprocess.run([
        "robocopy",
        source_dir,
        dest_dir,
        "/MIR",   # mirror
        "/FFT",   # use FAT file times (2-second tolerance, more reliable)
        "/Z",     # restartable mode in case of interruption
        "/NP"     # no progress percentage in output
    ], capture_output=True, text=True)
    # Robocopy exit codes 0-7 are success, 8+ are errors
    if result.returncode >= 8:
        raise RuntimeError(f"Robocopy failed with exit code {result.returncode}")

def save_live_to_profile(profile_name: str):
    mirror_directory(
        TEST_LIVE_MODS_DIR, 
        PROFILES_SNAPSHOT_DIR / profile_name,
        )
    
def get_unique_path(base_path: Path) -> Path:
    # Returns a Path that doesn't exist by appending (n) if necessary.
    if not base_path.exists():
        return base_path
    counter = 1
    # Keep trying new numbers until we find a path that doesn't exist
    while True:
        # This creates "Backed Up Profile (1)", etc.
        new_path = base_path.with_name(f"{base_path.name} ({counter})")
        if not new_path.exists():
            return new_path
        counter += 1

def load_profile_to_live(profile_name: str, cfg: AppConfig) -> bool:
    try:
        mirror_directory(
            PROFILES_SNAPSHOT_DIR / profile_name,
            TEST_LIVE_MODS_DIR,
            )
        # write to config file here
        print(f"Setting active profile to '{profile_name}' in config...")
        cfg.active_profile = profile_name
        cfg.save_config()
        return True
    except Exception as e:
        print(f"Error loading profile '{profile_name}': {e}")
        return False

def swap_profiles(profile_to_load: str, cfg: AppConfig):
    if cfg.active_profile == profile_to_load:
        print(f"'{profile_to_load}' is already the active profile. No changes made.")
        return cfg.active_profile
    elif not cfg.active_profile:
        backup_profile_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / "Backed Up Profile")
        backup_profile_dir.mkdir(parents=True, exist_ok=False)
        print(f"No active profile found. Backing up current live mods to '{backup_profile_dir.name}'...")
        save_live_to_profile(backup_profile_dir.name)
    else:
        print(f"Swapping from {cfg.active_profile} to {profile_to_load}...")
        save_live_to_profile(cfg.active_profile)
        print(f"{cfg.active_profile} saved to profile storage.")

    profile_to_load_dir = PROFILES_SNAPSHOT_DIR / profile_to_load
    if not profile_to_load_dir.exists():
        print(f"Profile '{profile_to_load}' does not exist in storage. No changes made to live mods.")
        return cfg.active_profile

    if not load_profile_to_live(profile_to_load, cfg):
        return cfg.active_profile

    print(f"{profile_to_load} loaded to live mods.")
    return cfg.active_profile

def create_new_profile(profile_name: str, cfg: AppConfig):
    unique_dir = get_unique_path(PROFILES_SNAPSHOT_DIR / profile_name)
    unique_dir.mkdir(parents=True, exist_ok=False)
    profile_name = unique_dir.name
    save_live_to_profile(profile_name)
    cfg.active_profile = profile_name
    cfg.save_config()
