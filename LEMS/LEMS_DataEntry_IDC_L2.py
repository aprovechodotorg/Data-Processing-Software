#    Copyright (C) 2022 Aprovecho Research Center
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Contact: sam@aprovecho.org

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from PEMS_SubtractBkg import PEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs_IDC import LEMS_EmissionCalcs_IDC
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
from LEMS_Scale import LEMS_Scale
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_TEOM import LEMS_TEOM
from LEMS_Sensirion import LEMS_Senserion
from LEMS_OPS import LEMS_OPS
from LEMS_Pico import LEMS_Pico
from LEMS_Realtime import LEMS_Realtime
from PEMS_L2 import PEMS_L2
from PIL import ImageTk as IT
from PIL import Image as I
import traceback
import csv
import subprocess
import logging
from datetime import datetime

def setup_logger(log_file):
    #Fuction purpose: define a logger that will log module runtime, important outputs, debug information, important outputs
    #Input: file path for where log file (txt format) is saved (within folder where data is being processed)
    #Output: Logger that can be called within other functions, logged git branch
    logger = logging.getLogger("LEMSL2Logger")
    logger.setLevel(logging.DEBUG)

    #create a file handler that logs the specified file path or append to file if it already exists
    file_mode = 'a' if os.path.exists(log_file) else 'w'
    file_handler = logging.FileHandler(log_file, mode=file_mode)
    file_handler.setLevel(logging.DEBUG)

    #Define the format for log messages
    formatter = logging.Formatter('%(asctime)s -%(levelname)s -%(message)s - Function: %(funcName)s')
    file_handler.setFormatter(formatter)

    #Add the file handler to the logger
    logger.addHandler(file_handler)

    #try and find git branch name
    try:
        branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    except subprocess.CalledProcessError:
        branch_name = "Unknown Branch"

    #log branch name
    start_time = datetime.now()
    logger.info(f"Log Started at: {start_time}")
    logger.info(f"Git Branch: {branch_name}")

    #try and get script version
    try:
        version = subprocess.check_output(["git", "log", "-n", "1", "--pretty=format:%h", "--", __file__], text=True).strip()
    except subprocess.CalledProcessError:
        version = "unknown version"

    #log version
    logger.info(f"Version: {version}")

    return logger
