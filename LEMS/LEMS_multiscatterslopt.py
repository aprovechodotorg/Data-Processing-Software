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
def LEMS_multiscaterplots(inputpath, parameterspath, savefigpath, logpath):
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

    #Check if parameters csv already exists
    if os.path.isfile(parameterspath):
        line = 'Parameters file already exists: ' + parameterspath
        print(line)
        logs.append(line)
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        for name in names: #create new names list with header that won't interfere with other calcs later
            if name != 'time' and name != 'seconds' and name != 'ID': #Don't add these values as plottable variables
                var.append(name)
        on = [0] * len(var) #Create a row to specify if that value is being plotted default is off (0)
        on[0] = 'Plotted'

        output = zip(var, on) #list of lists to be written switched to columns
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

    #selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    r = 0
    for selected_variable in plotnames:

        fig, ax = plt.subplots()

        selected_data = data_values[selected_variable]["values"]
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
            x_values = [i+1] * len(num_list) #x values are 1, 2, 3
            y_values = num_list

            ax.scatter(x_values, y_values, color='blue')

            try:
                avg_y = sum(y_values) / len(y_values)
            except:
                avg_y = 0
            ax.scatter(i+1, avg_y, color='red', marker='_', s=1000)

        y_label = selected_variable + ' (' + data_values[selected_variable]['units'] + ')'
        ax.set_ylabel(y_label)
        ax.set_xlabel('Test Names')

        #set x-ticks to be test names
        ax.set_xticks(range(1, len(test) + 1))
        ax.set_xticklabels(test)
        #plt.legend(test)
        plt.xticks(range(1, len(test) + 1), test)
        plt.xticks(rotation=45, ha='right')
        # Adjust bottom padding
        plt.subplots_adjust(bottom=0.4)  # You can adjust the value as needed
        plt.subplots_adjust(top=1)  # You can adjust the value as needed
        plt.subplots_adjust(left=0.03)  # You can adjust the value as needed
        plt.subplots_adjust(right=1)  # You can adjust the value as needed
        plt.grid()

        if r == 0:
            savefigpath = savefigpath + '_' + selected_variable + '.png'
            r+=1
        else:
            base, trash = savefigpath.split('Plot', 1) #split at last underscore
            savefigpath = base + 'Plot_' + selected_variable + '.png'
        plt.savefig(savefigpath, format="png", bbox_inches="tight")
        plt.show()

        line = 'Saved plot at: ' + savefigpath
        print(line)
        logs.append(line)
        plt.close()


    #print to log file
    io.write_logfile(logpath,logs)
