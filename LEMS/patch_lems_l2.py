# patch_lems_l2.py
import re

with open('LEMS_DataEntry_L2.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = []

def register(old, new, name=''):
    print(f"Checking {name}...", flush=True)
    if old not in content:
        raise ValueError(f"Match not found for {name}:\n{old[:120]}...")
    if content.count(old) > 1:
        raise ValueError(f"Multiple matches ({content.count(old)}) for {name}:\n{old[:120]}...")
    replacements.append((old, new, name))


# 1. Imports
register(
'''import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import io''',
'''import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_i18n as i18n
from LEMS_i18n import t, t_field
import io''',
'imports'
)

# 2. Cruncher init & build_ui
old_cruncher_init = '''class LEMSDataCruncher_L2(tk.Frame):
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

        instructions = f"Select a folder which contains test folders to analyze.\\n" \\
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
        browse_button = tk.Button(self.inner_frame, text="Browse", command=self.on_browse, bg='lightgreen')
        browse_button.grid(row=1, column=2)

        # OK button
        ok_button = tk.Button(self.inner_frame, text=f"Set Up & Run \\n (Step by step run with prompts)",
                              command=self.on_okay, bg='lightgreen')
        ok_button.anchor()
        ok_button.grid(row=4, column=0, pady=10, padx=(270, 0))

        # noninteractive button
        nonint_button = tk.Button(self.inner_frame, text=f"Run with Saved Settings \\n (Auto runs through steps "
                                                         f"with saved inputs)", command=self.on_nonint, bg='yellow')
        nonint_button.anchor()
        nonint_button.grid(row=4, column=1, pady=10, padx=(10, 270))

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.grid(row=0, column=0)'''

new_cruncher_init = '''class LEMSDataCruncher_L2(tk.Frame):
    def __init__(self, root): #Set window
        tk.Frame.__init__(self, root)
        self.root = root
        self.energy_files = []
        self.build_ui()

    def change_language(self, event=None):
        new_lang_name = self.lang_combo.get()
        langs = i18n.get_available_languages()
        new_code = "en"
        for code, name in langs.items():
            if name == new_lang_name or code == new_lang_name:
                new_code = code
                break
        if new_code == i18n.get_language():
            return
        saved_folder = self.folder_path_var.get() if hasattr(self, 'folder_path_var') else ""
        i18n.set_language(new_code, save=True)
        self.rebuild_ui(saved_folder)

    def rebuild_ui(self, saved_folder=""):
        for widget in self.winfo_children():
            widget.destroy()
        version = '5.0'
        self.root.title(t("app.title_l2", version=version))
        self.build_ui(saved_folder)

    def build_ui(self, initial_folder=""):
        self.notebook = ScrollableNotebook(self, wheelscroll=True, tabmenu=True)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create a new frame
        self.tab_frame = tk.Frame(self.notebook)
        self.notebook.add(self.tab_frame, text=t("tab.folder_selection"))
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

        instructions = t("instructions.folder_selection_l2")
        self.instructions = tk.Text(self.inner_frame, wrap="word", height=2, width=90)
        self.instructions.insert(tk.END, instructions)
        self.instructions.grid(row=0, column=0, columnspan=2)
        self.instructions.config(state="disabled")

        # File Path Entry
        tk.Label(self.inner_frame, text=t("label.select_folder")).grid(row=1, column=0)
        self.folder_path_var = tk.StringVar(value=initial_folder)
        self.folder_path = tk.Entry(self.inner_frame, textvariable=self.folder_path_var, width=150)
        self.folder_path.grid(row=1, column=0, columnspan=2)

        # create a button to browse folders on computer
        browse_button = tk.Button(self.inner_frame, text=t("btn.browse_short"), command=self.on_browse, bg='lightgreen')
        browse_button.grid(row=1, column=2)

        # Language dropdown selector
        lang_frame = tk.Frame(self.inner_frame, background="#ffffff")
        lang_frame.grid(row=1, column=3, sticky="w", padx=(10, 20))
        tk.Label(lang_frame, text=t("label.language"), background="#ffffff").pack(side="left", padx=5)
        langs = i18n.get_available_languages()
        self.lang_combo = ttk.Combobox(lang_frame, values=list(langs.values()), state="readonly", width=12)
        current_code = i18n.get_language()
        self.lang_combo.set(langs.get(current_code, "English"))
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.lang_combo.pack(side="left")

        # OK button
        ok_button = tk.Button(self.inner_frame, text=t("btn.setup_and_run_l2"),
                              command=self.on_okay, bg='lightgreen')
        ok_button.anchor()
        ok_button.grid(row=4, column=0, pady=10, padx=(270, 0))

        # noninteractive button
        nonint_button = tk.Button(self.inner_frame, text=t("btn.run_saved_l2"), command=self.on_nonint, bg='yellow')
        nonint_button.anchor()
        nonint_button.grid(row=4, column=1, pady=10, padx=(10, 270))

        # Bind the MouseWheel event to the onCanvasMouseWheel function
        self.canvas.bind_all("<MouseWheel>", self.onCanvasMouseWheel)

        self.grid(row=0, column=0)'''

register(old_cruncher_init, new_cruncher_init, 'cruncher_init')

# 3. on_nonint permission errors and UI setup
old_nonint_part = '''        except PermissionError:
            error = 1
            message = f"File: {csv_file_path} is open.. Close it and try again."
            # Error
            messagebox.showerror("Error", message)

        if error == 0:
            error = []
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                try:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                    self.input_list.append(output_path)
                    emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                    if os.path.isfile(emission_path):
                        self.emission_list.append(emission_path)
                except PermissionError:
                    error.append(folder)
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
                self.notebook.add(tab_frame, text="Menu")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Switch the view to the newly added menu tab
                self.notebook.select(tab_frame)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                blank = tk.Frame(self.frame, width=max(0, self.winfo_width() - 1040))
                blank.grid(row=0, column=2, rowspan=2)


                self.cali_button = tk.Button(self.frame, text="Step 2: Adjust Sensor Calibrations",
                                             command=self.on_cali)
                self.cali_button.grid(row=2, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text="Step 4: Subtract Background", command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))
                self.gas_button = tk.Button(self.frame, text="Step 3: Finalize Gas Checks (if performed)",
                                            command=self.on_gas)
                self.gas_button.grid(row=3, column=0, padx=(0, 50))

                self.grav_button = tk.Button(self.frame, text="Step 5: Calculate Gravametric Data (optional)",
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.bc_button = tk.Button(self.frame, text="Step 6: Calculate Black Carbon (pictures required)",
                                           command=self.on_bc)
                self.bc_button.grid(row=6, column=0, padx=(0, 10))

                self.emission_button = tk.Button(self.frame, text="Step 7: Calculate Emissions", command=self.on_em)
                self.emission_button.grid(row=7, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text="Step 8: Cut data as a Custom Time Period (Optional)",
                                            command=self.on_cut)
                self.cut_button.grid(row=8, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text="Compare All Tests and Create ISO Report", command=self.on_all)
                self.all_button.grid(row=9, column=0, padx=(0, 70))

                self.custom_button = tk.Button(self.frame, text="Create a Table of Selected Outputs", command=self.on_custom)
                self.custom_button.grid(row=10, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
                message = f'* Please use the following buttons in order to process your data.\\n' \\
                          f'* Buttons will turn green when successful.\\n' \\
                          f'* Buttons will turn red when unsuccessful.\\n' \\
                          f'* Tabs will appear which will contain outputs from each step.\\n' \\
                          f'* If data from a previous step is changed, all proceeding steps must be done again.\\n' \\
                          f'* Files with data outputs will appear in the folder you selected. Modifying these files will change the calculated result if steps are redone.\\n\\n' \\
                          f'DO NOT proceed with the next step until the previous step is successful.\\n' \\
                          f'If a step is unsuccessful and all instructions from the error message have been followed ' \\
                          f'or no error message appears, send a screenshot of the print out in your python interpreter' \\
                          f'or the second screen (black with white writing if using the app version) along with your ' \\
                          f'data to jaden@aprovecho.org.' \\
                          f'\\n\\n' \\
                          f'To process black carbon data. Take filter pictures according to instructions. Save' \\
                          f'pictures in test folder and name files as foldername_filternumber where the filter ' \\
                          f'number correlates with the filter ID used during gravimetric calculations.'
                instructions = tk.Text(self.frame, width=85, wrap="word", height=17)
                instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                instructions.insert(tk.END, message)
                instructions.configure(state="disabled")

                self.toggle = tk.Button(self.frame, text="Click here to run with pop-ups", bg='lightblue', command=self.update_input)'''

new_nonint_part = '''        except PermissionError:
            error = 1
            message = t("err.file.open_permission", path=csv_file_path)
            # Error
            messagebox.showerror(t("msg.error"), message)

        if error == 0:
            error = []
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                try:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                    self.input_list.append(output_path)
                    emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                    if os.path.isfile(emission_path):
                        self.emission_list.append(emission_path)
                except PermissionError:
                    error.append(folder)
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
                message = t("err.file.open_permission_l2_general")
                # Error
                messagebox.showerror(t("msg.error"), message)
            else:
                # Delete all tabs after the menu tab, starting from the second tab
                to_forget = []
                for i in range(self.notebook.index("end")):
                    if i == 0 or self.notebook.tab(i, "text") in ("Folder Selection", t("tab.folder_selection")):
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
                self.notebook.add(tab_frame, text=t("tab.menu"))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Switch the view to the newly added menu tab
                self.notebook.select(tab_frame)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text=t("btn.menu_step1"), command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                blank = tk.Frame(self.frame, width=max(0, self.winfo_width() - 1040))
                blank.grid(row=0, column=2, rowspan=2)

                self.cali_button = tk.Button(self.frame, text=t("btn.menu_step2"),
                                             command=self.on_cali)
                self.cali_button.grid(row=2, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text=t("btn.menu_step4"), command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))
                self.gas_button = tk.Button(self.frame, text=t("btn.menu_step3"),
                                            command=self.on_gas)
                self.gas_button.grid(row=3, column=0, padx=(0, 50))

                self.grav_button = tk.Button(self.frame, text=t("btn.menu_step5"),
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.bc_button = tk.Button(self.frame, text=t("btn.menu_step6"),
                                           command=self.on_bc)
                self.bc_button.grid(row=6, column=0, padx=(0, 10))

                self.emission_button = tk.Button(self.frame, text=t("btn.menu_step7"), command=self.on_em)
                self.emission_button.grid(row=7, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text=t("btn.menu_step8"),
                                            command=self.on_cut)
                self.cut_button.grid(row=8, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text=t("btn.compare_iso"), command=self.on_all)
                self.all_button.grid(row=9, column=0, padx=(0, 70))

                self.custom_button = tk.Button(self.frame, text=t("btn.create_custom_table"), command=self.on_custom)
                self.custom_button.grid(row=10, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text=t("btn.exit"), command=self.root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
                message = t("instructions.menu") + "\\n\\n" + t("instructions.menu_bc")
                instructions = tk.Text(self.frame, width=85, wrap="word", height=17)
                instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                instructions.insert(tk.END, message)
                instructions.configure(state="disabled")

                self.toggle = tk.Button(self.frame, text=t("btn.toggle_popups_off"), bg='lightblue', command=self.update_input)'''

register(old_nonint_part, new_nonint_part, 'nonint_part')

# 4. update_input
old_update_input = '''    def update_input(self):
        if self.inputmethod == '2':
            self.inputmethod = '1'
            self.toggle.config(text="Click here to run without pop-ups", bg='violet')
        elif self.inputmethod == '1':
            self.inputmethod = '2'
            self.toggle.config(text="Click here to run with pop-ups", bg='lightblue')'''

new_update_input = '''    def update_input(self):
        if self.inputmethod == '2':
            self.inputmethod = '1'
            self.toggle.config(text=t("btn.toggle_popups_on"), bg='violet')
        elif self.inputmethod == '1':
            self.inputmethod = '2'
            self.toggle.config(text=t("btn.toggle_popups_off"), bg='lightblue')'''

register(old_update_input, new_update_input, 'update_input')

# 5. on_okay permission errors and UI setup
old_okay_part = '''        except PermissionError:
            error = 1
            message = f"File: {csv_file_path} is open.. Close it and try again."
            # Error
            messagebox.showerror("Error", message)

        if error == 0:
            error = []
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                try:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                    self.input_list.append(output_path)
                    emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                    if os.path.isfile(emission_path):
                        self.emission_list.append(emission_path)
                except PermissionError:
                    error.append(folder)
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
                self.notebook.add(tab_frame, text="Menu")

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Switch the view to the newly added menu tab
                self.notebook.select(tab_frame)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text="Step 1: Energy Calculations", command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                blank = tk.Frame(self.frame, width=max(0, self.winfo_width() - 1040))
                blank.grid(row=0, column=2, rowspan=2)

                self.cali_button = tk.Button(self.frame, text="Step 2: Adjust Sensor Calibrations",
                                             command=self.on_cali)
                self.cali_button.grid(row=2, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text="Step 4: Subtract Background", command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))
                self.gas_button = tk.Button(self.frame, text="Step 3: Finalize Gas Checks (if performed)",
                                            command=self.on_gas)
                self.gas_button.grid(row=3, column=0, padx=(0, 50))

                self.grav_button = tk.Button(self.frame, text="Step 5: Calculate Gravametric Data (optional)",
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.bc_button = tk.Button(self.frame, text="Step 6: Calculate Black Carbon (pictures required)",
                                           command=self.on_bc)
                self.bc_button.grid(row=6, column=0, padx=(0, 10))

                self.emission_button = tk.Button(self.frame, text="Step 7: Calculate Emissions", command=self.on_em)
                self.emission_button.grid(row=7, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text="Step 8: Cut data as a Custom Time Period (Optional)",
                                            command=self.on_cut)
                self.cut_button.grid(row=8, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text="Compare All Tests and Create ISO Report", command=self.on_all)
                self.all_button.grid(row=9, column=0, padx=(0, 70))

                self.custom_button = tk.Button(self.frame, text="Create a Table of Selected Outputs",
                                               command=self.on_custom)
                self.custom_button.grid(row=10, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
                message = f'* Please use the following buttons in order to process your data.\\n' \\
                          f'* Buttons will turn green when successful.\\n' \\
                          f'* Buttons will turn red when unsuccessful.\\n' \\
                          f'* Tabs will appear which will contain outputs from each step.\\n' \\
                          f'* If data from a previous step is changed, all proceeding steps must be done again.\\n' \\
                          f'* Files with data outputs will appear in the folder you selected. Modifying these files will change the calculated result if steps are redone.\\n\\n' \\
                          f'DO NOT proceed with the next step until the previous step is successful.\\n' \\
                          f'If a step is unsuccessful and all instructions from the error message have been followed ' \\
                          f'or no error message appears, send a screenshot of the print out in your python interpreter' \\
                          f'or the second screen (black with white writing if using the app version) along with your ' \\
                          f'data to jaden@aprovecho.org.' \\
                          f'\\n\\n' \\
                          f'To process black carbon data. Take filter pictures according to instructions. Save' \\
                          f'pictures in test folder and name files as foldername_filternumber where the filter ' \\
                          f'number correlates with the filter ID used during gravimetric calculations.'
                instructions = tk.Text(self.frame, width=85, wrap="word", height=17)
                instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                instructions.insert(tk.END, message)
                instructions.configure(state="disabled")

                self.toggle = tk.Button(self.frame, text="Click here to run without pop-ups", bg='violet', command=self.update_input)'''

new_okay_part = '''        except PermissionError:
            error = 1
            message = t("err.file.open_permission", path=csv_file_path)
            # Error
            messagebox.showerror(t("msg.error"), message)

        if error == 0:
            error = []
            self.input_list = []
            self.emission_list = []
            for folder in self.energy_files:
                try:
                    output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                    log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                    [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                    self.input_list.append(output_path)
                    emission_path = folder.replace('EnergyInputs.csv', 'EmissionOutputs.csv')
                    if os.path.isfile(emission_path):
                        self.emission_list.append(emission_path)
                except PermissionError:
                    error.append(folder)
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
                message = t("err.file.open_permission_l2_general")
                # Error
                messagebox.showerror(t("msg.error"), message)
            else:
                # Delete all tabs after the menu tab, starting from the second tab
                to_forget = []
                for i in range(self.notebook.index("end")):
                    if i == 0 or self.notebook.tab(i, "text") in ("Folder Selection", t("tab.folder_selection")):
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
                self.notebook.add(tab_frame, text=t("tab.menu"))

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                # Switch the view to the newly added menu tab
                self.notebook.select(tab_frame)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

                self.energy_button = tk.Button(self.frame, text=t("btn.menu_step1"), command=self.on_energy)
                self.energy_button.grid(row=1, column=0, padx=(0, 140))

                blank = tk.Frame(self.frame, width=max(0, self.winfo_width() - 1040))
                blank.grid(row=0, column=2, rowspan=2)

                self.cali_button = tk.Button(self.frame, text=t("btn.menu_step2"),
                                             command=self.on_cali)
                self.cali_button.grid(row=2, column=0, padx=(0, 105))

                self.bkg_button = tk.Button(self.frame, text=t("btn.menu_step4"), command=self.on_bkg)
                self.bkg_button.grid(row=4, column=0, padx=(0, 133))
                self.gas_button = tk.Button(self.frame, text=t("btn.menu_step3"),
                                            command=self.on_gas)
                self.gas_button.grid(row=3, column=0, padx=(0, 50))

                self.grav_button = tk.Button(self.frame, text=t("btn.menu_step5"),
                                             command=self.on_grav)
                self.grav_button.grid(row=5, column=0, padx=(0, 45))

                self.bc_button = tk.Button(self.frame, text=t("btn.menu_step6"),
                                           command=self.on_bc)
                self.bc_button.grid(row=6, column=0, padx=(0, 10))

                self.emission_button = tk.Button(self.frame, text=t("btn.menu_step7"), command=self.on_em)
                self.emission_button.grid(row=7, column=0, padx=(0, 140))

                self.cut_button = tk.Button(self.frame, text=t("btn.menu_step8"),
                                            command=self.on_cut)
                self.cut_button.grid(row=8, column=0, padx=(0, 8))

                self.all_button = tk.Button(self.frame, text=t("btn.compare_iso"), command=self.on_all)
                self.all_button.grid(row=9, column=0, padx=(0, 70))

                self.custom_button = tk.Button(self.frame, text=t("btn.create_custom_table"),
                                               command=self.on_custom)
                self.custom_button.grid(row=10, column=0, padx=(0, 102))

                # Exit button
                exit_button = tk.Button(self.frame, text=t("btn.exit"), command=self.root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

                # Instructions
                message = t("instructions.menu") + "\\n\\n" + t("instructions.menu_bc")
                instructions = tk.Text(self.frame, width=85, wrap="word", height=17)
                instructions.grid(row=1, column=1, rowspan=320, padx=5, pady=(0, 320))
                instructions.insert(tk.END, message)
                instructions.configure(state="disabled")

                self.toggle = tk.Button(self.frame, text=t("btn.toggle_popups_on"), bg='violet', command=self.update_input)'''

register(old_okay_part, new_okay_part, 'okay_part')

# 6. on_gas
old_gas = '''            except PermissionError:
                message = f"File: {self.input_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.cali_button.config(bg="red")
                error = 1

            # Add the tab to the notebook with the folder name as the tab label
            testname = os.path.basename(os.path.dirname(folder))

            # Check if the Quality Control tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text").startswith("Quality Control " + testname):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                #self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text= "Quality Control " + testname)

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
                self.notebook.add(self.tab_frame, text= "Quality Control " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

new_gas = '''            except PermissionError:
                message = t("err.file.open_permission", path=self.inputpath)
                messagebox.showerror(t("msg.error"), message)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.cali_button.config(bg="red")
                error = 1

            # Add the tab to the notebook with the folder name as the tab label
            testname = os.path.basename(os.path.dirname(folder))

            # Check if the Quality Control tab exists
            target_tab = f"{t('tab.quality_control')} {testname}"
            legacy_tab = "Quality Control " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_gas, new_gas, 'on_gas')

