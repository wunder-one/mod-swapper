import argparse

from functions.file_actions import load_profile_to_live
from user_settings import UserSettings

def test():
    # Process arguments
    parser = argparse.ArgumentParser(description="Test the file swapping functionality.")
    parser.add_argument("profile_name", type=str, help="Name of the profile to load")
    args = parser.parse_args()

    user_settings = UserSettings.load_settings()

    load_profile_to_live(args.profile_name, user_settings)
    print(f"==> Saved live mods from:")
    for p in user_settings.swap_paths:
        print(f"- Copied {p}")
    print(f"  --> to profile '{args.profile_name}'")
    print('------ END OF TEST ------')
    print('')

if __name__ == "__main__":
    test()