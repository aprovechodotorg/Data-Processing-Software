import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from tkinter import simpledialog
import csv
from LEMS_FormatData_L3 import LEMS_FormatData_L3


class LEMSDataCruncher_L3(tk.Frame):
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

        instructions = f"Select a folder which contains test folders with Level 2 outputs to analyze."
        self.instructions = tk.Text(self.frame, wrap="word", height=1, width=90)
        self.instructions.insert(tk.END, instructions)
        self.instructions.grid(row=0, column=0, columnspan=2)
        self.instructions.config(state="disabled")

        # File Path Entry
        tk.Label(self.frame, text="Select Folder:").grid(row=1, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var, width=150)
        self.folder_path.grid(row=1, column=0)

        # Initialize energy_files as an instance variable
        self.energy_files = []

        # create a button to browse folders on computer
        browse_button = tk.Button(self.frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=1, column=1)

        # OK button
        ok_button = tk.Button(self.frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=4, column=0)

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

            csv_file_path = os.path.join(self.folder_path, "UnformattedDataL2FilePaths.csv")
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for path in selected_paths:
                    writer.writerow([path])
            self.L2_files = selected_paths
        except PermissionError:
            error = 1
            message = f"File: {csv_file_path} is open.. Close it and try again."
            # Error
            messagebox.showerror("Error", message)

        if error == 0:
            error = []
            input_list = []
            for folder in self.L2_files:
                try:
                    [names, units, values, data] = io.load_L2_constant_inputs(folder)
                    input_list.append(folder)
                except PermissionError:
                    error.append(folder)
            try:
                log_path = self.folder_path + '//log.txt'
                output_path = self.folder_path + '//UnFormattedDataL3.csv'
                data, units, logs = LEMS_FormatData_L3(selected_paths, output_path,log_path)
            except PermissionError:
                error.append(folder)

            if error:
                message = f"One or more UnFormattedDataL2 or UnFormattedDataL3 files are open in another program. Close them and try again."
                # Error
                messagebox.showerror("Error", message)
            else:
                self.frame.destroy()
                # Create a notebook to hold tabs
                self.main_frame = tk.Frame(self.canvas, background="#ffffff")
                # self.frame.bind("<Configure>", self.onFrameConfigure)
                self.notebook = ScrollableNotebook(root, wheelscroll=True, tabmenu=True)
                # self.notebook = ttk.Notebook(self.main_frame, height=30000)
                self.notebook.grid(row=0, column=0, sticky="nsew")
                # Create a notebook to hold tabs
                #self.notebook = ttk.Notebook(height=30000)
                #self.notebook.grid(row=0, column=0)
                #L3
                # L3 table
                data, units, logs = LEMS_FormatData_L3(input_list, output_path, log_path)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=os.path.basename('All Output Comparison'))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # L3 table
                self.create_L3_table(data, units)  # Adjust num_columns and num_rows as needed

                self.frame.configure(height=300 * 3000)

                # L3 ISO
                # L3 ISO table
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=os.path.basename('ISO Comparison'))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # L3 table
                self.create_L3iso_table(data, units)  # Adjust num_columns and num_rows as needed

                self.frame.configure(height=300 * 3000)
                
                input_list = []
                for folder in self.L2_files:
                    [names, units, values, data] = io.load_L2_constant_inputs(folder)

                    input_list.append(folder)

                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    #self.tab_frame.grid(row=1, column=0)
                    self.tab_frame.pack(side="left")
                    # Add the tab to the notebook with the folder name as the tab label
                    testname = os.path.basename(os.path.dirname(folder))
                    self.notebook.add(self.tab_frame, text=testname + ' All Outputs')

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
                    self.create_compare_table(data, units, testname)  # Adjust num_columns and num_rows as needed

                    self.frame.configure(height=300*3000)

                    #ISO table
                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    #self.tab_frame.grid(row=1, column=0)
                    self.tab_frame.pack(side="left")
                    # Add the tab to the notebook with the folder name as the tab label
                    self.notebook.add(self.tab_frame, text=testname + ' ISO Table')

                    # Set up the frame as you did for the original frame
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)

                    # ISO table
                    self.create_iso_table(data, units, testname)  # Adjust num_columns and num_rows as needed

                    self.frame.configure(height=300 * 3000)



    def create_compare_table(self, data, units, testname):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        compare_table = CompareTable(self.tab_frame, data, units, testname)
        # output_table.pack(fill="both", expand=True)
        compare_table.grid(row=0, column=0)

    def create_iso_table(self, data, units, testname):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        iso_table = ISOTable(self.tab_frame, data, units, testname)
        #output_table.pack(fill="both", expand=True)
        iso_table.grid(row=0, column=0)

    def create_L3_table(self, data, units):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        L3_table = L3Table(self.tab_frame, data, units)
        #output_table.pack(fill="both", expand=True)
        L3_table.grid(row=0, column=0)

    def create_L3iso_table(self, data, units):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        L3_table = L3ISOTable(self.tab_frame, data, units)
        #output_table.pack(fill="both", expand=True)
        L3_table.grid(row=0, column=0)
    def on_browse(self): #when browse button is pressed
        self.destroy_widgets()
        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Check if DataEntrySheetFilePaths.csv exists in the selected folder
        csv_file_path = os.path.join(self.folder_path, "UnformattedDataL2FilePaths.csv")
        existing_file_paths = []
        if os.path.exists(csv_file_path):
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    existing_file_paths.append(row[0])

        # Search for files ending with 'UnformattedL2.csv' in all folders
        self.L2_files = []
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('UnFormattedDataL2.csv'):
                    file_path = os.path.join(root, file)
                    #if file_path not in existing_file_paths:
                    self.L2_files.append(file_path)

        # Create a multiselection box in tkinter
        postselect = []
        if existing_file_paths or self.L2_files:
            instructions = f'The following paths were found within this directory.\n' \
                           f'Any preselected path were found in: {csv_file_path}\n' \
                           f'Please select which tests you would like to compare and press OK.'
            message = tk.Text(self.frame, wrap="word", width=112, height=4)
            message.grid(row=2, column=0)
            message.insert(tk.END, instructions)
            message.configure(state="disabled")

            for file in self.L2_files:
                if file not in existing_file_paths:
                    postselect.append(file)

            full_files = existing_file_paths + postselect
            defualt_selection = len(existing_file_paths)

            self.selected_files = tk.StringVar(value=list(full_files))
            self.file_selection_listbox = tk.Listbox(self.frame, listvariable=self.selected_files,
                                                     selectmode=tk.MULTIPLE, width=150, height=len(full_files))
            self.file_selection_listbox.grid(row=3, column=0, columnspan=1)

            self.file_selection_listbox.selection_set(0, defualt_selection - 1)

            ok_button = tk.Button(self.frame, text="OK", command=self.on_ok)
            ok_button.grid(row=4, column=0)
        else:
            instructions = f'No files ending with EnergyInputs were found inside this folder. ' \
                           f'Please check that files exist and are named correctly before trying again.'
            message = tk.Text(self.frame, wrap="word", width=112, height=4)
            message.grid(row=2, column=0)
            message.insert(tk.END, instructions)
            message.configure(state="disabled")

    def destroy_widgets(self):
        """
        Destroy previously created widgets.
        """
        if hasattr(self, 'message'):
            self.message.destroy()
        if hasattr(self, 'file_selection_listbox'):
            self.file_selection_listbox.destroy()
        if hasattr(self, 'ok_button'):
            self.ok_button.destroy()

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class L3ISOTable(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)


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
                    val = ""  # value['values']
                    avg = value['averageaverage']
                    n = value['Naverage']
                    stdev = value['stadevaverage']
                    int = value['intervalaverage']
                    high = value['high_tieraverage']
                    low = value['low_tieraverage']
                    cov = value['COVaverage']
                    ci = value['CIaverage']

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

