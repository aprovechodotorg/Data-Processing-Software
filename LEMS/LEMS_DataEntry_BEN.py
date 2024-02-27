import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
import csv


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

        # File Path Entry
        tk.Label(self.frame, text="Select Folder:").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var)
        self.folder_path.grid(row=0, column=1)

        #create a button to browse folders on computer
        browse_button = tk.Button(self.frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=0, column=2)

        # OK button
        ok_button = tk.Button(self.frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=5, column=0)

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

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.enviro_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.fuel_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.hpstart_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.hpend_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.mpstart_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.mpend_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.lpstart_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.lpend_info.check_input_validity(float_errors, blank_errors)

        # If errors, generate prompt, else, save to file
        if len(float_errors) != 0 and len(blank_errors) != 0:
            floatmessage = 'The following variables require a numerical input:'
            for name in float_errors:
                floatmessage = floatmessage + ' ' + name

            blankmessage = 'The following variables were left blank but require an input:'
            for name in blank_errors:
                blankmessage = blankmessage + ' ' + name
            # Error
            messagebox.showerror("Error", floatmessage + '\n' + blankmessage)
        elif len(float_errors) != 0 and len(blank_errors) == 0:
            floatmessage = 'The following variables require a numerical input:'
            for name in float_errors:
                floatmessage = floatmessage + ' ' + name

            # Error
            messagebox.showerror("Error", floatmessage)
        elif len(float_errors) == 0 and len(blank_errors) != 0:

            blankmessage = 'The following variables were left blank but require an input:'
            for name in blank_errors:
                blankmessage = blankmessage + ' ' + name
            # Error
            messagebox.showerror("Error", blankmessage)
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

            self.extradata = self.extra_test_inputs.get_data()
            self.extraunits = self.extra_test_inputs.get_units()
            for name in self.extradata:
                self.names.append(name)
                self.units[name] = self.extraunits[name].get()
                self.data[name] = self.extradata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            # Save to CSV
            #self.file_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)

            # Destroy the existing frame
            self.frame.destroy()

            # Create a new frame
            self.frame = tk.Frame(self.canvas, background="#ffffff")

            # Set the frame dimensions to be the window dimensions
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            self.frame.configure(width=window_width, height=window_height)
            self.canvas.create_window((8, 8), window=self.frame, anchor="nw", tags="self.frame")
            self.frame.bind("<Configure>", self.onFrameConfigure)

            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
            [trail, units, data] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)

            # Output table
            self.create_output_table(data, units, num_columns=window_width, num_rows=window_height)  # Adjust num_columns and num_rows as needed

            # Recenter view to top-left
            self.canvas.yview_moveto(0)
            self.canvas.xview_moveto(0)

    def create_output_table(self, data, units, num_columns, num_rows):
        text_widget = tk.Text(self.frame, wrap="none", height=num_rows,
                              width=num_columns * 20)  # Adjust width as needed
        text_widget.grid(row=5, column=0, columnspan=num_columns, padx=10, pady=10)

        # Header
        header = "{:<25} {:<20}".format("Variable", "Value (Units)")
        text_widget.insert(tk.END, header + "\n" + "-" * 45 + "\n")

        # Data
        for key, value in data.items():
            unit = units.get(key, "")  # Get the unit for the variable
            row = "{:<25} {:<20}".format(key, f"{value} {unit}")
            text_widget.insert(tk.END, row + "\n")

        # Additional formatting as needed
        text_widget.configure(state="disabled")


    def on_browse(self): #when browse button is hit, pull up file finder.
        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Check if _EnergyInputs.csv file exists
        self.file_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
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
        #if it exists and has inputs not specified on the entry sheet, add them in
        if data:
            self.extra_test_inputs = ExtraTestInputsFrame(self.frame, "Additional Test Inputs", data, units)
            self.extra_test_inputs.grid(row=4, column=0, columnspan=2)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.enviroinfo:
            try:
                test = float(self.entered_enviro_info[name].get())
            except ValueError:
                if self.entered_enviro_info[name].get() != '':
                    float_errors.append(name)
                elif (name == 'initial_air_temp' or name == 'initial_pressure') and 'final' not in name and \
                        'pot' not in name and self.entered_enviro_info[name].get() == '':
                    blank_errors.append(name)
                elif 'pot' in name and '1' in name and self.entered_enviro_info[name].get() == '':
                    blank_errors.append(name)

        return float_errors, blank_errors

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
        number_of_fuels = 3
        start = 1
        self.entered_fuel_units = {}
        while start <= number_of_fuels:
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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.fuelinfo:
            try:
                test = float(self.entered_fuel_info[name].get())
            except ValueError:
                if ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name) and \
                        self.entered_fuel_info[name].get() != '':
                    float_errors.append(name)
                elif ('fuel_type' not in name and 'fuel_source' not in name and 'fuel_dimensions' not in name and
                      '1' in name) and self.entered_fuel_info[name].get() == '':
                    blank_errors.append(name)

        return float_errors, blank_errors

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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.hpstartinfo:
            try:
                test = float(self.entered_hpstart_info[name].get())
            except ValueError:
                if self.entered_hpstart_info[name].get() != '' and 'time' not in name and name != 'fire_start_material_hp':
                    float_errors.append(name)
                #elif'time' not in name and name != 'fire_start_material_hp' and '1' in name and self.entered_hpstart_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_hpstart_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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
                            'max_water_temp_pot3_hp', 'max_water_temp_pot4_hp', 'final_pot1_mass_hp',
                            'final_pot2_mass_hp', 'final_pot3_mass_hp', 'final_pot4_mass_hp']
        self.hpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.hpendinfo:
            try:
                test = float(self.entered_hpend_info[name].get())
            except ValueError:
                if self.entered_hpend_info[name].get() != '' and 'time' not in name:
                    float_errors.append(name)
                #elif'time' not in name and '1' in name and self.entered_hpend_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_hpend_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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
                            'boil_time_hp']
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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.mpstartinfo:
            try:
                test = float(self.entered_mpstart_info[name].get())
            except ValueError:
                if self.entered_mpstart_info[name].get() != '' and 'time' not in name:
                    float_errors.append(name)
                #elif'time' not in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_mpstart_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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
                            'max_water_temp_pot3_mp', 'max_water_temp_pot4_mp', 'final_pot1_mass_mp',
                            'final_pot2_mass_mp', 'final_pot3_mass_mp', 'final_pot4_mass_mp']
        self.mpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
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

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.mpendinfo:
            try:
                test = float(self.entered_mpend_info[name].get())
            except ValueError:
                if self.entered_mpend_info[name].get() != '' and 'time' not in name:
                    float_errors.append(name)
                #elif'time' not in name and '1' in name and self.entered_mpend_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_mpend_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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
            if name == 'initial_fuel_mass_2_mp' or name == 'initial_fuel_mass_3_mp':
                self.entered_lpstart_info[name].insert(0, 0) #default of 0
            self.entered_lpstart_units[name] = tk.Entry(self)
            self.entered_lpstart_units[name].insert(0, self.lpstartunits[i])
            self.entered_lpstart_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.lpstartinfo:
            try:
                test = float(self.entered_lpstart_info[name].get())
            except ValueError:
                if self.entered_lpstart_info[name].get() != '' and 'time' not in name:
                    float_errors.append(name)
                #elif'time' not in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_lpstart_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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
                            'max_water_temp_pot3_lp', 'max_water_temp_pot4_lp', 'final_pot1_mass_lp',
                            'final_pot2_mass_lp', 'final_pot3_mass_lp', 'final_pot4_mass_lp']
        self.lpendunits = ['hh:mm:ss', 'kg', 'kg', 'kg', 'C', 'C', 'C', 'C', 'kg', 'kg', 'kg', 'kg']
        self.entered_lpend_info = {}
        self.entered_lpend_units = {}
        for i, name in enumerate(self.lpendinfo):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_lpend_info[name] = tk.Entry(self)
            self.entered_lpend_info[name].grid(row=i, column=2)
            if name == 'final_fuel_mass_2_mp' or name == 'final_fuel_mass_3_mp':
                self.entered_lpend_info[name].insert(0, 0) #default of 0
            self.entered_lpend_units[name] = tk.Entry(self)
            self.entered_lpend_units[name].insert(0, self.lpendunits[i])
            self.entered_lpend_units[name].grid(row=i, column=3)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        for name in self.lpendinfo:
            try:
                test = float(self.entered_lpend_info[name].get())
            except ValueError:
                if self.entered_lpend_info[name].get() != '' and 'time' not in name:
                    float_errors.append(name)
                #elif'time' not in name and '1' in name and self.entered_lpend_info[name].get() == '':
                    #blank_errors.append(name)
                #elif 'pot' in name and '1' in name and self.entered_lpend_info[name].get() == '':
                    #blank_errors.append(name)

        return float_errors, blank_errors

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

class ExtraTestInputsFrame(tk.LabelFrame):
    def __init__(self, root, text, new_vars: dict, units: dict):
        super().__init__(root, text=text, padx=10, pady=10)
        self.entered_test_info = {}
        self.entered_test_units = {}
        for i, name in enumerate(new_vars):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self, text=new_vars[name])
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
