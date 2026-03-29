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

def save_live_to_profile(profile_name):
    mirror_directory(
        TEST_LIVE_MODS_DIR, 
        PROFILES_SNAPSHOT_DIR / profile_name,
        )

def load_profile_to_live(profile_name):
    try:
        mirror_directory(
            PROFILES_SNAPSHOT_DIR / profile_name, 
            TEST_LIVE_MODS_DIR,
            )
        # write to config file here
    except Exception as e:
        print(f"Error loading profile '{profile_name}': {e}")
    

def swap_profiles(current_profile, profile_to_load):
    save_live_to_profile(current_profile)
    print(f"{current_profile} saved to profile storage.")
    PROFILE_SNAPSHOT_DIR = PROFILES_SNAPSHOT_DIR / profile_to_load
    if PROFILE_SNAPSHOT_DIR.exists():
        load_profile_to_live(profile_to_load)
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump({"current_profile": current_profile}, f, indent=4)
    else:
        print(f"Profile '{profile_to_load}' does not exist in storage. No changes made to live mods.")
        return
    print(f"{profile_to_load} loaded to live mods.")
    current_profile = profile_to_load
    return current_profile