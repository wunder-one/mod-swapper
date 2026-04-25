from pathlib import Path


def test():
    test_path = Path(r"C:\Users\wes\Documents\Learning")
    for dirpath, dirnames, filenames in test_path.walk():
        print(dirpath, dirnames, filenames)
    print("Done")


if __name__ == "__main__":
    test()
