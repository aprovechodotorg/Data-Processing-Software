import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from PEMS_SubtractBkg import PEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_Plotter1 import PEMS_Plotter
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PIL import Image, ImageTk
import webbrowser
import traceback
import csv

#For pyinstaller:
#C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS>pyinstaller --onefile -p C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS --icon=C:\Users\Jaden\Documents\GitHub\Data_Processing_aprogit\Data-Processing-Software\LEMS\ARC-Logo.ico LEMS_DataEntry_L1.py
class LEMSDataInput(tk.Frame):
    def __init__(self, root): #Set window
        tk.Frame.__init__(self, root)

        # Create a notebook to hold tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create a new frame
        self.tab_frame = tk.Frame(self.notebook)
        self.notebook.add(self.tab_frame, text="Data Entry")
        self.tab_frame.grid_rowconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.tab_frame, borderwidth=0, background="#ffffff")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        #create a bias check tab
        self.bias_frame = tk.Frame(self.notebook)
        self.notebook.add(self.bias_frame, text="Quality Control")
        self.bias_frame.grid_rowconfigure(0, weight=1)
        self.bias_frame.grid_columnconfigure(0, weight=1)
        self.bias_canvas = tk.Canvas(self.bias_frame, borderwidth=0, background="#ffffff")
        self.bias_canvas.grid(row=0, column=0, stick="nsew")

        # Create a frame inside the canvas
        self.inner_frame = tk.Frame(self.canvas, background="#ffffff")
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.bias_inner_frame = tk.Frame(self.bias_canvas, background="#ffffff")
        self.bias_canvas.create_window((0, 0), window=self.bias_inner_frame, anchor="nw")

        # vertical scrollbar
        self.vsb = tk.Scrollbar(self.tab_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set) #bind canvas to scrollbar
        self.vsb.grid(row=0, column=1, sticky="ns")

        # vertical scrollbar
        self.bias_vsb = tk.Scrollbar(self.bias_frame, orient="vertical", command=self.bias_canvas.yview)
        self.bias_canvas.configure(yscrollcommand=self.bias_vsb.set) #bind canvas to scrollbar
        self.bias_vsb.grid(row=0, column=1, sticky="ns")

        # horizontal scrollbar
        self.hsb = tk.Scrollbar(self.tab_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set) #bind canvas to scrollbar
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Configure canvas to fill the tab_frame
        self.canvas.grid_rowconfigure(0, weight=1)
        self.canvas.grid_columnconfigure(0, weight=1)

        self.bias_canvas.grid_rowconfigure(0, weight=1)
        self.bias_canvas.grid_columnconfigure(0, weight=1)

        # Bind scrollbars
        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)

        # Bind scrollbars
        self.bias_inner_frame.bind("<Configure>", self.onFrameConfigure_bias)
        self.bias_canvas.bind("<Configure>", self.onCanvasConfigure_bias)

        #################################
        #create data entry window

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

        self.instructions_frame = tk.Text(self.inner_frame, wrap="word", height=16, width=100)
        self.instructions_frame.insert(tk.END, instructions)
        self.instructions_frame.grid(row=1, column=1, columnspan=4, padx=(150, 0), pady=(10, 0))
        self.instructions_frame.config(state="disabled")

        # File Path Entry
        tk.Label(self.inner_frame, text="   Select Folder:   ").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.inner_frame, textvariable=self.folder_path_var, width=55)
        self.folder_path.grid(row=0, column=1)

        #create a button to browse folders on computer
        browse_button = tk.Button(self.inner_frame, text="  Browse  ", command=self.on_browse)
        browse_button.grid(row=0, column=2, padx=(0, 300))

        #create test info section
        self.test_info = TestInfoFrame(self.inner_frame, "Test Info")
        self.test_info.grid(row=1, column=0, columnspan=2, padx=(0, 170), pady=(100, 0))

        #create enviroment info section
        self.enviro_info = EnvironmentInfoFrame(self.inner_frame, "Test Conditions")
        self.enviro_info.grid(row=2, column=2, columnspan=2, pady=(10, 140), padx=(0, 40))

        #create comments section
        self.comments = CommentsFrame(self.inner_frame, "Comments")
        self.comments.grid(row=2, column=3, columnspan=3, pady=(10, 0), padx=(0, 70))

        # create fuel info section
        self.fuel_info = FuelInfoFrame(self.inner_frame, "Fuel Info")
        self.fuel_info.grid(row=2, column=0, columnspan=2)

        # create high power section
        self.hpstart_info = HPstartInfoFrame(self.inner_frame, "High Power Start")
        self.hpstart_info.grid(row=3, column=0, columnspan=2)
        self.hpend_info = HPendInfoFrame(self.inner_frame, "High Power End")
        self.hpend_info.grid(row=3, column=2, columnspan=2)

        # create medium power section
        self.mpstart_info = MPstartInfoFrame(self.inner_frame, "Medium Power Start")
        self.mpstart_info.grid(row=3, column=4, columnspan=2)
        self.mpend_info = MPendInfoFrame(self.inner_frame, "Medium Power End")
        self.mpend_info.grid(row=3, column=6, columnspan=2)

        # create low power section
        self.lpstart_info = LPstartInfoFrame(self.inner_frame, "Low Power Start")
        self.lpstart_info.grid(row=3, column=8, columnspan=2)
        self.lpend_info = LPendInfoFrame(self.inner_frame, "Low Power End")
        self.lpend_info.grid(row=3, column=10, columnspan=2)

        # create performance weight tiers
        self.weight_info = WeightPerformanceFrame(self.inner_frame, "Weighting for Voluntary Performance Tiers")
        self.weight_info.grid(row=4, column=0, columnspan=2, pady=(10, 0), padx=(0, 170))

        # interactive button
        ok_button = tk.Button(self.inner_frame, text="   Run for the first time   ", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=6, column=0, padx=(60, 0), pady=10)

        # noninteractive button
        nonint_button = tk.Button(self.inner_frame, text="   Run with previous inputs   ", command=self.on_nonint)
        nonint_button.anchor()
        nonint_button.grid(row=6, column=1, padx=(0, 60))

        #################################################################
        #Create Bias Check tab
        # File Path Entry
        tk.Label(self.bias_inner_frame, text="   Select Folder:   ").grid(row=0, column=0)
        self.folder_path_var_bias = tk.StringVar()
        self.folder_path_bias = tk.Entry(self.bias_inner_frame, textvariable=self.folder_path_var_bias, width=55)
        self.folder_path_bias.grid(row=0, column=1)

        #create a button to browse folders on computer
        browse_button = tk.Button(self.bias_inner_frame, text="  Browse  ", command=self.on_browse)
        browse_button.grid(row=0, column=2)

        gas_instructions = f"GAS CHECK INSTRUCTIONS:\n" \
                           f"The following entries are for gas checks. Gas checks are required before and after ISO " \
                           f"tests to ensure CO and CO2 sensors are working as inspected.\n" \
                           f"* Please follow your given gas check instruction.\n" \
                           f"* The concentrations of CO and CO2 as given by the manufacturer for the Zero and Span gas" \
                           f"will be written in the actual CO/CO2 concentration entry boxes (boxes are pre-populated " \
                           f"with standard defaults.\n" \
                           f"* Measurements of CO and CO2 will be entered as the average value given by the LEMS once stable.\n" \
                           f"* Measurements taken before the test will be entered in bias. Measurements taken after the " \
                           f"test will be entered in drift.\n" \
                           f"* Drift calculations cannot be preformed without bias calculations.\n" \
                           f"PLEASE NOTE: These values are calculated using your best estimation of average " \
                           f"concentration. To get official results, enter times for stable testing periods and proceed" \
                           f"with data entry steps (menu will prompt for final calculation). \n" \
                           f"* Press okay to update and record results. \n" \
                           f"RESULTS SHOWN ON THIS PAGE ARE NOT FINAL FOR GAS CHECKS"
        self.gas_instructions_frame = tk.Text(self.bias_inner_frame, wrap="word", height=23, width=60)
        self.gas_instructions_frame.insert(tk.END, gas_instructions)
        self.gas_instructions_frame.grid(row=1, column=0, rowspan=2, columnspan=3)
        self.gas_instructions_frame.config(state="disabled")

        self.gas_cal = GasCalibrationFrame(self.bias_inner_frame, "Gas Checks")
        self.gas_cal.grid(row=3, column=0, rowspan=2, columnspan=3)

        leak_instructions = f"LEAK CHECK INSTRUCTIONS:\n" \
                            f"The following entries are for leak checks. Leak checks are required before an ISO " \
                            f"test to ensure major leaks are not present in the system.\n" \
                            f"* Please follow your given leak check instructions for each system.\n" \
                            f"* ALL leak checks must pass before test can commence\n" \
                            f"* Press okay to update and recordresults.\n" \
                            f"RESULTS SHOWN ON THIS PAGE ARE FINAL FOR LEAK CHECKS"

        self.leak_instructions_frame = tk.Text(self.bias_inner_frame, wrap="word", height=9, width=60)
        self.leak_instructions_frame.insert(tk.END, leak_instructions)
        self.leak_instructions_frame.grid(row=1, column=3)
        self.leak_instructions_frame.config(state="disabled")

        self.leak_checks = LeakCheckFrame(self.bias_inner_frame, "Leak Checks")
        self.leak_checks.grid(row=2, column=3, rowspan=2, pady=(0,470))

        bias_ok_button = tk.Button(self.bias_inner_frame, text="OK", command=self.on_bias_okay)
        bias_ok_button.anchor()
        bias_ok_button.grid(row=3, column=3, padx=(500,0), pady=(890,0))

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        #self.bias_canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel_bias)

        self.grid(row=0, column=0)

    def onCanvasMouseWheel(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def onCanvasMouseWheel_bias(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.bias_canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.bias_canvas.yview_scroll(1, "units")

    def on_bias_okay(self):
        # create dictionary from user entries
        self.names = []  # list of names
        self.units = {}  # dictionary of units, keys are names
        self.data = {}  # dictionary of data, keys are names
        self.unc = {}  # dictionary of uncertainties, keys are names
        self.uval = {}  # dictionary of ufloats, keys are names

        # initialize a header
        name = 'variable_name'
        self.names.append(name)
        self.units[name] = 'units'
        self.data[name] = 'value'
        self.unc[name] = 'uncertainty'
        self.uval[name] = ''

        # go through each section and add entries to dictionaries
        self.biasdata = self.gas_cal.get_data()
        for name in self.biasdata:
            self.names.append(name)
            self.units[name] = ''
            try:
                self.data[name] = self.biasdata[name].get()
            except AttributeError:
                self.data[name] = self.biasdata[name]
            self.unc[name] = ''
            self.uval[name] = ''

        # go through each section and add entries to dictionaries
        self.leakcheck = self.leak_checks.get_data()
        for name in self.leakcheck:
            self.names.append(name)
            self.units[name] = ''
            try:
                self.data[name] = self.leakcheck[name].get()
            except AttributeError:
                self.data[name] = self.leakcheck[name]
            self.unc[name] = ''
            self.uval[name] = ''

        fail = []
        for name in self.names:
            if ['Rate', 'Chack', 'variable_name', 'start_time', 'end_time'] not in name:
                if self.data[name] != '':
                    try:
                        float(self.data[name])
                    except ValueError:
                        fail.append(name)

        if len(fail) != 0:
            errormessage = 'The following inputs were not entered as numbers:'
            for name in fail:
                errormessage = errormessage + ' ' + name
            messagebox.showerror("Error", errormessage)
        else:
            try:
                atm_pressure = float(self.data['Atmospheric_Pressure']) * 13.6  # Convert inHg to inH2O

                ########
                #Gravametric Sample Train leak check
                vol = float(self.data['Gravametric_Internal_Volume'])
                initial_pressure = float(self.data['Gravametric_Initial_Pressure'])
                final_pressure = float(self.data['Gravametric_Final_Pressure'])
                test_time = float(self.data['Gravametric_Test_Time'])
                flowrate = float(self.data['Gravametric_Nominal_flowrate'])

                leak_rate = (vol * abs(initial_pressure - final_pressure)) / (test_time * atm_pressure)

                self.data['Gravametric_Leak_Rate'] = f"{leak_rate:.6f}"

                # Update Gas_Sensor_Leak_Check
                if leak_rate < (flowrate * 0.001):
                    self.data['Gravametric_Leak_Check'] = 'PASS'
                    self.leak_checks.update_leak_check('Gravametric_Leak_Check', 'PASS', 'green')
                else:
                    self.data['Gravametric_Leak_Check'] = 'FAIL'
                    self.leak_checks.update_leak_check('Gravametric_Leak_Check', 'FAIL', 'red')

                self.leak_checks.update_leak_rate('Gravametric_Leak_Rate', self.data['Gravametric_Leak_Rate'])
            except:
                self.leak_checks.update_leak_rate('Gravametric_Leak_Rate', 'N/A')
                self.leak_checks.update_leak_check('Gravametric_Leak_Check', 'INVALID', 'red')

            try:
                #########
                #Gas Sample leack check
                vol = float(self.data['Sample_Line_Internal_Volume'])
                initial_pressure = float(self.data['Gas_Sensor_Initial_Pressure'])
                final_pressure = float(self.data['Gas_Sensor_Final_Pressure'])
                test_time = float(self.data['Gas_Sensor_Test_Time'])

                leak_rate = (vol * abs(initial_pressure - final_pressure)) / (test_time * atm_pressure)

                self.data['Gas_Sensor_Leak_Rate'] = f"{leak_rate:.6f}"

                flowrate = float(self.data['Gas_Sensor_Flow_Rate'])

                # Update Gas_Sensor_Leak_Check
                if leak_rate < (flowrate * 0.001):
                    self.data['Gas_Sensor_Leak_Check'] = 'PASS'
                    self.leak_checks.update_leak_check('Gas_Sensor_Leak_Check', 'PASS', 'green')
                else:
                    self.data['Gas_Sensor_Leak_Check'] = 'FAIL'
                    self.leak_checks.update_leak_check('Gas_Sensor_Leak_Check', 'FAIL', 'red')

                self.leak_checks.update_leak_rate('Gas_Sensor_Leak_Rate', self.data['Gas_Sensor_Leak_Rate'])
            except:
                self.leak_checks.update_leak_rate('Gas_Sensor_Leak_Rate', 'N/A')
                self.leak_checks.update_leak_check('Gas_Sensor_Leak_Check', 'INVALID', 'red')

            try:
                ########
                #Flow Grid leak check
                #negative
                initial_pressure = float(self.data['Negative_Pressure_Sensor_Initial_Pressure'])
                final_pressure = float(self.data['Negative_Pressure_Sensor_Final_Pressure'])

                leak_rate = (initial_pressure - final_pressure) / initial_pressure

                self.data['Negative_Pressure_Sensor_Leak_Rate'] = f"{leak_rate:.6f}"

                # Update Gas_Sensor_Leak_Check
                if leak_rate < 3 or leak_rate > -3:
                    self.data['Negative_Pressure_Sensor_Leak_Check'] = 'PASS'
                    self.leak_checks.update_leak_check('Negative_Pressure_Sensor_Leak_Check', 'PASS', 'green')
                else:
                    self.data['Negative_Pressure_Sensor_Leak_Check'] = 'FAIL'
                    self.leak_checks.update_leak_check('Negative_Pressure_Sensor_Leak_Check', 'FAIL', 'red')

                self.leak_checks.update_leak_rate('Negative_Pressure_Sensor_Leak_Rate', self.data['Negative_Pressure_Sensor_Leak_Rate'])

            except:
                self.leak_checks.update_leak_rate('Negative_Pressure_Sensor_Leak_Rate', 'N/A')
                self.leak_checks.update_leak_check('Negative_Pressure_Sensor_Leak_Check', 'INVALID', 'red')

            try:
                #postitive
                initial_pressure = float(self.data['Positive_Pressure_Sensor_Initial_Pressure'])
                final_pressure = float(self.data['Positive_Pressure_Sensor_Final_Pressure'])

                leak_rate = (initial_pressure - final_pressure) / initial_pressure

                self.data['Positive_Pressure_Sensor_Leak_Rate'] = f"{leak_rate:.6f}"

                # Update Gas_Sensor_Leak_Check
                if leak_rate < 3:
                    self.data['Positive_Pressure_Sensor_Leak_Check'] = 'PASS'
                    self.leak_checks.update_leak_check('Positive_Pressure_Sensor_Leak_Check', 'PASS', 'green')
                else:
                    self.data['Positive_Pressure_Sensor_Leak_Check'] = 'FAIL'
                    self.leak_checks.update_leak_check('Positive_Pressure_Sensor_Leak_Check', 'FAIL', 'red')

                self.leak_checks.update_leak_rate('Positive_Pressure_Sensor_Leak_Rate', self.data['Positive_Pressure_Sensor_Leak_Rate'])

            except:
                self.leak_checks.update_leak_rate('Positive_Pressure_Sensor_Leak_Rate', 'N/A')
                self.leak_checks.update_leak_check('Positive_Pressure_Sensor_Leak_Check', 'INVALID', 'red')

            #Span
            #CO
            #bias
            try:
                span_conc = float(self.data['Span_Gas_Actual_CO_Concentration'])
                span_measure = float(self.data['Span_Gas_Measured_CO_Concentration_Bias'])

                bias = ((span_measure - span_conc) / span_conc) * 100

                self.data['Span_Bias_CO'] = f"{bias:.6f}"

                if abs(bias) <= 5:
                    self.data['Span_Gas_Bias_Check_CO'] = 'PASS'
                    self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO', 'PASS', 'green')
                else:
                    self.data['Span_Gas_Bias_Check_CO'] = 'FAIL'
                    self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Span_Bias_CO', self.data['Span_Bias_CO'])
            except:
                self.gas_cal.update_gas_rate('Span_Bias_CO', 'N/A')
                self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO', 'INVALID', 'red')

            #drift
            try:
                span_conc = float(self.data['Span_Gas_Actual_CO_Concentration'])
                span_measure = float(self.data['Span_Gas_Measured_CO_Concentration_Drift'])

                drift = ((span_measure - span_conc) / span_conc) * 100 - float(self.data['Span_Bias_CO'])

                self.data['Span_Drift_CO'] = f"{drift:.6f}"

                if abs(drift) <= 3:
                    self.data['Span_Gas_Drift_Check_CO'] = 'PASS'
                    self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO', 'PASS', 'green')
                else:
                    self.data['Span_Gas_Drift_Check_CO'] = 'FAIL'
                    self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Span_Drift_CO', self.data['Span_Drift_CO'])
            except:
                self.gas_cal.update_gas_rate('Span_Drift_CO', 'N/A')
                self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO', 'INVALID', 'red')

            #CO2
            #bias
            try:
                span_conc = float(self.data['Span_Gas_Actual_CO2_Concentration'])
                span_measure = float(self.data['Span_Gas_Measured_CO2_Concentration_Bias'])

                bias = ((span_measure - span_conc) / span_conc) * 100

                self.data['Span_Bias_CO2'] = f"{bias:.6f}"

                if abs(bias) <= 5:
                    self.data['Span_Gas_Bias_Check_CO2'] = 'PASS'
                    self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO2', 'PASS', 'green')
                else:
                    self.data['Span_Gas_Bias_Check_CO2'] = 'FAIL'
                    self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO2', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Span_Bias_CO2', self.data['Span_Bias_CO2'])
            except:
                self.gas_cal.update_gas_rate('Span_Bias_CO2', 'N/A')
                self.gas_cal.update_gas_check('Span_Gas_Bias_Check_CO2', 'INVALID', 'red')

            #drift
            try:
                span_conc = float(self.data['Span_Gas_Actual_CO2_Concentration'])
                span_measure = float(self.data['Span_Gas_Measured_CO2_Concentration_Drift'])

                drift = ((span_measure - span_conc) / span_conc) * 100 - float(self.data['Span_Bias_CO2'])

                self.data['Span_Drift_CO2'] = f"{drift:.6f}"

                if abs(drift) <= 3:
                    self.data['Span_Gas_Drift_Check_CO2'] = 'PASS'
                    self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO2', 'PASS', 'green')
                else:
                    self.data['Span_Gas_Drift_Check_CO2'] = 'FAIL'
                    self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO2', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Span_Drift_CO2', self.data['Span_Drift_CO2'])
            except:
                self.gas_cal.update_gas_rate('Span_Drift_CO2', 'N/A')
                self.gas_cal.update_gas_check('Span_Gas_Drift_Check_CO2', 'INVALID', 'red')

            #Zero
            #CO
            #bias
            try:
                zero_conc = float(self.data['Zero_Gas_Actual_CO_Concentration'])
                span_conc = float(self.data['Span_Gas_Actual_CO_Concentration'])
                zero_measure = float(self.data['Zero_Gas_Measured_CO_Concentration_Bias'])

                bias = ((zero_measure - zero_conc) / span_conc) * 100

                self.data['Zero_Bias_CO'] = f"{bias:.6f}"

                if abs(bias) <= 5:
                    self.data['Zero_Gas_Bias_Check_CO'] = 'PASS'
                    self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO', 'PASS', 'green')
                else:
                    self.data['Zero_Gas_Bias_Check_CO'] = 'FAIL'
                    self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Zero_Bias_CO', self.data['Zero_Bias_CO'])
            except:
                self.gas_cal.update_gas_rate('Zero_Bias_CO', 'N/A')
                self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO', 'INVALID', 'red')

            #drift
            try:
                zero_conc = float(self.data['Zero_Gas_Actual_CO_Concentration'])
                span_conc = float(self.data['Span_Gas_Actual_CO_Concentration'])
                zero_measure = float(self.data['Zero_Gas_Measured_CO_Concentration_Drift'])

                drift = ((zero_measure - zero_conc) / span_conc) * 100 - float(self.data['Zero_Bias_CO'])

                self.data['Zero_Drift_CO'] = f"{drift:.6f}"

                if abs(drift) <= 3:
                    self.data['Zero_Gas_Drift_Check_CO'] = 'PASS'
                    self.gas_cal.update_gas_check('Zero_Gas_Drift_Check_CO', 'PASS', 'green')
                else:
                    self.data['Zero_Gas_Drift_Check_CO'] = 'FAIL'
                    self.gas_cal.update_gas_check('Zero_Gas_Drift_Check_CO', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Zero_Drift_CO', self.data['Zero_Drift_CO'])
            except:
                self.gas_cal.update_gas_rate('zero_Drift_CO', 'N/A')
                self.gas_cal.update_gas_check('zero_Gas_Drift_Check_CO', 'INVALID', 'red')

            #CO2
            # bias
            try:
                zero_conc = float(self.data['Zero_Gas_Actual_CO2_Concentration'])
                span_conc = float(self.data['Span_Gas_Actual_CO2_Concentration'])
                zero_measure = float(self.data['Zero_Gas_Measured_CO2_Concentration_Bias'])

                bias = ((zero_measure - zero_conc) / span_conc) * 100

                self.data['Zero_Bias_CO2'] = f"{bias:.6f}"

                if abs(bias) <= 5:
                    self.data['Zero_Gas_Bias_Check_CO2'] = 'PASS'
                    self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO2', 'PASS', 'green')
                else:
                    self.data['Zero_Gas_Bias_Check_CO2'] = 'FAIL'
                    self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO2', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Zero_Bias_CO2', self.data['Zero_Bias_CO2'])
            except:
                self.gas_cal.update_gas_rate('Zero_Bias_CO2', 'N/A')
                self.gas_cal.update_gas_check('Zero_Gas_Bias_Check_CO2', 'INVALID', 'red')

            # drift
            try:
                zero_conc = float(self.data['Zero_Gas_Actual_CO2_Concentration'])
                span_conc = float(self.data['Span_Gas_Actual_CO2_Concentration'])
                zero_measure = float(self.data['Zero_Gas_Measured_CO2_Concentration_Drift'])

                drift = ((zero_measure - zero_conc) / span_conc) * 100 - float(self.data['Zero_Bias_CO2'])

                self.data['Zero_Drift_CO2'] = f"{drift:.6f}"

                if abs(drift) <= 3:
                    self.data['Zero_Gas_Drift_Check_CO2'] = 'PASS'
                    self.gas_cal.update_gas_check('Zero_Gas_Drift_Check_CO2', 'PASS', 'green')
                else:
                    self.data['Zero_Gas_Drift_Check_CO2'] = 'FAIL'
                    self.gas_cal.update_gas_check('Zero_Gas_Drift_Check_CO2', 'FAIL', 'red')
                self.gas_cal.update_gas_rate('Zero_Drift_CO2', self.data['Zero_Drift_CO2'])
            except:
                self.gas_cal.update_gas_rate('zero_Drift_CO2', 'N/A')
                self.gas_cal.update_gas_check('zero_Gas_Drift_Check_CO2', 'INVALID', 'red')
            success = 0

            # Save to CSV
            try:
                self.bias_path = os.path.join(self.folder_path,
                                              f"{os.path.basename(self.folder_path)}_QualityControl.csv")
                try:
                    io.write_constant_outputs(self.bias_path, self.names, self.units, self.data, self.unc, self.uval)
                    success = 1
                    print("Quality checks have been recorded: " + self.bias_path)
                except AttributeError:
                    self.folder_path = self.folder_path.get()
                    self.bias_path = os.path.join(self.folder_path,
                                                  f"{os.path.basename(self.folder_path)}_QualityControl.csv")
                    io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                    success = 1
                except PermissionError:
                    message = self.file_path + ' is open in another program, please close it and try again.'
                    # Error
                    messagebox.showerror("Error", message)
            except TypeError:
                errormessage = 'Information not saved! Please select a folder and try again'
                messagebox.showerror("Error", errormessage)

    def on_nonint(self): #When okay button is pressed
        self.inputmethod = '2' #set to non interactive mode

        # for each frame, check inputs for errors
        float_errors = []
        blank_errors = []
        range_errors = []
        value_errors = []
        format_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.comments.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors, range_errors = self.enviro_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, range_errors = self.fuel_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, value_errors, format_errors = self.hpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.hpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.mpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.mpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.lpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.lpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors = self.weight_info.check_input_validity(float_errors, blank_errors)

        #provide error messages for any errors
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
        else: #If there's no errors, proceed to next window
            #create dictionary from user entries
            self.names = [] #list of names
            self.units = {} #dictionary of units, keys are names
            self.data = {} #dictionary of data, keys are names
            self.unc = {} #dictionary of uncertainties, keys are names
            self.uval = {} #dictionary of ufloats, keys are names

            #initialize a header
            name = 'variable_name'
            self.names.append(name)
            self.units[name] = 'units'
            self.data[name] = 'value'
            self.unc[name] = 'uncertainty'
            self.uval[name] = ''

            #go through each section and add entries to dictionaries
            self.testdata = self.test_info.get_data()
            for name in self.testdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.testdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.commentsdata = self.comments.get_data()
            for n, name in enumerate(self.commentsdata):
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.commentsdata[name].get("1.0", "end").strip()
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
            except AttributeError:
                self.folder_path = self.folder_path.get()
                self.file_path = os.path.join(self.folder_path,
                                              f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except PermissionError:
                message = self.file_path + ' is open in another program, please close it and try again.'
                # Error
                messagebox.showerror("Error", message)

            ################################################################
            #once successful, create a new window with menu options
            if success == 1:
                #ensure energy calculations will work (data entry was created correctly)
                success = 0
                self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
                self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
                try:
                    [trail, units, data, logs] = LEMS_EnergyCalcs(self.file_path, self.output_path, self.log_path)
                    success = 1
                except PermissionError:
                    message = self.output_path + ' is open in another program, please close it and try again.'
                    # Error
                    messagebox.showerror("Error", message)
                if success == 1:
                    #if energy calcs are succesful
                    #self.frame.destroy() #destroy data entry frame

                    # Create a notebook to hold tabs
                    #self.notebook = ttk.Notebook(height=30000)
                    #self.notebook.grid(row=0, column=0)

                    # Delete all tabs after the menu tab, starting from the second tab
                    to_forget = []
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == "Data Entry":
                            pass
                        else:
                            to_forget.append(i)
                    count = 0
                    for i in to_forget:
                        i = i - count
                        self.notebook.forget(i)
                        count += 1

                    tab_frame = tk.Frame(self.notebook)
                    self.notebook.add(tab_frame, text="Menu")
                    # Set up the frame for the menu tab content
                    self.frame = tk.Frame(tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)

                    # Switch the view to the newly added menu tab
                    self.notebook.select(tab_frame)

                    ######Create all the menu options. When their clicked they'll make a new tab in the notebook
                    self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations",
                                                   command=self.on_energy)
                    self.energy_button.grid(row=1, column=0, padx=(0,100))

                    self.cali_button = tk.Button(self.frame, text="Step 2: Adjust Sensor Calibrations", command=self.on_cali)
                    self.cali_button.grid(row=2, column=0, padx=(0,60))

                    self.bkg_button = tk.Button(self.frame, text="Step 3: Subtract Background", command=self.on_bkg)
                    self.bkg_button.grid(row=3, column=0, padx=(0,90))

                    self.grav_button = tk.Button(self.frame, text="Step 4: Calculate Gravametric Data (optional)", command=self.on_grav)
                    self.grav_button.grid(row=4, column=0, padx=0)

                    self.emission_button = tk.Button(self.frame, text="Step 5: Calculate Emissions", command=self.on_em)
                    self.emission_button.grid(row=5, column=0, padx=(0,100))

                    self.all_button = tk.Button(self.frame, text="View All Outputs", command=self.on_all)
                    self.all_button.grid(row=6, column=0, padx=(0,150))

                    self.plot_button = tk.Button(self.frame, text="Plot Data", command=self.on_plot)
                    self.plot_button.grid(row=7, column=0, padx=(0,190))

                    #spacer for formatting
                    blank = tk.Frame(self.frame, width=self.winfo_width()-1000)
                    blank.grid(row=0, column=2, rowspan=2)

                    # Exit button
                    exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                    exit_button.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")

                    #Instructions
                    message = f'* Please use the following buttons in order to process your data.\n' \
                              f'* Buttons will turn green when successful.\n' \
                              f'* Buttons will turn red when unsuccessful.\n' \
                              f'* Tabs will appear which will contain outputs from each step.\n' \
                              f'* If data from a previous step is changed, all proceeding steps must be done again.\n' \
                              f'* Files with data outputs will appear in the folder you selected. Modifying these files will change the calculated result if steps are redone.\n\n' \
                              f'DO NOT proceed with the next step until the previous step is successful.\n' \
                              f'If a step is unsuccessful and all instructions from the error message have been followed ' \
                              f'or no error message appears, send a screenshot of the print out in your python interpreter' \
                              f'or the second screen (black with white writing if using the app version) along with your ' \
                              f'data to jaden@aprovecho.org.'
                    instructions = tk.Text(self.frame, width=85, wrap="word", height=13)
                    instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                    instructions.insert(tk.END, message)
                    instructions.configure(state="disabled")

                    #button to toggle between interactive and non interactive methods
                    self.toggle = tk.Button(self.frame, text="      Click to enter new values       ", bg='lightblue',
                                            command=self.update_input)
                    self.toggle.grid(row=0, column=0)

                    # Recenter view to top-left
                    self.canvas.yview_moveto(0)
                    self.canvas.xview_moveto(0)

                    #auto run through all menu options
                    self.on_energy()
                    self.on_cali()
                    self.on_bkg()
                    self.on_grav()
                    self.on_em()
                    self.on_all()

    def on_okay(self): #When okay button is pressed
        #set method to interactive
        self.inputmethod = '1'

        # for each frame, check inputs for any errors
        float_errors = []
        blank_errors = []
        range_errors = []
        value_errors = []
        format_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors = self.comments.check_input_validity(float_errors, blank_errors)
        float_errors, blank_errors, range_errors = self.enviro_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, range_errors = self.fuel_info.check_input_validity(float_errors, blank_errors, range_errors)
        float_errors, blank_errors, value_errors, format_errors = self.hpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.hpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.mpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.mpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors, value_errors, format_errors = self.lpstart_info.check_input_validity(float_errors, blank_errors, value_errors, format_errors)
        float_errors, blank_errors, format_errors = self.lpend_info.check_input_validity(float_errors, blank_errors, format_errors)
        float_errors, blank_errors = self.weight_info.check_input_validity(float_errors, blank_errors)

        #display errors to user
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
        else: #if there's no errors, create dictionaries from user inputs
            self.names = [] #list of variable names
            self.units = {} #dictionary of units, key is names
            self.data = {} #dictionary of data, key is names
            self.unc = {} #dictionary of uncertainty, key is names
            self.uval = {} #dictionary of ufloats, key is names

            #initialize a header
            name = 'variable_name'
            self.names.append(name)
            self.units[name] = 'units'
            self.data[name] = 'value'
            self.unc[name] = 'uncertainty'
            self.uval[name] = ''

            #go through each section and add entries to dictionaries
            self.testdata = self.test_info.get_data()
            for name in self.testdata:
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.testdata[name].get()
                self.unc[name] = ''
                self.uval[name] = ''

            self.commentsdata = self.comments.get_data()
            for n, name in enumerate(self.commentsdata):
                self.names.append(name)
                self.units[name] = ''
                self.data[name] = self.commentsdata[name].get("1.0", "end").strip()
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
            self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")
            success = 0

            # Save to CSV
            try:
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except AttributeError:
                self.folder_path = self.folder_path.get()
                self.file_path = os.path.join(self.folder_path,
                                              f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
                io.write_constant_outputs(self.file_path, self.names, self.units, self.data, self.unc, self.uval)
                success = 1
            except PermissionError:
                message = self.file_path + ' is open in another program, please close it and try again.'
                # Error
                messagebox.showerror("Error", message)

            if success == 1:
                #check that energy calcs can be run
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
                    #if energy calcs can be run
                    #self.frame.destroy() #destroy data entry frame

                    # Create a notebook to hold tabs
                    #self.notebook = ttk.Notebook(height=30000)
                    #self.notebook.grid(row=0, column=0)

                    # Create a new frame
                    #self.tab_frame = tk.Frame(self.notebook, height=300000)
                    #self.tab_frame.grid(row=1, column=0)

                    # Add the tab to the notebook with the folder name as the tab label
                    #self.notebook.add(self.tab_frame, text="Menu")

                    # Set up the frame
                    #self.frame = tk.Frame(self.tab_frame, background="#ffffff", height=self.winfo_height(),
                                         # width=self.winfo_width() * 20)
                    #self.frame.grid(row=1, column=0)

                    # Delete all tabs after the menu tab, starting from the second tab
                    to_forget = []
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == "Data Entry":
                            pass
                        else:
                            to_forget.append(i)
                    count = 0
                    for i in to_forget:
                        i = i - count
                        self.notebook.forget(i)
                        count += 1

                    tab_frame = tk.Frame(self.notebook)
                    self.notebook.add(tab_frame, text="Menu")
                    # Set up the frame for the menu tab content
                    self.frame = tk.Frame(tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)

                    # Switch the view to the newly added menu tab
                    self.notebook.select(tab_frame)

                    #####Create menu option buttons
                    self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                    self.energy_button.grid(row=1, column=0, padx=(0,100))

                    self.cali_button = tk.Button(self.frame, text="Step 2: Adjust Sensor Calibrations", command=self.on_cali)
                    self.cali_button.grid(row=2, column=0, padx=(0,60))

                    self.bkg_button = tk.Button(self.frame, text="Step 3: Subtract Background", command=self.on_bkg)
                    self.bkg_button.grid(row=3, column=0, padx=(0,90))

                    self.grav_button = tk.Button(self.frame, text="Step 4: Calculate Gravametric Data (optional)", command=self.on_grav)
                    self.grav_button.grid(row=4, column=0, padx=0)

                    self.emission_button = tk.Button(self.frame, text="Step 5: Calculate Emissions", command=self.on_em)
                    self.emission_button.grid(row=5, column=0, padx=(0,100))

                    self.all_button = tk.Button(self.frame, text="View All Outputs", command=self.on_all)
                    self.all_button.grid(row=6, column=0, padx=(0,150))

                    self.plot_button = tk.Button(self.frame, text="Plot Data", command=self.on_plot)
                    self.plot_button.grid(row=7, column=0, padx=(0,190))

                    #spacer for formatting
                    blank = tk.Frame(self.frame, width=self.winfo_width()-1000)
                    blank.grid(row=0, column=2, rowspan=2)

                    # Exit button
                    exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                    exit_button.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")

                    #Instructions
                    message = f'* Please use the following buttons in order to process your data.\n' \
                              f'* Buttons will turn green when successful.\n' \
                              f'* Buttons will turn red when unsuccessful.\n' \
                              f'* Tabs will appear which will contain outputs from each step.\n' \
                              f'* If data from a previous step is changed, all proceeding steps must be done again.\n' \
                              f'* Files with data outputs will appear in the folder you selected. Modifying these files will change the calculated result if steps are redone.\n\n' \
                              f'DO NOT proceed with the next step until the previous step is successful.\n' \
                              f'If a step is unsuccessful and all instructions from the error message have been followed ' \
                              f'or no error message appears, send a screenshot of the print out in your python interpreter' \
                              f'or the second screen (black with white writing if using the app version) along with your ' \
                              f'data to jaden@aprovecho.org.'
                    instructions = tk.Text(self.frame, width=85, wrap="word", height=13)
                    instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                    instructions.insert(tk.END, message)
                    instructions.configure(state="disabled")

                    #toggle button for switching between interactive and non interactive
                    self.toggle = tk.Button(self.frame, text=" Click to run with current values ", bg='violet',
                                            command=self.update_input)
                    self.toggle.grid(row=0, column=0)

                    # Recenter view to top-left
                    self.canvas.yview_moveto(0)
                    self.canvas.xview_moveto(0)

    def update_input(self):
        #switch between interactive(1) and non interactive(2)
        if self.inputmethod == '2':
            self.inputmethod = '1'
            self.toggle.config(text=" Click to run with current values ", bg='violet')
        elif self.inputmethod == '1':
            self.inputmethod = '2'
            self.toggle.config(text="      Click to enter new values       ", bg='lightblue')

    def on_plot(self):
        # Function to handle OK button click
        def ok():
            nonlocal selected_phases
            selected_phases = [phases[i] for i in listbox.curselection()] #record all selected phases
            popup.destroy() #destroy window

        # Function to handle Cancel button click
        def cancel():
            popup.destroy()

        #phases that can be graphed
        phases = ['hp', 'mp', 'lp']

        # Create a popup for selection
        popup = tk.Toplevel(self)
        popup.title("Select Phases")

        selected_phases = []

        #Instructions for popuo=p
        message = tk.Label(popup, text="Select phases to graph")
        message.grid(row=0, column=0, columnspan=2, padx=20)

        # Listbox to display phases n popup
        listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE, height=5)
        for phase in phases:
            listbox.insert(tk.END, phase)
        listbox.grid(row=1, column=0, columnspan=2, padx=20)

        # OK button
        ok_button = tk.Button(popup, text="OK", command=ok)
        ok_button.grid(row=2, column=0, padx=5, pady=5)

        # Cancel button
        cancel_button = tk.Button(popup, text="Cancel", command=cancel)
        cancel_button.grid(row=2, column=1, padx=5, pady=5)

        # Wait for popup to be destroyed
        popup.wait_window()

        #ignore bonus sensors for heating stove tests
        self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")

        #For each selected phase, graph according to the time series metrics
        for phase in selected_phases:
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeriesMetrics_"
                                           + phase + ".csv")
            if os.path.isfile(self.input_path):  # check that the data exists
                try:
                    self.plots_path = os.path.join(self.folder_path,
                                                   f"{os.path.basename(self.folder_path)}_plots_"
                                                   + phase + ".csv")
                    self.fig_path = os.path.join(self.folder_path,
                                                   f"{os.path.basename(self.folder_path)}_plot_"
                                                   + phase + ".png")

                    names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                        PEMS_Plotter(self.input_path, self.fuel_path, self.fuelmetric_path, self.exact_path, self.scale_path,
                                     self.nano_path, self.teom_path, self.senserion_path, self.ops_path, self.pico_path, self.plots_path,
                                     self.fig_path, self.log_path)
                    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames,
                                        pnames, self.plots_path, self.fig_path)
                except PermissionError:
                    message = f"File: {self.plots_path} is open in another program, close and try again."
                    messagebox.showerror("Error", message)
                except ValueError as e:
                    print(e)
                    if 'could not convert' in str(e):
                        message = f'The scale input requires a valid number. Letters and blanks are not valid numbers. Please correct the issue and try again.'
                        messagebox.showerror("Error", message)
                    if 'invalid literal' in str(e):
                        message = f'The plotted input requires a valid input of an integer either 0 to not plot or any integer to plot. Please correct the issue and try again.'
                        messagebox.showerror("Error", message)
                    if 'valid value for color' in str(e):
                        message = f'One of the colors is invalid. A valid list of colors can be found at: '
                        error_win = tk.Toplevel(root)
                        error_win.title("Error")
                        error_win.geometry("400x100")

                        error_label = tk.Label(error_win, text=message)
                        error_label.pack(pady=10)

                        hyperlink = tk.Button(error_win,
                                              text="https://matplotlib.org/stable/gallery/color/named_colors.html",
                                              command=open_website)
                        hyperlink.pack()

                # Check if the plot tab exists
                tab_index = None
                for i in range(self.notebook.index("end")):
                    if self.notebook.tab(i, "text") == (phase + " Plot"):
                        tab_index = i
                if tab_index is None: #if no tab exists
                    # Create a new frame for each tab
                    self.tab_frame = tk.Frame(self.notebook, height=300000)
                    self.tab_frame.grid(row=1, column=0)
                    # Add the tab to the notebook with the folder name as the tab label
                    self.notebook.add(self.tab_frame, text=phase + " Plot")

                    # Set up the frame
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
                    self.notebook.add(self.tab_frame, text=phase + " Plot")

                    # Set up the frame
                    self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                    self.frame.grid(row=1, column=0)

                #create a frame to display the plot and plot options
                plot_frame = Plot(self.frame, self.plots_path, self.fig_path, self.folder_path, data)
                plot_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_all(self):
        try: #try loading in all outputs file
            self.all_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_AllOutputs.csv")
            names, units, data, unc, uval = io.load_constant_inputs(self.all_path)
            self.all_button.config(bg="lightgreen")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.all_button.config(bg="red")

        # Check if the all outputs tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "All Outputs":
                tab_index = i
        if tab_index is None: #if it doesn't, create it
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="All Outputs")

            # Set up the frame
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
            self.notebook.add(self.tab_frame, text="All Outputs")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        all_frame = All_Outputs(self.frame, data, units)
        all_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_em(self):
        try:
            #create needed file paths and run function
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeries.csv")
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.grav_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravOutputs.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EmissionOutputs.csv")
            self.all_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_AllOutputs.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
            self.sensor_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_SensorboxVersion.csv")
            self.emission_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EmissionInputs.csv")
            logs, data, units = LEMS_EmissionCalcs(self.input_path, self.energy_path, self.grav_path, self.average_path,
                                                   self.output_path, self.all_path, self.log_path, self.phase_path, self.sensor_path,
                                                   self.fuel_path, self.fuelmetric_path, self.exact_path,
                                                   self.scale_path, self.nano_path, self.teom_path, self.senserion_path,
                                                   self.ops_path, self.pico_path, self.emission_path, self.inputmethod)
            self.emission_button.config(bg="lightgreen")
        except PermissionError:
            message = f"One of the following files: {self.output_path}, {self.all_path} is open in another program. Please close and try again."
            messagebox.showerror("Error", message)
            self.emission_button.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.emission_button.config(bg="red")

        # Check if the emission Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Emission Calculations":
                tab_index = i
        if tab_index is None: #if it doesn't
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Emission Calculations")

            # Set up the frame
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
            self.notebook.add(self.tab_frame, text="Emission Calculations")

            # Set up the frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        em_frame = Emission_Calcs(self.frame, logs, data, units)
        em_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_grav(self):
        try:
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravInputs.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_GravOutputs.csv")
            logs, gravval, outval, gravunits, outunits = LEMS_GravCalcs(self.input_path, self.average_path,
                                                                        self.phase_path, self.energy_path,
                                                                        self.output_path, self.log_path, self.inputmethod)
            self.grav_button.config(bg="lightgreen")
        except PermissionError:
            message = f"File: {self.output_path} is open in another program. Please close and try again."
            messagebox.showerror("Error", message)
            self.grav_path.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.grav_button.config(bg="red")

        # Check if the grav Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Gravametric Calculations":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Gravametric Calculations")

            # Set up the frame
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
            self.notebook.add(self.tab_frame, text="Gravametric Calculations")

            # Set up the frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        grav_frame = Grav_Calcs(self.frame, logs, gravval, outval, gravunits, outunits)
        grav_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_bkg(self):
        try:
            self.energy_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyOutputs.csv")
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData_Recalibrated.csv")
            self.UC_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_UCInputs.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeries.csv")
            self.average_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Averages.csv")
            self.phase_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_PhaseTimes.csv")
            self.method_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_BkgMethods.csv")
            self.fig1 = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}__subtractbkg1.png")
            self.fig2 = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}__subtractbkg2.png")
            logs, methods, phases, data = PEMS_SubtractBkg(self.input_path, self.energy_path, self.UC_path, self.output_path,
                                              self.average_path, self.phase_path, self.method_path,self.log_path,
                                              self.fig1, self.fig2, self.inputmethod)
            self.bkg_button.config(bg="lightgreen")
        except PermissionError:
            message = f"One of the following files: {self.output_path}, {self.phase_path}, {self.method_path} is open in another program. Please close and try again."
            messagebox.showerror("Error", message)
            self.bkg_button.config(bg="red")
        except KeyError as e:
            print(e)
            if 'time' in str(e):
                error = str(e)
                wrong = error.split(':')
                message = f"Time entry for:{wrong} is either entered in an incorrect format or is a time that occured before or after data was collected.\n" \
                          f"    * Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                          f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                          f"    * Check that the entered time exist within the data\n" \
                          f"    * Check that the time has not been left blank when there should be an entry.\n" \
                          f"The file {self.phase_path} may need to be opened and changed or deleted."
            self.bkg_button.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.bkg_button.config(bg="red")

        # Check if the bkg Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Subtract Background":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.grid(row=1, column=0)
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Subtract Background")

            # Set up the frame
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
            self.notebook.add(self.tab_frame, text="Subtract Background")

            # Set up the frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        bkg_frame = Subtract_Bkg(self.frame, logs, self.fig1, self.fig2, methods, phases, data)
        bkg_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_cali(self):
        try:
            self.sensor_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_SensorboxVersion.csv")
            self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData.csv")
            self.output_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_RawData_Recalibrated.csv")
            self.header_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_Header.csv")
            logs, firmware = LEMS_Adjust_Calibrations(self.input_path, self.sensor_path, self.output_path, self.header_path, self.log_path, self.inputmethod)
            self.cali_button.config(bg="lightgreen")

        except UnboundLocalError:
            message = f'Something went wrong in Firmware calculations. \n' \
                      f'Please verify that the entered firmware version corresponds to the sensor box number.\n' \
                      f'Accepted firmware versions:\n' \
                      f'    *SB4003.16\n' \
                      f'    *SB3001\n' \
                      f'    *SB3002\n' \
                      f'If your sensor box firmware is not one of the ones listed, it can be entered but nothing will be recalibrated.\n' \
                      f'This may lead to issues later.'
            messagebox.showerror("Error", message)
            self.cali_button.config(bg="red")

        except PermissionError:
            message = f"File: {self.output_path} is open in another program. Please close and try again."
            messagebox.showerror("Error", message)
            self.cali_button.config(br="red")
        except IndexError:
            message = f'Program was unable to read the raw data file correctly. Please check the following:\n' \
                      f'    * There are no blank lines or cells within the data set\n' \
                      f'    * The sensor box was not reset at some point causing a header to be inserted into the middle of the data set.\n' \
                      f'    * There are no extra blank lines or non value lines at the end of the file.\n' \
                      f'Opening the file in a text editing program like notepad may be helpful.' \
                      f'Delete problems and try again.'
            messagebox.showerror("Error", message)
            self.cali_button.config(bg="red")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            self.cali_button.config(bg="red")

        # Check if the grav Calculations tab exists
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

            # Set up the frame
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

            # Set up the frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        adjust_frame = Adjust_Frame(self.frame, logs, firmware)
        adjust_frame.grid(row=3, column=0, padx=0, pady=0)

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

                # Set up the frame
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

                # Set up the frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            output_table = OutputTable(self.frame, data, units, logs, num_columns=self.winfo_width(),
                                       num_rows=self.winfo_height(), folder_path=self.folder_path)
            output_table.grid(row=3, column=0, columnspan=self.winfo_width(), padx=0, pady=0)

    def on_browse(self): #when browse button is hit, pull up file finder.
        self.destroy_widgets()

        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        self.folder_path_var_bias.set(self.folder_path)

        # Check if _EnergyInputs.csv file exists
        self.file_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_EnergyInputs.csv")
        try:
            [names,units,data,unc,uval] = io.load_constant_inputs(self.file_path)
            try:
                data.pop("variable_name")
            except:
                data.pop('nombre_variable')
            #if it does, load in previous data
            data = self.test_info.check_imported_data(data)
            data = self.comments.check_imported_data(data)
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
                self.extra_test_inputs = ExtraTestInputsFrame(self.inner_frame, "Additional Test Inputs", data, units)
                self.extra_test_inputs.grid(row=5, column=0, columnspan=2)
        except FileNotFoundError:
            pass #no loaded inputs, file will be created in selected folder

        # Check if _LeakCheck.csv file exists
        self.leak_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_QualityControl.csv")
        try:
            [names, units, bias_data, unc, uval] = io.load_constant_inputs(self.leak_path)
            try:
                bias_data.pop("variable_name")
            except:
                bias_data.pop('nombre_variable')
            # if it does, load in previous data
            bias_data = self.gas_cal.check_imported_data(bias_data)
            bias_data = self.leak_checks.check_imported_data(bias_data)
        except FileNotFoundError:
            pass #no loaded inputs, file will be created in selected folder

    def destroy_widgets(self):
        #Destroy previously created widgets.
        if hasattr(self, 'message'):
            self.message.destroy()
        if hasattr(self, 'file_selection_listbox'):
            self.file_selection_listbox.destroy()
        if hasattr(self, 'ok_button'):
            self.ok_button.destroy()

    def onFrameConfigure(self, event):
        #Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def onFrameConfigure_bias(self, event):
        #Reset the scroll region to encompass the inner frame
        self.bias_canvas.configure(scrollregion=self.bias_canvas.bbox("all"))

    def onCanvasConfigure_bias(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.bias_canvas.config(scrollregion=self.bias_canvas.bbox("all"))

class Plot(tk.Frame):
    def __init__(self, root, plotpath, figpath, folderpath, data):
        #creates a frame to show previous plot and allow user to plot with new variables
        tk.Frame.__init__(self, root)
        self.folder_path = folderpath
        self.plotpath = plotpath

        ###################################
        #plot selection section

        #read in csv of previous plot selections
        self.variable_data = self.read_csv(plotpath)

        #create canvas
        self.canvas = tk.Canvas(self, borderwidth=0, height=self.winfo_height()*530, width=500)

        #scrollbar for canvas
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        #bind canvas to scrollbar
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        #create entry table
        for i, variable_row in enumerate(self.variable_data):
            #variable name is the label
            variable_name = variable_row[0]
            tk.Label(self.scrollable_frame, text=variable_name).grid(row=i + 1, column=0)

            #entry options for plot, scale, and color
            plotted_entry = tk.Entry(self.scrollable_frame)
            plotted_entry.insert(0, variable_row[1])
            plotted_entry.grid(row=i + 1, column=1)

            scale_entry = tk.Entry(self.scrollable_frame)
            scale_entry.insert(0, variable_row[2])
            scale_entry.grid(row=i + 1, column=2)

            color_entry = tk.Entry(self.scrollable_frame)
            color_entry.insert(0, variable_row[3])
            color_entry.grid(row=i + 1, column=3)

            self.variable_data[i] = [variable_name, plotted_entry, scale_entry, color_entry]

        #okay button for when user wants to update plot
        ok_button = tk.Button(self.scrollable_frame, text="OK", command=self.save)
        ok_button.grid(row=len(self.variable_data) + 1, column=4, pady=10)

        # Set the height of the scrollable frame
        self.scrollable_frame.config(height=self.winfo_height() * 32)
        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Display image
        image1 = Image.open(figpath)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=1, column=2, padx=10, pady=5, columnspan=3)

    def read_csv(self, filepath):
        variable_data = []
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                variable_data.append(row)
        return variable_data

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def save(self):
        self.updated_variable_data = []
        for i, row in enumerate(self.variable_data):
            #get entered values
            plotted_value = self.variable_data[i][1].get()
            scale_value = self.variable_data[i][2].get()
            color_value = self.variable_data[i][3].get()

            self.updated_variable_data.append([row[0], plotted_value, scale_value, color_value])

        with open(self.plotpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in self.updated_variable_data:
                writer.writerow(row)

        #Rerun the plotter
        # Split the file name by '_' and '.csv'
        parts = self.plotpath.split('_')

        # Get the second last part (before '.csv') which should be the phase
        phase = parts[-1]
        parts = phase.split('.')
        phase = parts[0]

        self.fuel_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.fuelmetric_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.exact_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.scale_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.nano_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.teom_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.senserion_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.ops_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.pico_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_NA.csv")
        self.log_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_log.txt")

        self.input_path = os.path.join(self.folder_path, f"{os.path.basename(self.folder_path)}_TimeSeriesMetrics_"
                                       + phase + ".csv")
        self.plots_path = os.path.join(self.folder_path,
                                       f"{os.path.basename(self.folder_path)}_plots_"
                                       + phase + ".csv")
        self.fig_path = os.path.join(self.folder_path,
                                     f"{os.path.basename(self.folder_path)}_plot_"
                                     + phase + ".png")
        try:
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                PEMS_Plotter(self.input_path, self.fuel_path, self.fuelmetric_path, self.exact_path,
                             self.scale_path,
                             self.nano_path, self.teom_path, self.senserion_path, self.ops_path, self.pico_path,
                             self.plots_path,
                             self.fig_path, self.log_path)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames,
                                opsnames,
                                pnames, self.plots_path, self.fig_path)
        except PermissionError:
            message = f"File: {self.plots_path} is open in another program, close and try again."
            messagebox.showerror("Error", message)
        except ValueError as e:
            print(e)
            if 'could not convert' in str(e):
                message = f'The scale input requires a valid number. Letters and blanks are not valid numbers. Please correct the issue and try again.'
                messagebox.showerror("Error", message)
            if 'invalid literal' in str(e):
                message = f'The plotted input requires a valid input of an integer either 0 to not plot or any integer to plot. Please correct the issue and try again.'
                messagebox.showerror("Error", message)
            if 'valid value for color' in str(e):
                message = f'One of the colors is invalid. A valid list of colors can be found at: '
                error_win = tk.Toplevel(root)
                error_win.title("Error")
                error_win.geometry("400x100")

                error_label = tk.Label(error_win, text=message)
                error_label.pack(pady=10)

                hyperlink = tk.Button(error_win, text="https://matplotlib.org/stable/gallery/color/named_colors.html",
                                      command=open_website)
                hyperlink.pack()

        # Display image
        image1 = Image.open(self.fig_path)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=1, column=2, padx=10, pady=5, columnspan=3)

