import customtkinter

from file_actions import swap_profiles

class ProfileSelectorFrame(customtkinter.CTkFrame):
    def __init__(self, master, title, status, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title
        self.status = status
        self.radiobuttons = []
        self.variable = customtkinter.StringVar(value="")

        self.title = customtkinter.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.label = customtkinter.CTkLabel(self, text=f"Current Profile: {self.status}", fg_color="transparent")
        self.label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")

        for i, value in enumerate(self.values):
            radiobutton = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.variable)
            radiobutton.grid(row=i + 2, column=0, padx=10, pady=(10, 0), sticky="w")
            self.radiobuttons.append(radiobutton)

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(value)
    

class App(customtkinter.CTk):
    def __init__(self, current_profile=None, profiles=[]):
        super().__init__()
        self.current_profile = current_profile
        self.profiles = profiles

        self.title("BG3 Profile Swapper")
        self.geometry("340x340")
        self.grid_columnconfigure((0, 0), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.profile_selector_frame = ProfileSelectorFrame(self, "Profiles", status=current_profile, values=self.profiles)
        self.profile_selector_frame.grid(row=0, column=0, padx=(0, 10), pady=(10, 0), sticky="nsew")
        self.profile_selector_frame.configure(fg_color="transparent")

        self.button = customtkinter.CTkButton(self, text="Swap", command=self.button_callback)
        self.button.grid(row=3, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

    def button_callback(self):
        print("profile_selector_frame:", self.profile_selector_frame.get())
        selected_profile = self.profile_selector_frame.get()
        if selected_profile and selected_profile != self.current_profile:
            self.current_profile = swap_profiles(self.current_profile, selected_profile)
            self.profile_selector_frame.label.configure(text=f"Current Profile: {self.current_profile}")