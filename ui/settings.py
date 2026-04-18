from os import path
from pathlib import Path
from typing import Any
import customtkinter
from tkinter import filedialog

from user_settings import UserSettings

def bind_entry_show_path_tail(entry: customtkinter.CTkEntry, include_keyrelease: bool = False) -> None:
    # Keep long path entries scrolled to the right end.
    def _scroll_to_end(_event=None):
        entry.xview_moveto(1.0)

    entry.bind("<FocusIn>", _scroll_to_end)
    if include_keyrelease:
        entry.bind("<KeyRelease>", _scroll_to_end)
    _scroll_to_end()

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master, user_settings: UserSettings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.geometry("800x500")
        self.grid_columnconfigure((0, 1), weight=1)
        self.title("Settings")
        self.user_settings = user_settings

        self.title_header = customtkinter.CTkLabel(self, text="Settings", fg_color=("gray70", "gray30"), corner_radius=6)
        self.title_header.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")

        self.install_type_t = customtkinter.CTkLabel(self, text="Install Type")
        self.install_type_t.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.install_type_fr = DropdownPicker(self, values=["Steam", "GOG Galaxy", "Custom"])
        self.install_type_fr.grid(row=2, column=0, padx=20, pady=(0, 0), sticky="ew")        

        self.game_folder_t = customtkinter.CTkLabel(self, text="Game Folder")
        self.game_folder_t.grid(row=1, column=1, padx=20, pady=(10, 0), sticky="w")
        self.game_folder_fr = SingleDirPathSetting(self, self.user_settings.game_folder)
        self.game_folder_fr.grid(row=2, column=1, padx=20, pady=(0, 0), sticky="ew")

        self.swap_paths_t = customtkinter.CTkLabel(self, text="Files and folders to swap")
        self.swap_paths_t.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.swap_paths_fr = PathListEditor(self, self.user_settings.get_swap_paths())
        self.swap_paths_fr.grid(row=4, column=0, padx=20, pady=(0, 0), sticky="ew")

        self.protected_paths_t = customtkinter.CTkLabel(self, text="Protected files and folders")
        self.protected_paths_t.grid(row=3, column=1, padx=20, pady=(10, 0), sticky="w")
        self.protected_paths_fr = PathListEditor(self, self.user_settings.get_user_protected_paths())
        self.protected_paths_fr.grid(row=4, column=1, padx=20, pady=(0, 0), sticky="ew")

    def apply_settings(self):
        match self.install_type_fr.get():
            case "Steam":
                self.user_settings.install_type = "steam"
            case "GOG Galaxy":
                self.user_settings.install_type = "gog"
            case "Custom":
                self.user_settings.install_type = "custom"
        self.user_settings.game_folder = self.game_folder_fr.get()
        self.user_settings.swap_paths = self.swap_paths_fr.get()
        self.user_settings.user_protected_paths = self.protected_paths_fr.get()
        # fetch current values from settings window
        # and save to self.user_settings
        self.user_settings.save_settings()

class DropdownPicker(customtkinter.CTkFrame):
    def __init__(self, master, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color="transparent")
        self.install_type = customtkinter.CTkOptionMenu(self, values=values)
        self.install_type.grid(row=2, column=0, padx=0, pady=0, sticky="w")

    def get(self) -> str:
        return self.install_type.get()

class SingleDirPathSetting(customtkinter.CTkFrame):
    def __init__(self, master, path):
        path = path if path else ""
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color="transparent")
        self.path_str = customtkinter.StringVar(value=str(path))

        self.textbox = customtkinter.CTkEntry(self, textvariable=self.path_str)
        self.textbox.grid(row=1, column=0, padx=(0, 10), pady=0, sticky="ew")
        bind_entry_show_path_tail(self.textbox, include_keyrelease=True)

        self.browse_btn = customtkinter.CTkButton(self, text="Browse...", command=self.browse_folders, width=100)
        self.browse_btn.grid(row=1, column=1, padx=0, pady=0, sticky="e")

    def browse_folders(self):
        path = filedialog.askdirectory(
        parent=self.winfo_toplevel(),
        mustexist=True,
        initialdir=self.path_str.get() or None,
        )
        if path:
            self.path_str.set(str(path))
            bind_entry_show_path_tail(self.textbox, include_keyrelease=True)

    def get(self) -> Path:
        return Path(self.textbox.get())


