import subprocess
import os

def mirror_directory(source_dir, dest_dir):
    subprocess.run([
        "robocopy",
        source_dir,
        dest_dir,
        "/MIR",   # mirror - makes dest identical to source
        "/FFT",   # use FAT file times (2-second tolerance, more reliable)
        "/Z",     # restartable mode in case of interruption
        "/NP"     # no progress percentage in output (cleaner to parse)
    ])

def save_live_to_profile(profile_name):
    source = r"C:\Users\wes\Desktop\live-mods-test"
    local_appdata = os.getenv("LOCALAPPDATA")
    dest = rf"{local_appdata}\BGProfileSwapper\profiles\{profile_name}"
    mirror_directory(source, dest)
    