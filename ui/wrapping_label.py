import customtkinter


class WrappingLabel(customtkinter.CTkFrame):
    def __init__(self, master, text: str, *args, **kwargs):
        border_width = kwargs.pop("border_width", 0)
        super().__init__(master, *args, border_width=border_width, **kwargs)
        self.text = text

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(self, text=text, *args, **kwargs)
        self.label.grid(padx=10, pady=10, sticky="wesn")

        self._bind_id: str = self.bind("<Configure>", self._wrap)  # type: ignore

    def _wrap(self, _):
        self.label.configure(wraplength=self.winfo_width() * 0.7)