class PathListEditor(customtkinter.CTkFrame):
    def __init__(self, master, list_values: list[Path]):
        super().__init__(master)
        self.list_values = list_values
        self.grid_columnconfigure(2, weight=1)
        self.configure(border_width=2, corner_radius=8, fg_color="transparent")

        # self.title = customtkinter.CTkLabel(self, text=self.title)
        # self.title.grid(row=0, column=0, padx=0, pady=0, sticky="w")

        self.scrollable_path_frame = ScrollablePathFrame(self, list_values=self.list_values)
        self.scrollable_path_frame.grid(row=0, column=0, columnspan=4, padx=6, pady=(6, 4), sticky="ew")
        
        self.new_entry = customtkinter.CTkEntry(self)
        self.new_entry.grid(row=1, column=0, columnspan=3, padx=(6, 2), pady=(0, 2), sticky="ew")
        bind_entry_show_path_tail(self.new_entry, include_keyrelease=True)

        self.add_btn = customtkinter.CTkButton(self, text="+", width=28, height=26)
        self.add_btn.grid(row=1, column=3, padx=(0, 6), pady=(0, 2), sticky="e")
        self.add_btn.cget("font").configure(size=18) 

        self.browse_folder = customtkinter.CTkButton(self, text="Browse Folder", width=100, height=24)
        self.browse_folder.grid(row=2, column=0, padx=(7, 4), pady=(0, 6))
        
        self.browse_file = customtkinter.CTkButton(self, text="Browse File", width=100, height=24)
        self.browse_file.grid(row=2, column=1, padx=(0, 2), pady=(0, 6))

    def get(self) -> list[Path]:
        path_list = []
        for entry_f in self.scrollable_path_frame.list_items:
            path_list.append(Path(entry_f.value))
        return path_list

class ScrollablePathFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, list_values: list):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.list_values = list_values
        self.list_items = []

        # print(f"List Values -> {self.list_values}")
        for i, value in enumerate(self.list_values):
            entry_f = ScrollablePathFrameEntry(self, value)
            entry_f.grid(row=i, column=0, padx=(2, 0), pady=(2, 0), sticky="nsew")
            self.list_items.append(entry_f)

        self.configure(border_width=0, corner_radius=6, fg_color=("gray80", "gray20"), height=200)

class ScrollablePathFrameEntry(customtkinter.CTkFrame):
    def __init__(self, master, value):
        super().__init__(master)
        self.value = customtkinter.StringVar(value=value)
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkEntry(self, textvariable=self.value)
        self.textbox.insert(0, str(self.value))
        self.textbox.grid(row=0, column=0, padx=(2, 0), pady=1, sticky="ew")
        bind_entry_show_path_tail(self.textbox)
        self.textbox.configure(state="readonly", fg_color=("gray90", "gray14"), border_width=0)
        self.configure(fg_color=self.textbox.cget("fg_color"), border_width=0)
        # self.configure(fg_color="green", border_width=0)
        self.configure(border_width=0, corner_radius=5)

        self.delete_btn = customtkinter.CTkButton(self, text="x", width=24, height=24, border_width=0, corner_radius=5)
        self.delete_btn.grid(row=0, column=1, padx=(0, 4), pady=0, sticky="e")
        self.delete_btn.configure(fg_color=("gray40", "#343638"), hover_color=("#3B8ED0", "#1F6AA5"))
        # self.delete_btn.cget("font").configure(size=12) 

