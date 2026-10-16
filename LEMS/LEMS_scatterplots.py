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
import easygui
from easygui import choicebox
from LEMS_PairsPlotHelper import (
    format_plot_labels,
    apply_pair_shading,
    extract_individual_test_names,
    attach_hover_labels,
    merge_lp_cut_data_for_group,
)
def LEMS_scatterplots(inputpath, savefigpath, logpath, labels=None, pair_groups=None, lp_inputpath=None):
    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(logpath)
    plt.rcParams['savefig.directory'] = directory

    ver = '0.1'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_scatterplots v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names


    x = 0
    individual_test_names = []
    for i, path in enumerate(inputpath):

        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        if labels is not None and i < len(labels) and str(labels[i]).strip():
            testname = str(labels[i]).strip()
        header.append(testname)
        test.append(testname)

        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)
        individual_test_names.append(extract_individual_test_names(new_names, values))

        # Merge LP cut data from Step 21 if present
        merge_lp_cut_data_for_group(path, new_names, new_units, values, data, lp_inputpath=lp_inputpath, logs=None)

        # Make a complete list of all variable names from all tests
        for n, name in enumerate(new_names):
            if name not in names:  # If this is a new name, insert it into the ist of names
                names.insert(n, name)
                units[name] = new_units[name]

    for path in inputpath:
        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        # Merge LP cut data from Step 21 if present
        merge_lp_cut_data_for_group(path, new_names, new_units, values, data, lp_inputpath=lp_inputpath, logs=logs)

        if (x == 0):  # If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"][name]],
                                         "High Tier": [data["High Tier"][name]], "Low Tier": [data["Low Tier"][name]],
                                         "COV": [data["COV"][name]], "CI": [data["CI"][name]]}
                except:
                    data_values[name] = {"units": units.get(name, ''), "values": [['']], "average": [''], "confidence": [''], "N": [''],
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
                except:
                    data_values[name]["values"].append([''])
                    data_values[name]["average"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
                    data_values[name]["High Tier"].append('')
                    data_values[name]["Low Tier"].append('')
                    data_values[name]["COV"].append('')
                    data_values[name]["CI"].append('')
        x += 1
    selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    if selected_variable is None:
        line = 'Variable selection cancelled by user.'
        print(line)
        logs.append(line)
        io.write_logfile(logpath, logs)
        return

    selected_data = data_values[selected_variable]["values"]
    for odx in range(len(selected_data)):
        for idx in range(len(selected_data[odx])):
            try:
                selected_data[odx][idx] = float(selected_data[odx][idx])
            except:
                selected_data[odx][idx] = 0

    fig, ax = plt.subplots(figsize=(8.27, 11.69)) # width height, inches
    hover_items = []
    unit_str = data_values[selected_variable].get('units', '')
    for i, data_list in enumerate(selected_data):
        num_list = []
        point_labels = []
        g_names = individual_test_names[i] if i < len(individual_test_names) else []
        for j, data in enumerate(data_list):
            if data != 0 and str(data).strip().lower() not in ('nan', ''):
                try:
                    val_float = float(data)
                    num_list.append(val_float)
                    t_name = g_names[j] if j < len(g_names) else f"Test {j + 1}"
                    point_labels.append((t_name, val_float))
                except:
                    pass
        x_values = [i+1] * len(num_list) #x values are 1, 2, 3
        y_values = num_list

        if num_list:
            sc = ax.scatter(x_values, y_values, color='blue')
            hover_items.append((sc, point_labels, unit_str))
            try:
                avg_y = sum(y_values) / len(y_values)
            except:
                avg_y = 0
            sc_avg = ax.scatter(i+1, avg_y, color='red', marker='_', s=1000)
            group_name = test[i] if i < len(test) else f"Group {i + 1}"
            hover_items.append((sc_avg, [(f"{group_name} Average", avg_y)], unit_str))

    # TODO: Map selected_variable to a display name for y-axis label (e.g. from PlotSelection.csv or shared lookup)
    y_label = selected_variable + ' (' + data_values[selected_variable]['units'] + ')'
    ax.set_ylabel(y_label)
    ax.set_xlabel('Test Names')

    #set x-ticks to be test names
    if pair_groups:
        display_labels = format_plot_labels(test, max_width=18)
        ax.set_xticks(range(1, len(test) + 1))
        ax.set_xticklabels(display_labels, rotation=45, ha='right')
        apply_pair_shading(ax, pair_groups, x_offset=1, num_tests=len(test))
        plt.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.95)
    else:
        ax.set_xticks(range(1, len(test) + 1))
        ax.set_xticklabels(test, rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.4, top=1, left=0.03, right=1)
    plt.grid(axis='y', alpha=0.5)

    attach_hover_labels(fig, hover_items)

    savefigpath = savefigpath + '_' + selected_variable +'.png'
    #plt.savefig(savefigpath)
    plt.savefig(savefigpath, format="png", bbox_inches="tight")
    plt.show()


    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)

    return savefigpath, selected_variable
