import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
import threading
import traceback
import csv

#For pyinstaller:
#C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS>pyinstaller --onefile -p C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS LEMS_DataEntry_BEN.py
class LEMSDataInput(tk.Frame):
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


        #create test info section
        self.test_info = TestInfoFrame(self.frame, "Test Info")
        self.test_info.grid(row=1, column=0, columnspan=2)

        #add instructions
        instructions = f"*Please select a folder to store your inputs in.\n" \
                       f"*Folder should be named with the test name and contain LEMS raw data (labeled foldername_RawData.csv) if using.\n" \
                       f"*To enter values for charcoal created by wood stoves, please enter the information as a second or third fuel in Fuel\n" \
                       f"*with a cfrac db of greater than 0.75. Then enter charcoal weights as a fuel mass with the initial mass being 0 if the stove started with no charcoal.\n" \
                       f"*Default values for charcoal created in a wood stove are:\n" \
                       f"   mc (moisure content): 0%\n" \
                       f"   higher heating value: 32500kJ/kg\n" \
                       f"   cfrac db (carbon fraction on a dry basis): 0.9\n" \
                       f"*For max water temperature, enter the maximum temperature of the water.\n" \
                       f"*For end water temperature enter the temperature of the water at the end of the phase (at the end of shutdown for ISO tests).\n" \
                       f"*Please enter all times as either yyyymmdd HH:MM:SS or HH:MM:SS and enter all times in the same format."

        self.instructions_frame = tk.Text(self.frame, wrap="word", height=16, width=90)
        self.instructions_frame.insert(tk.END, instructions)
        self.instructions_frame.grid(row=1, column=2, columnspan=3)
        self.instructions_frame.config(state="disabled")

        #create enviroment info section
        self.enviro_info = EnvironmentInfoFrame(self.frame, "Test Conditions")
        self.enviro_info.grid(row=2, column=2, columnspan=2)

        # create fuel info section
        self.fuel_info = FuelInfoFrame(self.frame, "Fuel Info")
        self.fuel_info.grid(row=2, column=0, columnspan=2)

        # create high power section
        self.hpstart_info = HPstartInfoFrame(self.frame, "High Power Start")
        self.hpstart_info.grid(row=3, column=0, columnspan=2)
        self.hpend_info = HPendInfoFrame(self.frame, "High Power End")
        self.hpend_info.grid(row=3, column=2, columnspan=2)

        # create medium power section
        self.mpstart_info = MPstartInfoFrame(self.frame, "Medium Power Start")
        self.mpstart_info.grid(row=3, column=4, columnspan=2)
        self.mpend_info = MPendInfoFrame(self.frame, "Medium Power End")
        self.mpend_info.grid(row=3, column=6, columnspan=2)

        # create low power section
        self.lpstart_info = LPstartInfoFrame(self.frame, "Low Power Start")
        self.lpstart_info.grid(row=3, column=8, columnspan=2)
        self.lpend_info = LPendInfoFrame(self.frame, "Low Power End")
        self.lpend_info.grid(row=3, column=10, columnspan=2)

        # create performance weight tiers
        self.weight_info = WeightPerformanceFrame(self.frame, "Weighting for Voluntary Performance Tiers")
        self.weight_info.grid(row=4, column=0, columnspan=2)

        # File Path Entry
        tk.Label(self.frame, text="Select Folder:").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var, width=50)
        self.folder_path.grid(row=0, column=1)

        #create a button to browse folders on computer
        browse_button = tk.Button(self.frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=0, column=2)

        # OK button
        ok_button = tk.Button(self.frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=6, column=0)

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.pack(side=tk.TOP, expand=True)

    def onCanvasMouseWheel(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_okay(self): #When okay button is pressed
        # for each frame, check inputs
        float_errors = []
        blank_errors = []
        range_errors = []
        value_errors = []
        format_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors, range_errors = self.enviro_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, range_errors = self.fuel_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, value_errors, format_errors = self.hpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.hpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.mpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.mpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.lpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.lpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors = self.weight_info.check_input_validity(float_errors, blank_errors)

        message = ''
        if len(float_errors) != 0:
            floatmessage = 'The following variables require a numerical input:'
            for name in float_errors:
                floatmessage = floatmessage + ' ' + name

            message = message + floatmessage + '\n'

        if len(blank_errors) != 0:
            blankmessage = 'The following variables were left blank but require an input:'
            for name in blank_errors:
                blankmessage = blankmessage + ' ' + name

            message = message + blankmessage + '\n'

        if len(range_errors) != 0:
            rangemessage = 'The following variables are outside of the expected value range:'
            for name in range_errors:
                rangemessage = rangemessage + ' ' + name

            message = message + rangemessage + '\n'

        if len(value_errors) != 0:
            valuemessage = 'The following variables have an initial mass which is less than the final mass:'
            for name in value_errors:
                valuemessage = valuemessage + ' ' + name

            message = message + valuemessage + '\n'

        if len(format_errors) != 0:
            formatmessage = 'The following have an incorrect format for time or they do not match the ' \
                            'time format entered in other areas \n Accepted time formats are yyyymmdd HH:MM:SS or HH:MM:SS:'
            for name in format_errors:
                formatmessage = formatmessage + ' ' + name

            message = message + formatmessage + '\n'

        if message != '':
            # Error
            messagebox.showerror("Error", message)
        else:
            self.names = []
            self.units = {}
            self.data = {}
            self.unc = {}
            self.uval = {}

            name = 'variable_name'
            self.names.append(name)
            self.units[name] = 'units'
            self.data[name] = 'value'
            self.unc[name] = 'uncertainty'
            self.uval[name] = ''

            self.testdata = self.test_info.get_data()
            for name in self.testdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.testdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.envirodata = self.enviro_info.get_data()
            self.envirounits = self.enviro_info.get_units()
            for name in self.envirodata:
                self.names.append(name)
                self.units[name] = self.envirounits[name].get()
                self.data[name] = self.envirodata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.fueldata = self.fuel_info.get_data()
            self.fuelunits = self.fuel_info.get_units()
            for name in self.fueldata:
                self.names.append(name)
                self.units[name] = self.fuelunits[name].get()
                self.data[name] = self.fueldata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpstartdata = self.hpstart_info.get_data()
            self.hpstartunits = self.hpstart_info.get_units()
            for name in self.hpstartdata:
                self.names.append(name)
                self.units[name] = self.hpstartunits[name].get()
                self.data[name] = self.hpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.hpenddata = self.hpend_info.get_data()
            self.hpendunits = self.hpend_info.get_units()
            for name in self.hpenddata:
                self.names.append(name)
                self.units[name] = self.hpendunits[name].get()
                self.data[name] = self.hpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpstartdata = self.mpstart_info.get_data()
            self.mpstartunits = self.mpstart_info.get_units()
            for name in self.mpstartdata:
                self.names.append(name)
                self.units[name] = self.mpstartunits[name].get()
                self.data[name] = self.mpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.mpenddata = self.mpend_info.get_data()
            self.mpendunits = self.mpend_info.get_units()
            for name in self.mpenddata:
                self.names.append(name)
                self.units[name] = self.mpendunits[name].get()
                self.data[name] = self.mpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpstartdata = self.lpstart_info.get_data()
            self.lpstartunits = self.lpstart_info.get_units()
            for name in self.lpstartdata:
                self.names.append(name)
                self.units[name] = self.lpstartunits[name].get()
                self.data[name] = self.lpstartdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.lpenddata = self.lpend_info.get_data()
            self.lpendunits = self.lpend_info.get_units()
            for name in self.lpenddata:
                self.names.append(name)
                self.units[name] = self.lpendunits[name].get()
                self.data[name] = self.lpenddata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            try:
                self.extradata = self.extra_test_inputs.get_data()
                self.extraunits = self.extra_test_inputs.get_units()
                for name in self.extradata:
                    self.names.append(name)
                    self.units[name] = self.extraunits[name].get()
                    self.data[name] = self.extradata[name].get()
                    self.unc[name] = ''
                    self.uval[name] = ''
            except:
                pass

            self.weightdata = self.weight_info.get_data()
            for name in self.weightdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.weightdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            success = 0

            # Save to CSV
            try:
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except PermissionError:
                message = self.file_path + ' is open in another program, please close it and try again.'
                # Error
                messagebox.showerror("Error", message)

            if success == 1:
                success = 0
                self.output_path = os.path.join(self.folder_path,
                                                f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
                self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
                try:
                    [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
                    success = 1
                except PermissionError:
                    message = self.output_path + ' is open in another program, please close it and try again.'
                    # Error
                    messagebox.showerror("Error", message)
                if success == 1:
                    self.frame.destroy()
                    # Create a notebook to hold tabs
                    self.notebook = ttk.Notebook(height=30000)
                    self.notebook.grid(row=0, column=0)

                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Add the tab to the notebook with the folder name as the tab label
                    self.notebook.add(self.tab_frame, text="Menu")

                    # Set up the frame as you did for the original frame
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff", height=self.winfo_height(), width=self.winfo_width() * 20)
                    self.frame.grid(row=1, column=0)

                    self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                    self.energy_button.grid(row=0, column=0)

                    blank = tk.Frame(self.frame, width=self.winfo_width()-30)
                    blank.grid(row=0, column=1, rowspan=2)

                    self.cali_button = tk.Button(self.frame, text="Step 2: Adjust Sensor Calibrations", command=self.on_cali)
                    self.cali_button.grid(row=1, column=0)

                    # Recenter view to top-left
                    self.canvas.yview_moveto(0)
                    self.canvas.xview_moveto(0)

    def on_cali(self):
        try:
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData_Recalibrated.csv")
            self.header_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Header.csv")
            LEMS_Adjust_Calibrations(self.input_path, self.energy_path, self.output_path, self.header_path, self.log_path, inputmethod=str(1))
            self.cali_button.config(bg="lightgreen")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.cali_button.config(bg="red")

        # Check if the Energy Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Recalibration":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Recalibration")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Recalibration")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
    def on_energy(self):
            try:
                [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
                self.energy_button.config(bg="lightgreen")
            except:
                self.energy_button.config(bg="red")
            # round to 3 decimals
            round_data = {}
            for name in data:
                try:
                    rounded = round(data[name].n, 3)
                except:
                    rounded = data[name]
                round_data[name] = rounded
            data = round_data

            # Check if the Energy Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Energy Calculations":
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.grid(row=1, column=0)
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Energy Calculations")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.grid(row=1, column=0)
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Energy Calculations")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            # Output table
            self.create_output_table(data, units, logs, num_columns=self.winfo_width(),
                                     num_rows=self.winfo_height(), folder_path=self.folder_path)  # Adjust num_columns and num_rows as needed



    def create_output_table(self, data, units, logs, num_columns, num_rows, folder_path):
        output_table = OutputTable(self.frame, data, units, logs, num_columns, num_rows, folder_path)
        output_table.grid(row=3, column=0, columnspan=num_columns, padx=0, pady=0)

    def on_browse(self): #when browse button is hit, pull up file finder.
        self.destroy_widgets()

        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Check if _EnergyInputs.csv file exists
        self.file_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
        try:
            [names,units,data,unc,uval] = io.load_constant_inputs(self.file_path)
            data.pop("variable_name")
            data = self.test_info.check_imported_data(data)
            data = self.enviro_info.check_imported_data(data)
            data = self.fuel_info.check_imported_data(data)
            data = self.hpstart_info.check_imported_data(data)
            data = self.hpend_info.check_imported_data(data)
            data = self.mpstart_info.check_imported_data(data)
            data = self.mpend_info.check_imported_data(data)
            data = self.lpstart_info.check_imported_data(data)
            data = self.lpend_info.check_imported_data(data)
            data = self.weight_info.check_imported_data(data)
            #if it exists and has inputs not specified on the entry sheet, add them in
            if data:
                self.extra_test_inputs = ExtraTestInputsFrame(self.frame, "Additional Test Inputs", data, units)
                self.extra_test_inputs.grid(row=5, column=0, columnspan=2)
        except FileNotFoundError:
            pass

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

        ## Other menu options
        # subtract_bkg_button = tk.Button(self, text="Subtract Background", command=self.on_subtract_background(folder_path=folder_path))
        # subtract_bkg_button.grid(row=4, column=0, padx=5, pady=5)
        # Configure a tag for bold text

        #output table
        self.text_widget = tk.Text(self, wrap="none", height=num_rows, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<110}|".format("ALL ENERGY OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        #short table
        self.cut_table = tk.Text(self, wrap="none", height=num_rows, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=3, column=3, padx=0, pady=0, columnspan=3)
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

            tot_rows += 2

        self.text_widget.config(height=self.winfo_height()*(31-num_lines))
        self.cut_table.config(height=self.winfo_height()*(31-num_lines))

        self.text_widget.configure(state="disabled")
        self.warning_frame.configure(state="disabled")
        self.cut_table.configure(state="disabled")

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

class TestInfoFrame(tk.LabelFrame): #Test info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.testinfo = ['test_name', 'test_number', 'date', 'name_of_tester', 'location', 'stove_type/model']
        self.entered_test_info = {}
        for i, name in enumerate(self.testinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self)
            self.entered_test_info[name].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field in self.testinfo:
            if field in data:
                self.entered_test_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_test_info[field].insert(0, data.pop(field, ""))

        return data
    def get_data(self):
        return self.entered_test_info

class EnvironmentInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.enviroinfo = ['initial_air_temp', 'initial_RH', 'initial_pressure', 'initial_wind_velocity',
                           'final_air_temp', 'final_RH', 'final_pressure', 'final_wind_velocity',
                           'pot1_dry_mass', 'pot2_dry_mass', 'pot3_dry_mass', 'pot4_dry_mass']
        self.envirounits = ['C', '%', 'in Hg', 'm/s', 'C', '%', 'in Hg', 'm/s', 'kg', 'kg', 'kg', 'kg']
        self.entered_enviro_info = {}
        self.entered_enviro_units = {}
        for i, name in enumerate(self.enviroinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_enviro_info[name] = tk.Entry(self)
            self.entered_enviro_info[name].grid(row=i, column=2)
            self.entered_enviro_units[name] = tk.Entry(self)
            self.entered_enviro_units[name].insert(0, self.envirounits[i])
            self.entered_enviro_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, range_errors: list):
        for name in self.enviroinfo:
            try:
                test = float(self.entered_enviro_info[name].get())
            except ValueError:
                if self.entered_enviro_info[name].get() != '': #If not blank, string was entered instead of number
                    float_errors.append(name)
                if (name == 'initial_air_temp' or name == 'initial_pressure') and 'final' not in name and \
                        'pot' not in name and self.entered_enviro_info[name].get() == '': #Inital temp and pressure require inputs
                    blank_errors.append(name)
                if 'pot' in name and '1' in name and self.entered_enviro_info[name].get() == '': #dry weight of pot 1 required
                    blank_errors.append(name)
        #RH should not be above 100
        try:
            test = float(self.entered_enviro_info['initial_RH'].get())
            if float(self.entered_enviro_info['initial_RH'].get()) > 100:
                range_errors.append('initial_RH')
        except:
            pass
        try:
            float(self.entered_enviro_info['final_RH'].get())
            if float(self.entered_enviro_info['final_RH'].get()) > 100:
                range_errors.append('final_RH')
        except:
            pass

        return float_errors, blank_errors, range_errors

    def check_imported_data(self, data: dict):
        for field in self.enviroinfo:
            if field in data:
                self.entered_enviro_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_enviro_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_enviro_info

    def get_units(self):
        return self.entered_enviro_units

class FuelInfoFrame(tk.LabelFrame): #Fuel info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.singlefuelinfo = ['fuel_type', 'fuel_source', 'fuel_dimensions', 'fuel_mc', 'fuel_higher_heating_value', 'fuel_Cfrac_db']
        self.fuelunits = ['', '', 'cmxcmxcm', '%', 'kJ/kg', 'g/g']
        self.fuelinfo = []
        self.number_of_fuels = 3
        start = 1
        self.entered_fuel_units = {}
        while start <= self.number_of_fuels:
            for i, name in enumerate(self.singlefuelinfo):
                new_name = name + '_' + str(start)
                self.fuelinfo.append(new_name)
                self.entered_fuel_units[new_name] = tk.Entry(self)
                self.entered_fuel_units[new_name].insert(0, self.fuelunits[i])

            start += 1
        self.entered_fuel_info = {}
        for i, name in enumerate(self.fuelinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_fuel_info[name] = tk.Entry(self)
            self.entered_fuel_info[name].grid(row=i, column=2)
            self.entered_fuel_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, range_errors: list):
        self.fuel_2_values_entered = any(self.entered_fuel_info[name].get() != '' for name in self.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(self.entered_fuel_info[name].get() != '' for name in self.fuelinfo if '3' in name)

        for name in self.fuelinfo:
            try:
                test = float(self.entered_fuel_info[name].get())
            except ValueError:
                if ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name) and \
                        self.entered_fuel_info[name].get() != '':
                    float_errors.append(name)
                if ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '1' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)
                if self.fuel_2_values_entered and ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '2' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)
                if self.fuel_3_values_entered and ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                    '3' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)

        start = 1
        while start <= self.number_of_fuels:
            try:
                HV = float(self.entered_fuel_info['fuel_higher_heating_value_' + str(start)].get())
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if (HV < 11000 or HV > 25000) and cfrac < 0.75:
                    range_errors.append('fuel_higher_heating_value_' + str(start))
            except:
                pass

            try:
                HV = float(self.entered_fuel_info['fuel_higher_heating_value_' + str(start)].get())
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if (HV < 25000 or HV > 33500) and cfrac > 0.75:
                    range_errors.append('fuel_higher_heating_value_' + str(start))
            except:
                pass

            try:
                cfrac = float(self.entered_fuel_info['fuel_Cfrac_db_' + str(start)].get())
                if cfrac > 1:
                    range_errors.append('fuel_Cfrac_db_' + str(start))
            except:
                pass

            start += 1

        return float_errors, blank_errors, range_errors

    def check_imported_data(self, data: dict):
        for field in self.fuelinfo:
            if field in data:
                self.entered_fuel_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_fuel_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_fuel_info

    def get_units(self):
        return self.entered_fuel_units

class HPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.hpstartinfo = ['start_time_hp', 'initial_fuel_mass_1_hp', 'initial_fuel_mass_2_hp',
                            'initial_fuel_mass_3_hp','initial_water_temp_pot1_hp', 'initial_water_temp_pot2_hp',
                            'initial_water_temp_pot3_hp', 'initial_water_temp_pot4_hp', 'initial_pot1_mass_hp',
                            'initial_pot2_mass_hp', 'initial_pot3_mass_hp', 'initial_pot4_mass_hp', 'fire_start_material_hp',
                            'boil_time_hp']
        self.hpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', '', 'hh:mm:ss']
        self.entered_hpstart_info = {}
        self.entered_hpstart_units = {}
        for i, name in enumerate(self.hpstartinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_hpstart_info[name] = tk.Entry(self)
            self.entered_hpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_hp' or name == 'initial_fuel_mass_3_hp':
                self.entered_hpstart_info[name].insert(0, 0) #default of 0
            self.entered_hpstart_units[name] = tk.Entry(self)
            self.entered_hpstart_units[name].insert(0, self.hpstartunits[i])
            self.entered_hpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.hpend_info_frame = HPendInfoFrame(self, "HP End")
        self.entered_hpend_info = self.hpend_info_frame.get_data()
        hpstart_values_entered = any(self.entered_hpstart_info[name].get() != '' for name in self.hpstartinfo)
        #timeformat = 0
        if hpstart_values_entered:
            for name in self.hpstartinfo:
                try:
                    float(self.entered_hpstart_info[name].get())
                except ValueError:
                    if self.entered_hpstart_info[name].get() != '' and 'time' not in name and name != 'fire_start_material_hp':
                        float_errors.append(name)
                    if'time' not in name and name != 'fire_start_material_hp' and '1' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and name != 'fire_start_material_hp' and '2' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and name != 'fire_start_material_hp' and '3' in name and self.entered_hpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_hp'
                final_mass_name = f'final_pot{i}_mass_hp'
                try:
                    initial_mass = float(self.entered_hpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_hpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_hp')
                except ValueError:
                    pass

            if len(self.entered_hpstart_info['start_time_hp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_hp')
            #else:
                #timeformat = len(self.entered_hpstart_info['start_time_hp'].get())

            if len(self.entered_hpstart_info['boil_time_hp'].get()) not in (8, 17, 0):
                print(len(self.entered_hpstart_info['boil_time_hp'].get()))
                format_errors.append('boil_time_hp')

            return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.hpstartinfo:
            if field in data:
                self.entered_hpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_hpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_hpstart_info

    def get_units(self):
        return self.entered_hpstart_units

class HPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.hpendinfo = ['end_time_hp', 'final_fuel_mass_1_hp', 'final_fuel_mass_2_hp',
                            'final_fuel_mass_3_hp','max_water_temp_pot1_hp', 'max_water_temp_pot2_hp',
                            'max_water_temp_pot3_hp', 'max_water_temp_pot4_hp', 'end_water_temp_pot1_hp', 'final_pot1_mass_hp',
                            'final_pot2_mass_hp', 'final_pot3_mass_hp', 'final_pot4_mass_hp']
        self.hpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_hpend_info = {}
        self.entered_hpend_units = {}
        for i, name in enumerate(self.hpendinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_hpend_info[name] = tk.Entry(self)
            self.entered_hpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_hp' or name == 'final_fuel_mass_3_hp':
                self.entered_hpend_info[name].insert(0, 0) #default of 0
            self.entered_hpend_units[name] = tk.Entry(self)
            self.entered_hpend_units[name].insert(0, self.hpendunits[i])
            self.entered_hpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        hpend_values_entered = any(self.entered_hpend_info[name].get() != '' for name in self.hpendinfo)
        if hpend_values_entered:
            for name in self.hpendinfo:
                try:
                    float(self.entered_hpend_info[name].get())
                except ValueError:
                    if self.entered_hpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and self.entered_hpend_info[name].get() == '':
                        blank_errors.append(name)

            #if timeformat == 0:
            if len(self.entered_hpend_info['end_time_hp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_hp')
            #else:
                #timeformat = len(self.entered_hpend_info['end_time_hp'].get())
            #else:
            #if len(self.entered_hpend_info['end_time_hp'].get()) != (8 or 17 or 0):
                #format_errors.append('end_time_hp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.hpendinfo:
            if field in data:
                self.entered_hpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_hpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_hpend_info

    def get_units(self):
        return self.entered_hpend_units

class MPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.mpstartinfo = ['start_time_mp', 'initial_fuel_mass_1_mp', 'initial_fuel_mass_2_mp',
                            'initial_fuel_mass_3_mp','initial_water_temp_pot1_mp', 'initial_water_temp_pot2_mp',
                            'initial_water_temp_pot3_mp', 'initial_water_temp_pot4_mp', 'initial_pot1_mass_mp',
                            'initial_pot2_mass_mp', 'initial_pot3_mass_mp', 'initial_pot4_mass_mp',
                            'boil_time_mp']
        self.mpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', 'hh:mm:ss']
        self.entered_mpstart_info = {}
        self.entered_mpstart_units = {}
        for i, name in enumerate(self.mpstartinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_mpstart_info[name] = tk.Entry(self)
            self.entered_mpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_mp' or name == 'initial_fuel_mass_3_mp':
                self.entered_mpstart_info[name].insert(0, 0) #default of 0
            self.entered_mpstart_units[name] = tk.Entry(self)
            self.entered_mpstart_units[name].insert(0, self.mpstartunits[i])
            self.entered_mpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.mpend_info_frame = MPendInfoFrame(self, "MP End")
        self.entered_mpend_info = self.mpend_info_frame.get_data()
        mpstart_values_entered = any(self.entered_mpstart_info[name].get() != '' for name in self.mpstartinfo)
        if mpstart_values_entered:
            for name in self.mpstartinfo:
                try:
                    float(self.entered_mpstart_info[name].get())
                except ValueError:
                    if self.entered_mpstart_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and self.entered_mpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_mp'
                final_mass_name = f'final_pot{i}_mass_mp'
                try:
                    initial_mass = float(self.entered_mpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_mpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_mp')
                except ValueError:
                    pass

            #if self.timeformat == 0:
            if len(self.entered_mpstart_info['start_time_mp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_mp')
            #else:
                #self.timeformat = len(self.entered_mpstart_info['start_time_mp'].get())
            #else:
                #if len(self.entered_mpstart_info['start_time_mp'].get()) != (self.timeformat or 0):
                    #format_errors.append('start_time_mp')

            if (len(self.entered_mpstart_info['boil_time_mp'].get()) not in (8, 17, 0)) :
                format_errors.append('boil_time_mp')

        return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.mpstartinfo:
            if field in data:
                self.entered_mpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_mpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_mpstart_info

    def get_units(self):
        return self.entered_mpstart_units

class MPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.mpendinfo = ['end_time_mp', 'final_fuel_mass_1_mp', 'final_fuel_mass_2_mp',
                            'final_fuel_mass_3_mp','max_water_temp_pot1_mp', 'max_water_temp_pot2_mp',
                            'max_water_temp_pot3_mp', 'max_water_temp_pot4_mp', 'end_water_temp_pot1_mp', 'final_pot1_mass_mp',
                            'final_pot2_mass_mp', 'final_pot3_mass_mp', 'final_pot4_mass_mp']
        self.mpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_mpend_info = {}
        self.entered_mpend_units = {}
        for i, name in enumerate(self.mpendinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_mpend_info[name] = tk.Entry(self)
            self.entered_mpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_mp' or name == 'final_fuel_mass_3_mp':
                self.entered_mpend_info[name].insert(0, 0) #default of 0
            self.entered_mpend_units[name] = tk.Entry(self)
            self.entered_mpend_units[name].insert(0, self.mpendunits[i])
            self.entered_mpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        mpend_values_entered = any(self.entered_mpend_info[name].get() != '' for name in self.mpendinfo)
        if mpend_values_entered:
            for name in self.mpendinfo:
                try:
                    float(self.entered_mpend_info[name].get())
                except ValueError:
                    if self.entered_mpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and \
                            self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and \
                            self.entered_mpend_info[name].get() == '':
                        blank_errors.append(name)

            #if self.timeformat == 0:
            if len(self.entered_mpend_info['end_time_mp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_mp')
            #else:
                #self.timeformat = len(self.entered_mpend_info['end_time_mp'].get())
            #else:
                #if len(self.entered_mpend_info['end_time_mp'].get()) != (self.timeformat or 0):
                    #format_errors.append('end_time_mp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.mpendinfo:
            if field in data:
                self.entered_mpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_mpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_mpend_info

    def get_units(self):
        return self.entered_mpend_units

class LPstartInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.lpstartinfo = ['start_time_lp', 'initial_fuel_mass_1_lp', 'initial_fuel_mass_2_lp',
                            'initial_fuel_mass_3_lp','initial_water_temp_pot1_lp', 'initial_water_temp_pot2_lp',
                            'initial_water_temp_pot3_lp', 'initial_water_temp_pot4_lp', 'initial_pot1_mass_lp',
                            'initial_pot2_mass_lp', 'initial_pot3_mass_lp', 'initial_pot4_mass_lp',
                            'boil_time_lp']
        self.lpstartunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg', 'hh:mm:ss']
        self.entered_lpstart_info = {}
        self.entered_lpstart_units = {}
        for i, name in enumerate(self.lpstartinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_lpstart_info[name] = tk.Entry(self)
            self.entered_lpstart_info[name].grid(row=i, column=2)
            if name == 'initial_fuel_mass_2_lp' or name == 'initial_fuel_mass_3_lp':
                self.entered_lpstart_info[name].insert(0, 0) #default of 0
            self.entered_lpstart_units[name] = tk.Entry(self)
            self.entered_lpstart_units[name].insert(0, self.lpstartunits[i])
            self.entered_lpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, value_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        self.lpend_info_frame = LPendInfoFrame(self, "LP End")
        self.entered_lpend_info = self.lpend_info_frame.get_data()
        lpstart_values_entered = any(self.entered_lpstart_info[name].get() != '' for name in self.lpstartinfo)
        if lpstart_values_entered:
            for name in self.lpstartinfo:
                try:
                    float(self.entered_lpstart_info[name].get())
                except ValueError:
                    if self.entered_lpstart_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                        blank_errors.append(name)

            for i in range(1, 5):
                initial_mass_name = f'initial_pot{i}_mass_lp'
                final_mass_name = f'final_pot{i}_mass_lp'
                try:
                    initial_mass = float(self.entered_lpstart_info[initial_mass_name].get())
                    final_mass = float(self.entered_lpend_info[final_mass_name].get())
                    if initial_mass > final_mass:
                        value_errors.append(f'pot{i}_mass_mp')
                except ValueError:
                    pass

            #if self.timeformat == 0:
            if len(self.entered_lpstart_info['start_time_lp'].get()) not in (8, 17, 0):
                format_errors.append('start_time_lp')
            #else:
                #self.timeformat = len(self.entered_lpstart_info['start_time_lp'].get())
            #else:
                #if len(self.entered_lpstart_info['start_time_lp'].get()) != (self.timeformat or 0):
                    #format_errors.append('start_time_lp')

            if (len(self.entered_lpstart_info['boil_time_lp'].get()) not in (8, 17, 0)):
                format_errors.append('boil_time_lp')

        return float_errors, blank_errors, value_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.lpstartinfo:
            if field in data:
                self.entered_lpstart_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_lpstart_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_lpstart_info

    def get_units(self):
        return self.entered_lpstart_units

class LPendInfoFrame(tk.LabelFrame): #Environment info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.lpendinfo = ['end_time_lp', 'final_fuel_mass_1_lp', 'final_fuel_mass_2_lp',
                            'final_fuel_mass_3_lp','max_water_temp_pot1_lp', 'max_water_temp_pot2_lp',
                            'max_water_temp_pot3_lp', 'max_water_temp_pot4_lp', 'end_water_temp_pot1_lp', 'final_pot1_mass_lp',
                            'final_pot2_mass_lp', 'final_pot3_mass_lp', 'final_pot4_mass_lp']
        self.lpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_lpend_info = {}
        self.entered_lpend_units = {}
        for i, name in enumerate(self.lpendinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_lpend_info[name] = tk.Entry(self)
            self.entered_lpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_lp' or name == 'final_fuel_mass_3_lp':
                self.entered_lpend_info[name].insert(0, 0) #default of 0
            self.entered_lpend_units[name] = tk.Entry(self)
            self.entered_lpend_units[name].insert(0, self.lpendunits[i])
            self.entered_lpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list, format_errors: list):
        # Create an instance of FuelInfoFrame within HPstartInfoFrame
        self.fuel_info_frame = FuelInfoFrame(self, "Fuel Info")
        self.entered_fuel_info = self.fuel_info_frame.get_data()
        self.fuel_2_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '2' in name)
        self.fuel_3_values_entered = any(
            self.entered_fuel_info[name].get() != '' for name in self.fuel_info_frame.fuelinfo if '3' in name)
        lpend_values_entered = any(self.entered_lpend_info[name].get() != '' for name in self.lpendinfo)
        if lpend_values_entered:
            for name in self.lpendinfo:
                try:
                    test = float(self.entered_lpend_info[name].get())
                except ValueError:
                    if self.entered_lpend_info[name].get() != '' and 'time' not in name:
                        float_errors.append(name)
                    if'time' not in name and '1' in name and self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if 'pot' in name and '1' in name and self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_2_values_entered and 'time' not in name and '2' in name and \
                            self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)
                    if self.fuel_3_values_entered and 'time' not in name and '3' in name and \
                            self.entered_lpend_info[name].get() == '':
                        blank_errors.append(name)

            #if self.timeformat == 0:
            if len(self.entered_lpend_info['end_time_lp'].get()) not in (8, 17, 0):
                format_errors.append('end_time_lp')
            #else:
                #self.timeformat = len(self.entered_lpend_info['end_time_lp'].get())
            #else:
                #if len(self.entered_lpend_info['end_time_lp'].get()) != (self.timeformat or 0):
                    #format_errors.append('end_time_lp')

        return float_errors, blank_errors, format_errors

    def check_imported_data(self, data: dict):
        for field in self.lpendinfo:
            if field in data:
                self.entered_lpend_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_lpend_info[field].insert(0, data.pop(field, ""))

        return data

    def get_data(self):
        return self.entered_lpend_info

    def get_units(self):
        return self.entered_lpend_units

class WeightPerformanceFrame(tk.LabelFrame): #Test info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.testinfo = ['weight_hp', 'weight_mp', 'weight_lp', 'weight_total']
        self.entered_test_info = {}
        for i, name in enumerate(self.testinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self)
            self.entered_test_info[name].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field in self.testinfo:
            if field in data:
                self.entered_test_info[field].delete(0, tk.END)  # Clear existing content
                self.entered_test_info[field].insert(0, data.pop(field, ""))

        return data
    def get_data(self):
        return self.entered_test_info

class ExtraTestInputsFrame(tk.LabelFrame):
    def __init__(self, root, text, new_vars: dict, units: dict):
        super().__init__(root, text=text, padx=10, pady=10)
        self.entered_test_info = {}
        self.entered_test_units = {}
        for i, name in enumerate(new_vars):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self)
            self.entered_test_info[name].insert(0, new_vars[name])
            self.entered_test_info[name].grid(row=i, column=2)
            self.entered_test_units[name] = tk.Entry(self)
            self.entered_test_units[name].insert(0, units[name])
            self.entered_test_units[name].grid(row=i, column=3)

    def get_data(self):
        return self.entered_test_info

    def get_units(self):
        return self.entered_test_units


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataInput(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()
