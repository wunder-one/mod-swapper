from __future__ import annotations

import customtkinter
from typing import TYPE_CHECKING

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from storage.blob_store import BlobStore
from functions.update_mods import list_updates, Update

if TYPE_CHECKING:
    from ui.app import App

class UpdateDialog(customtkinter.CTkToplevel):
    def __init__(
        self,
        master: App,
        prof_state: ProfileState,
        user_settings: UserSettings,
        blob_store: BlobStore,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self._app: App = master
        self.prof_state = prof_state
        self.blob_store = blob_store
        self.user_settings = user_settings

        self.title("Updating Mods")
        win_width = 500
        win_height = 600
        win_x, win_y = self._app.get_child_window_location(win_width, win_height)
        self.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title_header = customtkinter.CTkLabel(
            self, text="Updating Mods", fg_color=("gray70", "gray30"), corner_radius=6
        )
        self.title_header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.status_frame = customtkinter.CTkFrame(self)
        self.status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(0, weight=1)

        self.status_label = customtkinter.CTkLabel(self.status_frame, text="Status")
        self.status_label.grid(row=0, column=0, padx=20, pady=(0, 0), sticky="w")

        self.status_progressbar = customtkinter.CTkProgressBar(self.status_frame)
        self.status_progressbar.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.status_progressbar.set(0)

        self.update_list = customtkinter.CTkTextbox(self)
        self.update_list.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

        update_list = list_updates(self.prof_state, self.blob_store, self.user_settings)

        for update in update_list:
            self.update_list.insert("end", f"{update['mod_name']} - {update['prev_version']} -> {update['new_version']}")
