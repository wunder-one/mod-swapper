import ui.app
from app_settings import AppConfig
from constants import PROFILES_SNAPSHOT_DIR, USER_CONFIG_DIR, USER_CONFIG_FILE

def main():
    cfg = AppConfig.load_config()
    print(f"Active profile from config: {cfg.active_profile}")
    print(f"Available profiles: {list(cfg.profiles.keys())}")

    app = ui.app.App(cfg=cfg)
    app.mainloop()


if __name__ == "__main__":
    main()