class LEMSDataCruncher_L2(tk.Frame):
    def __init__(self, root): #Set window
        tk.Frame.__init__(self, root)

        self.notebook = ScrollableNotebook(root, wheelscroll=True, tabmenu=True)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create a new frame
        self.tab_frame = tk.Frame(self.notebook)
        self.notebook.add(self.tab_frame, text="Folder Selection")
        self.tab_frame.grid_rowconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.tab_frame, borderwidth=0, background="#ffffff")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.inner_frame = tk.Frame(self.canvas, background="#ffffff")
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        #vertical scrollbar
        self.vsb = tk.Scrollbar(self.tab_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(row=0, column=1, sticky="ns")

        # horizontal scrollbar
        self.hsb = tk.Scrollbar(self.tab_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Configure canvas to fill the tab_frame
        self.canvas.grid_rowconfigure(0, weight=1)
        self.canvas.grid_columnconfigure(0, weight=1)

        # Bind scrollbars
        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onFrameConfigure)

        instructions = f"Select a folder which contains test folders to analyze.\n" \
                       f"Test Folder must have Energy Inputs."
        self.instructions = tk.Text(self.inner_frame, wrap="word", height=2, width=90)
        self.instructions.insert(tk.END, instructions)
        self.instructions.grid(row=0, column=0, columnspan=2)
        self.instructions.config(state="disabled")

        # File Path Entry
        tk.Label(self.inner_frame, text="Select Folder:").grid(row=1, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.inner_frame, textvariable=self.folder_path_var, width=150)
        self.folder_path.grid(row=1, column=0, columnspan=2)

        # Initialize energy_files as an instance variable
        self.energy_files = []

        # create a button to browse folders on computer
        browse_button = tk.Button(self.inner_frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=1, column=2)

        # OK button
        ok_button = tk.Button(self.inner_frame, text="   Run for the first time   ", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=4, column=0, pady=10, padx=(270, 0))

        # noninteractive button
        nonint_button = tk.Button(self.inner_frame, text="   Run with previous inputs   ", command=self.on_nonint)
        nonint_button.anchor()
        nonint_button.grid(row=4, column=1, pady=10, padx=(0, 270))

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.grid(row=0, column=0)

    def onCanvasMouseWheel(self, event):
        # Adjust the view of the canvas based on the mouse wheel movement
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_nonint(self):  # When okay button is pressed
        self.inputmethod = '2'
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
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                if os.path.isfile(emission_path):
                    self.emission_list.append(emission_path)
            try:
                emission_list = []
                all_list = []
                log_path = self.folder_path + '//log.txt'
                output_path = self.folder_path + '//UnFormattedDataL2.csv'
                try:
                    data, units, edata, eunits, logs = PEMS_L2(all_list, self.input_list, emission_list, output_path,
                                                               log_path)
                except:
                    data, units, logs = PEMS_L2(all_list, self.input_list, emission_list, output_path,
                                                               log_path)
            except PermissionError:
                error.append(folder)

            if error:
                message = f"One or more EnergyOutput or UnFormattedDataL2 files are open in another program. Close them and try again."
                # Error
                messagebox.showerror("Error", message)
            else:
                #self.frame.destroy()
                # Create a notebook to hold tabs
                #self.main_frame = tk.Frame(self.canvas, background="#ffffff")
                #self.frame.bind("<Configure>", self.onFrameConfigure)
                #self.notebook = ScrollableNotebook(root, wheelscroll=True, tabmenu=True)
                #self.notebook = ttk.Notebook(self.main_frame, height=30000)
                #self.notebook.grid(row=0, column=0, sticky="nsew")

                # Delete all tabs after the menu tab, starting from the second tab
                to_forget = []
                for i in range(self.notebook.index("end")):
                    if self.notebook.tab(i, "text") == "Folder Selection":
                        pass
                    else:
                        to_forget.append(i)
                count = 0
                for i in to_forget:
                    i = i - count
                    self.notebook.forget(i)
                    count += 1

                # Create a new frame
                tab_frame = tk.Frame(self.notebook)
                #self.tab_frame.grid(row=1, column=0)
                #self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(tab_frame, text="Menu")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                self.data_stream_button = tk.Button(self.frame, text="Step 2: Load Additional Data Streams (Optional)",
                                                    command=self.on_data_stream)
                self.data_stream_button.grid(row=2, column=0, padx=(0, 30))

                blank = tk.Frame(self.frame, width=self.winfo_width() - 1040)
                blank.grid(row=0, column=2, rowspan=2)


                self.cali_button = tk.Button(self.frame, text="Step 3: Adjust Sensor Calibrations",
                                             command=self.on_cali)
                self.cali_button.grid(row=3, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text="Step 4: Subtract Background", command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))

                self.grav_button = tk.Button(self.frame, text="Step 5: Calculate Gravametric Data (optional)",
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.emission_button = tk.Button(self.frame, text="Step 6: Calculate Emissions", command=self.on_em)
                self.emission_button.grid(row=6, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text="Step 7: Cut data as a Custom Time Period (Optional)",
                                            command=self.on_cut)
                self.cut_button.grid(row=7, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text="View All Outputs", command=self.on_all)
                self.all_button.grid(row=8, column=0, padx=(0, 195))

                self.custom_button = tk.Button(self.frame, text="Create a Table of Selected Outputs", command=self.on_custom)
                self.custom_button.grid(row=9, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
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

                self.toggle = tk.Button(self.frame, text="      Click to enter new values       ", bg='lightblue', command=self.update_input)
                self.toggle.grid(row=0, column=0)

                # Recenter view to top-left
                self.canvas.yview_moveto(0)
                self.canvas.xview_moveto(0)

                self.on_energy()
                self.on_data_stream()
                self.on_cali()
                self.on_bkg()
                self.on_grav()
                self.on_em()
                self.on_all()

                # Bind the notebook's horizontal scroll to the canvas
                self.notebook.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def update_input(self):
        if self.inputmethod == '2':
            self.inputmethod = '1'
            self.toggle.config(text=" Click to run with current values ", bg='violet')
        elif self.inputmethod == '1':
            self.inputmethod = '2'
            self.toggle.config(text="      Click to enter new values       ", bg='lightblue')

    def on_okay(self):  # When okay button is pressed
        self.inputmethod = '1'
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
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                if os.path.isfile(emission_path):
                    self.emission_list.append(emission_path)
            try:
                emission_list = []
                all_list = []
                log_path = self.folder_path + '//log.txt'
                output_path = self.folder_path + '//UnFormattedDataL2.csv'
                try:
                    data, units, edata, eunits, logs = PEMS_L2(all_list, self.input_list, emission_list, output_path,
                                                               log_path)
                except:
                    data, units, logs = PEMS_L2(all_list, self.input_list, emission_list, output_path,
                                                               log_path)
            except PermissionError:
                error.append(folder)

            if error:
                message = f"One or more EnergyOutput or UnFormattedDataL2 files are open in another program. Close them and try again."
                # Error
                messagebox.showerror("Error", message)
            else:
                #self.frame.destroy()
                # Create a notebook to hold tabs
                #self.main_frame = tk.Frame(self.canvas, background="#ffffff")
                #self.frame.bind("<Configure>", self.onFrameConfigure)
                #self.notebook = ScrollableNotebook(root, wheelscroll=True, tabmenu=True)
                #self.notebook = ttk.Notebook(self.main_frame, height=30000)
                #self.notebook.grid(row=0, column=0, sticky="nsew")
                # Delete all tabs after the menu tab, starting from the second tab
                to_forget = []
                for i in range(self.notebook.index("end")):
                    if self.notebook.tab(i, "text") == "Folder Selection":
                        pass
                    else:
                        to_forget.append(i)
                count = 0
                for i in to_forget:
                    i = i - count
                    self.notebook.forget(i)
                    count += 1

                # Create a new frame
                tab_frame = tk.Frame(self.notebook)
                #self.tab_frame.grid(row=1, column=0)
                #self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(tab_frame, text="Menu")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                self.data_stream_button = tk.Button(self.frame, text="Step 2: Load Additional Data Streams (Optional)",
                                                    command=self.on_data_stream)
                self.data_stream_button.grid(row=2, column=0, padx=(0, 30))

                blank = tk.Frame(self.frame, width=self.winfo_width() - 1040)
                blank.grid(row=0, column=2, rowspan=2)


                self.cali_button = tk.Button(self.frame, text="Step 3: Adjust Sensor Calibrations",
                                             command=self.on_cali)
                self.cali_button.grid(row=3, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text="Step 4: Subtract Background", command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))

                self.grav_button = tk.Button(self.frame, text="Step 5: Calculate Gravametric Data (optional)",
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.emission_button = tk.Button(self.frame, text="Step 6: Calculate Emissions", command=self.on_em)
                self.emission_button.grid(row=6, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text="Step 7: Cut data as a Custom Time Period (Optional)",
                                            command=self.on_cut)
                self.cut_button.grid(row=7, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text="View All Outputs", command=self.on_all)
                self.all_button.grid(row=8, column=0, padx=(0, 195))

                self.custom_button = tk.Button(self.frame, text="Create a Table of Selected Outputs", command=self.on_custom)
                self.custom_button.grid(row=9, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
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

                self.toggle = tk.Button(self.frame, text=" Click to run with current values ", bg='violet', command=self.update_input)
                self.toggle.grid(row=0, column=0)

                # Recenter view to top-left
                self.canvas.yview_moveto(0)
                self.canvas.xview_moveto(0)


                # Bind the notebook's horizontal scroll to the canvas
                self.notebook.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def onCanvasConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_cut(self):
        for file in self.input_list:
            # Function to handle OK button click
            def ok():
                nonlocal selected_phases
                selected_phases = [phases[i] for i in listbox.curselection()] #record all selected phases
                popup.destroy() #destroy window

            # Function to handle Cancel button click
            def cancel():
                popup.destroy()

            #phases that can be cut
            phases = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']

            # Create a popup for selection
            popup = tk.Toplevel(self)
            popup.title("Select Phases")

            selected_phases = []

            #Instructions for popuo=p
            message = tk.Label(popup, text="Select phases to cut")
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

            self.energypath = file.replace('EnergyOutputs.csv', "EnergyOutputs.csv")
            self.gravpath = file.replace('EnergyOutputs.csv', 'GravOutputs.csv')
            self.phasepath = file.replace('EnergyOutputs.csv', 'PhaseTimes.csv')
            self.periodpath = file.replace('EnergyOutputs.csv', 'AveragingPeriod.csv')
            self.outputpath = file.replace('EnergyOutputs.csv', 'AveragingPeriodTimeSeries.csv')
            self.averageoutputpath = file.replace('EnergyOutputs.csv', 'AveragingPeriodAverages.csv')
            self.fuelpath = file.replace('EnergyOutputs.csv', 'null.csv') #No fuel or exact taken in
            self.exactpath = file.replace('EnergyOutputs.csv', 'null.csv')
            self.fuelmetricpath = file.replace('EnergyOutputs.csv', 'null.csv')
            self.scalepath = file.replace('EnergyOutputs.csv', 'FormattedScaleData.csv')
            self.nanopath = file.replace('EnergyOutputs.csv', 'FormattedNanoscanData.csv')
            self.TEOMpath = file.replace('EnergyOutputs.csv', 'FormattedTEOMData.csv')
            self.senserionpath = file.replace('EnergyOutputs.csv', 'FormattedSenserionData.csv')
            self.OPSpath = file.replace('EnergyOutputs.csv', 'FormattedOPSData.csv')
            self.Picopath = file.replace('EnergyOutputs.csv', 'FormattedPicoData.csv')
            self.log_path = file.replace('EnergyOutputs.csv', 'log.txt')
            self.savefig = file.replace('EnergyOutputs.csv', 'AveragingPeriod.png')

            for phase in selected_phases:
                self.inputpath = file.replace('EnergyOutputs.csv', 'TimeSeriesMetrics_' + phase + '.csv')
                self.periodpath = file.replace('EnergyOutputs.csv', 'AveragingPeriod_' + phase + '.csv')
                self.outputpath = file.replace('EnergyOutputs.csv', 'AveragingPeriodTimeSeries_' + phase + '.csv')
                self.averageoutputpath = file.replace('EnergyOutputs.csv', 'AveragingPeriodAverages_' + phase + '.csv')


                if os.path.isfile(self.inputpath):
                    try:
                        data, units, logs, times = LEMS_Realtime(self.inputpath, self.energypath, self.gravpath, self.phasepath, self.periodpath, self.outputpath, self.averageoutputpath,
                                      self.savefig, phase, self.log_path, self.inputmethod, self.fuelpath, self.fuelmetricpath, self.exactpath, self.scalepath,
                                      self.nanopath, self.TEOMpath, self.senserionpath, self.OPSpath, self.Picopath)

                        self.cut_button.config(bg='lightgreen')
                    except PermissionError:
                        message = f"File: {self.plots_path} is open in another program, close and try again."
                        messagebox.showerror("Error", message)
                        self.cut_button.config(bg='red')
                    except Exception as e:  # If error in called fuctions, return error but don't quit
                        line = 'Error: ' + str(e)
                        print(line)
                        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                        self.cut_button.config(bg='red')

                    # Check if the tab exists
                    tab_index = None
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == phase + " Cut Period":
                            tab_index = i
                    if tab_index is None:
                        # Create a new frame for each tab
                        self.tab_frame = tk.Frame(self.notebook, height=300000)
                        # self.tab_frame.grid(row=1, column=0)
                        self.tab_frame.pack(side="left")
                        # Add the tab to the notebook with the folder name as the tab label
                        self.notebook.add(self.tab_frame, text=phase + " Cut Period")

                        # Set up the frame as you did for the original frame
                        self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                        self.frame.grid(row=1, column=0)
                    else:
                        # Overwrite existing tab
                        # Destroy existing tab frame
                        self.notebook.forget(tab_index)
                        # Create a new frame for each tab
                        self.tab_frame = tk.Frame(self.notebook, height=300000)
                        # self.tab_frame.grid(row=1, column=0)
                        self.tab_frame.pack(side="left")
                        # Add the tab to the notebook with the folder name as the tab label
                        self.notebook.add(self.tab_frame, text=phase + " Cut Period")

                        # Set up the frame as you did for the original frame
                        self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                        self.frame.grid(row=1, column=0)

                    self.savefig = file.replace('EnergyOutputs.csv', 'AveragingPeriod_' + phase + '.png')

                    # create a frame to display the plot and plot options
                    cut_frame = Cut(self.frame, data, units, logs, self.savefig, times)
                    cut_frame.grid(row=3, column=0, padx=0, pady=0)

                else:
                    tk.messagebox.showinfo(title='Phase not Found', message='File: ' + self.inputpath + ' does not exist.'
                                                                                                             'Please check folder and try again')

    def on_data_stream(self):
        files_finished = []
        all_logs = []
        for file in self.input_list:
            self.input_path = file.replace('EnergyOutputs.csv', "ScaleRawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedScaleData.csv')
            self.log_path = file.replace('EnergyOutputs.csv', "log.txt")
            try:
                logs = LEMS_Scale(self.input_path, self.output_path, self.log_path)
                files_finished.append(self.input_path)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

            self.input_path = file.replace('EnergyOutputs.csv', "NanoscanRawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedNanoscanData.csv')
            try:
                LEMS_Nanoscan(self.input_path, self.output_path, self.log_path)
                files_finished.append(self.input_path)

                for line in logs:
                    all_logs.append(line)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

            self.text_input_path = file.replace('EnergyOutputs.csv', "TEOMRawData.txt")
            self.input_path = file.replace('EnergyOutputs.csv', "TEOMRawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedTEOMData.csv')
            try:
                logs = LEMS_TEOM(self.text_input_path, self.input_path, self.output_path, self.log_path)
                files_finished.append(self.input_path)

                for line in logs:
                    all_logs.append(line)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

            self.input_path = file.replace('EnergyOutputs.csv', "SenserionRawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedSenserionData.csv')
            try:
                logs = LEMS_Senserion(self.input_path, self.output_path, self.log_path)
                files_finished.append(self.input_path)

                for line in logs:
                    all_logs.append(line)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

            self.input_path = file.replace('EnergyOutputs.csv', "OPSRawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedOPSData.csv')
            try:
                logs = LEMS_OPS(self.input_path, self.output_path, self.log_path)
                files_finished.append(self.input_path)

                for line in logs:
                    all_logs.append(line)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

            self.input_path = file.replace('EnergyOutputs.csv', "PicoRawData.csv")
            self.LEMS_data = file.replace('EnergyOutputs.csv', "RawData.csv")
            self.output_path = file.replace('EnergyOutputs.csv', 'FormattedPicoData.csv')
            try:
                logs = LEMS_Pico(self.input_path, self.LEMS_data,self.output_path, self.log_path)
                files_finished.append(self.input_path)

                for line in logs:
                    all_logs.append(line)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                traceback.print_exception(type(e), e, e.__traceback__)

        if len(files_finished) == 0:
            self.data_stream_button.config(bg="red")
        else:
            self.data_stream_button.config(bg="lightgreen")
            line = "The following sensor paths were processed: \n"
            for name in files_finished:
                line = line + name + '\n\n'
            line = line + "If a sensor was not processed, check the following: \n" \
                          " Sensor raw data file ends in '_[sensor name]RawData' and is saved as a csv file.\n" \
                          "     ex: NanoscanRawData.csv\n" \
                          " Data file is saved in the same folder as the EnergyInputs file.\n" \
                          " Data file has complete lines and no additional lines of text at the end\n" \
                          " Sensor is one of the supposrt sensors: Scale, Nanoscan, TEOM, Senserion, OPS, Pico"

            tk.messagebox.showinfo(title='Sensors Processed', message=line)

            # Check if the tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Additional Sensors":
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                # self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Additional Sensors")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                # self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Additional Sensors")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            # create a frame to display
            sensor_frame = AddSensors(self.frame, files_finished, logs)
            sensor_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_custom(self):
        error = 0
        self.input_path = []
        try:
            for file in self.input_list:
                testname = os.path.basename(os.path.dirname(file))
                self.input_path.append(file.replace('EnergyOutputs.csv', "AllOutputs.csv"))
            self.output_path = self.folder_path + '//CustomCutTable_L2.csv'
            self.output_path_excel = self.folder_path + '//CustomCutTable_L2.xlsx'
            self.choice_path = self.folder_path + '//CutTableParameters_L2.csv'
            self.log_path = self.folder_path + '//log.txt'
            write = 1
            data, units = LEMS_CSVFormatted_L2(self.input_path, self.output_path, self.output_path_excel, self.choice_path, self.log_path, write)
        except PermissionError:
            message = f"File: {self.plots_path} is open in another program, close and try again."
            messagebox.showerror("Error", message)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Custom Comparison":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Custom Comparison")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="Custom Comparison")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        # Output table
        ct_frame = CustomTable(self.frame, data, units, self.choice_path, self.input_path, self.folder_path)
        ct_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_em(self):
        error = 0
        for file in self.input_list:
            testname = os.path.basename(os.path.dirname(file))
            try:
                self.input_path = file.replace('EnergyOutputs.csv', "TimeSeries.csv")
                self.energy_path = file.replace('EnergyOutputs.csv', "EnergyOutputs.csv")
                self.grav_path = file.replace('EnergyOutputs.csv', "GravOutputs.csv")
                self.average_path = file.replace('EnergyOutputs.csv', "Averages.csv")
                self.output_path = file.replace('EnergyOutputs.csv', "EmissionOutputs.csv")
                self.all_path = file.replace('EnergyOutputs.csv', "AllOutputs.csv")
                self.phase_path = file.replace('EnergyOutputs.csv', "PhaseTimes.csv")
                self.fuel_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.fuelmetric_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.exact_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.scale_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.nano_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.teom_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.senserion_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.ops_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.pico_path = file.replace('EnergyOutputs.csv', "NA.csv")
                self.log_path = file.replace('EnergyOutputs.csv', "log.txt")
                self.sensorbox_path = file.replace('EnergyOutputs.csv', "SensorboxVersion.csv")
                self.emission_path = file.replace('EnergyOutputs.csv', "EmissionInputs.csv")
                self.bc_path = file.replace('EnergyOutputs.csv', "BCOutputs.csv")
                logs, data, units = LEMS_EmissionCalcs(self.input_path, self.energy_path, self.grav_path,
                                                       self.average_path,
                                                       self.output_path, self.all_path, self.log_path, self.phase_path, self.sensorbox_path,
                                                       self.fuel_path, self.fuelmetric_path, self.exact_path,
                                                       self.scale_path, self.nano_path, self.teom_path,
                                                       self.senserion_path,
                                                       self.ops_path, self.pico_path, self.emission_path, self.inputmethod, self.bc_path)
                #self.emission_button.config(bg="lightgreen")
            except PermissionError:
                message = f"One of the following files: {self.output_path}, {self.all_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                #self.emission_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.emission_button.config(bg="red")
                error = 1

            # Check if the grav Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Emission Calculations " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Emission Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Emission Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            em_frame = Emission_Calcs(self.frame, logs, data, units, testname)
            em_frame.grid(row=3, column=0, padx=0, pady=0)

        if error == 0:
            self.emission_button.config(bg="lightgreen")
        else:
            self.emission_button.config(bg="red")

    def on_grav(self):
        error = 0
        for file in self.input_list:
            testname = os.path.basename(os.path.dirname(file))
            try:
                self.input_path = file.replace('EnergyOutputs.csv', "GravInputs.csv")
                self.average_path = file.replace('EnergyOutputs.csv', "Averages.csv")
                self.phase_path = file.replace('EnergyOutputs.csv', "PhaseTimes.csv")
                self.energy_path = file.replace('EnergyOutputs.csv', "EnergyOutputs.csv")
                self.output_path = file.replace('EnergyOutputs.csv', "GravOutputs.csv")
                self.log_path = file.replace('EnergyOutputs.csv', "log.txt")
                logs, gravval, outval, gravunits, outunits = LEMS_GravCalcs(self.input_path, self.average_path,
                                                                            self.phase_path, self.energy_path,
                                                                            self.output_path, self.log_path, self.inputmethod)
                #self.grav_button.config(bg="lightgreen")
            except PermissionError:
                message = f"File: {self.output_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                #self.grav_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.grav_button.config(bg="red")
                error = 1

            # Check if the grav Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Gravametric Calculations " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Gravametric Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Gravametric Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            grav_frame = Grav_Calcs(self.frame, logs, gravval, outval, gravunits, outunits, testname)
            grav_frame.grid(row=3, column=0, padx=0, pady=0)

        if error == 0:
            self.grav_button.config(bg="lightgreen")
        else:
            self.grav_button.config(bg="red")

    def on_bkg(self):
        error = 0
        for file in self.input_list:
            testname = os.path.basename(os.path.dirname(file))
            try:
                self.energy_path = file.replace('EnergyOutputs.csv', "EnergyOutputs.csv")
                self.input_path = file.replace('EnergyOutputs.csv', "RawData_Recalibrated.csv")
                self.UC_path = file.replace('EnergyOutputs.csv', "UCInputs.csv")
                self.output_path = file.replace('EnergyOutputs.csv', "TimeSeries.csv")
                self.average_path = file.replace('EnergyOutputs.csv', "Averages.csv")
                self.phase_path = file.replace('EnergyOutputs.csv', "PhaseTimes.csv")
                self.method_path = file.replace('EnergyOutputs.csv', "BkgMethods.csv")
                self.fig1 = file.replace('EnergyOutputs.csv', "subtractbkg1.png")
                self.fig2 = file.replace('EnergyOutputs.csv', "subtractbkg2.png")
                self.log_path = file.replace('EnergyOutputs.csv', "log.txt")
                logs, methods, phases, data = PEMS_SubtractBkg(self.input_path, self.energy_path, self.UC_path,
                                                         self.output_path,
                                                         self.average_path, self.phase_path, self.method_path,
                                                         self.log_path,
                                                         self.fig1, self.fig2, self.inputmethod)
                #self.bkg_button.config(bg="lightgreen")
            except PermissionError:
                message = f"One of the following files: {self.output_path}, {self.phase_path}, {self.method_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                #self.bkg_button.config(bg="red")
                error = 1
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
                #self.bkg_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.bkg_button.config(bg="red")
                error = 1

            # Check if the Energy Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Subtract Background " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Subtract Background " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Subtract Background " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            bkg_frame = Subtract_Bkg(self.frame, logs, self.fig1, self.fig2, methods, phases, testname, data)
            bkg_frame.grid(row=3, column=0, padx=0, pady=0)

        if error == 0:
            self.bkg_button.config(bg="lightgreen")
        else:
            self.bkg_button.config(bg="red")

    def on_cali(self):
        error = 0
        for file in self.input_list:
            testname = os.path.basename(os.path.dirname(file))
            try:
                self.energy_path = file.replace('EnergyOutputs.csv', 'SensorboxVersion.csv')
                self.input_path = file.replace('EnergyOutputs.csv', 'RawData.csv')
                self.output_path = file.replace('EnergyOutputs.csv', "RawData_Recalibrated.csv")
                self.header_path = file.replace('EnergyOutputs.csv', "Header.csv")
                self.log_path = file.replace('EnergyOutputs.csv', "log.txt")
                logs, firmware = LEMS_Adjust_Calibrations(self.input_path, self.energy_path, self.output_path,
                                                          self.header_path, self.log_path, self.inputmethod)
                #self.cali_button.config(bg="lightgreen")

            except UnboundLocalError:
                message = f'Something went wrong in Firmware calculations. \n' \
                          f'Please verify that the entered firmware version corresponds to the sensor box number.\n' \
                          f'Accepted firmware versions:\n' \
                          f'    *SB4002\n' \
                          f'    *SB4003\n' \
                          f'    *SB4005\n' \
                          f'    *SB4007\n' \
                          f'    *SB4008\n' \
                          f'    *SB2041\n' \
                          f'    *SB3001\n' \
                          f'    *SB3002\n' \
                          f'    *SB3009\n' \
                          f'    *SB3015\n' \
                          f'    *SB3016\n' \
                          f'    *Possum2\n' \
                          f'If your sensor box firmware is not one of the ones listed, it can be entered but nothing will be recalibrated.\n' \
                          f'This may lead to issues later.'
                messagebox.showerror("Error", message)
                #self.cali_button.config(bg="red")
                error = 1
            except PermissionError:
                message = f"File: {self.output_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                #self.cali_button.config(br="red")
                error = 1
            except IndexError:
                message = f'Program was unable to read the raw data file correctly. Please check the following:\n' \
                          f'    * There are no blank lines or cells within the data set\n' \
                          f'    * The sensor box was not reset at some point causing a header to be inserted into the middle of the data set.\n' \
                          f'    * There are no extra blank lines or non value lines at the end of the file.\n' \
                          f'Opening the file in a text editing program like notepad may be helpful.' \
                          f'Delete problems and try again.'
                messagebox.showerror("Error", message)
                #self.cali_button.config(bg="red")
                error = 1
            except FileNotFoundError:
                message = f'Program was unable to find file path: {self.input_path}. Please check the following:\n' \
                          f'    * A _RawData file exists in the same folder as the _EnergyInputs file\n' \
                          f'    * The file starts with the folder name and ends with _RawData. Ex: test1_RawData\n' \
                          f'    * The file is saved as a csv file\n' \
                          f'Correct problems and try again.'
                messagebox.showerror("Error", message)
                self.cali_button.config(bg="red")
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.cali_button.config(bg="red")
                error = 1

            # Check if the Energy Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Recalibration " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Recalibration " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Recalibration " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            adjust_frame = Adjust_Frame(self.frame, logs, firmware, testname)
            adjust_frame.grid(row=3, column=0, padx=0, pady=0)

        if error == 0:
            self.cali_button.config(bg="lightgreen")
        else:
            self.cali_button.config(bg="red")

    def on_energy(self):
        error = 0
        input_list = []
        for folder in self.energy_files:
            self.output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
            self.log_path = folder.replace('EnergyInputs.csv', 'log.txt')
            try:
                [units, data, logs] = LEMS_EnergyCalcs(folder, self.output_path, self.logger)
                #self.energy_button.config(bg="lightgreen")
                input_list.append(self.output_path)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.cali_button.config(bg="red")
                error = 1

            # Add the tab to the notebook with the folder name as the tab label
            testname = os.path.basename(os.path.dirname(folder))

            # round to 3 decimals
            round_data = {}
            for name in data:
                try:
                    rounded = "{:.3g}".format(data[name].n) # Format to either show up to 3 significant digits or use scientific notation
                except:
                    try:
                        rounded = "{:.3g}".format(data[name])  # Format to either show up to 3 significant digits or use scientific notation
                    except:
                        rounded = data[name]
                round_data[name] = rounded

            data = round_data

            # Check if the Energy Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text").startswith("Energy Calculations " + testname):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Energy Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Energy Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            # Output table
            self.create_output_table(data, units, logs, num_columns=150, num_rows=300,folder_path=folder, testname=testname)  # Adjust num_columns and num_rows as needed
        if error == 0:
            self.energy_button.config(bg="lightgreen")
        else:
            self.energy_button.config(bg="red")
    def on_all(self):

        ########################################################
        #Full comparison table
        # Check if the Energy Calculations tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "All Output Comparison":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="All Output Comparison")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="All Output Comparison")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        log_path = self.folder_path + '//log.txt'
        output_path = self.folder_path + '//UnFormattedDataL2.csv'
        self.emission_list = []
        self.all_list = []
        for file in self.input_list:
            emfile = file.replace("EnergyOutputs.csv", "EmissionOutputs.csv")
            allfile = file.replace("EnergyOutputs.csv", "AllOutputs.csv")
            if os.path.isfile(emfile):
                self.emission_list.append(emfile)
            if os.path.isfile(allfile):
                self.all_list.append(allfile)
        try:
            data, units, emdata, emunits, logs = PEMS_L2(self.all_list, self.input_list, self.emission_list,
                                                         output_path, log_path)
        except:
            data, units, logs = PEMS_L2(self.all_list, self.input_list, self.emission_list, output_path, log_path)

        try:
            data.update(emdata)
            units.update(emunits)
        except:
            pass

        # round to 3 decimals
        round_data = {}
        for name in data:
            try:
                rounded = "{:.3g}".format(data[name].n) # Format to either show up to 3 significant digits or use scientific notation
            except:
                try:
                    rounded = "{:.3g}".format(data[name]) # Format to either show up to 3 significant digits or use scientific notation
                except:
                    rounded = data[name]
            round_data[name] = rounded

        data = round_data

        # Output table
        self.create_compare_table(data, units, logs)

        self.frame.configure(height=300 * 3000)

        ######################################################33
        #ISO comparison table
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "ISO Comparision":
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="ISO Comparision")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            #self.tab_frame.grid(row=1, column=0)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text="ISO Comparision")

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)

        # Output table
        self.create_iso_table(data, units, logs)

        self.frame.configure(height=300 * 3000)

    def create_custom_table(self, data, units, choice_path):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        custom_table = CustomTable(self.tab_frame, data, units, choice_path)
        custom_table.grid(row=0, column=0)

    def create_output_table(self, data, units, logs, num_columns, num_rows, folder_path, testname):
        # Destroy any existing widgets in the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Create a new OutputTable instance and pack it into the frame
        output_table = OutputTable(self.tab_frame, data, units, logs, num_columns, num_rows, folder_path, testname)
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
        self.destroy_widgets()

        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Setup logger
        self.log_file = os.path.join(self.folder_path, "log.txt")
        self.logger = setup_logger(self.log_file)

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
            message = tk.Text(self.inner_frame, wrap="word", width=112, height=4)
            message.grid(row=2, column=0, columnspan=2)
            message.insert(tk.END, instructions)
            message.configure(state="disabled")

            for file in self.energy_files:
                if file not in existing_file_paths:
                    postselect.append(file)

            full_files = existing_file_paths + postselect
            defualt_selection = len(existing_file_paths)

            self.selected_files = tk.StringVar(value=list(full_files))
            self.file_selection_listbox = tk.Listbox(self.inner_frame, listvariable=self.selected_files,
                                                     selectmode=tk.MULTIPLE, width=150, height=len(full_files))
            self.file_selection_listbox.grid(row=3, column=0, columnspan=2)

            self.file_selection_listbox.selection_set(0, defualt_selection -1)

            ok_button = tk.Button(self.inner_frame, text="OK", command=self.on_ok)
            ok_button.grid(row=4, column=0)
        else:
            instructions = f'No files ending with EnergyInputs were found inside this folder. ' \
                           f'Please check that files exist and are named correctly before trying again.'
            message = tk.Text(self.innner_frame, wrap="word", width=112, height=4)
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

class Cut(tk.Frame):
    def __init__(self, root, data, units, logs, figpath, times):
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
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=75)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<120}|".format("CUT PERIOD AVERAGE OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                try:
                    val = "{:.3g}".format(value.n) # Format to either show up to 3 significant digits or use scientific notation
                except:
                    try:
                        val = "{:.3g}".format(value) # Format to either show up to 3 significant digits or use scientific notation
                    except:
                        val = value

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                row = "{:<35} | {:<10} | {:<17} |".format(key, unit, val)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 70 + "\n")
        self.text_widget.config(height=self.winfo_height() * 33)
        self.text_widget.configure(state="disabled")

        time_message = tk.Text(self, wrap="word", height=len(times.keys()) + 1, width=50)
        time_message.grid(row=1, column=4, rowspan=2)
        time_message.insert(tk.END, "Cut Times Used:")
        for key in times:
            time_message.insert(tk.END, "\n" + key + ': ' + times[key])
        time_message.configure(state="disabled")

        # Display images below the Advanced section
        image1 = I.open(figpath)
        image1 = image1.resize((550, 420), I.LANCZOS)
        photo1 = IT.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=550)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=2, column=4, pady=5, columnspan=3, rowspan=3)

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

