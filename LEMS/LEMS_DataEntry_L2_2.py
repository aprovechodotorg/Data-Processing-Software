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
        self.notebook = ttk.Notebook(height=3000)
        self.notebook.grid(row=4, column=0)
        for folder in self.energy_files:
            try:
                output_path = folder.replace('EnergyInputs.csv', 'EnergyOutputs.csv')
                log_path = folder.replace('EnergyInputs.csv', 'log.txt')
                [trail, units, data, logs] = LEMS_EnergyCalcs(folder, output_path, log_path)
                tab = ttk.Frame(self.notebook)
                tab.grid(row=0, column=0)
                self.notebook.add(tab, text=os.path.basename(os.path.dirname(folder)))
                #self.notebookframe = tk.Frame(tab, background="#ffffff")
                #self.notebookframe.grid(row=0, column=0)
                # Exit button
                exit_button = tk.Button(tab, text="EXIT", command=root.quit, bg="red", fg="white")
                exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

                self.text_widget = tk.Text(tab, wrap="none", height=30, width=72)
                self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

                # Configure a tag for bold text
                self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))

                header = "{:<110}|".format("ALL ENERGY OUTPUTS")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
                header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
                self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

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
                self.text_widget.config(height=tot_rows*200)
                self.text_widget.configure(state="disabled")
                #self.notebookframe.config(height=tot_rows)
                #self.notebook.config(height=tot_rows)
                #tab.config(height=tot_rows)

            except PermissionError:
                error.append(folder)

        if error:
            message = f"One or more files are open in another program. Close them and try again."
            # Error
            messagebox.showerror("Error", message)

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

class OutputTable(tk.Frame):
    def __init__(self, root, data, units, logs):
        tk.Frame.__init__(self, root)

        # Exit button
        exit_button = tk.Button(self, text="EXIT", command=root.quit, bg="red", fg="white")
        exit_button.grid(row=0, column=4, padx=(350, 5), pady=5, sticky="e")

        self.text_widget = tk.Text(self, wrap="none", height=72, width=72)
        self.text_widget.grid(row=3, column=0, columnspan=3, padx=0, pady=0)

        # Configure a tag for bold text
        self.text_widget.tag_configure("bold", font=("Helvetica", 12, "bold"))

        header = "{:<110}|".format("ALL ENERGY OUTPUTS")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")
        header = "{:<64} | {:<31} | {:<18} |".format("Variable", "Value", "Units")
        self.text_widget.insert(tk.END, header + "\n" + "_" * 63 + "\n", "bold")

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

        self.text_widget.config(height=tot_rows)
        self.text_widget.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App L2")
    root.geometry('1200x600')  # Adjust the width to a larger value

    window = LEMSDataCruncher_L2(root)
    window.grid(row=0, column=0, columnspan=12, sticky="nsew")  # Set columnspan to 8 and sticky to "nsew"

    root.grid_rowconfigure(0, weight=1)  # Allow row 0 to grow with the window width
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to grow with the window height

    root.mainloop()