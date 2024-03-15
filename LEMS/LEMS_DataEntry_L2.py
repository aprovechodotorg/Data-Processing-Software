import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from tkinter import simpledialog
import csv
from PEMS_L2 import PEMS_L2


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
        error = 0
        try:
            # Write selected file paths to the csv, overwriting the content
            selected_indices = self.file_selection_listbox.curselection()
            selected_paths = [self.file_selection_listbox.get(idx) for idx in selected_indices]

            csv_file_path = os.path.join(self.folder_path, "DataEntrySheetFilePaths.csv")
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for path in selected_paths:
                    writer.writerow([path])
            self.energy_files = selected_paths
        except PermissionError:
            error = 1
            message = f"File: {csv_file_path} is open.. Close it and try again."
            # Error
            messagebox.showerror("Error", message)

        if error == 0:
            error = []
            input_list = []
            for folder in self.energy_files:
                try:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                    input_list.append(output_path)
                except PermissionError:
                    error.append(folder)
            try:
                emission_list = []
                log_path = self.folder_path + '//log.txt'
                output_path = self.folder_path + '//UnformattedL2.csv'
                data, units, logs = PEMS_L2(input_list, emission_list, output_path, log_path)
            except PermissionError:
                error.append(folder)

            if error:
                message = f"One or more EnergyOutput or UnformattedL2 files are open in another program. Close them and try again."
                # Error
                messagebox.showerror("Error", message)
            else:
                self.frame.destroy()
                # Create a notebook to hold tabs
                self.notebook = ttk.Notebook(height=30000)
                self.notebook.grid(row=0, column=0)
                input_list = []
                for folder in self.energy_files:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)

                    input_list.append(output_path)

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

                ########################################################
                #Full comparison table
                # Create a new frame for tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.grid(row=1, column=0)
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text='All Energy Output Comparision')

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                emission_list = []
                log_path = self.folder_path + '//log.txt'
                output_path = self.folder_path + '//UnformattedL2.csv'
                data, units, logs = PEMS_L2(input_list, emission_list, output_path, log_path)

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
                self.create_compare_table(data, units, logs)

                self.frame.configure(height=300 * 3000)

                ######################################################33
                #ISO comparison table
                # Create a new frame for tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.grid(row=1, column=0)
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text='ISO Comparision')

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Output table
                self.create_iso_table(data, units, logs)

                self.frame.configure(height=300 * 3000)


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

    def create_compare_table(self, data, units, logs):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        compare_table = CompareTable(self.tab_frame, data, units, logs)
        #output_table.pack(fill="both", expand=True)
        compare_table.grid(row=0, column=0)

    def create_iso_table(self, data, units, logs):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        iso_table = ISOTable(self.tab_frame, data, units, logs)
        #output_table.pack(fill="both", expand=True)
        iso_table.grid(row=0, column=0)

    def on_browse(self): #when browse button is pressed
        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Check if DataEntrySheetFilePaths.csv exists in the selected folder
        csv_file_path = os.path.join(self.folder_path, "DataEntrySheetFilePaths.csv")
        existing_file_paths = []
        if os.path.exists(csv_file_path):
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    existing_file_paths.append(row[0])

            # Search for files ending with 'EnergyInputs.csv' in all folders
            self.energy_files = []
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith('EnergyInputs.csv'):
                        file_path = os.path.join(root, file)
                        #if file_path not in existing_file_paths:
                        self.energy_files.append(file_path)

            # Create a multiselection box in tkinter
            postselect = []
            if existing_file_paths or self.energy_files:
                instructions = f'The following paths were found within this directory.\n' \
                               f'Any preselected path were found in: {csv_file_path}\n' \
                               f'Please select which tests you would like to compare and press OK.'
                message = tk.Text(self.frame, wrap="word", width=112, height=4)
                message.grid(row=1, column=0)
                message.insert(tk.END, instructions)

                for file in self.energy_files:
                    if file not in existing_file_paths:
                        postselect.append(file)

                full_files = existing_file_paths + postselect
                defualt_selection = len(existing_file_paths)

                self.selected_files = tk.StringVar(value=list(full_files))
                self.file_selection_listbox = tk.Listbox(self.frame, listvariable=self.selected_files,
                                                         selectmode=tk.MULTIPLE, width=150, height=len(full_files))
                self.file_selection_listbox.grid(row=2, column=0, columnspan=1)

                self.file_selection_listbox.selection_set(0, defualt_selection -1)

                ok_button = tk.Button(self.frame, text="OK", command=self.on_ok)
                ok_button.grid(row=3, column=0)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class ISOTable(tk.Frame):
    def __init__(self, root, data, units, logs):
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

        self.header = tk.Text(self, wrap="word", height=6, width=149)
        self.header.grid(row=2, column=0, columnspan=11, padx=0, pady=0, rowspan=1)

        self.text_widget = tk.Text(self, wrap="word", height=72, width=149)
        self.text_widget.grid(row=3, column=0, columnspan=11, padx=0, pady=0)

        # Configure a tag for bold text
        self.header.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))

        header = "{:<282}|".format("ISO TABLE")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
        header = "{:<60} | {:<16} | {:<18} | {:<9} | {:<11} | {:<12} | {:<11} | {:<11} | {:<9} | {:<40} |".format("Variable", "Units",
                                                                                         "Average", "N", "Standard Dev",
                                                                                         "Interval", "High Tier", "Low Tier",
                                                                                         "COV", "CI")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")

        phases = ['_weighted', '_hp', '_mp', '_lp']
        params = ['eff_wo_char', 'eff_w_char', 'char_energy_productivity', 'char_mass_productivity', 'cooking_power', 'burn_rate']

        for phase in phases:
            if phase == '_weighted':
                header = "{:<280}|".format("COMBINED")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
            elif phase == '_hp':
                header = "{:<278}|".format("HIGH POWER")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
            elif phase == '_mp':
                header = "{:<274}|".format("MEDIUM POWER")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
            elif phase == '_lp':
                header = "{:<278}|".format("LOW POWER")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")

            phase_params = [p + phase for p in params]

            # Sort the keys based on the index of the parameter in the params list
            sorted_keys = sorted(data.keys(),
                                 key=lambda x: phase_params.index(x) if x in phase_params else float('inf'))

            for key in sorted_keys:
                if key.startswith('variable'):
                    pass
                elif key.endswith(phase) and key in phase_params:
                    value = data[key]
                    unit = units.get(key, "")
                    val = ""#value['values']
                    avg = value['average']
                    n = value['N']
                    stdev = value['stdev']
                    int = value['interval']
                    high = value['high_tier']
                    low = value['low_tier']
                    cov = value['COV']
                    ci = value['CI']

                    if not val:
                        val = " "
                    if not unit:
                        unit = " "
                    if not avg:
                        avg = " "
                    if not n:
                        n = " "
                    if not stdev:
                        stdev = " "
                    if not int:
                        int = " "
                    if not high:
                        high = " "
                    if not low:
                        low = " "
                    if not cov:
                        cov = " "
                    if not ci:
                        ci = " "
                    row = "{:<33} | {:<9} | {:<12} | {:<4} | {:<11} | {:<8} | {:<8} | {:<8} | {:<6} | {:<20} |".format(key, unit, avg, n, stdev, int, high, low, cov, ci)
                    self.text_widget.insert(tk.END, row + "\n")
                    self.text_widget.insert(tk.END, "_" * 148 + "\n")

        self.text_widget.config(height=self.winfo_height() * 25)

        self.text_widget.configure(state="disabled")
        self.header.configure(state="disabled")

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

