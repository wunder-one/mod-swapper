import ui.app
from app_settings import AppConfig

def main():
    cfg = AppConfig.load_config()
    print(f"Active profile from config: {cfg.active_profile}")
    print(f"Available profiles: {list(cfg.profiles.keys())}")

    app = ui.app.App(cfg=cfg)
    app.mainloop()

    print("Saving configuration...")
    cfg.save_config()
    print("Shutdown complete.")


if __name__ == "__main__":
    main()