class L3Table(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)


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
                avg = value['averageaverage']
                n = value['Naverage']
                stdev = value['stadevaverage']
                int = value['intervalaverage']
                high = value['high_tieraverage']
                low = value['low_tieraverage']
                cov = value['COVaverage']
                ci = value['CIaverage']

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

        self.text_widget.config(height=self.winfo_height() * 27)

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
class ISOTable(tk.Frame):
    def __init__(self, root, data, units, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=1, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        self.header = tk.Text(self, wrap="word", height=6, width=149)
        self.header.grid(row=3, column=0, columnspan=11, padx=0, pady=0, rowspan=1)

        self.text_widget = tk.Text(self, wrap="word", height=72, width=149)
        self.text_widget.grid(row=4, column=0, columnspan=11, padx=0, pady=0)

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
            sorted_keys = sorted(data['average'].keys(),
                                 key=lambda x: phase_params.index(x) if x in phase_params else float('inf'))

            for key in sorted_keys:
                if key.startswith('variable') or key.startswith('Energy Outputs') or key.startswith('average'):
                    pass
                elif key.endswith(phase) and key in phase_params:
                    unit = units.get(key, "")
                    val = ""  # value['values']
                    avg = data['average'][key]
                    n = data['N'][key]
                    stdev = data['stdev'][key]
                    int = data['Interval'][key]
                    high = data['High Tier'][key]
                    low = data['Low Tier'][key]
                    cov = data['COV'][key]
                    ci = data['CI'][key]

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
                    row = "{:<33} | {:<9} | {:<12} | {:<4} | {:<11} | {:<8} | {:<8} | {:<8} | {:<6} | {:<20} |".format(
                        key, unit, avg, n, stdev, int, high, low, cov, ci)
                    self.text_widget.insert(tk.END, row + "\n")
                    self.text_widget.insert(tk.END, "_" * 148 + "\n")

        self.text_widget.config(height=self.winfo_height() * 26)

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


    def __init__(self, root, data, units, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=1, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        self.header = tk.Text(self, wrap="word", height=6, width=149)
        self.header.grid(row=3, column=0, columnspan=11, padx=0, pady=0, rowspan=1)

        self.text_widget = tk.Text(self, wrap="word", height=72, width=149)
        self.text_widget.grid(row=4, column=0, columnspan=11, padx=0, pady=0)

        # Configure a tag for bold text
        self.header.tag_configure("bold", font=("Helvetica", 12, "bold"))

        header = "{:<266}|".format("ALL ENERGY OUTPUTS")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
        header = "{:<60} | {:<16} | {:<18} | {:<9} | {:<11} | {:<12} | {:<11} | {:<11} | {:<9} | {:<40} |".format("Variable", "Units",
                                                                                         "Average", "N", "Standard Dev",
                                                                                         "Interval", "High Tier", "Low Tier",
                                                                                         "COV", "CI")
        self.header.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")

        for key in data['average']:
            if key.startswith('variable') or key.startswith('Energy Outputs') or key.startswith('average'):
                pass
            else:
                unit = units.get(key, "")
                val = ""  # value['values']
                avg = data['average'][key]
                n = data['N'][key]
                stdev = data['stdev'][key]
                int = data['Interval'][key]
                high = data['High Tier'][key]
                low = data['Low Tier'][key]
                cov = data['COV'][key]
                ci = data['CI'][key]

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
                row = "{:<33} | {:<9} | {:<12} | {:<4} | {:<11} | {:<8} | {:<8} | {:<8} | {:<6} | {:<20} |".format(
                    key, unit, avg, n, stdev, int, high, low, cov, ci)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 148 + "\n")

        self.text_widget.config(height=self.winfo_height() * 26)

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

from tkinter import *
from tkinter import ttk
class ScrollableNotebook(ttk.Frame):
    def __init__(self,parent,wheelscroll=False,tabmenu=False,*args,**kwargs):
        ttk.Frame.__init__(self, parent, *args)
        self.xLocation = 0
        self.notebookContent = ttk.Notebook(self,**kwargs)
        self.notebookContent.pack(fill="both", expand=True)
        self.notebookTab = ttk.Notebook(self,**kwargs)
        self.notebookTab.bind("<<NotebookTabChanged>>",self._tabChanger)
        if wheelscroll==True: self.notebookTab.bind("<MouseWheel>", self._wheelscroll)
        slideFrame = ttk.Frame(self)
        slideFrame.place(relx=1.0, x=0, y=1, anchor=NE)
        self.menuSpace=30
        if tabmenu==True:
            self.menuSpace=50
            bottomTab = ttk.Label(slideFrame, text="\u2630")
            bottomTab.bind("<ButtonPress-1>",self._bottomMenu)
            bottomTab.pack(side=RIGHT)
        leftArrow = ttk.Label(slideFrame, text=" \u276E")
        leftArrow.bind("<ButtonPress-1>",self._leftSlideStart)
        leftArrow.bind("<ButtonRelease-1>",self._slideStop)
        leftArrow.pack(side=LEFT)
        rightArrow = ttk.Label(slideFrame, text=" \u276F")
        rightArrow.bind("<ButtonPress-1>",self._rightSlideStart)
        rightArrow.bind("<ButtonRelease-1>",self._slideStop)
        rightArrow.pack(side=RIGHT)
        self.notebookContent.bind("<Configure>", self._resetSlide)
        self.contentsManaged = []

    def _wheelscroll(self, event):
        if event.delta > 0:
            self._leftSlide(event)
        else:
            self._rightSlide(event)

    def _bottomMenu(self, event):
        tabListMenu = Menu(self, tearoff = 0)
        for tab in self.notebookTab.tabs():
            tabListMenu.add_command(label=self.notebookTab.tab(tab, option="text"),command= lambda temp=tab: self.select(temp))
        try:
            tabListMenu.tk_popup(event.x_root, event.y_root)
        finally:
            tabListMenu.grab_release()

    def _tabChanger(self, event):
        try: self.notebookContent.select(self.notebookTab.index("current"))
        except: pass

    def _rightSlideStart(self, event=None):
        if self._rightSlide(event):
            self.timer = self.after(100, self._rightSlideStart)

    def _rightSlide(self, event):
        if self.notebookTab.winfo_width()>self.notebookContent.winfo_width()-self.menuSpace:
            if (self.notebookContent.winfo_width()-(self.notebookTab.winfo_width()+self.notebookTab.winfo_x()))<=self.menuSpace+5:
                self.xLocation-=20
                self.notebookTab.place(x=self.xLocation,y=0)
                return True
        return False

    def _leftSlideStart(self, event=None):
        if self._leftSlide(event):
            self.timer = self.after(100, self._leftSlideStart)

    def _leftSlide(self, event):
        if not self.notebookTab.winfo_x()== 0:
            self.xLocation+=20
            self.notebookTab.place(x=self.xLocation,y=0)
            return True
        return False

    def _slideStop(self, event):
        if self.timer != None:
            self.after_cancel(self.timer)
            self.timer = None

    def _resetSlide(self,event=None):
        self.notebookTab.place(x=0,y=0)
        self.xLocation = 0

    def add(self,frame,**kwargs):
        if len(self.notebookTab.winfo_children())!=0:
            self.notebookContent.add(frame, text="",state="hidden")
        else:
            self.notebookContent.add(frame, text="")
        self.notebookTab.add(ttk.Frame(self.notebookTab),**kwargs)
        self.contentsManaged.append(frame)

    def forget(self,tab_id):
        content_tab_id = self.__ContentTabID(tab_id)
        if content_tab_id is not None:
            self.notebookContent.forget(content_tab_id)
        try:
            index = self.notebookTab.index(tab_id)
            if index is not None and index < len(self.contentsManaged):
                self.notebookTab.forget(tab_id)
                self.contentsManaged[index].destroy()
                self.contentsManaged.pop(index)
        except Exception as e:
            print("Error:", e)

    def hide(self,tab_id):
        self.notebookContent.hide(self.__ContentTabID(tab_id))
        self.notebookTab.hide(tab_id)

    def identify(self,x, y):
        return self.notebookTab.identify(x,y)

    def index(self,tab_id):
        return self.notebookTab.index(tab_id)

    def __ContentTabID(self,tab_id):
        tab_ids = self.notebookTab.tabs()
        if tab_id in tab_ids:
            return self.notebookContent.tabs()[tab_ids.index(tab_id)]
        else:
            return None  # Handle the case when tab_id is not found

    def insert(self,pos,frame, **kwargs):
        self.notebookContent.insert(pos,frame, **kwargs)
        self.notebookTab.insert(pos,frame,**kwargs)

    def select(self,tab_id):
##        self.notebookContent.select(self.__ContentTabID(tab_id))
        self.notebookTab.select(tab_id)

    def tab(self,tab_id, option=None, **kwargs):
        kwargs_Content = kwargs.copy()
        kwargs_Content["text"] = ""  # important
        try:
            content_tab_id = self.__ContentTabID(tab_id)
            if content_tab_id is not None:
                self.notebookContent.tab(content_tab_id, option=option, **kwargs_Content)
        except Exception as e:
            print("Error:", e)
        return self.notebookTab.tab(tab_id, option=option, **kwargs)

    def tabs(self):
##        return self.notebookContent.tabs()
        return self.notebookTab.tabs()

    def enable_traversal(self):
        self.notebookContent.enable_traversal()
        self.notebookTab.enable_traversal()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App L3")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L3(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()