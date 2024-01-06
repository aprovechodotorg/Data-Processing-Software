import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import LEMS_DataProcessing_IO as io
import os
import csv


class LEMSDataInput(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        #scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

        #create test info section
        self.test_info = TestInfoFrame(self.frame, "Test Info")
        self.test_info.grid(row=1, column=0, columnspan=2)

        # File Path Entry
        tk.Label(self.frame, text="Select Folder:").grid(row=0, column=0)
        self.folder_path_var = tk.StringVar()
        self.folder_path = tk.Entry(self.frame, textvariable=self.folder_path_var)
        self.folder_path.grid(row=0, column=1)

        browse_button = tk.Button(self.frame, text="Browse", command=self.on_browse)
        browse_button.grid(row=0, column=2)

        # OK button
        ok_button = tk.Button(self.frame, text="OK", command=self.on_okay)
        ok_button.anchor()
        ok_button.grid(row=2, column=0)

        self.pack(side=tk.TOP, expand=True)

    def on_okay(self):
        # for each frame, check inputs
        float_errors = []
        blank_errors = []

        float_errors, blank_errors = self.test_info.check_input_validity(float_errors, blank_errors)

        # If errors, generate prompt, else, save to file
        if float_errors or blank_errors:
            # Error
            print("Errors")
        else:
            # Save to CSV
            print("No Errors")

    def on_browse(self):
        self.folder_path = filedialog.askdirectory()
        self.folder_path_var.set(self.folder_path)

        # Check if _EnergyInputs.csv file exists
        file_name = f"{os.path.basename(self.folder_path)}_EnergyInputs.csv"
        file_path = os.path.join(self.folder_path, file_name)
        [names,units,data,unc,uval] = io.load_constant_inputs(file_path)
        data.pop("variable_name")
        data = self.test_info.check_imported_data(data)

        if data:
            self.extra_test_inputs = ExtraTestInputsFrame(self.frame, "Additional Test Inputs", data)
            self.extra_test_inputs.grid(row=3, column=0, columnspan=2)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class TestInfoFrame(tk.LabelFrame):
    def __init__(self, root, text):
        super().__init__(root, text=text, padx=10, pady=10)
        self.testinfo = ['test_name', 'test_number', 'data', 'name_of_tester', 'location', 'stove_type/model']
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

class ExtraTestInputsFrame(tk.LabelFrame):
    def __init__(self, root, text, new_vars: dict):
        super().__init__(root, text=text, padx=10, pady=10)
        self.entered_test_info = {}
        for i, name in enumerate(new_vars):
            tk.Label(self, text=f"{name.capitalize().replace('_', ' ')}:").grid(row=i, column=0)
            self.entered_test_info[name] = tk.Entry(self, text=new_vars[name])
            self.entered_test_info[name].insert(0, new_vars[name])
            self.entered_test_info[name].grid(row=i, column=2)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test App")
    root.geometry('480x360')

    window = LEMSDataInput(root)
    window.mainloop()
