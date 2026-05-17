import logging

import customtkinter

logger = logging.getLogger(__name__)


class MigrationProgress(customtkinter.CTkToplevel):
    def __init__(self, master, total_profiles: int | None = None):
        super().__init__(master)
        self.title("Migration Progress")
        x = master.winfo_screenwidth() // 2 - self.winfo_width() // 2
        y = master.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"360x140+{x}+{y}")
        self.resizable(False, False)
        self.transient(master)
        self.update_idletasks()
        self.total_profiles = total_profiles
        self.migrated_profiles = 0
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
        self.status_label.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="ew")

        self.lift()
        self.focus_set()

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def update_progress(self, value: float):
        self.migrated_profiles = value
        self.progress_bar.set(value)
        if self.total_profiles and self.migrated_profiles == self.total_profiles:
            self.progress_bar.set(value=1.0)
            self.status_label.configure(text="Migration complete!")
