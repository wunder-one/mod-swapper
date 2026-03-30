import subprocess
import os
import json
from pathlib import Path
from constants import PROFILES_SNAPSHOT_DIR, TEST_LIVE_MODS_DIR, USER_CONFIG_FILE

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

def load_profile_to_live(profile_name: str, cfg):
    try:
        mirror_directory(
            PROFILES_SNAPSHOT_DIR / profile_name, 
            TEST_LIVE_MODS_DIR,
            )
        # write to config file here
        print(f"Setting active profile to '{profile_name}' in config...")
        cfg.active_profile = profile_name
        cfg.save_config()
    except Exception as e:
        print(f"Error loading profile '{profile_name}': {e}")

def swap_profiles(profile_to_load: str, cfg: object):
    print(f"Swapping from {cfg.active_profile} to {profile_to_load}...")
    save_live_to_profile(cfg.active_profile)
    print(f"{cfg.active_profile} saved to profile storage.")
    profile_to_load_dir = PROFILES_SNAPSHOT_DIR / profile_to_load
    if profile_to_load_dir.exists():
        load_profile_to_live(profile_to_load, cfg)
    else:
        print(f"Profile '{profile_to_load}' does not exist in storage. No changes made to live mods.")
        return
    print(f"{profile_to_load} loaded to live mods.")    
    return cfg.active_profile

def create_new_profile(profile_name: str, cfg: object):
    new_dir = PROFILES_SNAPSHOT_DIR / profile_name
    new_dir.mkdir(parents=True, exist_ok=True)
    cfg.profiles = cfg.get_profiles()
    cfg.active_profile = profile_name
    cfg.save_config()
    save_live_to_profile(profile_name)