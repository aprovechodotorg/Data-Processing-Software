import tkinter as tk

from ui_base import FormFrame, ExitButtonMixin
from ui_forms import (
    TEST_INFO_FIELDS,
    COMMENTS_FIELDS,
    ENVIRONMENT_FIELDS,
    ENVIRONMENT_UNITS,
)

from ui_scroll import ScrollableFrame

class LEMSDataInput(tk.Frame, ExitButtonMixin):
    def __init__(self, root):
        super().__init__(root)
        self.pack(fill="both", expand=True)

        self.add_exit_button(root)

        self.test_info = FormFrame(
            self,
            "Test Information",
            TEST_INFO_FIELDS
        )
        self.test_info.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.comments = FormFrame(
            self,
            "Comments",
            COMMENTS_FIELDS,
            multiline=True
        )
        self.comments.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.environment = FormFrame(
            self,
            "Environmental Conditions",
            ENVIRONMENT_FIELDS,
            ENVIRONMENT_UNITS
        )
        self.environment.grid(row=3, column=0, sticky="w", padx=10, pady=5)


if __name__ == "__main__":
    from ui_scroll import ScrollableFrame
    root = tk.Tk()
    root.title("App L1. Version: 7.0")
    root.geometry("1200x600")

    scroll_container = ScrollableFrame(root)
    scroll_container.pack(fill="both", expand=True)

    app = LEMSDataInput(scroll_container.scroll)

