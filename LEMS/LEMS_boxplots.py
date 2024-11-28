# v0.0  Python3

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

from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import os
import matplotlib.pyplot as plt
import easygui
import subprocess

# inputs (which files are being pulled and written) #############
inputpath = ['stove1_UnformattedDataL2.csv', 'stove2_UnformattedDataL2.csv']  # read
savefigpath = ['foldename_L3BarChart']  # write
logger = 'logging Python package'


##########################################


def LEMS_boxplots(inputpath, savefigpath, logger):
    # Function purpose: Take in averages data of L2 test outputs and compare through chosen metric

    # Inputs:
    # List of level 2 paths for averages
    # logger: python logging function

    # Outputs:
    # Saved photo of graph
    # logs: list of notebale events

    # Called by LEMS_DataEntry_L3 and LEMSDataCruncher_L3

    logs = []  # list of important events

    # Record start time of script
    func_start_time = dt.now()
    log = f"Started at: {func_start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    # Log script version if available
    try:
        version = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%h", "--", __file__], text=True
        ).strip()
    except subprocess.CalledProcessError:
        version = "unknown_version"
    log = f"Version: {version}"
    print(log)
    logger.info(log)
    logs.append(log)

    header = ['units']  # establish header
    data_values = {}  # nested dictionary. Keys are variable names
    test = []  # list of test names
    units = {}
    names = []  # list of variable names

    x = 0
    for path in inputpath:

        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        # Make a complete list of all variable names from all tests
        for n, name in enumerate(new_names):
            if name not in names:  # If this is a new name, insert it into the ist of names
                names.insert(n, name)
                units[name] = new_units[name]

    for path in inputpath:
        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        line = 'Loaded: ' + path
        print(line)
        logger.info(line)
        logs.append(line)

        if x == 0:  # If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"]],
                                         "High Tier": [data["High Tier"][name]], "Low Tier": [data["Low Tier"][name]],
                                         "COV": [data["COV"][name]], "CI": [data["CI"][name]]}
                except KeyError:
                    data_values[name] = {"units": '', "values": [''], "average": [''], "confidence": [''], "N": [''],
                                         "stdev": [''], "High Tier": [''], "Low Tier": [''], "COV": [''], "CI": ['']}
        else:
            for name in names:  # append values to dictionary
                try:
                    data_values[name]["values"].append(values[name])
                    data_values[name]["average"].append(data["average"][name])
                    data_values[name]["confidence"].append(data["Interval"][name])
                    data_values[name]["N"].append(data["N"][name])
                    data_values[name]["stdev"].append(data["stdev"][name])
                    data_values[name]["High Tier"].append(data["High Tier"][name])
                    data_values[name]["Low Tier"].append(data["Low Tier"][name])
                    data_values[name]["COV"].append(data["COV"][name])
                    data_values[name]["CI"].append(data["CI"][name])
                except KeyError:
                    data_values[name]["values"].append('')
                    data_values[name]["average"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
                    data_values[name]["High Tier"].append('')
                    data_values[name]["Low Tier"].append('')
                    data_values[name]["COV"].append('')
                    data_values[name]["CI"].append('')
        x += 1

    # Ask for a varible to plot
    selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))

    fig, ax = plt.subplots(tight_layout=True)

    # Find variable values of each test
    selected_data = data_values[selected_variable]["values"]
    for odx in range(len(selected_data)):
        for idx in range(len(selected_data[odx])):
            try:
                selected_data[odx][idx] = float(selected_data[odx][idx])
            except ValueError:
                selected_data[odx][idx] = 0

    # Plot individual values
    for i, data_list in enumerate(selected_data):
        num_list = []
        for data in data_list:
            try:
                num_list.append(float(data))
            except ValueError:
                pass
        x_values = [i + 1] * len(num_list)  # x values are 1, 2, 3
        y_values = num_list

        ax.scatter(x_values, y_values, color='blue', s=12)

    # Plot box and whisker plot
    ax.boxplot(selected_data, widths=0.8, showmeans=True,
               meanprops={"marker": 'x', "markeredgecolor": 'black', "markersize": "8"})
    y_label = selected_variable + ' (' + data_values[selected_variable]['units'] + ')'
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlabel('Test Names', fontsize=10)
    ax.set_xticks(range(1, len(test) + 1), test, fontsize=8, rotation=90)
    ax.tick_params(axis='both', which='major', labelsize=8)
    savefigpath = savefigpath + '_' + selected_variable + '.png'
    plt.savefig(savefigpath)
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logger.info(line)
    logs.append(line)

    ##############################################
    end_time = dt.now()  # record function execution time
    log = f"Execution time: {end_time - func_start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    return savefigpath, selected_variable

########################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_boxplots(inputpath, savefigpath, logger)