# 7. on_cut
old_cut = '''            # Create a popup for selection
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
            cancel_button.grid(row=2, column=1, padx=5, pady=5)'''

new_cut = '''            # Create a popup for selection
            popup = tk.Toplevel(self)
            popup.title(t("title.select_phases"))

            selected_phases = []

            #Instructions for popuo=p
            message = tk.Label(popup, text=t("label.select_phases_cut"))
            message.grid(row=0, column=0, columnspan=2, padx=20)

            # Listbox to display phases n popup
            listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE, height=5)
            for phase in phases:
                listbox.insert(tk.END, phase)
            listbox.grid(row=1, column=0, columnspan=2, padx=20)

            # OK button
            ok_button = tk.Button(popup, text=t("btn.ok"), command=ok)
            ok_button.grid(row=2, column=0, padx=5, pady=5)

            # Cancel button
            cancel_button = tk.Button(popup, text=t("btn.cancel"), command=cancel)
            cancel_button.grid(row=2, column=1, padx=5, pady=5)'''

register(old_cut, new_cut, 'on_cut_popup')

old_cut_err = '''                    except PermissionError:
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
                                                                                                             'Please check folder and try again')'''


new_cut_err = '''                    except PermissionError:
                        message = t("err.file.open_permission", path=getattr(self, 'plots_path', ''))
                        messagebox.showerror(t("msg.error"), message)
                        self.cut_button.config(bg='red')
                    except Exception as e:  # If error in called fuctions, return error but don't quit
                        line = 'Error: ' + str(e)
                        print(line)
                        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                        self.cut_button.config(bg='red')

                    # Check if the tab exists
                    clean_cut_text = t("tab.cut_period").replace("{phase}", "").strip()
                    target_tab = f"{phase} {clean_cut_text}"
                    legacy_tab = phase + " Cut Period"
                    tab_index = None
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                            tab_index = i
                    if tab_index is None:
                        # Create a new frame for each tab
                        self.tab_frame = tk.Frame(self.notebook, height=300000)
                        self.tab_frame.pack(side="left")
                        # Add the tab to the notebook with the folder name as the tab label
                        self.notebook.add(self.tab_frame, text=target_tab)

                        # Set up the frame as you did for the original frame
                        self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                        self.frame.grid(row=1, column=0)
                    else:
                        # Overwrite existing tab
                        # Destroy existing tab frame
                        self.notebook.forget(tab_index)
                        # Create a new frame for each tab
                        self.tab_frame = tk.Frame(self.notebook, height=300000)
                        self.tab_frame.pack(side="left")
                        # Add the tab to the notebook with the folder name as the tab label
                        self.notebook.add(self.tab_frame, text=target_tab)

                        # Set up the frame as you did for the original frame
                        self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                        self.frame.grid(row=1, column=0)

                    self.savefig = file.replace('EnergyOutputs.csv', 'AveragingPeriod_' + phase + '.png')

                    # create a frame to display the plot and plot options
                    cut_frame = Cut(self.frame, data, units, logs, self.savefig, times)
                    cut_frame.grid(row=3, column=0, padx=0, pady=0)

                else:
                    tk.messagebox.showinfo(title=t("msg.phase_not_found"), message=t("err.file.phase_not_found", path=self.inputpath))'''

