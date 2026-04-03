import argparse

from functions.file_actions import save_live_to_profile
from user_settings import UserSettings

def test():
    # Process arguments
    parser = argparse.ArgumentParser(description="Test the file swapping functionality.")
    parser.add_argument("profile_name", type=str, help="Name of the profile to save to")
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()

    save_live_to_profile(args.profile_name, user_settings.swap_paths)
    print(f"==> Saved live mods from:")
    for k, v in user_settings.swap_paths.items():
        print(f"- {k} Folder at {v}")
    print(f"  >to profile '{args.profile_name}'")
    print('------ END OF TEST ------')
    print('')

if __name__ == "__main__":
    test()