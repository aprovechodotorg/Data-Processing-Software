import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from tkinter import simpledialog
import csv


class LEMSDataCruncher_L2(tk.Frame):
    def __init__(self, root): #Set window
        tk.Frame.__init__(self, root)

        #vertical scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")

        # horizontal scrollbar
        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.pack(side="bottom", fill="x")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((8, 8), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

        # File Path Entry
        tk.Label(self.frame, text="Select Folder:").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var, width=150)
        self.folder_path.grid(row=0, column=0)

        # Initialize energy_files as an instance variable
        self.energy_files = []

        # create a button to browse folders on computer
        browse_button = tk.Button(self.frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=0, column=1)

        # Create a notebook to hold tabs
        #self.notebook = ttk.Notebook(self.canvas)
        #self.notebook.pack(side="top", fill="both", expand=True)

        # OK button
        ok_button = tk.Button(self.frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=3, column=0)

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.pack(side=tk.TOP, expand=True)

    def onCanvasMouseWheel(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_okay(self):  # When okay button is pressed
        error = []
        # Create a notebook to hold tabs
        self.notebook = ttk.Notebook(height=30000)
        self.notebook.grid(row=0, column=0)
        for folder in self.energy_files:
            try:
                output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)

                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.grid(row=1, column=0)
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=os.path.basename(os.path.dirname(folder)))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # round to 3 decimals
                round_data = {}
                for name in data:
                    try:
                        rounded = round(data[name].n, 3)
                    except:
                        rounded = data[name]
                    round_data[name] = rounded

                data = round_data

                # Output table
                self.create_output_table(data, units, logs, num_columns=150,
                                         num_rows=300,
                                         folder_path=folder)  # Adjust num_columns and num_rows as needed

                self.frame.configure(height=300*3000)




            except PermissionError:
                error.append(folder)

        if error:
            message = f"One or more files are open in another program. Close them and try again."
            # Error
            messagebox.showerror("Error", message)

        # Set the notebook to recenter the view to top-left when a tab is selected
        self.notebook.bind("<ButtonRelease-1>", lambda event: self.canvas.yview_moveto(0))

    def create_output_table(self, data, units, logs, num_columns, num_rows, folder_path):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        output_table = OutputTable(self.tab_frame, data, units, logs, num_columns, num_rows, folder_path)
        #output_table.pack(fill="both", expand=True)
        output_table.grid(row=0, column=0)

    def on_browse(self): #when browse button is pressed
        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Search for files ending with 'EnergyInputs.csv' in all folders
        self.energy_files = []
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('EnergyInputs.csv'):
                    file_path = os.path.join(root, file)
                    self.energy_files.append(file_path)

        if self.energy_files: #if not empty
            self.file_list = tk.Text(self.frame, wrap="word", width=115)
            self.file_list.grid(row=2, column=0, columnspan=1)
            self.file_list.insert(tk.END, "The following Energy Input Paths were found. Press OK to proceed. \n \n")
            rows = 3
            for path in self.energy_files:
                message = f"* {path} \n"
                self.file_list.insert(tk.END, message)
                rows += 1
            self.file_list.config(height=rows)
            self.file_list.config(state="disabled")

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
class CollapsibleFrame(ttk.Frame):
    def __init__(self, master, text, collapsed=True, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.is_collapsed = tk.BooleanVar(value=collapsed)

        # Header
        self.header = ttk.Label(self, text=f"▼ {text}", style="CollapsibleFrame.TLabel")
        self.header.grid(row=0, column=0, sticky="w", pady=5)
        self.header.bind("<Button-1>", self.toggle)

        # Content Frame
        self.content_frame = tk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="w")

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Call toggle to set initial state
        self.toggle()

    def toggle(self, event=None):
        if self.is_collapsed.get():
            self.content_frame.grid_remove()
            self.header["text"] = f"▼ {self.header['text'][2:]}"
        else:
            self.content_frame.grid()
            self.header["text"] = f"▲ {self.header['text'][2:]}"

        self.is_collapsed.set(not self.is_collapsed.get())
