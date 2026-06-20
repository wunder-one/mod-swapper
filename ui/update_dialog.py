from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter

from config.profile_state import ProfileState
from config.user_settings import UserSettings
from storage.blob_store import BlobStore
from functions.update_mods import list_updates, Update, copy_updates
from functions.profile_ops import OnStoreFile, chain_store_file_callbacks
from functions.manifest import update_manifest

if TYPE_CHECKING:
    from ui.app import App

logger = logging.getLogger(__name__)


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
        self._updates: list[Update] = []
        self._dialog_busy = False

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

        self.phase_label = customtkinter.CTkLabel(
            self.status_frame,
            text="Preparing: Updating manifest...",
            anchor="w",
            justify="left",
        )
        self.phase_label.grid(row=0, column=0, padx=20, pady=(0, 0), sticky="w")

        self.status_progressbar = customtkinter.CTkProgressBar(self.status_frame)
        self.status_progressbar.grid(row=1, column=0, padx=20, pady=(0, 0), sticky="ew")
        self.status_progressbar.set(0)

        self.status_label = customtkinter.CTkLabel(
            self.status_frame, text="Updating manifest...", anchor="w", justify="left"
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=(6, 0), sticky="w")

        self.update_list = customtkinter.CTkTextbox(self)
        self.update_list.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.update_list.configure(state="disabled")

        self.button_bar = ButtonBar(self, self._app)
        self.button_bar.grid(row=3, column=0, padx=0, pady=(10, 0), sticky="ew")
        self.button_bar.configure(corner_radius=0)
        self.button_bar.update_button.configure(state="disabled")

        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)
        self._start_update_scan()

    def _set_buttons_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.button_bar.cancel_button.configure(state=state)
        self.button_bar.update_button.configure(state=state)

    def _show_done_button(self) -> None:
        self.button_bar.cancel_button.configure(state="disabled")
        self.button_bar.update_button.configure(
            text="Done",
            command=self.destroy,
            state="normal",
        )

    def _on_close_requested(self) -> None:
        if self._dialog_busy:
            return
        self.destroy()

    def _set_phase(self, text: str) -> None:
        def apply() -> None:
            if not self.winfo_exists():
                return
            self.phase_label.configure(text=text)

        self.after(0, apply)

    def _report_progress(
        self,
        message: str,
        *,
        progress: float | None = None,
        update: Update | None = None,
    ) -> None:
        def apply() -> None:
            if not self.winfo_exists():
                return
            self.status_label.configure(text=message)
            if progress is not None:
                self.status_progressbar.set(progress)
            if update is not None:
                self.update_list.configure(state="normal")
                self.update_list.insert(
                    "end",
                    f"{update['mod_name']} - {update['prev_version']} -> {update['new_version']}\n",
                )
                self.update_list.see("end")
                self.update_list.configure(state="disabled")

        self.after(0, apply)

    def _make_store_file_callback(self) -> OnStoreFile:
        def on_file(
            file_path: Path, index: int, total: int, copied_to_store: bool
        ) -> None:
            progress = (index / total) * 0.05 if total else 0.05
            verb = "Copying" if copied_to_store else "Storing"
            self._report_progress(f"{verb} {file_path.name}...", progress=progress)

        return on_file

    def _on_scan_complete(self, updates: list[Update], *, failed: bool = False) -> None:
        if not self.winfo_exists():
            return
        if failed:
            self._set_phase("Step 1 of 2: Scan failed")
            self.status_label.configure(text="Update scan failed.")
            self.status_progressbar.set(0)
            self.button_bar.update_button.configure(state="disabled")
            return

        self._updates = updates
        count = len(updates)
        if count == 0:
            self._set_phase("Step 1 of 2: Complete — no updates found")
            self.status_label.configure(text="No updates found.")
            self._show_done_button()
        else:
            self._set_phase("Step 1 of 2: Complete — review updates below")
            self.status_label.configure(
                text=f"Found {count} update(s). Ready to update."
            )
            self.button_bar.update_button.configure(state="normal")
        self.status_progressbar.set(1.0)

    def _on_update_clicked(self) -> None:
        if not self._updates:
            return
        self._start_update_file_copy(self._updates)

    def _begin_step_1_scan(self) -> None:
        self._set_phase(
            "Step 1 of 2: Saving current profile and scanning for updates..."
        )
        self._report_progress("Saving profile snapshot...", progress=0.0)
        self._app.begin_save_progress()

    def _start_update_scan(self) -> None:
        self._set_phase("Preparing: Updating manifest...")
        self._report_progress("Updating manifest...", progress=0.0)
        self._app.set_busy(True)
        self.update_idletasks()
        on_file = chain_store_file_callbacks(
            self._make_store_file_callback(),
            self._app.make_store_file_callback(),
        )

        def manifest_progress(message: str, *, progress: float) -> None:
            self._report_progress(message, progress=progress)

        def scan_worker() -> list[Update] | None:
            updates: list[Update] = []
            failed = False
            try:
                update_manifest(on_progress=manifest_progress)
                self.after(0, self._begin_step_1_scan)
                updates = list_updates(
                    self.prof_state,
                    self.blob_store,
                    self.user_settings,
                    on_progress=self._report_progress,
                    on_file=on_file,
                )
            except Exception:
                logger.exception("Update scan failed.")
                failed = True
                return None

            def on_done() -> None:
                self._app.hide_progress_bar()
                self._app.set_busy(False)
                self._on_scan_complete(updates, failed=failed)

            self.after(0, on_done)
            return updates

        threading.Thread(target=scan_worker, daemon=True).start()

    def _start_update_file_copy(self, updates: list[Update]) -> None:
        self._set_phase("Step 2 of 2: Applying updates...")
        self._dialog_busy = True
        self._app.set_busy(True)
        self._set_buttons_busy(True)
        self.update_idletasks()

        def copy_worker() -> None:
            failed = False
            self._app.after(0, self._app.begin_save_progress)
            try:
                copy_updates(
                    updates,
                    self.blob_store,
                    on_progress=self._report_progress,
                )
            except Exception:
                logger.exception("Update copy failed.")
                failed = True

            def on_done() -> None:
                self._dialog_busy = False
                self._app.hide_progress_bar()
                self._app.set_busy(False)
                if not self.winfo_exists():
                    return
                if failed:
                    self._set_phase("Step 2 of 2: Update failed")
                    self.status_label.configure(text="Update failed.")
                    self._set_buttons_busy(False)
                else:
                    self._set_phase("Step 2 of 2: Complete")
                    self.status_label.configure(text=f"Updated {len(updates)} mod(s).")
                    self._updates = []
                    self._show_done_button()

            self.after(0, on_done)

        threading.Thread(target=copy_worker, daemon=True).start()


class ButtonBar(customtkinter.CTkFrame):
    def __init__(self, master: UpdateDialog, app: App) -> None:
        super().__init__(master)
        self._master: UpdateDialog = master
        self._app: App = app
        self.grid_columnconfigure(3, weight=1)

        self.cancel_button = customtkinter.CTkButton(
            self, text="Cancel", command=self._master.destroy, width=100
        )
        self.cancel_button.grid(row=0, column=3, padx=(0, 6), pady=6, sticky="e")

        self.update_button = customtkinter.CTkButton(
            self,
            text="Update Mods",
            command=self._master._on_update_clicked,
            width=100,
        )
        self.update_button.grid(row=0, column=4, padx=(0, 6), pady=6, sticky="e")
