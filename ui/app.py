import logging
import threading

import customtkinter

from ui.settings import SettingsWindow
from ui.overwrite_dialog import OverwriteDialog
from config.profile_state import ProfileState
from config.user_settings import UserSettings
from functions.file_actions import swap_profiles, create_new_profile
from ui.ui_fuctions import load_window_geometry, save_window_geometry

logger = logging.getLogger(__name__)


class App(customtkinter.CTk):
    def __init__(self, prof_state: ProfileState, user_settings: UserSettings):
        super().__init__()
        self.prof_state = prof_state
        self.user_settings = user_settings
        self.profile_list = list[str](self.prof_state.profiles.keys())
        self.profile_frames = {}

        self.title("BG3 Profile Swapper") 
        no_of_rows = (len(self.profile_list) - 1) // 3 + 1
        window_geometry = load_window_geometry("app") or {}

        if "winfo_x" in window_geometry and "winfo_y" in window_geometry:
            self.geometry(f"{190 * 3}x{52 + 96 * (no_of_rows + 1)}+{window_geometry['winfo_x']}+{window_geometry['winfo_y']}")
        else:
            self.geometry(f"{190 * 3}x{52 + 96 * (no_of_rows + 1)}")
            
        self.grid_columnconfigure((0, 1, 2), weight=1)
        # Keep row 1 height when the bar is grid_removed so profile tiles do not jump.
        # self._progress_bar_grid = dict(row=1, column=0, columnspan=3, padx=0, pady=0, sticky="ew")
        self.grid_rowconfigure(1, minsize=10)

        self.button_bar = ButtonBar(self, self.profile_list, self.prof_state, self.user_settings)
        self.button_bar.grid(row=0, column=0, pady=(0, 0), columnspan=3, sticky="ew")
        self.button_bar.configure(corner_radius=0)

        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", mode="indeterminate", corner_radius=0)
        self.progress_bar.grid(row=1, column=0, columnspan=3, padx=0, pady=0, sticky="ew")
        self.progress_bar.grid_remove()

        self.draw_profile_frames()
        
        self.settings_window: SettingsWindow | None = None
        self.overwrite_dialog: OverwriteDialog | None = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # self.show_progress_bar()


    def show_progress_bar(self) -> None:
        self.progress_bar.grid()
        self.progress_bar.start()

    def hide_progress_bar(self) -> None:
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

    def draw_profile_frames(self):
        self.profile_list = list[str](self.prof_state.profiles.keys())
        for i, profile_name in enumerate(self.profile_list):
            profile_frame = ProfileFrame(self, profile_name, self.prof_state, self.user_settings)
            left_pad = 10 if i % 3 == 0 else 0
            profile_frame.grid(row=i // 3 + 2, column=i % 3, padx=(left_pad, 10), pady=(10, 0), sticky="nsew")
            # self.profile_frame.configure(fg_color="transparent")
            self.profile_frames[profile_name] = profile_frame
        self.update_profile_frames()

    def update_profile_frames(self):
        for frame_title in self.profile_frames:
            frame = self.profile_frames[frame_title]
            frame.set_active_appearance(frame.profile == self.prof_state.active_profile)

    def refresh_profiles(self):
        logger.debug("Refreshing profile list UI.")
        # Clear existing frames
        for frame_title in self.profile_frames:
            frame = self.profile_frames[frame_title]
            frame.destroy()
        self.profile_frames.clear()
        self.draw_profile_frames()

    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            window = SettingsWindow(self, self.user_settings)
            self.settings_window = window
            window.bind('<Map>', lambda event: window.focus())
        else:
            self.settings_window.focus()

    def open_overwrite_dialog(self):
        if self.overwrite_dialog is None or not self.overwrite_dialog.winfo_exists():
            self.overwrite_dialog = OverwriteDialog(self, self.prof_state, self.user_settings)
        else:
            self.overwrite_dialog.lift()
            self.overwrite_dialog.focus_set()

    def on_close(self):
        save_window_geometry("app", winfo_x=self.winfo_x(), winfo_y=self.winfo_y())
        self.quit()

class ProfileFrame(customtkinter.CTkFrame):
    def __init__(self, master: App, profile: str, prof_state: ProfileState, user_settings: UserSettings):
        super().__init__(master)
        self._app: App = master
        self.profile = profile
        self.prof_state = prof_state
        self.user_settings = user_settings

        # Setup grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Profile title
        self.title = customtkinter.CTkLabel(self, text=self.profile, corner_radius=6)
        self.title.cget("font").configure(size=16, weight="bold")
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # Profile action buttons
        self.activate_button = customtkinter.CTkButton(self, text="Activate Profile", command=self.activate_button_callback)
        self.activate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def activate_button_callback(self):
        self._app.show_progress_bar()
        self._app.update_idletasks()

        def worker():
            try:
                swap_profiles(self.profile, self.prof_state, self.user_settings)
            except ValueError as e:
                logger.info("Profile swap skipped: %s", e)
            except Exception:
                logger.exception("Profile swap failed.")

            def on_done():
                self._app.update_profile_frames()
                self._app.hide_progress_bar()

            self._app.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def set_active_appearance(self, is_active: bool):
        if is_active:
            self.configure(fg_color=("gray86", "gray17"), border_color="green", border_width=2)
            self.activate_button.configure(state="disabled", fg_color=("#F9F9FA", "#343638"), text="Active Profile")
        else:
            self.configure(fg_color=("gray98", "gray11"), border_color=("gray85", "gray18"), border_width=2)
            self.activate_button.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"), text="Activate Profile")

class ButtonBar(customtkinter.CTkFrame):
    def __init__(self, master: App, profile: list[str], prof_state: ProfileState, user_settings: UserSettings):
        super().__init__(master)
        self._app: App = master
        self.grid_columnconfigure(2, weight=1)
        self.profile = profile
        self.prof_state = prof_state
        self.user_settings = user_settings

        self.new_profile_button = customtkinter.CTkButton(self, text="New Profile", command=self.new_profile_callback, width=100)
        self.new_profile_button.grid(row=0, column=0, padx=(6, 0), pady=6)

        self.overwrite_button = customtkinter.CTkButton(self, text="Overwrite Profile", command=self._app.open_overwrite_dialog, width=100)
        self.overwrite_button.grid(row=0, column=1, padx=(6, 0), pady=6)

        self.settings_button = customtkinter.CTkButton(self, text="Settings", command=self._app.open_settings_window, width=100)
        self.settings_button.grid(row=0, column=3, padx=(0, 6), pady=6, sticky="e")


    def new_profile_callback(self):
        new_profile_dialog = customtkinter.CTkInputDialog(text="This will create a new profile from your currently active mods.\n\nProfile Name:", title="New Profile")
        new_name = new_profile_dialog.get_input()
        if new_name is None or new_name.strip() == "":
            logger.info("New profile dialog cancelled or empty name.")
            return
        self._app.show_progress_bar()
        self._app.update_idletasks()

        def worker():
            try:
                set_name = create_new_profile(new_name.strip(), self.prof_state, self.user_settings)
            except ValueError as e:
                logger.info("Profile creation skipped: %s", e)
            except Exception:
                logger.exception("Profile creation failed.")

            def on_done():
                self._app.refresh_profiles()    
                logger.info("Created profile %r.", set_name)
                self._app.hide_progress_bar()

            self._app.after(0, on_done)
        threading.Thread(target=worker, daemon=True).start()