class AddSensors(tk.Frame):
    def __init__(self, root, sensorpaths, logs):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(100, 5), pady=5, sticky="e")

        #sensors
        sensor_message = tk.Text(self, wrap="word", height=len(sensorpaths) + 1, width=130)
        sensor_message.grid(row=1, column=0, columnspan=4)
        sensor_message.insert(tk.END, "Additional Sensors Processed:")
        for sensor in sensorpaths:
            sensor_message.insert(tk.END, "\n" + sensor)
        sensor_message.configure(state="disabled")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=75)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

class Emission_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<124}|".format("EMISSION OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")
        header = "{:<54} | {:<31} | {:<38} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 68 + "\n", "bold")

        rownum = 0
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = "{:.3g}".format(value.n) # Format to either show up to 3 significant digits or use scientific notation
            except:
                try:
                    val = "{:.3g}".format(value) # Format to either show up to 3 significant digits or use scientific notation
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
        self.cut_table.grid(row=3, column=4, padx=0, pady=0, columnspan=3)
        cut_header = "{:<113}|".format("WEIGHTED METRICS")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        cut_header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.cut_table.insert(tk.END, cut_header + "\n" + "_" * 63 + "\n", "bold")
        for key, value in data.items():
            unit = units.get(key, "")
            try:
                val = "{:.3g}".format(value.n) # Format to either show up to 3 significant digits or use scientific notation
            except:
                try:
                    val = "{:.3g}".format(value) # Format to either show up to 3 significant digits or use scientific notation
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
                    val = "{:.3g}".format(value.n) # Format to either show up to 3 significant digits or use scientific notation
                except:
                    try:
                        val = "{:.3g}".format(value) # Format to either show up to 3 significant digits or use scientific notation
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
    def __init__(self, root, logs, gravval, outval, gravunits, outunits, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text="Find", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=70)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # output table
        self.text_widget = tk.Text(self, wrap="none", height=1, width=75)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

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
        self.out_widget.grid(row=3, column=4, columnspan=3, padx=0, pady=0)

        self.out_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<118}|".format("GRAV OUTPUTS")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<44} | {:<31} | {:<38} |".format("Variable", "Value", "Units")
        self.out_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

        for key, value in outval.items():
            if 'variable' not in key:
                unit = outunits.get(key, "")
                try:
                    val = "{:.3g}".format(value.n) # Format to either show up to 3 significant digits or use scientific notation
                except:
                    try:
                        val = "{:.3g}".format(value) # Format to either show up to 3 significant digits or use scientific notation
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
    def __init__(self, root, logs, fig1, fig2, methods, phases, testname, data):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=4, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=65)
        self.logs_text.grid(row=4, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=4, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

        # Collapsible 'Phases' section for logs
        self.phase_section = CollapsibleFrame(self, text="Phase Times", collapsed=True)
        self.phase_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for phases and add a vertical scrollbar
        self.phase_text = tk.Text(self.phase_section.content_frame, wrap="word", height=10, width=65)
        self.phase_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        phase_scrollbar = tk.Scrollbar(self.phase_section.content_frame, command=self.phase_text.yview)
        phase_scrollbar.grid(row=2, column=3, sticky="ns")

        self.phase_text.config(yscrollcommand=phase_scrollbar.set)

        for key, value in phases.items():
            if 'variable' not in key:
                self.phase_text.insert(tk.END, key + ': ' + value + "\n")

        self.phase_text.configure(state="disabled")

        # Collapsible 'Method' section for logs
        self.method_section = CollapsibleFrame(self, text="Subtraction Methods", collapsed=True)
        self.method_section.grid(row=3, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for phases and add a vertical scrollbar
        self.method_text = tk.Text(self.method_section.content_frame, wrap="word", height=10, width=65)
        self.method_text.grid(row=3, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        method_scrollbar = tk.Scrollbar(self.method_section.content_frame, command=self.method_text.yview)
        method_scrollbar.grid(row=3, column=3, sticky="ns")

        self.method_text.config(yscrollcommand=method_scrollbar.set)

        for key, value in methods.items():
            if 'chan' not in key:
                self.method_text.insert(tk.END, key + ': ' + value + "\n")

        self.method_text.configure(state="disabled")

        # Display images below the Advanced section
        image1 = I.open(fig1)
        image1 = image1.resize((575, 420), I.LANCZOS)
        photo1 = IT.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=5, column=0, padx=10, pady=5, columnspan=3)

        image2 = I.open(fig2)
        image2 = image2.resize((550, 420), I.LANCZOS)
        photo2 = IT.PhotoImage(image2)
        label2 = tk.Label(self, image=photo2, width=575)
        label2.image = photo2  # to prevent garbage collection
        label2.grid(row=5, column=4, padx=10, pady=5, columnspan=3)

        #Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text="Warnings", collapsed=False) #start open
        self.warning_section.grid(row=1, column=0, pady=0, padx=0, sticky='w')

        self.warning_frame = tk.Text(self.warning_section.content_frame, wrap="word", width=70, height=10)
        self.warning_frame.grid(row=1, column=0, columnspan=6)

        warn_scrollbar = tk.Scrollbar(self.warning_section.content_frame, command=self.warning_frame.yview)
        warn_scrollbar.grid(row=1, column=6, sticky='ns')
        self.warning_frame.config(yscrollcommand=warn_scrollbar.set)

        self.warning_frame.tag_configure("red", foreground="red")
        num_lines = 0

        emissions = ['CO', 'CO2', 'CO2v', 'PM']
        for key, value in data.items():
            if key.endswith('prebkg') and 'temp' not in key:
                try:
                    value = value.n
                except:
                    pass
                try:
                    for em in emissions:
                        if em in key:
                            if value < -1.0:
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
                            if value < -1.0:
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
                            if value > 1.0:
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
                            if value > 1.0:
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
    def __init__(self, root, logs, firmware, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap="word", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, "Test Name: " + testname)
        self.test.configure(state="disabled")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        #Firmware version
        firm_message = tk.Text(self, wrap="word", height=1, width=80)
        firm_message.grid(row=1, column=0, columnspan=3)
        firm_message.insert(tk.END, f"Firmware Version Used: {firmware}")
        firm_message.configure(state="disabled")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=75)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        self.logs_text.configure(state="disabled")

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

        self.text_widget = tk.Text(self, wrap="none", height=72, width=149)
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

        phases = ['_weighted', '_L1', '_hp', '_mp', '_lp', '_L5']
        params = ['eff_wo_char', 'eff_w_char', 'char_energy_productivity', 'char_mass_productivity', 'cooking_power',
                  'burn_rate', 'phase_time', 'CO_useful_eng_deliver', 'PM_useful_eng_deliver', 'PM_mass_time',
                  'PM_heat_mass_time', 'CO_mass_time']
        header = "{:<287}|".format("TIERS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
        for key, value in data.items():
            if 'tier' in key:
                value = data[key]
                unit = units.get(key, "")
                val = ""#value['values']
                avg = value['average']
                n = value['N']

                if not val:
                    val = " "
                if not unit:
                    unit = " "
                if not avg:
                    avg = " "
                if not n:
                    n = " "
                row = "{:<33} | {:<9} | {:<12} | {:<4} |".format(key, unit, avg, n)
                self.text_widget.insert(tk.END, row + "\n")
                self.text_widget.insert(tk.END, "_" * 148 + "\n")

        for phase in phases:
            if phase == '_weighted':
                header = "{:<280}|".format("COMBINED")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 132 + "\n", "bold")
            elif phase == '_L1':
                header = "{:<278}|".format("STARTUP")
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
            elif phase == '_L5':
                header = "{:<278}|".format("GHOST PHASE")
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

class CustomTable(tk.Frame):
    def __init__(self, root, data, units, choice_path, inputpath, folderpath):
        tk.Frame.__init__(self, root)

        self.choicepath = choice_path
        self.input_path = inputpath
        self.folder_path = folderpath

        # read in csv of previous selections
        self.variable_data = self.read_csv(choice_path)

        #create canvas
        self.canvas = tk.Canvas(self, borderwidth=0, height=self.winfo_height()*530, width=450)

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
            variable_name = variable_row[0]
            tk.Label(self.scrollable_frame, text=variable_name).grid(row=i+1, column=0)
            variable_units = variable_row[1]
            tk.Label(self.scrollable_frame, text=variable_units).grid(row=i+1, column=1)

            table_entry = tk.Entry(self.scrollable_frame)
            table_entry.insert(0, variable_row[2])
            table_entry.grid(row=i+1, column=2)

            self.variable_data[i] = [variable_name, variable_units, table_entry]

        #okay button for when user wants to update plot
        ok_button = tk.Button(self.scrollable_frame, text="OK", command=self.save)
        ok_button.grid(row=len(self.variable_data) + 1, column=2, pady=10)

        # Set the height of the scrollable frame
        self.scrollable_frame.config(height=self.winfo_height() * 31)
        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Create a frame to hold the table
        self.table_frame = tk.Frame(self)
        self.table_frame.grid(row=1, column=2, columnspan=3, padx=0, pady=0, sticky="nsew")

        # Create a canvas to hold the table frame
        self.canvas_table = tk.Canvas(self.table_frame, borderwidth=0, height=self.winfo_height() * 530, width=self.winfo_width() * 700)
        self.canvas_table.grid(row=1, column=0, sticky="nsew")

        # Create a scrollbar for the canvas
        self.scrollbar_table = tk.Scrollbar(self.table_frame, orient="horizontal", command=self.canvas_table.xview)
        self.scrollbar_table.grid(row=0, column=0, sticky="ew")

        # Create a frame inside the canvas to hold the table
        self.scrollable_frame_table = tk.Frame(self.canvas_table)
        self.canvas_table.create_window((0, 0), window=self.scrollable_frame_table, anchor="nw")

        # Bind the canvas to the scrollbar and set the scrollable region
        self.scrollable_frame_table.bind("<Configure>", lambda e: self.canvas_table.configure(
            scrollregion=self.canvas_table.bbox("all")))
        self.canvas_table.configure(xscrollcommand=self.scrollbar_table.set)

        testname = []
        for file in self.input_path:
            testname.append(os.path.basename(os.path.dirname(file)))

        text_widget_width = 50 + (len(testname) * 17)
        # Create the text widget for the table inside the scrollable frame
        self.text_widget = tk.Text(self.scrollable_frame_table, wrap="none", height=1, width=text_widget_width)
        self.text_widget.grid(row=0, column=0, sticky="nsew")

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<120}".format("OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * (63 * (30 * len(testname))) + "\n", "bold")
        headerformat = "{:<64} | {:<12} |" + "|".join(["{:<30}"] *len(testname))
        header = headerformat.format("Variable", "Units", *testname)
        self.text_widget.insert(tk.END, header + "\n" + "_" * (63 * (30 * len(testname))) + "\n", "bold")

        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                row_values = []
            for i, test_name in enumerate(testname):
                try:
                    row_values.append(round(float(value['values'][i]), 3))
                except ValueError:
                    row_values.append(value['values'][i])
                except TypeError:
                    row_values.append(value['values'][i])
                except IndexError:
                    row_values.append(" ")
            row_format = "{:<35} | {:<7} | " + " | ".join(["{:<15}"] * len(testname))
            row = row_format.format(key, unit, *row_values)
            self.text_widget.insert(tk.END, row + "\n")
            self.text_widget.insert(tk.END, "_" * (70 + 18 * len(testname)) + "\n")

        self.text_widget.config(height=self.winfo_height() * 31)
        self.text_widget.configure(state="disabled")

        # Update the scrollable region of the canvas after inserting all text
        self.canvas_table.configure(scrollregion=self.canvas_table.bbox("all"))
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def read_csv(self, filepath):
        variable_data = []
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                variable_data.append(row)
        return variable_data

    def save(self):
        self.updated_variable_data = []
        for i, row in enumerate(self.variable_data):
            table_value = self.variable_data[i][2].get()

            self.updated_variable_data.append([row[0], row[1], table_value])

        with open(self.choicepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in self. updated_variable_data:
                writer.writerow(row)

        try:
            self.output_path = self.folder_path + '//CustomCutTable_L2.csv'
            self.output_path_excel = self.folder_path + '//CustomCutTable_L2.xlsx'
            self.choice_path = self.folder_path + '//CutTableParameters_L2.csv'
            self.log_path = self.folder_path + '//log.txt'
            write = 1
            data, units = LEMS_CSVFormatted_L2(self.input_path, self.output_path, self.output_path_excel, self.choice_path, self.log_path, write)
        except PermissionError:
            message = f"File: {self.plots_path} is open in another program, close and try again."
            messagebox.showerror("Error", message)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        #call update table
        self.update_table(data, units)

    def update_table(self, data, units):
        # Clear the existing table
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)

        testname = []
        for file in self.input_path:
            testname.append(os.path.basename(os.path.dirname(file)))

        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))
        header = "{:<120}".format("OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * (63 * (31 * len(testname))) + "\n", "bold")
        headerformat = "{:<64} | {:<12} |" + "|".join(["{:<31}"] *len(testname))
        header = headerformat.format("Variable", "Units", *testname)
        self.text_widget.insert(tk.END, header + "\n" + "_" * (63 * (31 * len(testname))) + "\n", "bold")

        for key, value in data.items():
            if key.startswith('variable'):
                pass
            else:
                unit = units.get(key, "")
                row_values = []
            for i, test_name in enumerate(testname):
                try:
                    row_values.append(value['values'][i])
                except IndexError:
                    row_values.append(" ")
            row_format = "{:<35} | {:<7} | " + " | ".join(["{:<15}"] * len(testname))
            row = row_format.format(key, unit, *row_values)
            self.text_widget.insert(tk.END, row + "\n")
            self.text_widget.insert(tk.END, "_" * (70 + 18 * len(testname)) + "\n")

        self.text_widget.config(height=self.winfo_height() * 31)
        self.text_widget.configure(state="disabled")

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

        self.text_widget = tk.Text(self, wrap="none", height=72, width=149)
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
            if key.startswith('variable') or key.endswith("comments"):
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
    def __init__(self, root, data, units, logs, num_columns, num_rows, folder_path, testname):
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

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text="Advanced", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky="w")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap="word", height=10, width=65)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky="ew", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky="ns")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + "\n")

        # Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text="Warnings", collapsed=False)  # start open
        self.warning_section.grid(row=3, column=0, pady=0, padx=0, sticky='w')

        self.warning_frame = tk.Text(self.warning_section.content_frame, wrap="word", width=70, height=10)
        self.warning_frame.grid(row=3, column=0, columnspan=6)

        warn_scrollbar = tk.Scrollbar(self.warning_section.content_frame, command=self.warning_frame.yview)
        warn_scrollbar.grid(row=3, column=6, sticky='ns')
        self.warning_frame.config(yscrollcommand=warn_scrollbar.set)

        self.text_widget = tk.Text(self, wrap="none", height=num_rows, width=72)
        self.text_widget.grid(row=4, column=0, columnspan=3, padx=0, pady=0)

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

        self.cut_table.grid(row=4, column=3, padx=0, pady=0, columnspan=3, rowspan=self.winfo_height()*30)

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

            self.warning_frame.tag_configure("red", foreground="red")
            self.warning_frame.tag_configure("orange", foreground="orange")

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
                        #self.warning_frame.tag_configure("red", foreground="red")
                        #self.warning_frame.tag_add("red", "1.0", "end")
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
                        #self.warning_frame.tag_configure("red", foreground="red")
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

            if key.startswith('eff_w_char'):
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
                        #self.warning_frame.tag_configure("red", foreground="red")
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
            if key.startswith('char_mass_L1') or key.startswith('char_mass_hp') or key.startswith('char_mass_mp') or key.startswith('char_mass_lp') or key.startswith('char_mass_L5'):
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
                        self.warning_frame.insert(tk.END, warning_message)
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
                                            f"\n    ISO tests require a shutdown period of 5 minutes or when the max water temperture drops to 5 degrees below boiling temperature..\n"
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
                        self.cut_table.tag_configure("fault", background="red")

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

# -*- coding: utf-8 -*-

# Copyright (c) Muhammet Emin TURGUT 2020
# For license see LICENSE
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
    version = '2.0'
    root.title("App L2. Version: " + version)
    try:
        root.iconbitmap("ARC-Logo.ico")
    except:
        try:
            root.iconbitmap("C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\LEMS\\ARC-Logo.ico")
        except:
            pass
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()