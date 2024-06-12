import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
from LEMS_EnergyCalcs_ISO import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from tkinter import simpledialog
import csv
from LEMS_FormatData_L3 import LEMS_FormatData_L3
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
import traceback
from LEMS_boxplots import LEMS_boxplots
from LEMS_barcharts import LEMS_barcharts
from LEMS_scatterplots import LEMS_scatterplots
import PIL.Image
from PIL import ImageTk


class LEMSDataCruncher_L3(tk.Frame):
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

        instructions = f"Select a folder which contains test folders with Level 2 outputs to analyze."
        self.instructions = tk.Text(self.inner_frame, wrap="word", height=1, width=90)
        self.instructions.insert(tk.END, instructions)
        self.instructions.grid(row=0, column=0, columnspan=2)
        self.instructions.config(state="disabled")

        # File Path Entry
        tk.Label(self.inner_frame, text="Select Folder:").grid(row=1, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.inner_frame, textvariable=self.folder_path_var, width=150)
        self.folder_path.grid(row=1, column=0)

        # Initialize energy_files as an instance variable
        self.energy_files = []

        # create a button to browse folders on computer
        browse_button = tk.Button(self.inner_frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=1, column=1)

        # OK button
        ok_button = tk.Button(self.inner_frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=4, column=0)

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.grid(row=0, column=0)

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
                #self.frame.destroy()
                # Create a notebook to hold tabs
                #self.main_frame = tk.Frame(self.canvas, background="#ffffff")
                # self.frame.bind("<Configure>", self.onFrameConfigure)
                #self.notebook = ScrollableNotebook(root, wheelscroll=True, tabmenu=True)
                # self.notebook = ttk.Notebook(self.main_frame, height=30000)
                #self.notebook.grid(row=0, column=0, sticky="nsew")
                # Create a notebook to hold tabs
                #self.notebook = ttk.Notebook(height=30000)
                #self.notebook.grid(row=0, column=0)
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

                #L3
                # L3 table
                data, units, logs = LEMS_FormatData_L3(input_list, output_path, log_path)
                # Create a new frame for each tab
                tab_frame = tk.Frame(self.notebook)
                #self.tab_frame.grid(row=1, column=0)
                self.notebook.add(tab_frame, text="Menu")
                # Add the tab to the notebook with the folder name as the tab label
                #self.notebook.add(self.tab_frame, text=os.path.basename('All Output Comparison'))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Switch the view to the newly added menu tab
                #self.notebook.select("Menu")

                ################################################
                #menu set up
                blank = tk.Frame(self.frame, width=self.winfo_width() - 880)
                blank.grid(row=0, column=2, rowspan=2)

                # Exit button
                exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=25, pady=5, sticky="e")

                self.custom_table = tk.Button(self.frame, text="Create a Table of Selected Outputs", command=self.on_custom)
                self.custom_table.grid(row=1, column=0)

                self.boxplot_button = tk.Button(self.frame, text="Create Boxplot", command=self.on_boxplot)
                self.boxplot_button.grid(row=2, column=0)

                self.barchart_button = tk.Button(self.frame, text="Create Bar Chart", command=self.on_barchart)
                self.barchart_button.grid(row=3, column=0)

                self.scatterplot_button = tk.Button(self.frame, text="Create Scatter Plot", command=self.on_scatterplot)
                self.scatterplot_button.grid(row=4, column=0)

                # Instructions
                message = f'Use the following menu options to graph and analyze data.\n' \
                          f'Box plots take the value of each level 1 test value in a level 2 group and create a boxplot.\n' \
                          f'Box plots are recommended for tests with several runs.\n' \
                          f'Bar charts take the average from each level 2 as makes that the height of the bar.\n' \
                          f'Bar charts also take the calculated uncertainty to create error bars.\n' \
                          f'Scatter plots plot each individual point with a red line indicating the mean.'
                instructions = tk.Text(self.frame, width=85, wrap="word", height=13)
                instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                instructions.insert(tk.END, message)
                instructions.configure(state="disabled")

                # L3 table
                #self.create_L3_table(data, units)  # Adjust num_columns and num_rows as needed

                #self.frame.configure(height=300 * 3000)

                # L3 ISO
                # L3 ISO table
                # Create a new frame for each tab
                #self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                #self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                #self.notebook.add(self.tab_frame, text=os.path.basename('ISO Comparison'))

                # Set up the frame as you did for the original frame
                #self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                #self.frame.grid(row=1, column=0)

                # L3 table
                #self.create_L3iso_table(data, units)  # Adjust num_columns and num_rows as needed

                #self.frame.configure(height=300 * 3000)
                
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

    def on_custom(self):
        error = 0
        self.input_path = []
        try:
            for file in self.L2_files:
                testname = os.path.basename(os.path.dirname(file))
                self.input_path.append(file.replace('EnergyOutputs.csv', "AllOutputs.csv"))
            self.output_path = self.folder_path + '//CustomCutTable_L2.csv'
            self.output_path_excel = self.folder_path + '//CustomCutTable_L2.xlsx'
            self.choice_path = self.folder_path + '//CutTableParameters_L2.csv'
            self.log_path = self.folder_path + '//log.txt'
            write = 0
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

    def on_scatterplot(self):
        savefigpath = os.path.join(self.folder_path, 'L3ScatterPlot')
        logpath = os.path.join(self.folder_path, 'log,txt')
        try:
            savefigpath, variable = LEMS_scatterplots(self.L2_files, savefigpath, logpath)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the plot tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == (""):
                tab_index = i
        if tab_index is None:  # if no tab exists
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Scatter Plot")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Scatter Plot")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)

        # create a frame to display the plot and plot options
        scatterplot_frame = ScatterPlot(self.newframe, savefigpath)
        scatterplot_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_barchart(self):
        savefigpath = os.path.join(self.folder_path, 'L3BarChart')
        logpath = os.path.join(self.folder_path, 'log,txt')
        try:
            savefigpath, variable = LEMS_barcharts(self.L2_files, savefigpath, logpath)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the plot tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == (""):
                tab_index = i
        if tab_index is None:  # if no tab exists
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Bar Chart")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Bar Chart")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)

        # create a frame to display the plot and plot options
        barchart_frame = BarChart(self.newframe, savefigpath)
        barchart_frame.grid(row=3, column=0, padx=0, pady=0)

    def on_boxplot(self):
        savefigpath = os.path.join(self.folder_path, 'L3BoxPlot')
        logpath = os.path.join(self.folder_path, 'log,txt')
        try:
            savefigpath, variable = LEMS_boxplots(self.L2_files, savefigpath, logpath)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the plot tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == (""):
                tab_index = i
        if tab_index is None:  # if no tab exists
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Box Plot")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.newtab_frame = tk.Frame(self.notebook, height=300000)
            self.newtab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.newtab_frame, text=variable + " Box Plot")

            # Set up the frame
            self.newframe = tk.Frame(self.newtab_frame, background="#ffffff")
            self.newframe.grid(row=1, column=0)

        # create a frame to display the plot and plot options
        boxplot_frame = BoxPlot(self.newframe, savefigpath)
        boxplot_frame.grid(row=3, column=0, padx=0, pady=0)

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
            message = tk.Text(self.inner_frame, wrap="word", width=112, height=4)
            message.grid(row=2, column=0)
            message.insert(tk.END, instructions)
            message.configure(state="disabled")

            for file in self.L2_files:
                if file not in existing_file_paths:
                    postselect.append(file)

            full_files = existing_file_paths + postselect
            defualt_selection = len(existing_file_paths)

            self.selected_files = tk.StringVar(value=list(full_files))
            self.file_selection_listbox = tk.Listbox(self.inner_frame, listvariable=self.selected_files,
                                                     selectmode=tk.MULTIPLE, width=150, height=len(full_files))
            self.file_selection_listbox.grid(row=3, column=0, columnspan=1)

            self.file_selection_listbox.selection_set(0, defualt_selection - 1)

            ok_button = tk.Button(self.inner_frame, text="OK", command=self.on_ok)
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
            data, units = LEMS_CSVFormatted_L2(self.input_path, self.output_path, self.output_path_excel, self.choice_path, self.log_path)
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