register(old_cut_err, new_cut_err, 'on_cut_err_tab')

# 8. on_custom
old_custom = '''        except PermissionError:
            message = f"File: {self.plots_path} is open in another program, close and try again."
            messagebox.showerror("Error", message)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the tab exists
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Custom Comparison":
                tab_index = i
        if tab_index is not None:
            # Overwrite existing tab
            self.notebook.forget(tab_index)

        # Create a new frame for each tab
        self.tab_frame = tk.Frame(self.notebook)
        self.tab_frame.grid_rowconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(0, weight=1)
        # Add the tab to the notebook with the folder name as the tab label
        self.notebook.add(self.tab_frame, text="Custom Comparison")'''

new_custom = '''        except PermissionError:
            message = t("err.file.open_permission", path=getattr(self, 'plots_path', ''))
            messagebox.showerror(t("msg.error"), message)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

        # Check if the tab exists
        target_tab = t("tab.custom_comparison")
        legacy_tab = "Custom Comparison"
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                tab_index = i
        if tab_index is not None:
            # Overwrite existing tab
            self.notebook.forget(tab_index)

        # Create a new frame for each tab
        self.tab_frame = tk.Frame(self.notebook)
        self.tab_frame.grid_rowconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(0, weight=1)
        # Add the tab to the notebook with the folder name as the tab label
        self.notebook.add(self.tab_frame, text=target_tab)'''

register(old_custom, new_custom, 'on_custom')

