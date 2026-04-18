import customtkinter

from config.profile_state import ProfileState

class OverwriteDialog(customtkinter.CTkToplevel):
    def __init__(self, master, prof_state: ProfileState, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.transient(master)
        self.geometry("400x200")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.title("Overwrite Profile")
        self.prof_state = prof_state
        self.bind("<Map>", self._on_map)

    def _on_map(self, _event=None):
        # Defer past WM paint; on Windows, lift + focus in the same tick as Map often fails.
        self.after(10, self._bring_to_front)

    def _bring_to_front(self):
        self.lift()
        self.focus_set()