class OutputTable(tk.Frame):
    def __init__(self, root, data, units, logs, num_columns, num_rows, folder_path):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=65)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.warning_frame = tk.Text(self, wrap="none", width=144, height=1)
        self.warning_frame.grid(row=2, column=0, columnspan=6)

        self.text_widget = tk.Text(self, wrap="none", height=num_rows, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        ## Other menu options
        #subtract_bkg_button = tk.Button(self, text="Subtract Background", command=self.on_subtract_background(folder_path=folder_path))
        #subtract_bkg_button.grid(row=4, column=0, padx=5, pady=5)
        # Configure a tag for bold text
        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))

        header = "{:<110}|".format("ALL ENERGY OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        self.cut_table = tk.Text(self, wrap="none", height=num_rows, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))

        self.cut_table.grid(row=3, column=3, padx=0, pady=0, columnspan=3)

        # Bind the MouseWheel event to the on_canvas_mouse_wheel function for both text_widget and cut_table
        self.text_widget.bind("<MouseWheel>", self.on_canvas_mouse_wheel)
        self.cut_table.bind("<MouseWheel>", self.on_canvas_mouse_wheel)

        cut_header = "{:<113}|".format("WEIGHTED METRICS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value

            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.endswith('weighted'):
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")

        cut_header = "{:<70}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<128}|".format("ISO TIERS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<60} |".format("Variable", "Tier")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = value.n
            except:
                val = value

            if not val:
                val = " "
            if not unit:
                unit = " "
            if key.startswith('tier'):
                row = "{:<35} | {:<30} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        cut_header = "{:<69}".format(" ")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 70 + "\n")
        cut_header = "{:<109}|".format("IMPORTANT VARIABLES")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_parameters = ['eff_w_char', 'eff_wo_char', 'char_mass_productivity', 'char_energy_productivity',
                          'cooking_power', 'burn_rate', 'phase_time']
        tot_rows = 1
        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = value.n
                except:
                    val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")

                if any(key.startswith(param) for param in cut_parameters):
                    unit = units.get(key, "")
                    try:
                        val = value.n
                    except:
                        val = value

                    if not val:
                        val = " "
                    if not unit:
                        unit = " "
                    row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                    self.cut_table.insert(tk.END, row + "\n")
                    self.cut_table.insert(tk.END, "_" * 70 + "\n")
        self.text_widget.config(height=tot_rows*200)
        self.cut_table.config(height=tot_rows*200)

        self.text_widget.configure(state="disabled")
        self.warning_frame.configure(state="disabled")

    #def on_subtract_background(self, folder_path):
        #self.energy_path = os.path.join(folder_path,
                                        #f"{os.path.basename(folder_path)}_EnergyOutputs.csv")
        #self.input_path = os.path.join(folder_path,
                                        #f"{os.path.basename(folder_path)}_RawData.csv")
        #self.recal_path = os.path.join(folder_path,
                                        #f"{os.path.basename(folder_path)}_RawData_Recalibrated.csv")
        #self.header_path = os.path.join(folder_path,
                                        #f"{os.path.basename(folder_path)}_Header.csv")
        #self.log_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}_log.txt")

        #LEMS_Adjust_Calibrations(self.input_path, self.energy_path, self.recal_path, self.header_path, self.log_path, inputmethod=1)

    def find_text(self):
        search_text = self.find_entry.get()

        if search_text:
            self.text_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("highlight", background="yellow")

        if search_text:
            self.cut_table.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.cut_table.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.cut_table.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.cut_table.tag_configure("highlight", background="yellow")

    def on_canvas_mouse_wheel(self, event):
        # Get the current scroll position
        text_widget_position = self.text_widget.yview()[0]
        cut_table_position = self.cut_table.yview()[0]

        # Adjust the view of the widgets based on the mouse wheel movement
        if event.delta > 0:
            new_position = max(text_widget_position - 0.1, 0)
        elif event.delta < 0:
            new_position = min(text_widget_position + 0.1, 1)

        # Set the new scroll position for both widgets
        self.text_widget.yview_moveto(new_position)
        self.cut_table.yview_moveto(new_position)

        # Focus on the cut_table to ensure it receives mouse wheel events
        self.cut_table.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App L2")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()