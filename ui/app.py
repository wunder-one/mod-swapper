import customtkinter

from file_actions import swap_profiles

class App(customtkinter.CTk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.profile_list = list(cfg.profiles.keys())

        self.title("BG3 Profile Swapper")
        self.geometry(f"{300 * len(self.profile_list)}x340")
        # self.grid_columnconfigure((0, 3), weight=1)
        self.grid_rowconfigure(0, weight=1)

        for i, profile in enumerate(self.profile_list):
            self.grid_columnconfigure(i, weight=1)
            self.profile_frame = ProfileFrame(self, profile, cfg)
            self.profile_frame.grid(row=0, column=i, padx=(0, 10), pady=(10, 10), sticky="nsew")
            self.profile_frame.configure(fg_color="transparent")

    # ----- Full width button for later -----
    #     self.button = customtkinter.CTkButton(self, text="Swap", command=self.button_callback)
    #     self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew", columnspan=len(self.profile_list))

    # def button_callback(self):
    #     pass


class ProfileFrame(customtkinter.CTkFrame):
    def __init__(self, master, profile, cfg):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.variable = customtkinter.StringVar(value="")
        self.profile = profile
        self.cfg = cfg
        print(f"Self Profile: {self.profile}")
        print(f"CFG Active Profile: {self.cfg.active_profile}")

        self.title = customtkinter.CTkLabel(self, text=self.profile, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.label = customtkinter.CTkLabel(self, text=f"Active Profile: {cfg.active_profile}", fg_color="transparent")
        self.label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.activate_button = customtkinter.CTkButton(self, text="Swap", command=self.activate_button_callback)
        self.activate_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

    def activate_button_callback(self):
        if self.profile != self.cfg.active_profile:
            # self.cfg.active_profile = swap_profiles(selected_profile, self.cfg)
            swap_profiles(self.profile, self.cfg)
            self.label.configure(text=f"Active Profile: {self.cfg.active_profile}")
        else:
            print("No profile selected or selected profile is already active.")

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(value)
