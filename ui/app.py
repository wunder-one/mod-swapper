import customtkinter

from file_actions import swap_profiles

class App(customtkinter.CTk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg

        self.title("BG3 Profile Swapper")
        self.geometry("340x340")
        self.grid_columnconfigure((0, 0), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.profile_selector_frame = ProfileSelectorFrame(self, cfg)
        self.profile_selector_frame.grid(row=0, column=0, padx=(0, 10), pady=(10, 0), sticky="nsew")
        self.profile_selector_frame.configure(fg_color="transparent")

        self.button = customtkinter.CTkButton(self, text="Swap", command=self.button_callback)
        self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

    def button_callback(self):
        selected_profile = self.profile_selector_frame.get()
        if selected_profile and selected_profile != self.cfg.active_profile:
            self.cfg.active_profile = swap_profiles(selected_profile, self.cfg)
            self.profile_selector_frame.label.configure(text=f"Active Profile: {self.cfg.active_profile}")
        else:
            print("No profile selected or selected profile is already active.")


class ProfileSelectorFrame(customtkinter.CTkFrame):
    def __init__(self, master, cfg):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.variable = customtkinter.StringVar(value="")
        self.radiobuttons = []

        self.title = customtkinter.CTkLabel(self, text="Profiles", fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.label = customtkinter.CTkLabel(self, text=f"Active Profile: {cfg.active_profile}", fg_color="transparent")
        self.label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")

        for i, value in enumerate(cfg.profiles.keys()):
            radiobutton = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.variable)
            radiobutton.grid(row=i + 2, column=0, padx=10, pady=(10, 0), sticky="w")
            self.radiobuttons.append(radiobutton)

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(value)
