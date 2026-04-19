from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter
from tkinter import filedialog
from typing import TYPE_CHECKING

from config.user_settings import UserSettings

if TYPE_CHECKING:
    from ui.app import App

def bind_entry_show_path_tail(entry: customtkinter.CTkEntry, include_keyrelease: bool = False) -> None:
    # Keep long path entries scrolled to the right end.
    def _scroll_to_end(_event=None):
        entry.xview_moveto(1.0)

    entry.bind("<FocusIn>", _scroll_to_end)
    if include_keyrelease:
        entry.bind("<KeyRelease>", _scroll_to_end)
    _scroll_to_end()

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master: App, user_settings: UserSettings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._app: App = master
        win_width = 800
        win_height = 500
        win_x, win_y = self._app.get_child_window_location(win_width, win_height)
        self.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)
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
        self.swap_paths_fr = PathListEditor(self, self.user_settings.get_swap_paths(), self.user_settings.game_folder)
        self.swap_paths_fr.grid(row=4, column=0, padx=20, pady=(0, 0), sticky="nsew")

        self.protected_paths_t = customtkinter.CTkLabel(self, text="Protected files and folders")
        self.protected_paths_t.grid(row=3, column=1, padx=20, pady=(10, 0), sticky="w")
        self.protected_paths_fr = PathListEditor(self, self.user_settings.get_user_protected_paths(), self.user_settings.game_folder)
        self.protected_paths_fr.grid(row=4, column=1, padx=20, pady=(0, 0), sticky="nsew")

        self.button_bar = customtkinter.CTkFrame(self)
        self.button_bar.grid(row=5, column=0, columnspan=2, padx=0, pady=(30, 0), sticky="ew")
        self.button_bar.grid_columnconfigure(0, weight=1)

        self.reset_defaults_btn = customtkinter.CTkButton(self.button_bar, text="Reset to Defaults", command=self.reset_default_settings)
        self.reset_defaults_btn.grid(row=0, column=0, padx=(20, 0), pady=10, sticky="w")
        self.cancel_btn = customtkinter.CTkButton(self.button_bar, text="Cancel", command=self.cancel_settings, width=100)
        self.cancel_btn.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="e")
        self.apply_btn = customtkinter.CTkButton(self.button_bar, text="Apply", command=self.apply_settings, width=100)
        self.apply_btn.grid(row=0, column=2, padx=(10, 0), pady=10, sticky="e")
        self.ok_btn = customtkinter.CTkButton(self.button_bar, text="OK", command=self.ok_settings, width=100)
        self.ok_btn.grid(row=0, column=3, padx=(10, 20), pady=10, sticky="e")

    def cancel_settings(self):
        self.destroy()

    def ok_settings(self):
        self.apply_settings()
        self.destroy()

    def reset_default_settings(self):
        self.user_settings.reset_to_defaults()
        match self.user_settings.install_type:
            case "steam":
                self.install_type_fr.dropdown.set("Steam")
            case "gog":
                self.install_type_fr.dropdown.set("GOG Galaxy")
            case "custom":
                self.install_type_fr.dropdown.set("Custom")
        self.game_folder_fr.path_str.set(str(self.user_settings.game_folder))
        self.swap_paths_fr.reset_paths(self.user_settings.swap_paths)
        self.protected_paths_fr.reset_paths(self.user_settings.user_protected_paths)

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
        self.dropdown = customtkinter.CTkOptionMenu(self, values=values)
        self.dropdown.grid(row=2, column=0, padx=0, pady=0, sticky="w")

    def get(self) -> str:
        return self.dropdown.get()

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

