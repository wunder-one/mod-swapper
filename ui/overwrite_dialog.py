import sys
import customtkinter

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from functions.file_actions import overwrite_profile
from ui.wrapping_label import WrappingLabel


class OverwriteDialog(customtkinter.CTkToplevel):
    def __init__(self, master, prof_state: ProfileState, user_settings: UserSettings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.prof_state = prof_state
        self.user_settings = user_settings
        self.transient(master)
        # transient() runs after CTk's initial title-bar setup; on Windows 10/11 that resets DWM
        # immersive dark mode for this HWND — re-run the same hook CTk uses in __init__ / resizable.
        if sys.platform == "win32":
            self.after(10, self._reapply_windows_titlebar)
        # self.geometry("235x500")
        self.geometry(f"235x{210 + len(self.prof_state.profiles) * 40}")
        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(4, weight=1)
        self.title("Overwrite Profile")

        self.bind("<Map>", self._on_map)

        self.info_label = WrappingLabel(self, text="Select a profile to overwrite.", fg_color="transparent")
        self.info_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="new")

        self.info_label = WrappingLabel(self, text="Warning: Overwriting will erase all data in the profile you select.")
        self.info_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="new")

        for index, profile in enumerate(self.prof_state.profiles.keys()):
            profile_button = customtkinter.CTkButton(self, text=profile, command=lambda: self._on_profile_button_click(profile))
            profile_button.grid(row=2 + index, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.destroy)
        self.cancel_button.grid(row=2 + len(self.prof_state.profiles), column=0, padx=20, pady=(40, 20), sticky="ew")


    def _on_profile_button_click(self, profile: str):
        try:
            overwrite_profile(profile, self.prof_state, self.user_settings)
            self.destroy()
        except Exception as e:
            print(f"Error overwriting profile: {e}")

    def _reapply_windows_titlebar(self) -> None:
        if not self.winfo_exists():
            return
        try:
            self._windows_set_titlebar_color(self._get_appearance_mode())
        except Exception:
            pass

    def _on_map(self, _event=None):
        # Defer past WM paint; on Windows, lift + focus in the same tick as Map often fails.
        self.after(10, self._bring_to_front)

    def _bring_to_front(self):
        self.lift()
        self.focus_set()
