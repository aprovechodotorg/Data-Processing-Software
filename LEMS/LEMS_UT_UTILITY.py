import tkinter as tk
import io
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

class InfoToolTip:

    def __init__(self):
        self.hover_popup = None
        self.latex_image = None

    def show_info_popup(self, message, anchor_widget, formula=None, align="left"):
        if self.hover_popup is not None:

            # Destroy existing popups first so they do not stack up

            self.hover_popup.destroy()
            self.hover_popup = None


        # Creating the new popup window
        self.hover_popup = tk.Toplevel(anchor_widget)
        self.hover_popup.wm_overrideredirect(True)
        self.hover_popup.attributes("-topmost", True)

        # Position to the left of the widget
        popup_width = 270  # approximate width of the popup
        x = anchor_widget.winfo_rootx() - popup_width
        y = anchor_widget.winfo_rooty() + 20
        self.hover_popup.geometry(f"+{x}+{y}")

        # Alter the popup frame, adjusting color and padding (borders)
        frame = tk.Frame(self.hover_popup, bg="lightyellow", padx=5, pady=5, bd=1, relief="solid")
        frame.pack()

        label = tk.Label(frame, text=message, bg="lightyellow", justify="left", wraplength=250)
        label.pack()

        if formula:
            image = self.create_latex_image(formula)
            self.latex_image = ImageTk.PhotoImage(image)  # Keep a reference!
            img_label = tk.Label(frame, image=self.latex_image, bg="lightyellow")
            img_label.pack()


    def hide_info_popup(self):
        if hasattr(self, "hover_popup") and self.hover_popup is not None:
            self.hover_popup.destroy()
            self.hover_popup = None

    def create_latex_image(self, formula):
        fig = Figure(figsize=(0.01, 0.01))
        canvas = FigureCanvasAgg(fig)

        ax = fig.add_subplot(111)
        fig.patch.set_visible(False)
        ax.axis("off")

        ax.text(0, 0, f"${formula}$", fontsize=14)

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            bbox_inches="tight",
            pad_inches=0.2,
            transparent=True
        )

        buf.seek(0)
        return Image.open(buf)

 def highlight_search_text(search_text, text_widgets, tag_name = "highlight"):

    for widget in text_widgets:
        widget.tag_remove("highlight", "1.0", tk.END)

    if not search_text:
        return


     for widget in text_widgets:
            start_pos = "1.0"

            while True:
                start_pos = widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            widget.tag_configure(tag_name, background="yellow")



    def read_csv(filepath):
        variable_data = []
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                variable_data.append(row)
        return variable_data

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
