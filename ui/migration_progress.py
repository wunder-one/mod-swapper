import logging

import customtkinter

logger = logging.getLogger(__name__)


class MigrationProgress(customtkinter.CTkToplevel):
    def __init__(self, master, total_profiles: int | None = None):
        super().__init__(master)
        self.total_profiles = total_profiles
        self.step = 0
        self.cancelled = False

        self.title("Migration Progress")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.info_label = customtkinter.CTkLabel(
            self, text="Migrating profile data to new format...", fg_color="transparent"
        )
        self.info_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(
            self, orientation="horizontal", corner_radius=6
        )
        self.progress_bar.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")

        if not self.total_profiles:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(value=0)

        self.status_label = customtkinter.CTkLabel(
            self, text="", fg_color="transparent"
        )
        self.status_label.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="ew")

        self.cancel_button = customtkinter.CTkButton(
            self, text="Cancel", command=self._on_cancel, width=80
        )
        self.cancel_button.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="e")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        x = master.winfo_screenwidth() // 2 - 180
        y = master.winfo_screenheight() // 2 - 85
        self.geometry(f"360x170+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_set()
        self.update()

    def _on_cancel(self):
        self.cancelled = True
        self.cancel_button.configure(state="disabled")
        self.status_label.configure(text="Cancelling...")

    def check_cancelled(self) -> bool:
        self.master.update()
        return self.cancelled

    def set_total_profiles(self, total_profiles: int):
        print("Setting Total Profiles")
        self.total_profiles = total_profiles
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(value=0)
        self.master.update()

    def set_status(self, text: str):
        self.status_label.configure(text=text)
        self.master.update()

    def update_progress(self, step: int):
        self.step = step
        if self.total_profiles is not None:
            self.progress_bar.set(self.step / self.total_profiles)
        if self.total_profiles and self.step == self.total_profiles:
            self.progress_bar.set(value=1.0)
            self.status_label.configure(text="Migration complete!")
        self.master.update()
