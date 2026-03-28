import argparse

from poc_file_swap import save_live_to_profile

def test():
    # Process arguments
    parser = argparse.ArgumentParser(description="Test the file swapping functionality.")
    parser.add_argument("profile_name", type=str, help="Name of the profile to save to")
    args = parser.parse_args()


    save_live_to_profile(args.profile_name)
    print(f"==> Saved live mods to profile '{args.profile_name}'")
    print('------ END OF TEST ------')
    print('')

if __name__ == "__main__":
    test()