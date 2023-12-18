import tkinter as tk
from tkinter import filedialog
import sys
import easygui
import os
import LEMS_DataProcessing_IO as io
from PEMS_EnergyCalcs import PEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from PEMS_SubtractBkg import PEMS_SubtractBkg
from PEMS_GravCalcs import PEMS_GravCalcs
from PEMS_CarbonBalanceCalcs import PEMS_CarbonBalanceCalcs
from PEMS_Plotter1 import PEMS_Plotter
from PEMS_Realtime import PEMS_Realtime
from PEMS_FuelExactCuts import PEMS_FuelExactCuts
from PEMS_FuelCuts import PEMS_FuelCuts
from PEMS_FuelScript import PEMS_FuelScript
from PEMS_2041 import PEMS_2041
import traceback
from PEMS_SubtractBkgPitot import PEMS_SubtractBkgPitot
from PEMS_StackFlowCalcs import PEMS_StackFlowCalcs
from PEMS_StackFlowMetricCalcs import PEMS_StackFlowMetricCalcs
from PEMS_MultiCutPeriods import PEMS_MultiCutPeriods
from turtle import shape
import pandas as pd
import numpy as np
import glob
from csv import reader
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import PEMS_FuelCalcs
import itertools
from decimal import *
import itertools
from itertools import chain
from io import StringIO
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PEMSDataCruncherGUI:
    def __init__(self, master, funs):
        self.master = master
        self.funs = funs
        self.file_path_var = tk.StringVar()

        master.title("PEMS Data Cruncher GUI")

        # Entry for file path
        self.file_entry = tk.Entry(master, textvariable=self.file_path_var, width=40)
        self.file_entry.grid(row=0, column=0, padx=10, pady=10)

        # Browse button
        self.browse_button = tk.Button(master, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=0, column=1, padx=10, pady=10)

        # Output display
        self.output_text = tk.Text(master, height=10, width=50)
        self.output_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Menu option buttons
        self.menu_buttons = []
        for i, fun in enumerate(self.funs, start=1):
            button = tk.Button(master, text=f"Option {i}: {fun}", command=lambda opt=i: self.run_option(opt))
            button.grid(row=i + 1, column=0, columnspan=2, padx=10, pady=5)
            self.menu_buttons.append(button)

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        self.file_path_var.set(file_path)

    def run_option(self, option):
        file_path = self.file_path_var.get()
        if not file_path:
            self.display_output("Please provide a file path.")
            return

        try:
            # Update donelist based on the selected option
            if option == 1:
                # Replace the code here with the functionality of option 1
                self.plot_graph()
            elif option == 2:
                # Replace the code here with the functionality of option 2
                pass
            elif option == 3:
                # Replace the code here with the functionality of option 3
                pass
            # Add more conditions for other options as needed

            # Display success message and change button color to green
            self.display_output(f"Option {option} completed successfully.")
            self.menu_buttons[option - 1].config(bg='green')
        except Exception as e:
            # Display error message and change button color to red
            self.display_output(f"Error in option {option}: {e}")
            self.menu_buttons[option - 1].config(bg='red')

    def display_output(self, output):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, output)

    def plot_graph(self):
        # Replace this with the actual code for plotting using Matplotlib
        # Example plot: a simple line plot
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]

        fig, ax = plt.subplots()
        ax.plot(x_values, y_values)
        ax.set_title("Sample Matplotlib Graph")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")

        # Embed the Matplotlib plot in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.master)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=1, column=0, columnspan=2, padx=10, pady=10)


if __name__ == "__main__":
    funs = ['plot raw data', 'calculate fuel metrics', 'calculate energy metrics', 'adjust sensor calibrations',
            'correct for response times', 'subtract background', 'calculate gravimetric PM',
            'calculate emission metrics', 'zero pitot tube', 'calculate stack flow',
            'calculate stack flow metrics', 'perform realtime calculations (one cut period)',
            'perform realtime calculations (multiple cut periods)', 'plot processed data',
            'plot processed data for averaging period only']

    root = tk.Tk()
    app = PEMSDataCruncherGUI(root, funs)
    root.mainloop()