def open_website():
    webbrowser.open_new("https://matplotlib.org/stable/gallery/color/named_colors.html")

class All_Outputs(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        #output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<120}|".format("ALL OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<10} | {:<17} |".format(key, unit, val)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")
        self.text_widget.config(height=self.winfo_height()*33)
        self.text_widget.configure(state="disabled")

        # short table
        self.cut_table = tk.Text(self, wrap="none", height=1, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=3, column=4, padx=0, pady=0, columnspan=3)
        cut_header = "{:<113}|".format("WEIGHTED METRICS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = round(float(value.n))
            except:
                try:
                    val = round(float(value))
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
                          'cooking_power', 'burn_rate', 'phase_time', 'CO_useful_eng_deliver', 'PM_useful_eng_deliver',
                          'PM_mass_time', 'PM_heat_mass_time', 'CO_mass_time']
        for key, value in data.items():
            if any(key.startswith(param) for param in cut_parameters):
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 70 + "\n")
        self.cut_table.config(height=self.winfo_height()*33)
        self.cut_table.configure(state="disabled")

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

class Emission_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<124}|".format("EMISSION OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")
        header = "{:<54} | {:<31} | {:<38} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")

        rownum = 0
        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value
                if not val:
                    val = " "
                row = "{:<30} | {:<17} | {:<20} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 75 + "\n")

        self.text_widget.config(height=self.winfo_height() * 32)
        self.text_widget.configure(state="disabled")

        # short table
        self.cut_table = tk.Text(self, wrap="none", height=1, width=72)
        # Configure a tag for bold text
        self.cut_table.tag_configure("bold", font=("Helvetica", 12, "bold"))
        self.cut_table.grid(row=2, column=4, padx=0, pady=0, columnspan=3)
        cut_header = "{:<113}|".format("WEIGHTED METRICS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = round(float(value.n))
            except:
                try:
                    val = round(float(value))
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

        cut_header = "{:<115}|".format("IMPORTANT VARIABLES")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 68 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 68 + "\n", "bold")
        cut_parameters = ['CO_useful_eng_deliver', 'PM_useful_eng_deliver',
                          'PM_mass_time', 'PM_heat_mass_time', 'CO_mass_time']
        for key, value in data.items():
            if any(key.startswith(param) for param in cut_parameters):
                unit = units.get(key, "")
                try:
                    val = round(float(value.n), 3)
                except:
                    try:
                        val = round(float(value), 3)
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<17} | {:<10} |".format(key, val, unit)
                self.cut_table.insert(tk.END, row + "\n")
                self.cut_table.insert(tk.END, "_" * 75 + "\n")
        self.cut_table.config(height=self.winfo_height() * 32)
        self.cut_table.configure(state="disabled")

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

