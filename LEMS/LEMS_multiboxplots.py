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
import csv
from easygui import choicebox
from LEMS_PairsPlotHelper import (
    format_plot_labels,
    apply_pair_shading,
    ensure_plot_selection_csv,
    load_plot_selection_csv,
    get_y_axis_label,
)
def LEMS_multiboxplots(inputpath, parameterspath, savefigpath, logpath, labels=None, pair_groups=None):
    # labels: optional list of x-axis labels (one per inputpath). Blank/missing entries fall back to folder name.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_multiboxplots v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names


    x = 0
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

        if (x == 0):  # If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"]],
                                         "High Tier": [data["High Tier"][name]], "Low Tier": [data["Low Tier"][name]],
                                         "COV": [data["COV"][name]], "CI": [data["CI"][name]]}
                except:
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
                except:
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

    # Check / create parameters csv
    created = ensure_plot_selection_csv(parameterspath, names)
    if created:
        line = 'Parameter file created: ' + parameterspath
    else:
        line = 'Parameters file already exists: ' + parameterspath
    print(line)
    logs.append(line)

    # Load plot selection and display names (from Name column)
    plotnames, display_names = load_plot_selection_csv(parameterspath)

    #selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    r = 0
    for selected_variable in plotnames:

        selected_data = data_values[selected_variable]["values"]
        for odx in range(len(selected_data)):
            for idx in range(len(selected_data[odx])):
                try:
                    selected_data[odx][idx] = float(selected_data[odx][idx])
                except:
                    selected_data[odx][idx] = 0
        fig, ax = plt.subplots()
        ax.boxplot(selected_data)
        y_label = get_y_axis_label(selected_variable, data_values[selected_variable]['units'], display_names)
        ax.set_ylabel(y_label)
        ax.set_xlabel('Test Names')
        # plt.legend(test)
        if pair_groups:
            display_labels = format_plot_labels(test, max_width=18)
            ax.set_xticks(range(1, len(test) + 1))
            ax.set_xticklabels(display_labels, rotation=45, ha='right')
            apply_pair_shading(ax, pair_groups, x_offset=1, num_tests=len(test))
            plt.subplots_adjust(top=0.90, bottom=0.25)
        else:
            ax.set_xticks(range(1, len(test) + 1))
            ax.set_xticklabels(test, rotation=45, ha='right')
            plt.tight_layout()
        if r == 0:
            savefigpath = savefigpath + '_' + selected_variable + '.png'
            r+=1
        else:
            base, trash = savefigpath.split('Plot', 1) #split at last underscore
            savefigpath = base + 'Plot_' + selected_variable + '.png'
        plt.savefig(savefigpath, bbox_inches='tight')
        plt.show()

        line = 'Saved plot at: ' + savefigpath
        print(line)
        logs.append(line)
        plt.close()

    #print to log file
    io.write_logfile(logpath,logs)
