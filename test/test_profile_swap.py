import argparse

from poc_file_swap import swap_profiles

def test():
    # Process arguments
    parser = argparse.ArgumentParser(description="Test swapping profiles.")
    parser.add_argument("current_profile", type=str, help="Name of the profile to save to storage")
    parser.add_argument("profile_to_load", type=str, help="Name of the profile to load")
    args = parser.parse_args()


    swap_profiles(args.current_profile, args.profile_to_load)
    print(f"==> Saved live mods to profile '{args.current_profile}'")
    print(f"==> Loaded profile '{args.profile_to_load}' to live mods")  
    print('------ END OF TEST ------')
    print('')

if __name__ == "__main__":
    test()