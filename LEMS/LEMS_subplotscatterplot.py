#v0.0  Python3

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
plt.rcParams.update({'font.size': 14}) #set font size
import easygui
import csv
from easygui import choicebox
def LEMS_subplotscatterplot(inputpath, parameterspath, savefigpath, logpath):
    ver = '0.0'
    directory, filename = os.path.split(logpath)
    plt.rcParams['savefig.directory'] = directory

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_boxplots v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names

    # Ask user to select phases
    available_phases = ['L1', 'hp', 'mp', 'lp', 'L5']
    selected_phases = easygui.multchoicebox("Select phases to graph:", "Phase Selection", available_phases)
    if not selected_phases:
        print("No phases selected. Exiting.")
        return


    x = 0
    all_names = set()  # Use a set to automatically handle duplicates
    phase_suffixes = ['_L1', '_hp', '_mp', '_lp', '_L5']
    for path in inputpath:

        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        # Add names to the set, removing phase suffixes
        for name in new_names:
            base_name = name
            for suffix in phase_suffixes:
                if name.endswith(suffix):
                    base_name = name[:-len(suffix)]
                    break
            all_names.add(base_name)

    # Convert set to sorted list for consistent ordering
    names = sorted(list(all_names))

    # Initialize units dictionary with empty strings
    units = {name: '' for name in names}

    # Initialize data_values dictionary
    data_values = {name: {"units": '', "values": [], "average": [], "confidence": [], "N": [],
                          "stdev": [], "High Tier": [], "Low Tier": [], "COV": [], "CI": []} for name in names}

    for path in inputpath:
        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        # Map phase-specific names to base names
        name_mapping = {}
        for name in new_names:
            base_name = name
            for suffix in phase_suffixes:
                if name.endswith(suffix):
                    base_name = name[:-len(suffix)]
                    break
            name_mapping[name] = base_name

        for name in names:
            matching_names = [orig_name for orig_name, base in name_mapping.items() if base == name]
            if matching_names:
                orig_name = matching_names[0]  # Take the first matching name
                units[name] = new_units[orig_name]
                data_values[name]["units"] = new_units[orig_name]
                data_values[name]["values"].append(values[orig_name])
                data_values[name]["average"].append(data["average"][orig_name])
                data_values[name]["confidence"].append(data["Interval"][orig_name])
                data_values[name]["N"].append(data["N"][orig_name])
                data_values[name]["stdev"].append(data["stdev"][orig_name])
                data_values[name]["High Tier"].append(data["High Tier"][orig_name])
                data_values[name]["Low Tier"].append(data["Low Tier"][orig_name])
                data_values[name]["COV"].append(data["COV"][orig_name])
                data_values[name]["CI"].append(data["CI"][orig_name])
            else:
                # If no matching name is found, append empty values
                for key in data_values[name]:
                    if key != "units":
                        data_values[name][key].append('')

        x += 1

    #Check if parameters csv already exists
    if os.path.isfile(parameterspath):
        line = 'Parameters file already exists: ' + parameterspath
        print(line)
        logs.append(line)
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        plottable_vars = []
        for name in names:
            if name not in ['time', 'seconds', 'ID']:  # Don't add these values as plottable variables
                var.append(name)
                plottable_vars.append(name)

        # Use easygui to select variables to plot
        selected_vars = easygui.multchoicebox("Select variables to plot:", "Variable Selection", plottable_vars)

        if selected_vars is None:
            print("No variables selected. Exiting.")
            return

        on = ['Plotted']  # First row is header
        for name in var[1:]:  # Skip the 'Variable' header
            on.append(1 if name in selected_vars else 0)

        output = zip(var, on)  # list of lists to be written switched to columns
        with open(parameterspath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in output:
                writer.writerow(row)

        line = 'Parameter file created: ' + parameterspath
        print(line)
        logs.append(line)

    #load input file
    stuff=[]
    var = []
    on = {}
    with open(parameterspath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    #put inputs in a dictionary
    for row in stuff:
        name = row[0]
        on[name] = row[1]
        var.append(name)

    plotnames = [] #Run through names in plotpath csv to see what the user wants plotted
    var.remove(var[0])
    for name in var:
        if int(on[name]) == 1:
            plotnames.append(name)

    # Create a mapping of base names to their phase-specific versions
    base_to_phase_names = {}
    for full_name in data_values.keys():
        base_name = full_name
        for suffix in phase_suffixes:
            if full_name.endswith(suffix):
                base_name = full_name[:-len(suffix)]
                break
        if base_name not in base_to_phase_names:
            base_to_phase_names[base_name] = []
        base_to_phase_names[base_name].append(full_name)

    # Create subplot structure
    num_rows = len(plotnames)
    num_cols = len(selected_phases)
    fig, axs = plt.subplots(num_rows, num_cols, sharex='col', sharey='row', gridspec_kw={'hspace': 0.0, 'wspace': 0.0})


    fig.set_figheight(15)
    fig.set_figwidth(15)

    for row, variable in enumerate(plotnames):
        for col, phase in enumerate(selected_phases):
            ax = axs[row, col] if num_rows > 1 else axs[col]

            # Find the correct phase-specific name for this variable and phase
            phase_specific_name = next((name for name in base_to_phase_names.get(variable, [])
                                        if name.endswith('_' + phase)), variable)

            if phase_specific_name in data_values:
                selected_data = data_values[phase_specific_name]["values"]

                for odx in range(len(selected_data)):
                    for idx in range(len(selected_data[odx])):
                        try:
                            selected_data[odx][idx] = float(selected_data[odx][idx])
                        except:
                            selected_data[odx][idx] = 0

                for i, data_list in enumerate(selected_data):
                    num_list = []
                    for data in data_list:
                        try:
                            if data != 0:
                                num_list.append(float(data))
                        except:
                            pass
                    x_values = [i + 1] * len(num_list)
                    y_values = num_list

                    ax.scatter(x_values, y_values, color='blue')

                    try:
                        avg_y = sum(y_values) / len(y_values)
                    except:
                        avg_y = 0
                    ax.scatter(i + 1, avg_y, color='red', marker='_', s=1000)

                if col == 0:  # Only set y-label for leftmost column
                    y_label = variable + ' (' + data_values[phase_specific_name]['units'] + ')'
                    ax.set_ylabel(y_label,rotation=85)

                if row == num_rows - 1:  # Only set x-label for bottom row
                    ax.set_xlabel('Test Names')
                    ax.set_xticks(range(1, len(test) + 1))
                    ax.set_xticklabels(test, rotation=45, ha='right')
                else:
                    ax.set_xticklabels([])

                if row == 0:  # Only set title for top row
                    ax.set_title(phase)

                # Set grid lines to match number of tests
                ax.set_xticks(range(1, len(test) + 1))
                ax.grid(True, axis='x', which='major')
                ax.grid(True, axis='y', which='major', alpha=0.5)  # Make horizontal grid lines less prominent

                # Ensure all spines are visible and set to black
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_color('black')

            else:
                ax.text(0.5, 0.5, f"No data for {variable}\nin phase {phase}",
                        ha='center', va='center', transform=ax.transAxes)

            # Ensure all subplots in a column have the same x-axis limits
            if row == 0:
                x_min, x_max = ax.get_xlim()
            else:
                ax.set_xlim(x_min, x_max)

    plt.subplots_adjust(bottom=0.28, top=0.955)

    # Align y-axis labels
    fig.align_ylabels()

    savefigpath = savefigpath
    plt.savefig(savefigpath)
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)
    plt.close()

    #print to log file
    io.write_logfile(logpath,logs)