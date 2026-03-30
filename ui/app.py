import customtkinter

from file_actions import swap_profiles

class App(customtkinter.CTk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.profile_list = list(cfg.profiles.keys())
        self.profile_frames = []

        self.title("BG3 Profile Swapper")
        self.geometry(f"{190 * len(self.profile_list)}x240")
        self.grid_rowconfigure(0, weight=1)
        self.create_profile_frames()
        # self.test_button = customtkinter.CTkButton(self, text="Refresh", command=self.refresh_profiles)
        # self.test_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew", columnspan=len(self.profile_list))
    def combobox_callback(choice):
        print("combobox dropdown clicked:", choice)

    def create_profile_frames(self):
        for i, profile in enumerate(self.profile_list):
            self.grid_columnconfigure(i, weight=1)
            self.profile_frame = ProfileFrame(self, profile, self.cfg)
            if i == 0:
                self.profile_frame.grid(row=0, column=i, padx=(10, 10), pady=(10, 10), sticky="nsew")
            else:
                self.profile_frame.grid(row=0, column=i, padx=(0, 10), pady=(10, 10), sticky="nsew")
            # self.profile_frame.configure(fg_color="transparent")
            self.profile_frames.append(self.profile_frame)
            new_profile_frame_index = i + 1
        self.new_profile_frame = NewProfileFrame(self, self.cfg)
        self.new_profile_frame.configure(fg_color=("gray86", "gray17"))
        self.new_profile_frame.grid(row=0, column=new_profile_frame_index, padx=(0, 10), pady=(10, 10), sticky="nsew")
        self.update_profile_frames()

    def update_profile_frames(self):
        for frame in self.profile_frames:
            frame.set_active_appearance(frame.profile == self.cfg.active_profile)

    def refresh_profiles(self):
        print("Refreshing profiles...")
        # Clear existing frames
        for frame in self.profile_frames:
            frame.destroy()
        self.profile_frames.clear()

        # Reload profiles from config
        self.cfg.profiles = self.cfg.get_profiles()
        self.profile_list = list(self.cfg.profiles.keys())
        self.create_profile_frames()

    # ----- Full width button for later -----
    # def button_callback(self):
    #     print("Button clicked! Refreshing profiles...")
    #     self.refresh_profiles()


class ProfileFrame(customtkinter.CTkFrame):
    def __init__(self, master, profile, cfg):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.profile = profile
        self.cfg = cfg
        print(f"Self Profile: {self.profile}")
        print(f"CFG Active Profile: {self.cfg.active_profile}")

        self.title = customtkinter.CTkLabel(self, text=self.profile, corner_radius=6)
        self.title.cget("font").configure(size=16, weight="bold")
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.activate_button = customtkinter.CTkButton(self, text="Activate Profile", command=self.activate_button_callback)
        self.activate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def activate_button_callback(self):
        if self.profile != self.cfg.active_profile:
            swap_profiles(self.profile, self.cfg)
        else:
            print("No profile selected or selected profile is already active.")
        self.master.update_profile_frames()

    def set_active_appearance(self, is_active):
        if is_active:
            self.configure(fg_color=("gray86", "gray17"), border_color="green", border_width=2)
            self.activate_button.configure(state="disabled", fg_color=("#F9F9FA", "#343638"), text="Active Profile")
        else:
            self.configure(fg_color=("gray98", "gray11"), border_width=0)
            self.activate_button.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"), text="Activate Profile")

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(value)

class NewProfileFrame(customtkinter.CTkFrame):
    def __init__(self, master, cfg):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.cfg = cfg
