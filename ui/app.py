import customtkinter
from profile_state import ProfileState
from user_settings import UserSettings
from functions.file_actions import swap_profiles, create_new_profile

class App(customtkinter.CTk):
    def __init__(self, prof_state: ProfileState, user_settings: UserSettings):
        super().__init__()
        self.prof_state = prof_state
        self.user_settings = user_settings
        self.profile_list = list(self.prof_state.profiles.keys())
        self.profile_frames = {}

        self.title("BG3 Profile Swapper")
        no_of_rows = (len(self.profile_list) - 1) // 3 + 1
        self.geometry(f"{190 * 3}x{52 + 96 * no_of_rows}")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        # self.grid_rowconfigure(1, weight=1)

        self.button_bar = ButtonBar(self, self.profile_list, self.prof_state, self.user_settings)
        self.button_bar.grid(row=0, column=0, pady=(0, 0), columnspan=3, sticky="ew")
        self.button_bar.configure(corner_radius=0)
        self.create_profile_frames()

    def create_profile_frames(self):
        self.profile_list = list(self.prof_state.profiles.keys())
        for i, profile_name in enumerate(self.profile_list):
            profile_frame = ProfileFrame(self, profile_name, self.prof_state, self.user_settings)
            left_pad = 10 if i % 3 == 0 else 0
            profile_frame.grid(row=i // 3 + 1, column=i % 3, padx=(left_pad, 10), pady=(10, 0), sticky="nsew")
            # self.profile_frame.configure(fg_color="transparent")
            self.profile_frames[profile_name] = profile_frame
        self.update_profile_frames()

    def update_profile_frames(self):
        for frame_title in self.profile_frames:
            frame = self.profile_frames[frame_title]
            frame.set_active_appearance(frame.profile == self.prof_state.active_profile)

    def refresh_profiles(self):
        print("Refreshing profiles...")
        # Clear existing frames
        for frame_title in self.profile_frames:
            frame = self.profile_frames[frame_title]
            frame.destroy()
        self.profile_frames.clear()
        self.create_profile_frames()

    # ----- Full width button for later -----
    # def button_callback(self):
    #     print("Button clicked! Refreshing profiles...")
    #     self.refresh_profiles()


class ProfileFrame(customtkinter.CTkFrame):
    def __init__(self, master, profile, prof_state: ProfileState, user_settings: UserSettings):
        super().__init__(master)
        self.profile = profile
        self.prof_state = prof_state
        self.user_settings = user_settings

        # Setup grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Profile title
        self.title = customtkinter.CTkLabel(self, text=self.profile, corner_radius=6)
        self.title.cget("font").configure(size=16, weight="bold")
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # Profile action buttons
        self.activate_button = customtkinter.CTkButton(self, text="Activate Profile", command=self.activate_button_callback)
        self.activate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def activate_button_callback(self):
        try:
            swap_profiles(self.profile, self.prof_state, self.user_settings)
            # Success! Play sound or update status here
        except ValueError as e:
            print(f"Notice: {e}")
        except Exception as e:
            print(f"Error swapping profiles: {e}")
        # Always update the UI frames to reflect the current state
        self.master.update_profile_frames() # type: ignore

    def set_active_appearance(self, is_active: bool):
        if is_active:
            self.configure(fg_color=("gray86", "gray17"), border_color="green", border_width=2)
            self.activate_button.configure(state="disabled", fg_color=("#F9F9FA", "#343638"), text="Active Profile")
        else:
            self.configure(fg_color=("gray98", "gray11"), border_width=0)
            self.activate_button.configure(state="normal", fg_color=("#3B8ED0", "#1F6AA5"), text="Activate Profile")

class ButtonBar(customtkinter.CTkFrame):
    def __init__(self, master, profile, prof_state: ProfileState, user_settings: UserSettings):
        super().__init__(master)
        self.grid_columnconfigure(2, weight=1)
        self.profile = profile
        self.prof_state = prof_state
        self.user_settings = user_settings

        self.new_profile_button = customtkinter.CTkButton(self, text="New Profile", command=self.new_profile_callback, width=100)
        self.new_profile_button.grid(row=0, column=0, padx=(6, 0), pady=6)

        self.overwrite_button = customtkinter.CTkButton(self, text="Overwrite Profile", command=self.new_profile_callback, width=100)
        self.overwrite_button.grid(row=0, column=1, padx=(6, 0), pady=6)

        self.settings_button = customtkinter.CTkButton(self, text="Settings", command=self.master.refresh_profiles, width=100)  # type: ignore
        self.settings_button.grid(row=0, column=3, padx=(0, 6), pady=6, sticky="e")

    def new_profile_callback(self):
        new_profile_dialog = customtkinter.CTkInputDialog(text="This will create a new profile from your currently active mods.\n\nProfile Name:", title="New Profile")
        new_name = new_profile_dialog.get_input()
        if new_name is None or new_name.strip() == "":
            print("Profile creation cancelled or invalid name entered.")
            return
        print("Name:", new_name)
        create_new_profile(new_name, self.prof_state, self.user_settings)
        self.master.refresh_profiles()  # type: ignore