# 9. on_em
old_em = '''            except PermissionError:
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

            # Check if the quality checks tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Quality Checks " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                # self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Quality Checks " + testname)

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
                self.notebook.add(self.tab_frame, text="Quality Checks " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

new_em = '''            except PermissionError:
                message = t("err.file.open_permission_multi", files=f"{self.output_path}, {self.all_path}")
                messagebox.showerror(t("msg.error"), message)
                #self.emission_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.emission_button.config(bg="red")
                error = 1

            # Check if the grav Calculations tab exists
            target_tab = f"{t('tab.emission_calcs')} {testname}"
            legacy_tab = "Emission Calculations " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)

            em_frame = Emission_Calcs(self.frame, logs, data, units, testname)
            em_frame.grid(row=3, column=0, padx=0, pady=0)

            # Check if the quality checks tab exists
            target_tab2 = f"{t('tab.quality_checks')} {testname}"
            legacy_tab2 = "Quality Checks " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab2, legacy_tab2):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab2)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab2)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_em, new_em, 'on_em')

# 10. on_bc
old_bc = '''            except PermissionError:
                message = f"File: {self.outputpath} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                error = 1

            # Check if the grav Calculations tab exists
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Black Carbon Calculations " + testname:
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                # self.tab_frame.grid(row=1, column=0)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text="Black Carbon Calculations " + testname)

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
                self.notebook.add(self.tab_frame, text="Black Carbon Calculations " + testname)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

new_bc = '''            except PermissionError:
                message = t("err.file.open_permission", path=self.outputpath)
                messagebox.showerror(t("msg.error"), message)
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                error = 1

            # Check if the grav Calculations tab exists
            target_tab = f"{t('tab.black_carbon')} {testname}"
            legacy_tab = "Black Carbon Calculations " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_bc, new_bc, 'on_bc')

# 11. on_grav
old_grav = '''            except PermissionError:
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
                self.frame.grid(row=1, column=0)'''

new_grav = '''            except PermissionError:
                message = t("err.file.open_permission", path=self.output_path)
                messagebox.showerror(t("msg.error"), message)
                #self.grav_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.grav_button.config(bg="red")
                error = 1

            # Check if the grav Calculations tab exists
            target_tab = f"{t('tab.gravimetric')} {testname}"
            legacy_tab = "Gravametric Calculations " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_grav, new_grav, 'on_grav')

# 12. on_bkg
old_bkg = '''            except PermissionError:
                message = f"One of the following files: {self.output_path}, {self.phase_path}, {self.method_path} is open in another program. Please close and try again."
                messagebox.showerror("Error", message)
                #self.bkg_button.config(bg="red")
                error = 1
            except KeyError as e:
                print(e)
                if 'time' in str(e):
                    error = str(e)
                    wrong = error.split(':')
                    message = f"Time entry for:{wrong} is either entered in an incorrect format or is a time that occured before or after data was collected.\\n" \\
                              f"    * Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\\n" \\
                              f"    * Check that no letters, symbols, or spaces are included in the time entry\\n" \\
                              f"    * Check that the entered time exist within the data\\n" \\
                              f"    * Check that the time has not been left blank when there should be an entry.\\n" \\
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
                self.frame.grid(row=1, column=0)'''

new_bkg = '''            except PermissionError:
                message = t("err.file.open_permission_multi", files=f"{self.output_path}, {self.phase_path}, {self.method_path}")
                messagebox.showerror(t("msg.error"), message)
                #self.bkg_button.config(bg="red")
                error = 1
            except KeyError as e:
                print(e)
                if 'time' in str(e):
                    error = str(e)
                    wrong = error.split(':')
                    message = t("err.bkg.time_format", wrong=wrong, path=self.phase_path)
                    messagebox.showerror(t("msg.error"), message)
                #self.bkg_button.config(bg="red")
                error = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.bkg_button.config(bg="red")
                error = 1

            # Check if the Energy Calculations tab exists
            target_tab = f"{t('tab.subtract_bkg')} {testname}"
            legacy_tab = "Subtract Background " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_bkg, new_bkg, 'on_bkg')

# 13. on_cali
old_cali = '''            except UnboundLocalError:
                message = f'Something went wrong in Firmware calculations. \\n' \\
                          f'Please verify that the entered firmware version corresponds to the sensor box number.\\n' \\
                          f'Accepted firmware versions:\\n' \\
                      f'    *SB4002\\n' \\
                      f'    *SB4003\\n' \\
                      f'    *SB4004\\n' \\
                      f'    *SB4005\\n' \\
                      f'    *SB4007\\n' \\
                      f'    *SB4008\\n' \\
                      f'    *SB4010\\n' \\
                      f'    *SB4011\\n' \\
                      f'    *SB4012\\n' \\
                      f'    *SB4013\\n' \\
                      f'    *SB4016\\n' \\
                      f'    *SB4017\\n' \\
                      f'    *SB4018\\n' \\
                      f'    *SB2041\\n' \\
                      f'    *SB3001\\n' \\
                      f'    *SB3002\\n' \\
                      f'    *SB3009\\n' \\
                      f'    *SB3015\\n' \\
                      f'    *SB3016\\n' \\
                      f'    *Possum2\\n' \\
                          f'If your sensor box firmware is not one of the ones listed, it can be entered but nothing will be recalibrated.\\n' \\
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
                message = f'Program was unable to read the raw data file correctly. Please check the following:\\n' \\
                          f'    * There are no blank lines or cells within the data set\\n' \\
                          f'    * The sensor box was not reset at some point causing a header to be inserted into the middle of the data set.\\n' \\
                          f'    * There are no extra blank lines or non value lines at the end of the file.\\n' \\
                          f'Opening the file in a text editing program like notepad may be helpful.' \\
                          f'Delete problems and try again.'
                messagebox.showerror("Error", message)
                #self.cali_button.config(bg="red")
                error = 1
            except FileNotFoundError:
                message = f'Program was unable to find file path: {self.input_path}. Please check the following:\\n' \\
                          f'    * A _RawData file exists in the same folder as the _EnergyInputs file\\n' \\
                          f'    * The file starts with the folder name and ends with _RawData. Ex: test1_RawData\\n' \\
                          f'    * The file is saved as a csv file\\n' \\
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
                self.frame.grid(row=1, column=0)'''

