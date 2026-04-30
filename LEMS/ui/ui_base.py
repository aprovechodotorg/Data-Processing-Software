import tkinter as tk
from typing import Optional, List


class ExitButtonMixin:
    def add_exit_button(self, root, row=0, column=4):
        btn = tk.Button(
            self,
            text="EXIT",
            command=root.quit,
            bg="red",
            fg="white"
        )
        btn.grid(row=row, column=column, padx=(410, 5), pady=5, sticky="e")


class FormFrame(tk.LabelFrame):
    """
    Generic form builder for label + entry (+ unit) layouts.
    Defensive signature to avoid import/version mismatch issues.
    """

    def __init__(
        self,
        root,
        frame_title,
        fields=None,
        units: Optional[List[str]] = None,
        defaults: Optional[dict] = None,
        multiline: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(root, text=frame_title, padx=10, pady=10)

        if fields is None:
            fields = {}

        self.entries = {}
        self.units = {}
        defaults = defaults or {}

        for row, (key, label_text) in enumerate(fields.items()):
            tk.Label(self, text=f"{label_text}:").grid(row=row, column=0, sticky="w")

            if multiline:
                widget = tk.Text(self, height=6, width=51, wrap="word")
            else:
                widget = tk.Entry(self)

            if key in defaults:
                widget.insert("1.0" if multiline else 0, defaults[key])

            widget.grid(row=row, column=2)
            self.entries[key] = widget

            if units:
                unit_entry = tk.Entry(self, width=10)
                unit_entry.insert(0, units[row])
                unit_entry.grid(row=row, column=3)
                self.units[key] = unit_entry
