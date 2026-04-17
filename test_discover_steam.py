from functions.discover_steam import find_game_install_path
from constants import BG3_STEAM_ID

def test():

    result = find_game_install_path(BG3_STEAM_ID)
    if result:
        print(f"[FOUND] Game Folder -> {result}")
    else:
        print("Returned None")
    print('------ END OF TEST ------')
    print('')

if __name__ == "__main__":
    test()