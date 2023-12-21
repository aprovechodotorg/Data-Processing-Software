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
import numpy as np
def LEMS_comparativebarcharts(inputpath, savefigpath, logpath):
    ver = '0.0'

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

        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        if (x == 0):  # If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "uncertainty": [data["uncertainty"][name]],
                                         "confidence": [data["Interval"][name]], "N": [data["N"][name]],
                                         "stdev": [data["stdev"]], "High Tier": [data["High Tier"][name]],
                                         "Low Tier": [data["Low Tier"][name]], "COV": [data["COV"][name]],
                                         "CI": [data["CI"][name]]}
                except:
                    data_values[name] = {"units": '', "values": [''], "average": [''],"uncertainty": [''],
                                         "confidence": [''], "N": [''], "stdev": [''], "High Tier": [''],
                                         "Low Tier": [''], "COV": [''], "CI": ['']}
        else:
            for name in names:  # append values to dictionary
                try:
                    data_values[name]["values"].append(values[name])
                    data_values[name]["average"].append(data["average"][name])
                    data_values[name]["uncertainty"].append(data["uncertainty"][name])
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
                    data_values[name]["uncertainty"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
                    data_values[name]["High Tier"].append('')
                    data_values[name]["Low Tier"].append('')
                    data_values[name]["COV"].append('')
                    data_values[name]["CI"].append('')
        x += 1
    selected_variable = easygui.multchoicebox("Select multiple variables to compare", choices=list(data_values.keys()))

    fig, ax = plt.subplots(tight_layout=True)

    select_num = len(selected_variable)
    number = len(data_values[selected_variable[0]]["average"])
    ind = np.arange(number)
    width = 0.8 / select_num
    count = 1
    for variable in selected_variable:
        selected_data = data_values[variable]["average"]
        confidence = data_values[variable]["confidence"]
        uncertainty = data_values[variable]["uncertainty"]

        for odx in range(len(selected_data)):
            try:
                if variable == 'Firepower':
                    selected_data[odx] = float(selected_data[odx])/1000
                else:
                    selected_data[odx] = float(selected_data[odx])
            except:
                selected_data[odx] = 0

        for odx in range(len(confidence)):
            try:
                confidence[odx] = float(confidence[odx])
            except:
                confidence[odx] = 0

        for odx in range(len(uncertainty)):
            try:
                if variable == 'Firepower':
                    uncertainty[odx] = float(uncertainty[odx])/1000
                else:
                    uncertainty[odx] = float(uncertainty[odx])
            except:
                uncertainty[odx] = 0

        error = []
        for n, con in enumerate(confidence):
            try:
                error.append(uncertainty[n])
            except:
                error.append(con)
        ax.bar(ind, selected_data, yerr=error, width=width, capsize=5, label=variable)

        ind = ind + (width * count)
        count += 1

    y_label = ''
    for variable in selected_variable:
        y_label = y_label + ' (' + variable + ' ' + data_values[variable]['units'] + ')'
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlabel('Test Names', fontsize=10)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis='both', which='major', labelsize=10)
    #ax.set_xticklabels(test, fontsize=10)
    ax.legend(fontsize=10, bbox_to_anchor=(1, 0.5), loc='upper right')
    #plt.legend(test)
    ax.set_xticks(range(0, len(test)), test)
    var_str = '_'
    for variable in selected_variable:
        var_str = var_str + variable
    savefigpath = savefigpath + '_' + var_str +'.png'
    plt.savefig(savefigpath)
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)