# --- Path List Editor Classes ---
class PathListEditor(customtkinter.CTkFrame):
    def __init__(self, master, list_values: list[Path], default_path: Path | None):
        super().__init__(master)
        self.list_values = list_values
        self.default_path = default_path
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(border_width=2, corner_radius=8, fg_color="transparent")

        self.scrollable_path_frame = ScrollablePathFrame(self, list_values=self.list_values)
        self.scrollable_path_frame.grid(row=0, column=0, columnspan=4, padx=6, pady=(6, 4), sticky="nsew")
        
        self.new_entry = customtkinter.CTkEntry(self)
        self.new_entry.grid(row=1, column=0, columnspan=3, padx=(6, 2), pady=(0, 2), sticky="ew")
        bind_entry_show_path_tail(self.new_entry, include_keyrelease=True)

        self.add_btn = customtkinter.CTkButton(self, command=self.add_entry_to_list, text="+", width=28, height=26)
        self.add_btn.grid(row=1, column=3, padx=(0, 6), pady=(0, 2), sticky="e")
        self.add_btn.cget("font").configure(size=18) 

        self.browse_folder = customtkinter.CTkButton(self, command=self.browse_folders, text="Browse Folder", width=100, height=24)
        self.browse_folder.grid(row=2, column=0, padx=(7, 4), pady=(0, 6), sticky="s")
        
        self.browse_file = customtkinter.CTkButton(self, command=self.browse_files, text="Browse File", width=100, height=24)
        self.browse_file.grid(row=2, column=1, padx=(0, 2), pady=(0, 6), sticky="s")

    def add_entry_to_list(self):
        path = self.new_entry.get()
        if path:
            self.scrollable_path_frame.add_new_path(Path(path))

    def browse_folders(self):
        path = filedialog.askdirectory(
        parent=self.winfo_toplevel(),
        mustexist=True,
        initialdir=self.default_path or None,
        )
        if path:
            self.scrollable_path_frame.add_new_path(Path(path))

    def browse_files(self):
        path = filedialog.askopenfilename(
        parent=self.winfo_toplevel(),
        initialdir=self.default_path or None,
        )
        if path:
            self.scrollable_path_frame.add_new_path(Path(path))

    def get(self) -> list[Path]:
        return self.scrollable_path_frame.get()

    def reset_paths(self, new_list: list[Path]):
        self.scrollable_path_frame.reset_paths(new_list)

class ScrollablePathFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, list_values: list[Path]):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.list_values = list_values
        self.list_items = []

        self.populate_list()
        self.configure(border_width=0, corner_radius=6, fg_color=("gray80", "gray20"))

    def get(self) -> list[Path]:
        return_list = []
        for entry_f in self.list_items:
            return_list.append(Path(entry_f.value.get()))
        return return_list

    def populate_list(self):
        for i, value in enumerate(self.list_values):
            entry_f = ScrollablePathFrameEntry(self, value)
            entry_f.grid(row=i, column=0, padx=(2, 0), pady=(2, 0), sticky="nsew")
            self.list_items.append(entry_f)

    def add_new_path(self, path: Path):
        entry_f = ScrollablePathFrameEntry(self, path)
        entry_f.grid(row=len(self.list_items), column=0, padx=(2, 0), pady=(2, 0), sticky="nsew")
        self.list_items.append(entry_f)

    def _relayout_path_rows(self) -> None:
        for i, entry_f in enumerate(self.list_items):
            entry_f.grid(row=i, column=0, padx=(2, 0), pady=(2, 0), sticky="nsew")

    def reset_paths(self, new_list: list[Path]):
        self.list_values = new_list
        for path_entry_fr in reversed(self.list_items):
            path_entry_fr.destroy()
        self.list_items.clear()
        self.populate_list()

class ScrollablePathFrameEntry(customtkinter.CTkFrame):
    def __init__(self, master, value: Path):
        super().__init__(master)
        self.value = customtkinter.StringVar(value=str(value))
        self.grid_columnconfigure(0, weight=1)
        self.textbox = customtkinter.CTkEntry(self, textvariable=self.value)
        self.textbox.grid(row=0, column=0, padx=(2, 0), pady=1, sticky="ew")
        bind_entry_show_path_tail(self.textbox)
        self.textbox.configure(state="readonly", fg_color=("gray90", "gray14"), border_width=0)
        self.configure(fg_color=self.textbox.cget("fg_color"), border_width=0)
        self.configure(border_width=0, corner_radius=5)

        self.delete_btn = customtkinter.CTkButton(self, text="x", command=self._on_delete, width=24, height=24, border_width=0, corner_radius=5)
        self.delete_btn.grid(row=0, column=1, padx=(0, 4), pady=0, sticky="e")
        self.delete_btn.configure(fg_color=("gray40", "#343638"), hover_color=("#3B8ED0", "#1F6AA5"))

    def _on_delete(self) -> None:
        parent = self.master
        li = getattr(parent, "list_items", None)
        if li is not None:
            try:
                li.remove(self)
            except ValueError:
                pass
        self.destroy()
        if isinstance(parent, ScrollablePathFrame):
            parent._relayout_path_rows()

# --- End Path List Editor Classes ---
