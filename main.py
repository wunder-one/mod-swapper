import ui.app
from profile_state import ProfileState

def main():
    prof_state = ProfileState.load_config()
    print(f"Active profile from config: {prof_state.active_profile}")
    print(f"Available profiles: {list(prof_state.profiles.keys())}")

    app = ui.app.App(prof_state=prof_state)
    app.mainloop()

    print("Saving configuration...")
    prof_state.save_config()
    print("Shutdown complete.")


if __name__ == "__main__":
    main()
