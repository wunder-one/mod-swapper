import customtkinter
from tkinter import filedialog

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master, user_settings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.geometry("400x600")
        self.grid_columnconfigure(0, weight=1)
        self.title("Settings")
        self.user_settings = user_settings

        self.title_header = customtkinter.CTkLabel(self, text="Settings", fg_color="gray30", corner_radius=6)
        self.title_header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.install_type_fr = DropdownPicker(self, "Install Type")
        self.install_type_fr.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")        

        self.game_folder_fr = SingleDirPathSetting(self, "Game Folder")
        self.game_folder_fr.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.swap_paths_fr = PathListEditor(self, "Files and folders to swap")
        self.swap_paths_fr.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")

    def apply_settings(self):
        # fetch current values from settings window
        # and apply to master.user_settings.<field_name>
        self.user_settings.save_settings()

class DropdownPicker(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.title = title
        self.configure(fg_color="transparent")

        self.title = customtkinter.CTkLabel(self, text=self.title)
        self.title.grid(row=0, column=0, padx=0, pady=0, sticky="w")

        self.install_type = customtkinter.CTkOptionMenu(self, values=["Steam", "GOG Galaxy", "Custom"])
        self.install_type.grid(row=2, column=0, padx=0, pady=0, sticky="w")

class SingleDirPathSetting(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.title = title
        self.configure(fg_color="transparent")

        self.title = customtkinter.CTkLabel(self, text=self.title)
        self.title.grid(row=0, column=0, padx=0, pady=0, sticky="w")

        self.textbox = customtkinter.CTkTextbox(master=self, height=28, wrap='none')
        self.textbox.grid(row=1, column=0, padx=(0, 10), pady=0, sticky="ew")

        self.browse_btn = customtkinter.CTkButton(self, text="Browse...", command=self.browse_folders, width=100)
        self.browse_btn.grid(row=1, column=1, padx=0, pady=0, sticky="e")

    def browse_folders(self):
        filedialog.askdirectory(mustexist=True)

class PathListEditor(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.title = title
        self.configure(fg_color="transparent")

        self.title = customtkinter.CTkLabel(self, text=self.title)
        self.title.grid(row=0, column=0, padx=0, pady=0, sticky="w")

        self.scrollable_path_frame = ScrollablePathFrame(self)
        self.scrollable_path_frame.grid(row=1, column=0, columnspan=4, padx=0, pady=0, sticky="ew")

class ScrollablePathFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        # self.configure(fg_color="transparent")
        # TODO: replace temp_values
        self.temp_values = ["this", "is", "a list"]
        self.populate_list()

    def populate_list(self):
        for i in range(len(self.temp_values)):
            self.textbox = customtkinter.CTkTextbox(master=self, height=28, wrap='none')
            self.textbox.insert("0.0", self.temp_values[i])
            self.textbox.grid(row=i, column=0, padx=10, pady=0, sticky="ew")
            self.textbox.configure(state="disabled")
            self.delete_btn = customtkinter.CTkButton(self, text="x", width=28)
            self.delete_btn.grid(row=i, column=1, sticky="e")

