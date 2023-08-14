#v0.2 Python3

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

# calculates PM mass concentration by gravimetric method
# inputs gravimetric filter weights
# determines which test phases and which flow trains by reading which variable names are present in the grav input file
# inputs phase times input file to calculate phase time length
# outputs filter net mass, flow, duration, and concentration for each phase
# outputs report to terminal and log file

import LEMS_DataProcessing_IO as io
import csv
import os
from datetime import datetime as dt

def LEMS_CSVFormatted_L1(inputpath, outputpath, csvpath, testname, logpath):
    #function takes in file and creates/reads csv file of wanted outputs and creates shortened output list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_CSVFormatted_L1 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #load in inputs
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath)
    line = 'loaded processed data file without = names, units: ' + inputpath
    print(line)
    logs.append(line)

    names.remove(names[0])

    #add some parameters that can be in cut table (averages over all phases)
    averaged_values = ['eff_w_char',
                       'eff_wo_char',
                       'char_mass_productivity',
                       'char_energy_productivity',
                       'cooking_power',
                       'burn_rate',
                       'CO_useful_eng_deliver',
                       'CO2_useful_eng_deliver',
                       'CO_mass_time',
                       'CO2_mass_time',
                       'PM_mass_time',
                       'PM_heat_mass_time']

    for name in averaged_values:
        names.append(name)
        phase_name = name + '_hp'
        try:
            units[name] = units[phase_name]
        except:
            units[name] = ''

    # Check if plot csv already exists
    if os.path.isfile(csvpath):
        line = 'CSV file already exists: ' + csvpath
        print(line)
        logs.append(line)
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        un = ['Units']
        for name in names:  # create new names list with header that won't interfere with other calcs later
            var.append(name)
            un.append(units[name])
        on = [0] * len(var)  # Create a row to specify if that value is being plotted default is off (0)
        on[0] = 'Included'

        output = zip(var, un, on)  # list of lists to be written switched to columns
        with open(csvpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row in output:
                writer.writerow(row)
        line = 'CSV file created: ' + csvpath
        print(line)
        logs.append(line)

    var = []
    on = {}

    # load csv input file
    stuff = []
    with open(csvpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # put inputs in a dictionary
    for row in stuff:
        name = row[0]
        on[name] = row[2]
        var.append(name)

    copied_values = [] #Run through names in csvpath csv to see what the user wants in cut table
    var.remove(var[0])
    for name in var:
        if on[name] != '0':
            copied_values.append(name)

    # Populate header
    header = ['Variable', 'units']
    header.append(testname)

    phases = ['_hp', '_mp', '_lp']
    #check if IDC test
    if 'start_time_L1' in names:
        phases.insert(0, '_L1')
    if 'start_time_L5' in names:
        phases.append('_L5')

    for each in averaged_values:
        #some math will need to be done for averaged values
        if each in copied_values:
            # add name and unit to dictionary for calculation
            name = each
            names.append(name)

            sum_list = []
            for phase in phases:
                try:
                    sum_list.append(float(values[each + phase]))
                except:
                    pass

            # find the averages of all the phases
            total = sum(sum_list)
            try:
                cal = round((total / len(sum_list)), 3)
            except:
                cal = ''
            values[name] = cal

    output = []
    for name in copied_values:
        row = []
        row.append(name)
        row.append(units[name])
        row.append(values[name])
        output.append(row)

        # print to the output file
    with open(outputpath, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # add header
        writer.writerow(header)
        writer.writerows(output)

    line = 'Custom table created: ' + outputpath
    print(line)
    logs.append(line)
    line = 'To change custom table outputs open: ' + csvpath + ' and edit parameters. Save and rerun menu option.'
    print(line)