class Grav_Calcs(tk.Frame):
    def __init__(self, root, logs, gravval, outval, gravunits, outunits):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<122}|".format("GRAV INPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<44} | {:<31} | {:<38} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        rownum = 0
        for key, value in gravval.items():
            if 'variable' not in key:
                unit = gravunits.get(key, "")
                try:
                    val = value.n
                except:
                    val = value
                if not val:
                    val = " "
                row = "{:<25} | {:<17} | {:<20} |".format(key, val, unit)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")
                rownum += 2

        self.text_widget.config(height=self.winfo_height() * 32)
        self.text_widget.configure(state="disabled")

        # output table
        self.out_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.out_widget.grid(row=2, column=4, columnspan=3, padx=0, pady=0)

        self.out_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<118}|".format("GRAV OUTPUTS")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<44} | {:<31} | {:<38} |".format("Variable", "Value", "Units")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in outval.items():
            if 'variable' not in key:
                unit = outunits.get(key, "")
                try:
                    val = round(value.n, 3)
                except:
                    try:
                        val = round(value, 3)
                    except:
                        try:
                            val = value.n
                        except:
                            val = value
                if not val:
                    val = " "
                row = "{:<25} | {:<17} | {:<20} |".format(key, val, unit)
                self.out_widget.insert(tk.END, row + "\n")
                self.out_widget.insert(tk.END, "_" * 70 + "\n")

        self.out_widget.config(height=self.winfo_height() * 32)
        self.out_widget.configure(state="disabled")

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
            self.out_widget.tag_remove("highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.out_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.out_widget.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos

            self.out_widget.tag_configure("highlight", background="yellow")

class Subtract_Bkg(tk.Frame):
    def __init__(self, root, logs, fig1, fig2, methods, phases, data):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=3, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=65)
        self.logs_text.grid(row=3, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=3, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Collapsible 'Phases' section for logs
        self.phase_section = CollapsibleFrame(self, text="Phase Times", collapsed=True)
        self.phase_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for phases and add a vertical scrollbar
        self.phase_text = tk.Text(self.phase_section.content_frame, wrap="word", height=10, width=65)
        self.phase_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        phase_scrollbar = tk.Scrollbar(self.phase_section.content_frame, command=self.phase_text.yview)
        phase_scrollbar.grid(row=1, column=3, sticky="ns")

        self.phase_text.config(yscrollcommand=phase_scrollbar.set)

        for key, value in phases.items():
            if 'variable' not in key:
                self.phase_text.insert(tk.END, key + ': ' + value + "\n")

        self.phase_text.configure(state="disabled")

        # Collapsible 'Method' section for logs
        self.method_section = CollapsibleFrame(self, text="Subtraction Methods", collapsed=True)
        self.method_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for phases and add a vertical scrollbar
        self.method_text = tk.Text(self.method_section.content_frame, wrap="word", height=10, width=65)
        self.method_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        method_scrollbar = tk.Scrollbar(self.method_section.content_frame, command=self.method_text.yview)
        method_scrollbar.grid(row=2, column=3, sticky="ns")

        self.method_text.config(yscrollcommand=method_scrollbar.set)

        for key, value in methods.items():
            if 'chan' not in key:
                self.method_text.insert(tk.END, key + ': ' + value + "\n")

        self.method_text.configure(state="disabled")

        # Display images below the Advanced section
        image1 = Image.open(fig1)
        image1 = image1.resize((575, 450), Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=4, column=0, padx=10, pady=5, columnspan=3)

        image2 = Image.open(fig2)
        image2 = image2.resize((550, 450), Image.LANCZOS)
        photo2 = ImageTk.PhotoImage(image2)
        label2 = tk.Label(self, image=photo2, width=575)
        label2.image = photo2  # to prevent garbage collection
        label2.grid(row=4, column=4, padx=10, pady=5, columnspan=3)

        #Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text="Warnings", collapsed=False) #start open
        self.warning_section.grid(row=0, column=0, pady=0, padx=0, sticky='w')

        self.warning_frame = tk.Text(self.warning_section.content_frame, wrap="word", width=70, height=10)
        self.warning_frame.grid(row=0, column=0, columnspan=6)

        warn_scrollbar = tk.Scrollbar(self.warning_section.content_frame, command=self.warning_frame.yview)
        warn_scrollbar.grid(row=0, column=6, sticky='ns')
        self.warning_frame.config(yscrollcommand=warn_scrollbar.set)

        self.warning_frame.tag_configure("red", foreground="red")

        emissions = ['CO', 'CO2', 'CO2v', 'PM']
        num_lines = 0
        for key, value in data.items():
            if key.endswith('prebkg') and 'temp' not in key:
                try:
                    value = value.n
                except:
                    pass
                try:
                    for em in emissions:
                        if em in key:
                            if value < -10.0:
                                self.warning_frame.insert(tk.END, "WARNING:\n")
                                warning_message = f"{em} for the pre background period is negative. The value should be close to 0.\n" \
                                                  f"If this period is being used for background subtraction, this may cause errors.\n" \
                                                  f"Zoom in on period in the graph to ensure period looks correct\n" \
                                                  f"Ensure the subtraction period is flat\n" \
                                                  f"Ensure the sensors were given time to flatline.\n" \
                                                  f"If this background period is not suitable, do not use it for subtraction\n"
                                self.warning_frame.insert(tk.END, warning_message, "red")
                                num_lines = warning_message.count('\n') + 1
                                self.warning_frame.config(height=num_lines)
                except:
                    pass

            if key.endswith('postbkg') and 'temp' not in key:
                try:
                    value = value.n
                except:
                    pass
                try:
                    for em in emissions:
                        if em in key:
                            if value < -10.0:
                                self.warning_frame.insert(tk.END, "WARNING:\n")
                                warning_message = f"{em} for the post background period is negative. The value should be close too 0.\n" \
                                                  f"If this period is being used for background subtraction, this may cause errors.\n" \
                                                  f"Zoom in on period in the graph to ensure period looks correct\n" \
                                                  f"Ensure the subtraction period is flat\n" \
                                                  f"Ensure the sensors were given time to flatline.\n" \
                                                  f"If this background period is not suitable, do not use it for subtraction\n"
                                self.warning_frame.insert(tk.END, warning_message, "red")
                                try:
                                    num_lines = num_lines + warning_message.count('\n') + 1
                                except:
                                    num_lines = warning_message.count('\n') + 1
                                self.warning_frame.config(height=num_lines)
                except:
                    pass

            if key.endswith('prebkg') and 'temp' not in key:
                try:
                    value = value.n
                except:
                    pass
                try:
                    for em in emissions:
                        if em in key:
                            if value > 10.0:
                                self.warning_frame.insert(tk.END, "WARNING:\n")
                                warning_message = f"{em} for the pre background period is more than 1. The value should be close to 0.\n" \
                                                  f"If this period is being used for background subtraction, this may cause errors.\n" \
                                                  f"Zoom in on period in the graph to ensure period looks correct\n" \
                                                  f"Ensure the subtraction period is flat\n" \
                                                  f"Ensure the sensors were given time to flatline.\n" \
                                                  f"If this background period is not suitable, do not use it for subtraction\n"
                                self.warning_frame.insert(tk.END, warning_message, "red")
                                try:
                                    num_lines = num_lines + warning_message.count('\n') + 1
                                except:
                                    num_lines = warning_message.count('\n') + 1
                                self.warning_frame.config(height=num_lines)
                except:
                    pass

            if key.endswith('postbkg') and 'temp' not in key:
                try:
                    value = value.n
                except:
                    pass
                try:
                    for em in emissions:
                        if em in key:
                            if value > 10.0:
                                self.warning_frame.insert(tk.END, "WARNING:\n")
                                warning_message = f"{em} for the post background period is more than 1. The value should be close too 0.\n" \
                                                  f"If this period is being used for background subtraction, this may cause errors.\n" \
                                                  f"Zoom in on period in the graph to ensure period looks correct\n" \
                                                  f"Ensure the subtraction period is flat\n" \
                                                  f"Ensure the sensors were given time to flatline.\n" \
                                                  f"If this background period is not suitable, do not use it for subtraction\n"
                                self.warning_frame.insert(tk.END, warning_message, "red")
                                try:
                                    num_lines = num_lines + warning_message.count('\n') + 1
                                except:
                                    num_lines = warning_message.count('\n') + 1
                                self.warning_frame.config(height=num_lines)
                except:
                    pass

        # After inserting all the warnings, check if num_lines is greater than 0
        if num_lines == 0:
            # If there are no warnings, delete the warning frame
            self.warning_frame.grid_remove()
            self.warning_section.grid_remove()
        else:
            self.warning_frame.config(height=8)

        self.warning_frame.configure(state="disabled")

class Adjust_Frame(tk.Frame):
    def __init__(self, root, logs, firmware):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        #Firmware version
        firm_message = tk.Text(self, wrap="word", height=1, width=80)
        firm_message.grid(row=0, column=0, columnspan=3)
        firm_message.insert(tk.END, f"Firmware Version Used: {firmware}")
        firm_message.configure(state="disabled")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=1, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=75)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

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
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=1, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=1, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        #Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text="Warnings", collapsed=False) #start open
        self.warning_section.grid(row=2, column=0, pady=0, padx=0, sticky='w')

        self.warning_frame = tk.Text(self.warning_section.content_frame, wrap="word", width=70, height=10)
        self.warning_frame.grid(row=2, column=0, columnspan=6)

        warn_scrollbar = tk.Scrollbar(self.warning_section.content_frame, command=self.warning_frame.yview)
        warn_scrollbar.grid(row=2, column=6, sticky='ns')
        self.warning_frame.config(yscrollcommand=warn_scrollbar.set)

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

        self.warning_frame.tag_configure("red", foreground="red")
        self.warning_frame.tag_configure("orange", foreground="orange")
        tot_rows = 1
        for key, value in data.items():
            if key.startswith('variable') or key.endswith("comments"):
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
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is higher than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_add("orange", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 100. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is lower than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message,tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_w_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_3 = f"      Check that the char_mass (charcoal created) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            ########################################################################3
            #TE wo char
            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 55 and float(val) < 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is higher than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) > 100:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 100. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too low.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a large difference (more than 1000g (1L)).\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too high.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="yellow")
                        #self.warning_frame.tag_add("yellow", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 10 and float(val) > 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is lower than typical. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            if key.startswith('eff_wo_char'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the fuel_mass (fuel consumed) is a realistic weight and not too high.\n"
                        warning_message_4 = f"      Check that final_water_mass - initial_water_mass don't result in a small difference.\n"
                        warning_message_5 = f"      Check that max_water_temp - initial_water_temp is not too low.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")

                except:
                    pass
            ##########################################################################################
            #Char productivity
            if key.startswith('char_energy_productivity') or key.startswith('char_mass_productivity'):
                try:
                    if val and float(val) < 0:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("fault highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("fault highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("fault highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("fault highlight", background="red")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is negative. This is incorrect results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_2 = f"      Check that the char_mass (char created) is not negative.\n"
                        warning_message_4 = f"      Check that the gross calorific value for charcoal is correct.\n"
                        warning_message_5 = f"      Check that no fuels that are not char were entered with a carbon fraction above 0.75.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_4 + warning_message_5

                        tag = "red"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #############################################################
            #char mass
            if key.startswith('char_mass_hp') or key.startswith('char_mass_mp') or key.startswith('char_mass_lp'):
                try:
                    if val and float(val) > 0.050:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is a large mass. This does not mean it is incorrect but results should be checked.\n" \
                                            f"  This may be an entry issue. Please check the values of the following:\n"
                        warning_message_5 = f"      Check that no fuels that are not char were entered with a carbon fraction above 0.75.\n"
                        warning_message = warning_message_1 + warning_message_5

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
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
                        self.text_widget.tag_add("warn highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("warn highlight", background="orange")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("warn highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("warn highlight", background="orange")

                        self.warning_frame.insert(tk.END, 'WARNING:\n')
                        warning_message_1 = f"  {key} is more than 10 degrees from ambient temp.\n"
                        warning_message = warning_message_1

                        tag = "orange"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            #######################################################33
            #ISO checks
            if key.startswith('phase_time'):
                try:
                    if val and float(val) < 30:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("fault highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("fault highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("fault highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("fault highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO FAULT:\n')
                        warning_message_1 = f"  {key} is less than 30 minutes. ISO tests REQUIRE 30 minute phase periods.\n"
                        warning_message_2 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2

                        tag = "red"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass
            if key.startswith('phase_time'):
                try:
                    if val and float(val) > 35:
                        start_pos = self.text_widget.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.text_widget.tag_add("fault highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("fault highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("fault highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("fault highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO FAULT:\n')
                        warning_message_1 = f"  {key} is more than 35. ISO tests REQUIRE a maximum of 35 minute phase periods (including shutdown).\n"
                        warning_message_2 = f"      Test phases may be 60 minutes long if a single phase is being run.\n"
                        warning_message_3 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        tag = "red"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
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
                        self.text_widget.tag_add("fault highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("fault highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("fault highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("fault highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO FAULT:\n')
                        warning_message_1 = f"  max_water_temp_pot1' {phase} - {key} is not 5 degrees. " \
                                            f"\n    ISO tests REQUIRE a shutdown period of 5 minutes or when the max water temperture drops to 5 degrees below boiling temperature..\n"
                        warning_message_2 = f"      This warning may be ignored if the 5minute shutdown procedure was performed.\n"
                        warning_message_3 = f"      This warning may be ignored if an ISO test is not being run.\n"
                        warning_message = warning_message_1 + warning_message_2 + warning_message_3

                        tag = "red"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
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
                        self.text_widget.tag_add("fault highlight", start_pos, end_pos)
                        self.text_widget.tag_configure("fault highlight", background="red")

                        start_pos = self.cut_table.search(row, "1.0", tk.END)
                        end_pos = f"{start_pos}+{len(row)}c"
                        self.cut_table.tag_add("fault highlight", start_pos, end_pos)
                        self.cut_table.tag_configure("fault highlight", background="red")

                        self.warning_frame.insert(tk.END, 'ISO FAULT:\n')
                        warning_message_1 = f"  {key} not between high power and low power. ISO tests REQUIRE medium power firepower to be between high and low power.\n"
                        warning_message = warning_message_1

                        tag = "red"
                        self.warning_frame.insert(tk.END, warning_message, tag)
                        try:
                            num_lines = num_lines + warning_message.count('\n') + 1
                        except:
                            num_lines = warning_message.count('\n') + 1
                        self.warning_frame.config(height=num_lines)
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
                except:
                    pass

            tot_rows += 2

        self.text_widget.config(height=self.winfo_height()*(30))
        self.cut_table.config(height=self.winfo_height()*(30))
        self.warning_frame.config(height=8)

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
            self.text_widget.tag_remove("search highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("search highlight", start_pos, end_pos)
                start_pos = end_pos

            self.text_widget.tag_configure("search highlight", background="yellow")

        if search_text:
            self.cut_table.tag_remove("search highlight", "1.0", tk.END)
            start_pos = "1.0"
            while True:
                start_pos = self.cut_table.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.cut_table.tag_add("search highlight", start_pos, end_pos)
                start_pos = end_pos

            self.cut_table.tag_configure("search highlight", background="yellow")

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

class CommentsFrame(tk.LabelFrame): #Test info entry area
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.comments = ['general_comments', 'high_power_comments', 'medium_power_comments', 'low_power_comments']
        self.entered_comments = {}
        for i, name in enumerate(self.comments):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_comments[name] = tk.Text(self, height=6, width=25, wrap="word")
            self.entered_comments[name].grid(row=i, column=2)

    def check_input_validity(self, float_errors: list, blank_errors: list):
        return [], []

    def check_imported_data(self, data: dict):
        for field in self.comments:
            if field in data:
                self.entered_comments[field].delete("1.0", tk.END)  # Clear existing content
                self.entered_comments[field].insert(tk.END, data.pop(field, ""))

        return data
    def get_data(self):
        return self.entered_comments

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

class GasCalibrationFrame(tk.LabelFrame):
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.gas_cal = ["Span_Gas_Actual_CO_Concentration",
                        "Span_Gas_Actual_CO2_Concentration", "Span_Gas_Measured_CO_Concentration_Bias",
                        "Span_Gas_Measured_CO2_Concentration_Bias", "Span_Gas_Measured_CO_Concentration_Drift",
                        "Span_Gas_Measured_CO2_Concentration_Drift", "Span_Gas_Start_Time_Bias",
                        "Span_Gas_End_Time_Bias", "Span_Gas_Start_Time_Drift",
                        "Span_Gas_End_Time_Drift", "Zero_Gas_Actual_CO_Concentration",
                        "Zero_Gas_Actual_CO2_Concentration", "Zero_Gas_Measured_CO_Concentration_Bias",
                        "Zero_Gas_Measured_CO2_Concentration_Bias", "Zero_Gas_Measured_CO_Concentration_Drift",
                        "Zero_Gas_Measured_CO2_Concentration_Drift", "Zero_Gas_Start_Time_Bias",
                        "Zero_Gas_End_Time_Bias", "Zero_Gas_Start_Time_Drift", "Zero_Gas_End_Time_Drift"]
        self.gas_cal_units = ['ppm', 'ppm', 'ppm', 'ppm', 'ppm', 'ppm', 'hh:mm:ss', 'hh:mm:ss', 'hh:mm:ss', 'hh:mm:ss',
                              'ppm', 'ppm', 'ppm', 'ppm', 'ppm', 'ppm', 'hh:mm:ss', 'hh:mm:ss', 'hh:mm:ss', 'hh:mm:ss']
        self.entered_gas_cal = {}
        self.entered_gas_cal_units = {}
        gas_row = 0
        for i, name in enumerate(self.gas_cal):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=gas_row, column=0)
            self.entered_gas_cal[name] = tk.Entry(self)
            if name == "Span_Gas_Actual_CO_Concentration":
                self.entered_gas_cal[name].insert(0, '500')
            elif name == "Span_Gas_Actual_CO2_Concentration":
                self.entered_gas_cal[name].insert(0, '8000')
            elif name == "Zero_Gas_Actual_CO2_Concentration":
                self.entered_gas_cal[name].insert(0, '0')
            elif name == "Zero_Gas_Actual_CO_Concentration":
                self.entered_gas_cal[name].insert(0, '0')
            self.entered_gas_cal[name].grid(row=gas_row, column=2)
            self.entered_gas_cal_units[name] = tk.Entry(self)
            self.entered_gas_cal_units[name].insert(0, self.gas_cal_units[i])
            self.entered_gas_cal_units[name].grid(row=gas_row, column=3)

            # Add a blank row after the desired entries
            if name in ["Span_Gas_Actual_CO2_Concentration", "Span_Gas_Measured_CO2_Concentration_Drift",
                        "Span_Gas_End_Time_Drift", "Zero_Gas_Actual_CO2_Concentration", "Zero_Gas_Measured_CO2_Concentration_Drift"]:
                tk.Label(self, text="").grid(row=gas_row + 1, column=0, columnspan=4)
                gas_row += 1
            gas_row += 1

        tk.Label(self, text="").grid(row=gas_row, column=0, columnspan=4)
        gas_row += 1

        self.gas_pass = ["Span_Bias_CO", "Span_Gas_Bias_Check_CO", "Span_Drift_CO",
                         "Span_Gas_Drift_Check_CO", "Zero_Bias_CO", "Zero_Gas_Bias_Check_CO",
                         "Zero_Drift_CO", "Zero_Gas_Drift_Check_CO", "Span_Bias_CO2", "Span_Gas_Bias_Check_CO2",
                         "Span_Drift_CO2", "Span_Gas_Drift_Check_CO2", "Zero_Bias_CO2",
                         "Zero_Gas_Bias_Check_CO2", "Zero_Drift_CO2", "Zero_Gas_Drift_Check_CO2"]
        self.gas_pass_units = ['%', '', '%', '', '%', '', '%', '', '%', '', '%', '', '%', '', '%', '']
        self.gas_pass_labels = {}
        for i, name in enumerate(self.gas_pass):
            self.entered_gas_cal[name] = ""
            self.entered_gas_cal_units[name] = self.gas_pass_units[i]
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i + gas_row, column=0)
            self.gas_pass_labels[name] = tk.Label(self, text="   NULL")
            self.gas_pass_labels[name].grid(row=i + gas_row, column=1, columnspan=2)
            tk.Label(self, text=self.gas_pass_units[i]).grid(row=i+gas_row, column=3)

    def check_imported_data(self, data: dict):
        for field in self.gas_cal:
            if field in data:
                self.entered_gas_cal[field].delete(0, tk.END)  # Clear existing content
                self.entered_gas_cal[field].insert(0, data.pop(field, ""))

        for field in self.gas_pass:
            if field in data:
                self.entered_gas_cal[field] = data[field]
                data.pop(field," ")

        return data

    def get_data(self):
        return self.entered_gas_cal

    def get_units(self):
        return self.entered_gas_cal_units

    def update_gas_rate(self, name, value):
        if name in self.gas_pass_labels:
            self.gas_pass_labels[name].config(text=value)

    def update_gas_check(self, name, value, color):
        if name in self.gas_pass_labels:
            self.gas_pass_labels[name].config(text=value, bg=color)

class LeakCheckFrame(tk.LabelFrame):
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.leak_names = ["Atmospheric_Pressure", "Gravametric_Internal_Volume", "Gravametric_Nominal_flowrate",
                           "Gravametric_Initial_Pressure", "Gravametric_Final_Pressure", "Gravametric_Test_Time",
                           "Sample_Line_Internal_Volume", "Gas_Sensor_Flow_Rate", "Gas_Sensor_Initial_Pressure", "Gas_Sensor_Final_Pressure", "Gas_Sensor_Test_Time",
                           "Negative_Pressure_Sensor_Initial_Pressure", "Negative_Pressure_Sensor_Final_Pressure",
                           "Negative_Pressure_Sensor_Test_Time", "Positive_Pressure_Sensor_Initial_Pressure",
                           "Positive_Pressure_Sensor_Final_Pressure", "Positive_Pressure_Sensor_Test_Time"]
        self.leak_units = ['in Hg', 'L', 'LPM', 'in H2O', 'in H20', 'min', 'ml', 'LPM', 'in H20', 'in H2O', 'min', 'in H2O', 'in H2O', 'min', 'in H2O', 'in H20', 'min', ]
        self.entered_leak_check = {}
        self.entered_leak_units = {}
        leak_row = 0
        for i, name in enumerate(self.leak_names):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=leak_row, column=0)
            self.entered_leak_check[name] = tk.Entry(self)
            if name == "Gravametric_Internal_Volume":
                self.entered_leak_check[name].insert(0, '0.4')
            elif name == "Gravametric_Nominal_flowrate":
                self.entered_leak_check[name].insert(0, '16.7')
            elif name == "Sample_Line_Internal_Volume":
                self.entered_leak_check[name].insert(0, "250")
            elif name == "Gas_Sensor_Flow_Rate":
                self.entered_leak_check[name].insert(0, "4.5")
            self.entered_leak_check[name].grid(row=leak_row, column=2)
            self.entered_leak_units[name] = tk.Entry(self)
            self.entered_leak_units[name].insert(0, self.leak_units[i])
            self.entered_leak_units[name].grid(row=leak_row, column=3)

            # Add a blank row after the desired entries
            if name in ["Atmospheric_Pressure", "Gravametric_Test_Time", "Gas_Sensor_Test_Time", "Negative_Pressure_Sensor_Test_Time"]:
                tk.Label(self, text="").grid(row=leak_row + 1, column=0, columnspan=4)
                leak_row += 1
            leak_row += 1

        tk.Label(self, text="").grid(row=leak_row, column=0, columnspan=4)
        leak_row += 1

        self.leak_pass = ["Gravametric_Leak_Rate", "Gravametric_Leak_Check", "Gas_Sensor_Leak_Rate",
                          "Gas_Sensor_Leak_Check", "Negative_Pressure_Sensor_Leak_Rate",
                          "Negative_Pressure_Sensor_Leak_Check", "Positive_Pressure_Sensor_Leak_Rate",
                          "Positive_Pressure_Sensor_Leak_Check"]
        self.leak_pass_units = ['l/min', '', 'l/min', '', '%', '', '%', '']
        self.leak_pass_labels = {}
        for i, name in enumerate(self.leak_pass):
            self.entered_leak_check[name] = ''
            self.entered_leak_units[name] = self.leak_pass_units[i]
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i + leak_row, column=0)
            self.leak_pass_labels[name] = tk.Label(self, text="   NULL")
            self.leak_pass_labels[name].grid(row=i + leak_row, column=1, columnspan=2)
            tk.Label(self, text=self.leak_pass_units[i]).grid(row=i+leak_row, column=3)

    def check_imported_data(self, data: dict):
        for field in self.leak_names:
            if field in data:
                self.entered_leak_check[field].delete(0, tk.END)  # Clear existing content
                self.entered_leak_check[field].insert(0, data.pop(field, ""))

        for field in self.leak_pass:
            if field in data:
                self.entered_leak_check[field] = data[field]

                if 'Rate' in field:
                    self.update_leak_rate(field, data[field])
                else:
                    if 'PASS' in data[field]:
                        self.update_leak_check(field, data[field], 'green')
                    else:
                        self.update_leak_check(field, data[field], 'red')

                data.pop(field, " ")

        return data
    def update_leak_rate(self, name, value):
        if name in self.leak_pass_labels:
            self.leak_pass_labels[name].config(text=value)

    def update_leak_check(self, name, value, color):
        if name in self.leak_pass_labels:
            self.leak_pass_labels[name].config(text=value, bg=color)

    def get_data(self):
        return self.entered_leak_check

    def get_units(self):
        return self.entered_leak_units

if __name__ == "__main__":
    root = tk.Tk()
    version = '1.0'
    root.title("App L1. Version: " + version)
    try:
        root.iconbitmap("ARC-Logo.ico")
    except:
        try:
            root.iconbitmap("C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\LEMS\\ARC-Logo.ico")
        except:
            pass
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataInput(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()
