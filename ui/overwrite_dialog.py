from __future__ import annotations

import logging
import sys
import threading
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from functions.file_actions import overwrite_profile
from ui.wrapping_label import WrappingLabel

if TYPE_CHECKING:
    from ui.app import App

logger = logging.getLogger(__name__)


class OverwriteDialog(customtkinter.CTkToplevel):
    def __init__(self, master, prof_state: ProfileState, user_settings: UserSettings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._app: App = master
        self.prof_state = prof_state
        self.user_settings = user_settings
        self.transient(master)
        # transient() runs after CTk's initial title-bar setup; on Windows 10/11 that resets DWM
        # immersive dark mode for this HWND — re-run the same hook CTk uses in __init__ / resizable.
        if sys.platform == "win32":
            self.after(10, self._reapply_windows_titlebar)
        win_width = 235
        win_height = 240 + len(self.prof_state.profiles) * 40
        win_x, win_y = self._app.get_child_window_location(win_width, win_height)
        self.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")
        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(4, weight=1)
        self.title("Overwrite Profile")

        self.bind("<Map>", self._on_map)

        self.info_label = WrappingLabel(self, text="Select a profile to overwrite.", fg_color="transparent")
        self.info_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="new")

        self.warning_label = WrappingLabel(self, text="Warning: Overwriting will erase all data in the profile you select.")
        self.warning_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="new")

        self.profile_button_fr = customtkinter.CTkFrame(self, fg_color="transparent", border_width=2)
        self.profile_button_fr.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.profile_button_fr.grid_columnconfigure(0, weight=1)

        for index, profile in enumerate(self.prof_state.profiles.keys()):
            profile_button = customtkinter.CTkButton(
                self.profile_button_fr,
                text=profile,
                command=lambda p=profile: self._on_profile_button_click(p),
            )
            if index == 0:
                profile_button.grid(row=2 + index, column=0, padx=10, pady=10, sticky="ew")
            else:
                profile_button.grid(row=2 + index, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.destroy)
        self.cancel_button.grid(row=2 + len(self.prof_state.profiles), column=0, padx=20, pady=(40, 20), sticky="ew")


    def _on_profile_button_click(self, profile: str):
        confirm_dialog = messagebox.askyesno("Confirm Overwrite", f"Are you sure you want to overwrite {profile}?")
        if not confirm_dialog:
            return
        logger.info("Overwriting profile: %s", profile)

        self.destroy()
        self._app.show_progress_bar()
        self._app.update_idletasks()

        def worker():
            try:
                overwrite_profile(profile, self.prof_state, self.user_settings)
            except ValueError as e:
                logger.info("Profile overwrite skipped: %s", e)
            except Exception:
                logger.exception("Profile overwrite failed.")

            def on_done():
                self._app.hide_progress_bar()
                logger.info("Profile %r overwritten.", profile)

            self._app.after(0, on_done)
        threading.Thread(target=worker, daemon=True).start()

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
