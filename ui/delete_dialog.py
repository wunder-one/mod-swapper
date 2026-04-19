from __future__ import annotations

import logging
import sys
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter

from config.profile_state import ProfileState
from ui.wrapping_label import WrappingLabel

if TYPE_CHECKING:
    from ui.app import App

logger = logging.getLogger(__name__)


class DeleteDialog(customtkinter.CTkToplevel):
    def __init__(self, master: App, prof_state: ProfileState, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._app: App = master
        self.prof_state = prof_state
        self.transient(master)
        # transient() runs after CTk's initial title-bar setup; on Windows 10/11 that resets DWM
        # immersive dark mode for this HWND — re-run the same hook CTk uses in __init__ / resizable.
        if sys.platform == "win32":
            self.after(10, self._reapply_windows_titlebar)
        # self.geometry("235x500")
        self.geometry(f"235x{240 + len(self.prof_state.profiles) * 40}")
        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(4, weight=1)
        self.title("Delete Profile")

        self.bind("<Map>", self._on_map)

        self.info_label = WrappingLabel(self, text="Choose a profile to delete.", fg_color="transparent")
        self.info_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="new")

        self.profile_button_fr = customtkinter.CTkFrame(self, fg_color="transparent", border_width=2)
        self.profile_button_fr.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.profile_button_fr.grid_columnconfigure(0, weight=1)

        for index, profile in enumerate(self.prof_state.profiles.keys()):
            profile_button = customtkinter.CTkButton(
                self.profile_button_fr,
                text=profile,
                command=lambda p=profile: self._on_profile_button_click(p),
            )
            if profile == self.prof_state.active_profile:
                profile_button.configure(state="disabled")
            if index == 0:
                profile_button.grid(row=2 + index, column=0, padx=10, pady=10, sticky="ew")
            else:
                profile_button.grid(row=2 + index, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.destroy)
        self.cancel_button.grid(row=2 + len(self.prof_state.profiles), column=0, padx=20, pady=(40, 20), sticky="ew")


    def _on_profile_button_click(self, profile: str):
        confirm_dialog = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {profile}?")
        if not confirm_dialog:
            return
        logger.info("Deleting profile: %s", profile)
        app = self._app
        self.destroy()
        app.delete_profile_async(profile)

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