class ScatterPlot(tk.Frame):
    def __init__(self, root, figpath):
        tk.Frame.__init__(self, root)

        blank = tk.Frame(self, width=self.winfo_width() - 1000)
        blank.grid(row=0, column=0, columnspan=4)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Display image
        image1 = PIL.Image.open(figpath)
        image1 = image1.resize((900, 520), PIL.Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=900)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=1, column=1, padx=10, pady=5, columnspan=4)
class BarChart(tk.Frame):
    def __init__(self, root, figpath):
        tk.Frame.__init__(self, root)

        blank = tk.Frame(self, width=self.winfo_width() - 1000)
        blank.grid(row=0, column=0, columnspan=4)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Display image
        image1 = PIL.Image.open(figpath)
        image1 = image1.resize((900, 540), PIL.Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=900)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=1, column=1, padx=10, pady=5, columnspan=4)

class BoxPlot(tk.Frame):
    def __init__(self, root, figpath):
        tk.Frame.__init__(self, root)

        blank = tk.Frame(self, width=self.winfo_width() - 1000)
        blank.grid(row=0, column=0, columnspan=4)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky="e")

        # Display image
        image1 = PIL.Image.open(figpath)
        image1 = image1.resize((900, 540), PIL.Image.LANCZOS)
        photo1 = ImageTk.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=900)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=1, column=1, padx=10, pady=5, columnspan=4)
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
                if key.startswith('variable') or key.endswith("comments"):
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
            if key.startswith('variable') or key.endswith("comments"):
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
        if tab_id in self.tabs():
            self.notebookTab.select(tab_id)
            content_tab_id = self.__ContentTabID(tab_id)
            if content_tab_id is not None:
                self.notebookContent.select(content_tab_id)
        else:
            print("Error: Tab ID '{}' not found in the notebook.".format(tab_id))

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
    version = '1.0'
    root.title("App L3. Version: " + version)
    try:
        root.iconbitmap("ARC-Logo.ico")
    except:
        try:
            root.iconbitmap("C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\LEMS\\ARC-Logo.ico")
        except:
            pass
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L3(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()