new_cali = '''            except UnboundLocalError:
                message = t("err.firmware.calculation")
                messagebox.showerror(t("msg.error"), message)
                #self.cali_button.config(bg="red")
                error = 1
            except PermissionError:
                message = t("err.file.open_permission", path=self.output_path)
                messagebox.showerror(t("msg.error"), message)
                #self.cali_button.config(br="red")
                error = 1
            except IndexError:
                message = t("err.file.raw_data_format")
                messagebox.showerror(t("msg.error"), message)
                #self.cali_button.config(bg="red")
                error = 1
            except FileNotFoundError:
                message = t("err.file.raw_data_missing", path=self.input_path)
                messagebox.showerror(t("msg.error"), message)
                self.cali_button.config(bg="red")
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                #self.cali_button.config(bg="red")
                error = 1

            # Check if the Energy Calculations tab exists
            target_tab = f"{t('tab.recalibration')} {testname}"
            legacy_tab = "Recalibration " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_cali, new_cali, 'on_cali')

# 14. on_energy
old_energy = '''            # Check if the Energy Calculations tab exists
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
                self.frame.grid(row=1, column=0)'''

new_energy = '''            # Check if the Energy Calculations tab exists
            target_tab = f"{t('tab.energy_calcs')} {testname}"
            legacy_tab = "Energy Calculations " + testname
            tab_index = None
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") in (target_tab, legacy_tab):
                    tab_index = i
            if tab_index is None:
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)
            else:
                # Overwrite existing tab
                # Destroy existing tab frame
                self.notebook.forget(tab_index)
                # Create a new frame for each tab
                self.tab_frame = tk.Frame(self.notebook, height=300000)
                self.tab_frame.pack(side="left")
                # Add the tab to the notebook with the folder name as the tab label
                self.notebook.add(self.tab_frame, text=target_tab)

                # Set up the frame as you did for the original frame
                self.frame = tk.Frame(self.tab_frame, background="#ffffff")
                self.frame.grid(row=1, column=0)'''

register(old_energy, new_energy, 'on_energy')

# 15. on_all
old_all = '''        #Full comparison table
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
            self.frame.grid(row=1, column=0)'''

new_all = '''        #Full comparison table
        # Check if the Energy Calculations tab exists
        target_tab1 = t("tab.all_output_comparison")
        legacy_tab1 = "All Output Comparison"
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") in (target_tab1, legacy_tab1):
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text=target_tab1)

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text=target_tab1)

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)'''

register(old_all, new_all, 'on_all_tab1')

old_all_iso = '''        ######################################################33
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
            self.frame.grid(row=1, column=0)'''

new_all_iso = '''        ######################################################33
        #ISO comparison table
        target_tab2 = t("tab.iso_comparison")
        legacy_tab2 = "ISO Comparison"
        tab_index = None
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") in (target_tab2, legacy_tab2, "ISO Comparision"):
                tab_index = i
        if tab_index is None:
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text=target_tab2)

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)
        else:
            # Overwrite existing tab
            # Destroy existing tab frame
            self.notebook.forget(tab_index)
            # Create a new frame for each tab
            self.tab_frame = tk.Frame(self.notebook, height=300000)
            self.tab_frame.pack(side="left")
            # Add the tab to the notebook with the folder name as the tab label
            self.notebook.add(self.tab_frame, text=target_tab2)

            # Set up the frame as you did for the original frame
            self.frame = tk.Frame(self.tab_frame, background="#ffffff")
            self.frame.grid(row=1, column=0)'''

register(old_all_iso, new_all_iso, 'on_all_iso')

# 16. on_browse
old_browse = '''        if existing_file_paths or self.energy_files:
            instructions = f\'The following paths were found within this directory.\\n\' \\
                           f\'Any preselected path were found in: {csv_file_path}\\n\' \\
                           f\'Please select which tests you would like to compare and press OK.\'
            message = tk.Text(self.inner_frame, wrap=\"word\", width=112, height=4)
            message.grid(row=2, column=0, columnspan=2)
            message.insert(tk.END, instructions)
            message.configure(state=\"disabled\")

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

            ok_button = tk.Button(self.inner_frame, text=\"OK\", command=self.on_ok)
            ok_button.grid(row=4, column=0)
        else:
            instructions = f\'No files ending with EnergyInputs were found inside this folder. \' \\
                           f\'Please check that files exist and are named correctly before trying again.\'
            message = tk.Text(self.innner_frame, wrap=\"word\", width=112, height=4)
            message.grid(row=2, column=0)
            message.insert(tk.END, instructions)
            message.configure(state=\"disabled\")'''

new_browse = '''        if existing_file_paths or self.energy_files:
            instructions = t("instructions.paths_found_l2", csv_file_path=csv_file_path)
            message = tk.Text(self.inner_frame, wrap=\"word\", width=112, height=4)
            message.grid(row=2, column=0, columnspan=2)
            message.insert(tk.END, instructions)
            message.configure(state=\"disabled\")
            self.message = message

            for file in self.energy_files:
                if file not in existing_file_paths:
                    postselect.append(file)

            full_files = existing_file_paths + postselect
            defualt_selection = len(existing_file_paths)

            self.selected_files = tk.StringVar(value=list(full_files))
            self.file_selection_listbox = tk.Listbox(self.inner_frame, listvariable=self.selected_files,
                                                     selectmode=tk.MULTIPLE, width=150, height=len(full_files))
            self.file_selection_listbox.grid(row=3, column=0, columnspan=2)

            self.file_selection_listbox.selection_set(0, defualt_selection - 1)

            ok_button = tk.Button(self.inner_frame, text=t("btn.ok"), command=self.on_okay)
            ok_button.grid(row=4, column=0)
            self.ok_button = ok_button
        else:
            instructions = t("instructions.no_energy_files_l2")
            message = tk.Text(self.inner_frame, wrap=\"word\", width=112, height=4)
            message.grid(row=2, column=0)
            message.insert(tk.END, instructions)
            message.configure(state=\"disabled\")
            self.message = message'''

register(old_browse, new_browse, 'on_browse')

# 17. Quality_Checks
old_qc = '''class Quality_Checks(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # output table
        self.text_widget = tk.Text(self, wrap=\"none\", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure(\"bold\", font=(\"Helvetica\", 12, \"bold\"))
        self.text_widget.tag_configure(\"pass_row\", foreground=\"green\")
        self.text_widget.tag_configure(\"fail_row\", foreground=\"red\")
        header = \"{:<127}|\".format(\"PM2.5 Quality Control\")
        self.text_widget.insert(tk.END, header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''

new_qc = '''class Quality_Checks(tk.Frame):
    def __init__(self, root, data, units):
        tk.Frame.__init__(self, root)
        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # output table
        self.text_widget = tk.Text(self, wrap=\"none\", height=1, width=75)
        self.text_widget.grid(row=2, column=0, columnspan=3, padx=0, pady=0)

        self.text_widget.tag_configure(\"bold\", font=(\"Helvetica\", 12, \"bold\"))
        self.text_widget.tag_configure(\"pass_row\", foreground=\"green\")
        self.text_widget.tag_configure(\"fail_row\", foreground=\"red\")
        header = \"{:<127}|\".format(t(\"section.pm_quality_control\"))
        self.text_widget.insert(tk.END, header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''

register(old_qc, new_qc, 'quality_checks_top')

old_qc_sec2 = '''        dil_header = \"{:<115}|\".format(\"Dilution Tunnel Quality Control\")
        self.text_widget.insert(tk.END, dil_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
new_qc_sec2 = '''        dil_header = \"{:<115}|\".format(t(\"section.dilution_tunnel_qc\"))
        self.text_widget.insert(tk.END, dil_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
register(old_qc_sec2, new_qc_sec2, 'qc_sec2')

old_qc_sec3 = '''        gas_header = \"{:<115}|\".format(\"Gas Sensor Quality Control\")
        self.text_widget.insert(tk.END, gas_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
new_qc_sec3 = '''        gas_header = \"{:<115}|\".format(t(\"section.gas_sensor_qc\"))
        self.text_widget.insert(tk.END, gas_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
register(old_qc_sec3, new_qc_sec3, 'qc_sec3')

old_qc_sec4 = '''        env_header = \"{:<115}|\".format(\"Environmental Quality Control\")
        self.text_widget.insert(tk.END, env_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
new_qc_sec4 = '''        env_header = \"{:<115}|\".format(t(\"section.environmental_qc\"))
        self.text_widget.insert(tk.END, env_header + \"\\n\" + \"_\" * 68 + \"\\n\", \"bold\")'''
register(old_qc_sec4, new_qc_sec4, 'qc_sec4')

# 18. Quality_Control
old_qctrl = '''class Quality_Control(tk.Frame):
    def __init__(self, root, data, units, names, savefig):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")'''

new_qctrl = '''class Quality_Control(tk.Frame):
    def __init__(self, root, data, units, names, savefig):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")'''
register(old_qctrl, new_qctrl, 'quality_control_exit')

old_qctrl_err = '''        if len(fail) != 0:
            message = 'The following quality control items resulted in numbers outside the accepted range. ' \\
                      'Please follow steps to fix the problem before redoing the test.'
            for f in fail:
                message = message + '\\n' + f
            messagebox.showerror(\"Error\", message)'''

new_qctrl_err = '''        if len(fail) != 0:
            message = t("err.qc.outside_range")
            for f in fail:
                message = message + '\\n' + f
            messagebox.showerror(t("msg.error"), message)'''
register(old_qctrl_err, new_qctrl_err, 'quality_control_err')

# 19. Cut
old_cut_class = '''class Cut(tk.Frame):
    def __init__(self, root, data, units, logs, figpath, times):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_cut_class = '''class Cut(tk.Frame):
    def __init__(self, root, data, units, logs, figpath, times):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_cut_class, new_cut_class, 'cut_class')

old_cut_times = '''        time_message.insert(tk.END, \"Cut Times Used:\")'''
new_cut_times = '''        time_message.insert(tk.END, t("label.cut_times_used"))'''
register(old_cut_times, new_cut_times, 'cut_times')

# 20. Emission_Calcs
old_em_class = '''class Emission_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_em_class = '''class Emission_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_em_class, new_em_class, 'emission_calcs_class')

# 21. BC_Calcs
old_bc_class = '''class BC_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units, pic_list, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_bc_class = '''class BC_Calcs(tk.Frame):
    def __init__(self, root, logs, data, units, pic_list, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_bc_class, new_bc_class, 'bc_calcs_class')

old_bc_instr = '''        instructions = (
            \"Please check each image to verify that the green circle is fully on the filter \"
            \"and there is a white square in each gradient square except for the corners. \"
            \"If these indicators are not properly aligned, the resulting values will not be \"
            \"accurate and the picture should be taken again.\"
        )'''
new_bc_instr = '''        instructions = t(\"instructions.filter_qc\")'''
register(old_bc_instr, new_bc_instr, 'bc_calcs_instructions')

old_bc_lbl = '''                tk.Label(image_frame, text=f\"Filter: {filename}\", font=(\"Helvetica\", 12, \"bold\")).pack(pady=(10, 0))'''
new_bc_lbl = '''                tk.Label(image_frame, text=t(\"label.filter_name\", filename=filename), font=(\"Helvetica\", 12, \"bold\")).pack(pady=(10, 0))'''
register(old_bc_lbl, new_bc_lbl, 'bc_calcs_label')

# 22. Grav_Calcs
old_grav_class = '''class Grav_Calcs(tk.Frame):
    def __init__(self, root, logs, gravval, outval, gravunits, outunits, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_grav_class = '''class Grav_Calcs(tk.Frame):
    def __init__(self, root, logs, gravval, outval, gravunits, outunits, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_grav_class, new_grav_class, 'grav_calcs_class')

# 23. Subtract_Bkg
old_bkg_class = '''class Subtract_Bkg(tk.Frame):
    def __init__(self, root, logs, fig1, fig2, methods, phases, testname, data):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)
        self.advanced_section.grid(row=4, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap=\"word\", height=10, width=65)
        self.logs_text.grid(row=4, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=4, column=3, sticky=\"ns\")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + \"\\n\")

        self.logs_text.configure(state=\"disabled\")

        # Collapsible 'Phases' section for logs
        self.phase_section = CollapsibleFrame(self, text=\"Phase Times\", collapsed=True)
        self.phase_section.grid(row=2, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for phases and add a vertical scrollbar
        self.phase_text = tk.Text(self.phase_section.content_frame, wrap=\"word\", height=10, width=65)
        self.phase_text.grid(row=2, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        phase_scrollbar = tk.Scrollbar(self.phase_section.content_frame, command=self.phase_text.yview)
        phase_scrollbar.grid(row=2, column=3, sticky=\"ns\")

        self.phase_text.config(yscrollcommand=phase_scrollbar.set)

        for key, value in phases.items():
            if 'variable' not in key:
                self.phase_text.insert(tk.END, key + ': ' + value + \"\\n\")

        self.phase_text.configure(state=\"disabled\")

        # Collapsible 'Method' section for logs
        self.method_section = CollapsibleFrame(self, text=\"Subtraction Methods\", collapsed=True)
        self.method_section.grid(row=3, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for phases and add a vertical scrollbar
        self.method_text = tk.Text(self.method_section.content_frame, wrap=\"word\", height=10, width=65)
        self.method_text.grid(row=3, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        method_scrollbar = tk.Scrollbar(self.method_section.content_frame, command=self.method_text.yview)
        method_scrollbar.grid(row=3, column=3, sticky=\"ns\")

        self.method_text.config(yscrollcommand=method_scrollbar.set)

        for key, value in methods.items():
            if 'chan' not in key:
                self.method_text.insert(tk.END, key + ': ' + value + \"\\n\")

        self.method_text.configure(state=\"disabled\")

        # Display images below the Advanced section
        image1 = I.open(fig1)
        image1 = image1.resize((575, 430), I.LANCZOS)
        photo1 = IT.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=5, column=0, padx=10, pady=5, columnspan=3)

        image2 = I.open(fig2)
        image2 = image2.resize((550, 430), I.LANCZOS)
        photo2 = IT.PhotoImage(image2)
        label2 = tk.Label(self, image=photo2, width=575)
        label2.image = photo2  # to prevent garbage collection
        label2.grid(row=5, column=4, padx=10, pady=5, columnspan=3)

        #Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text=\"Warnings\", collapsed=False) #start open'''

new_bkg_class = '''class Subtract_Bkg(tk.Frame):
    def __init__(self, root, logs, fig1, fig2, methods, phases, testname, data):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)
        self.advanced_section.grid(row=4, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap=\"word\", height=10, width=65)
        self.logs_text.grid(row=4, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=4, column=3, sticky=\"ns\")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + \"\\n\")

        self.logs_text.configure(state=\"disabled\")

        # Collapsible 'Phases' section for logs
        self.phase_section = CollapsibleFrame(self, text=t("section.phase_times"), collapsed=True)
        self.phase_section.grid(row=2, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for phases and add a vertical scrollbar
        self.phase_text = tk.Text(self.phase_section.content_frame, wrap=\"word\", height=10, width=65)
        self.phase_text.grid(row=2, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        phase_scrollbar = tk.Scrollbar(self.phase_section.content_frame, command=self.phase_text.yview)
        phase_scrollbar.grid(row=2, column=3, sticky=\"ns\")

        self.phase_text.config(yscrollcommand=phase_scrollbar.set)

        for key, value in phases.items():
            if 'variable' not in key:
                self.phase_text.insert(tk.END, key + ': ' + value + \"\\n\")

        self.phase_text.configure(state=\"disabled\")

        # Collapsible 'Method' section for logs
        self.method_section = CollapsibleFrame(self, text=t("section.subtraction_methods"), collapsed=True)
        self.method_section.grid(row=3, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for phases and add a vertical scrollbar
        self.method_text = tk.Text(self.method_section.content_frame, wrap=\"word\", height=10, width=65)
        self.method_text.grid(row=3, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        method_scrollbar = tk.Scrollbar(self.method_section.content_frame, command=self.method_text.yview)
        method_scrollbar.grid(row=3, column=3, sticky=\"ns\")

        self.method_text.config(yscrollcommand=method_scrollbar.set)

        for key, value in methods.items():
            if 'chan' not in key:
                self.method_text.insert(tk.END, key + ': ' + value + \"\\n\")

        self.method_text.configure(state=\"disabled\")

        # Display images below the Advanced section
        image1 = I.open(fig1)
        image1 = image1.resize((575, 430), I.LANCZOS)
        photo1 = IT.PhotoImage(image1)
        label1 = tk.Label(self, image=photo1, width=575)
        label1.image = photo1  # to prevent garbage collection
        label1.grid(row=5, column=0, padx=10, pady=5, columnspan=3)

        image2 = I.open(fig2)
        image2 = image2.resize((550, 430), I.LANCZOS)
        photo2 = IT.PhotoImage(image2)
        label2 = tk.Label(self, image=photo2, width=575)
        label2.image = photo2  # to prevent garbage collection
        label2.grid(row=5, column=4, padx=10, pady=5, columnspan=3)

        #Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text=t("section.warnings"), collapsed=False) #start open'''
register(old_bkg_class, new_bkg_class, 'bkg_class')

old_bkg_warn1 = '''                            if value < -1.0:
                                self.warning_frame.insert(tk.END, "WARNING:\\n")
                                warning_message = f"{em} for the pre background period is negative. The value should be close to 0.\\n" \\
                                                  f"If this period is being used for background subtraction, this may cause errors.\\n" \\
                                                  f"Zoom in on period in the graph to ensure period looks correct\\n" \\
                                                  f"Ensure the subtraction period is flat\\n" \\
                                                  f"Ensure the sensors were given time to flatline.\\n" \\
                                                  f"If this background period is not suitable, do not use it for subtraction\\n"'''
new_bkg_warn1 = '''                            if value < -1.0:
                                self.warning_frame.insert(tk.END, t("warn.bkg.title"))
                                warning_message = t("warn.bkg.pre_negative", em=em) + "\\n"'''
register(old_bkg_warn1, new_bkg_warn1, 'bkg_warn1')

old_bkg_warn2 = '''                            if value < -1.0:
                                self.warning_frame.insert(tk.END, "WARNING:\\n")
                                warning_message = f"{em} for the post background period is negative. The value should be close too 0.\\n" \\
                                                  f"If this period is being used for background subtraction, this may cause errors.\\n" \\
                                                  f"Zoom in on period in the graph to ensure period looks correct\\n" \\
                                                  f"Ensure the subtraction period is flat\\n" \\
                                                  f"Ensure the sensors were given time to flatline.\\n" \\
                                                  f"If this background period is not suitable, do not use it for subtraction\\n"'''
new_bkg_warn2 = '''                            if value < -1.0:
                                self.warning_frame.insert(tk.END, t("warn.bkg.title"))
                                warning_message = t("warn.bkg.post_negative", em=em) + "\\n"'''
register(old_bkg_warn2, new_bkg_warn2, 'bkg_warn2')

old_bkg_warn3 = '''                            if value > 1.0:
                                self.warning_frame.insert(tk.END, "WARNING:\\n")
                                warning_message = f"{em} for the pre background period is more than 1. The value should be close to 0.\\n" \\
                                                  f"If this period is being used for background subtraction, this may cause errors.\\n" \\
                                                  f"Zoom in on period in the graph to ensure period looks correct\\n" \\
                                                  f"Ensure the subtraction period is flat\\n" \\
                                                  f"Ensure the sensors were given time to flatline.\\n" \\
                                                  f"If this background period is not suitable, do not use it for subtraction\\n"'''
new_bkg_warn3 = '''                            if value > 1.0:
                                self.warning_frame.insert(tk.END, t("warn.bkg.title"))
                                warning_message = t("warn.bkg.pre_high", em=em) + "\\n"'''
register(old_bkg_warn3, new_bkg_warn3, 'bkg_warn3')

old_bkg_warn4 = '''                            if value > 1.0:
                                self.warning_frame.insert(tk.END, "WARNING:\\n")
                                warning_message = f"{em} for the post background period is more than 1. The value should be close too 0.\\n" \\
                                                  f"If this period is being used for background subtraction, this may cause errors.\\n" \\
                                                  f"Zoom in on period in the graph to ensure period looks correct\\n" \\
                                                  f"Ensure the subtraction period is flat\\n" \\
                                                  f"Ensure the sensors were given time to flatline.\\n" \\
                                                  f"If this background period is not suitable, do not use it for subtraction\\n"'''
new_bkg_warn4 = '''                            if value > 1.0:
                                self.warning_frame.insert(tk.END, t("warn.bkg.title"))
                                warning_message = t("warn.bkg.post_high", em=em) + "\\n"'''
register(old_bkg_warn4, new_bkg_warn4, 'bkg_warn4')

# 24. Adjust_Frame
old_adj = '''class Adjust_Frame(tk.Frame):
    def __init__(self, root, logs, firmware, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        #Firmware version
        firm_message = tk.Text(self, wrap=\"word\", height=1, width=80)
        firm_message.grid(row=1, column=0, columnspan=3)
        firm_message.insert(tk.END, f\"Firmware Version Used: {firmware}\")
        firm_message.configure(state=\"disabled\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_adj = '''class Adjust_Frame(tk.Frame):
    def __init__(self, root, logs, firmware, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(410, 5), pady=5, sticky=\"e\")

        #Firmware version
        firm_message = tk.Text(self, wrap=\"word\", height=1, width=80)
        firm_message.grid(row=1, column=0, columnspan=3)
        firm_message.insert(tk.END, t("label.firmware_used", firmware=firmware))
        firm_message.configure(state=\"disabled\")

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_adj, new_adj, 'adjust_frame')

# 25. ISOTable
old_iso_class = '''class ISOTable(tk.Frame):
    def __init__(self, root, data, units, logs):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_iso_class = '''class ISOTable(tk.Frame):
    def __init__(self, root, data, units, logs):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_iso_class, new_iso_class, 'iso_table_class')

# 26. CustomTable
old_custom_tbl = '''        title_lbl = tk.Label(top_bar, text=\"Custom Output Table Generator\", font=(\"Helvetica\", 12, \"bold\"), bg=\"#f5f5f5\")
        title_lbl.pack(side=\"left\", padx=5)

        exit_button = tk.Button(top_bar, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\", font=(\"Helvetica\", 10, \"bold\"))
        exit_button.pack(side=\"right\", padx=5)

        # Left Panel: Variable Selection Controls and Scrollable List
        self.left_panel = tk.Frame(self, width=520)
        self.left_panel.grid(row=1, column=0, sticky=\"nsew\", padx=(10, 5), pady=5)
        self.left_panel.pack_propagate(False)

        # Control Bar: Action Buttons and Selection Counter
        ctrl_frame = tk.Frame(self.left_panel)
        ctrl_frame.pack(fill=\"x\", pady=(0, 4))

        ok_btn = tk.Button(ctrl_frame, text=\"OK / Update Table\", command=self.save, bg=\"#4CAF50\", fg=\"black\", font=(\"Helvetica\", 10, \"bold\"))
        ok_btn.pack(side=\"left\", padx=(0, 4))

        sel_all_btn = tk.Button(ctrl_frame, text=\"Select All\", command=self.select_all)
        sel_all_btn.pack(side=\"left\", padx=2)

        desel_all_btn = tk.Button(ctrl_frame, text=\"Deselect All\", command=self.deselect_all)
        desel_all_btn.pack(side=\"left\", padx=2)

        self.sel_count_lbl = tk.Label(ctrl_frame, text=\"Selected: 0\", font=(\"Helvetica\", 10, \"bold\"), fg=\"#1b5e20\")
        self.sel_count_lbl.pack(side=\"right\", padx=5)

        # Search / Filter Bar
        filter_frame = tk.Frame(self.left_panel)
        filter_frame.pack(fill=\"x\", pady=(2, 4))
        tk.Label(filter_frame, text=\"Filter:\", font=(\"Helvetica\", 10)).pack(side=\"left\", padx=(2, 4))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add(\"write\", self._on_filter_changed)
        self.filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var, font=(\"Helvetica\", 10))
        self.filter_entry.pack(side=\"left\", fill=\"x\", expand=True, padx=(0, 4))
        clear_btn = tk.Button(filter_frame, text=\"Clear\", command=lambda: self.filter_var.set(\"\"), font=(\"Helvetica\", 9))
        clear_btn.pack(side=\"right\")

        # Fixed Header Bar for columns
        hdr_frame = tk.Frame(self.left_panel, bg=\"#e8e8e8\", relief=\"groove\", bd=1)
        hdr_frame.pack(fill=\"x\", pady=(0, 2))
        tk.Label(hdr_frame, text=\"Select\", font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"center\", width=6).grid(row=0, column=0, sticky=\"w\", padx=(6, 4), pady=4)
        tk.Label(hdr_frame, text=\"Variable\", font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"w\").grid(row=0, column=1, sticky=\"w\", padx=(4, 10), pady=4)
        tk.Label(hdr_frame, text=\"Units\", font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"w\").grid(row=0, column=2, sticky=\"w\", padx=(0, 10), pady=4)'''

new_custom_tbl = '''        title_lbl = tk.Label(top_bar, text=t("label.custom_table_generator"), font=(\"Helvetica\", 12, \"bold\"), bg=\"#f5f5f5\")
        title_lbl.pack(side=\"left\", padx=5)

        exit_button = tk.Button(top_bar, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\", font=(\"Helvetica\", 10, \"bold\"))
        exit_button.pack(side=\"right\", padx=5)

        # Left Panel: Variable Selection Controls and Scrollable List
        self.left_panel = tk.Frame(self, width=520)
        self.left_panel.grid(row=1, column=0, sticky=\"nsew\", padx=(10, 5), pady=5)
        self.left_panel.pack_propagate(False)

        # Control Bar: Action Buttons and Selection Counter
        ctrl_frame = tk.Frame(self.left_panel)
        ctrl_frame.pack(fill=\"x\", pady=(0, 4))

        ok_btn = tk.Button(ctrl_frame, text=t("btn.update_table"), command=self.save, bg=\"#4CAF50\", fg=\"black\", font=(\"Helvetica\", 10, \"bold\"))
        ok_btn.pack(side=\"left\", padx=(0, 4))

        sel_all_btn = tk.Button(ctrl_frame, text=t("btn.select_all"), command=self.select_all)
        sel_all_btn.pack(side=\"left\", padx=2)

        desel_all_btn = tk.Button(ctrl_frame, text=t("btn.deselect_all"), command=self.deselect_all)
        desel_all_btn.pack(side=\"left\", padx=2)

        self.sel_count_lbl = tk.Label(ctrl_frame, text=t("label.selected_count", count=0), font=(\"Helvetica\", 10, \"bold\"), fg=\"#1b5e20\")
        self.sel_count_lbl.pack(side=\"right\", padx=5)

        # Search / Filter Bar
        filter_frame = tk.Frame(self.left_panel)
        filter_frame.pack(fill=\"x\", pady=(2, 4))
        tk.Label(filter_frame, text=t("label.filter"), font=(\"Helvetica\", 10)).pack(side=\"left\", padx=(2, 4))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add(\"write\", self._on_filter_changed)
        self.filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var, font=(\"Helvetica\", 10))
        self.filter_entry.pack(side=\"left\", fill=\"x\", expand=True, padx=(0, 4))
        clear_btn = tk.Button(filter_frame, text=t("btn.clear"), command=lambda: self.filter_var.set(\"\"), font=(\"Helvetica\", 9))
        clear_btn.pack(side=\"right\")

        # Fixed Header Bar for columns
        hdr_frame = tk.Frame(self.left_panel, bg=\"#e8e8e8\", relief=\"groove\", bd=1)
        hdr_frame.pack(fill=\"x\", pady=(0, 2))
        tk.Label(hdr_frame, text=t("header.select"), font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"center\", width=6).grid(row=0, column=0, sticky=\"w\", padx=(6, 4), pady=4)
        tk.Label(hdr_frame, text=t("header.variable"), font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"w\").grid(row=0, column=1, sticky=\"w\", padx=(4, 10), pady=4)
        tk.Label(hdr_frame, text=t("header.units"), font=(\"Helvetica\", 10, \"bold\"), bg=\"#e8e8e8\", anchor=\"w\").grid(row=0, column=2, sticky=\"w\", padx=(0, 10), pady=4)'''
register(old_custom_tbl, new_custom_tbl, 'custom_tbl_headers')

old_custom_btm_btn = '''        ok_button_bottom = tk.Button(self.scrollable_frame, text=\"OK / Update Table\", command=self.save, bg=\"#4CAF50\", fg=\"black\", font=(\"Helvetica\", 10, \"bold\"))'''
new_custom_btm_btn = '''        ok_button_bottom = tk.Button(self.scrollable_frame, text=t("btn.update_table"), command=self.save, bg=\"#4CAF50\", fg=\"black\", font=(\"Helvetica\", 10, \"bold\"))'''
register(old_custom_btm_btn, new_custom_btm_btn, 'custom_btm_btn')

old_custom_count = '''    def _update_count(self):
        c = sum(1 for item in self.variable_data if hasattr(item[2], \"get\") and item[2].get() == \"1\")
        if hasattr(self, \"sel_count_lbl\"):
            self.sel_count_lbl.config(text=f\"Selected: {c}\")'''

new_custom_count = '''    def _update_count(self):
        c = sum(1 for item in self.variable_data if hasattr(item[2], \"get\") and item[2].get() == \"1\")
        if hasattr(self, \"sel_count_lbl\"):
            self.sel_count_lbl.config(text=t("label.selected_count", count=c))'''
register(old_custom_count, new_custom_count, 'custom_count')

old_custom_perm = '''        except PermissionError:
            message = f"File: {self.choicepath} is open in another program, close and try again."
            messagebox.showerror("Error", message)
            return'''

new_custom_perm = '''        except PermissionError:
            message = t("err.file.open_permission", path=self.choicepath)
            messagebox.showerror(t("msg.error"), message)
            return'''

register(old_custom_perm, new_custom_perm, 'custom_perm')

# 27. CompareTable
old_cmp_class = '''class CompareTable(tk.Frame):
    def __init__(self, root, data, units, logs):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)'''

new_cmp_class = '''class CompareTable(tk.Frame):
    def __init__(self, root, data, units, logs):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=0, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=0, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)'''
register(old_cmp_class, new_cmp_class, 'compare_table_class')

old_cmp_hdr = '''        header = \"{:<266}|\".format(\"ALL ENERGY OUTPUTS\")'''
new_cmp_hdr = '''        header = \"{:<266}|\".format(t(\"section.all_energy_outputs\"))'''
register(old_cmp_hdr, new_cmp_hdr, 'compare_table_header')

# 28. OutputTable
old_out_class = '''class OutputTable(tk.Frame):
    def __init__(self, root, data, units, logs, num_columns, num_rows, folder_path, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, \"Test Name: \" + testname)
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=\"EXIT\", command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=1, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=\"Find\", command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=\"Advanced\", collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap=\"word\", height=10, width=65)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky=\"ns\")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + \"\\n\")

        # Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text=\"Warnings\", collapsed=False)  # start open'''

new_out_class = '''class OutputTable(tk.Frame):
    def __init__(self, root, data, units, logs, num_columns, num_rows, folder_path, testname):
        tk.Frame.__init__(self, root)

        self.test = tk.Text(self, wrap=\"word\", height=1, width=75)
        self.test.grid(row=0, column=0, padx=0, pady=0, columnspan=3)
        self.test.insert(tk.END, t("label.test_name_header", testname=testname))
        self.test.configure(state=\"disabled\")

        # Exit button
        exit_button = tk.Button(self, text=t("btn.exit"), command=root.quit, bg=\"red\", fg=\"white\")
        exit_button.grid(row=1, column=4, padx=(350, 5), pady=5, sticky=\"e\")

        self.find_entry = tk.Entry(self, width=100)
        self.find_entry.grid(row=1, column=0, padx=0, pady=0, columnspan=3)

        find_button = tk.Button(self, text=t("btn.find"), command=self.find_text)
        find_button.grid(row=1, column=3, padx=0, pady=0)

        # Collapsible 'Advanced' section for logs
        self.advanced_section = CollapsibleFrame(self, text=t("section.advanced"), collapsed=True)
        self.advanced_section.grid(row=2, column=0, pady=0, padx=0, sticky=\"w\")

        # Use a Text widget for logs and add a vertical scrollbar
        self.logs_text = tk.Text(self.advanced_section.content_frame, wrap=\"word\", height=10, width=65)
        self.logs_text.grid(row=2, column=0, padx=10, pady=5, sticky=\"ew\", columnspan=3)

        logs_scrollbar = tk.Scrollbar(self.advanced_section.content_frame, command=self.logs_text.yview)
        logs_scrollbar.grid(row=2, column=3, sticky=\"ns\")

        self.logs_text.config(yscrollcommand=logs_scrollbar.set)

        for log_entry in logs:
            self.logs_text.insert(tk.END, log_entry + \"\\n\")

        # Collapsible Warning section
        self.warning_section = CollapsibleFrame(self, text=t("section.warnings"), collapsed=False)  # start open'''
register(old_out_class, new_out_class, 'output_table_class')

old_out_hdr = '''        header = \"{:<110}|\".format(\"ALL ENERGY OUTPUTS\")'''
new_out_hdr = '''        header = \"{:<110}|\".format(t(\"section.all_energy_outputs\"))'''
register(old_out_hdr, new_out_hdr, 'output_table_hdr')

# 29. Main entry point
old_main = '''if __name__ == "__main__":
    root = tk.Tk()
    version = '5.0'
    root.title("App L2. Version: " + version)
    try:
        root.iconbitmap("ARC-Logo.ico")
    except:
        try:
            root.iconbitmap("C:\\\\Users\\\\Jaden\\\\Documents\\\\GitHub\\\\Data_Processing_aprogit\\\\Data-Processing-Software\\\\LEMS\\\\ARC-Logo.ico")
        except:
            pass
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()'''

new_main = '''if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LEMS Data Entry L2")
    parser.add_argument("--lang", choices=list(i18n.get_available_languages().keys()), default=None, help="Set language")
    args, unknown = parser.parse_known_args()
    if args.lang:
        i18n.set_language(args.lang)

    root = tk.Tk()
    version = '5.0'
    root.title(t("app.title_l2", version=version))
    try:
        root.iconbitmap("ARC-Logo.ico")
    except:
        try:
            root.iconbitmap("C:\\\\Users\\\\Jaden\\\\Documents\\\\GitHub\\\\Data_Processing_aprogit\\\\Data-Processing-Software\\\\LEMS\\\\ARC-Logo.ico")
        except:
            pass
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()'''

register(old_main, new_main, 'main')

# Apply all replacements
new_content = content
for old, new, name in replacements:
    new_content = new_content.replace(old, new, 1)

with open('LEMS_DataEntry_L2.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully applied {len(replacements)} translation replacements to LEMS_DataEntry_L2.py!")