class CompareTable(tk.Frame):
    def __init__(self, root, data, units, logs):
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

        self.header = tk.Text(self, wrap="word", height=6, width=149)
        self.header.grid(row=2, column=0, columnspan=11, padx=0, pady=0, rowspan=1)

        self.text_widget = tk.Text(self, wrap="word", height=72, width=149)
        self.text_widget.grid(row=3, column=0, columnspan=11, padx=0, pady=0)

        # Configure a tag for bold text
        self.header.tag_configure("bold", font=("Helvetica", 12, "bold"))

        header = "{:<266}|".format("ALL ENERGY OUTPUTS")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
        header = "{:<60} | {:<16} | {:<18} | {:<9} | {:<11} | {:<12} | {:<11} | {:<11} | {:<9} | {:<40} |".format("Variable", "Units",
                                                                                         "Average", "N", "Standard Dev",
                                                                                         "Interval", "High Tier", "Low Tier",
                                                                                         "COV", "CI")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")

        tot_rows = 1
        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                val = ""#value['values']
                avg = value['average']
                n = value['N']
                stdev = value['stdev']
                int = value['interval']
                high = value['high_tier']
                low = value['low_tier']
                cov = value['COV']
                ci = value['CI']

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                if not avg:
                    avg = " "
                if not n:
                    n = " "
                if not stdev:
                    stdev = " "
                if not int:
                    int = " "
                if not high:
                    high = " "
                if not low:
                    low = " "
                if not cov:
                    cov = " "
                if not ci:
                    ci = " "
                row = "{:<33} | {:<9} | {:<12} | {:<4} | {:<11} | {:<8} | {:<8} | {:<8} | {:<6} | {:<20} |".format(key, unit, avg, n, stdev, int, high, low, cov, ci)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 148 + "\n")

        self.text_widget.config(height=self.winfo_height() * 25)

        self.text_widget.configure(state="disabled")
        self.header.configure(state="disabled")


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

        self.cut_table.grid(row=3, column=3, padx=0, pady=0, columnspan=3, rowspan=self.winfo_height()*30)

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

            # Check condition and highlight in red with warning message
            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) > 55 and float(val) < 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is higher than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 100. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is lower than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            ########################################################################3
            #TE wo char
            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 55 and float(val) < 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is higher than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 100. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="yellow")
                        self.warning_frame.tag_add("yellow", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is lower than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")

                except:
                    pass
            ##########################################################################################
            #Char productivity
            if key.startswith('char_energy_productivity') or key.startswith('char_mass_productivity'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the char_mass (char created) is not negative.\n"
                        warning_message_4 = f"      Check that the gross calorific value for charcoal is correct.\n"
                        warning_message_5 = f"      Check that no fuels that are not char were entered with a carbon fraction above 0.75.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #############################################################
            #char mass
            if key.startswith('char_mass_hp') or key.startswith('char_mass_mp') or key.startswith('char_mass_lp'):
                try:
                    if val and float(val) > 0.050:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is a large mass. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_5 = f"      Check that no fuels that are not char were entered with a carbon fraction above 0.75.\n"
                        warning_message = warning_message_1 + warning_message_5

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #############################################################
            # water temp
            if key.startswith('initial_water_temp'):
                try:
                    delta = abs(float(val) - float(data['initial_air_temp'].n))
                    if val and delta > 10:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 10 degrees from ambient temp.\n"
                        warning_message = warning_message_1

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #######################################################33
            #ISO checks
            if key.startswith('phase_time'):
                try:
                    if val and float(val) < 30:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO WARNING:\n')
                        warning_message_1 = f"  {key} is less than 30 minutes. ISO tests require 30 minute phase periods.\n"
                        warning_message_2 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            if key.startswith('phase_time'):
                try:
                    if val and float(val) > 35:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO WARNING:\n')
                        warning_message_1 = f"  {key} is more than 35. ISO tests require a maximum of 35 minute phase periods (including shutdown).\n"
                        warning_message_2 = f"      Test phases may be 60 minutes long if a single phase is being run.\n"
                        warning_message_3 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            if key.startswith('end_water_temp'):
                try:
                    phase = key[-3:]
                    max_temp = data['max_water_temp_pot1' + phase]
                    delta = float(max_temp.n) - float(val)
                    print(delta)
                    if val and (delta > 5 or delta < 5) and float(data['phase_time' + phase]) < 35:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO WARNING:\n')
                        warning_message_1 = f"  max_water_temp_pot1' {phase} - {key} is not 5 degrees. " \
                                            f"\n    ISO tests require a shutdown period of 5 minutes or when the max water temperture drops to 5 degrees below boiling temperature..\n"
                        warning_message_2 = f"      This warning may be ignored if the 5minute shutdown procedure was performed.\n"
                        warning_message_3 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('firepower_w_char_mp'):
                try:
                    hp = float(data['firepower_w_char_hp'])
                    mp = float(val)
                    lp = float(data['firepower_w_char_lp'])
                    result = lp <= mp <= hp and lp + 1 <= mp <= hp - 1
                    if result:
                        pass
                    else:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO WARNING:\n')
                        warning_message_1 = f"  {key} not between high power and low power. ISO tests require medium power firepower to be between high and low power.\n"
                        warning_message = warning_message_1

                        self.warning_frame.insert(tk.END, warning_message)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        self.warning_frame.tag_configure("red", foreground="red")
                        self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
        self.text_widget.config(height=self.winfo_height()*(32-num_lines))
        self.cut_table.config(height=self.winfo_height()*(32-num_lines))

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

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App L2")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()