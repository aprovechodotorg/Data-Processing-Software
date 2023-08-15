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
import statistics
from scipy import stats
import pandas as pd

def LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logpath):
    #function takes in files and creates/reads csv file of wanted outputs and creates shortened output list comparing inputs.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_CSVFormatted_L2 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #load in inputs
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath[0])
    line = 'loaded processed data file without = names, units: ' + inputpath[0]
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

    # dictionary of data for each test run
    data_values = {}

    # Populate header
    header = ['variable', 'units']
    testname_list = []

    x = 0
    # Run through all tests entered
    for path in inputpath:
        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        testname_list.append(testname)

        # load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)

        phases = ['_hp', '_mp', '_lp']

        # load in first input file to check if IDC
        [pnames, punits, pvalues, punc, puval] = io.load_constant_inputs(inputpath[0])
        if 'start_time_L1' in pnames:
            phases.insert(0, '_L1')
        if 'start_time_L5' in pnames:
            phases.append('_L5')

        # Add dictionaries for additional columns of comparative data
        average = {}
        N = {}
        stadev = {}
        interval = {}
        high_tier = {}
        low_tier = {}
        COV = {}
        CI = {}

        for each in averaged_values:
            # some math will need to be done for averaged values
            if each in copied_values:
                # add name and unit to dictionary for calculation
                name = each
                names.append(name)
                try:
                    units[name] = units[name + '_hp']
                except:
                    units[name] = ''

                sum_list = []
                for phase in phases:
                    try:
                        val = float(values[name + phase])
                        sum_list.append(val)
                    except:
                        pass

                total = sum(sum_list)
                try:
                    cal = round((total / len(sum_list)), 3)
                except:
                    cal = ''

                values[name] = cal

        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add dictionary
        if (x == 0):
            for name in copied_values:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]]}
                except:
                    data_values[name] = {"units": '', "values": ['']}
        else:
            for name in copied_values:
                try:
                    data_values[name]["values"].append(values[name])
                except:
                    data_values[name]["values"].append('')
        x += 1

    #Add headers for additional columns of comparative data
    header.append("average")
    header.append("N")
    header.append("stdev")
    header.append("interval")
    header.append("high_tier")
    header.append("low_tier")
    header.append("COV")
    header.append("CI")


    #loop through each variable the user selected
    for variable in copied_values:
        num_list = []

        #Loop through each value for the variable.
        #This loop is needed to sort through data entries that are blank and ignore them instead of throwing errors
        for value in data_values[variable]["values"]:
            #If the vaule is blank, do nothing (error is a throw away variable)
            if value == '':
                error = 1
            #Otherwise, the value is a number, add it to list of values that have numbers
            #Note: Could add to if loop to sort out str values right now those throw errors although there may not be str values
            else:
                try:
                    num_list.append(float(value))
                except:
                    num_list.append(value)

        #Try averaging the list of numbered values
        try:
            average[variable] = round(sum(num_list)/len(num_list), 3)

        #If the list of number values is blank (you try dividing by 0) make average nan
        except:
            average[variable] = ''

        #Update dictionary to add average dictionary
        data_values[variable].update({"average": average[variable]})

        #Count the number of tests done for this value
        N[variable] = len(num_list)
        #Add the count dictionary to the dictionary
        data_values[variable].update({"N" : N[variable]})

        try:
            #Standard deviation of numbered values
            stadev[variable] = round(statistics.stdev(num_list), 3)
        except:
            stadev[variable] = ''

        #Add the standard deviation dictionary to the dictionary
        data_values[variable].update({"stdev" : stadev[variable]})

        #t-statistic
        #p<0.1, 2-tail, n-1
        try:
            interval[variable] = ((stats.t.ppf(1-0.05, (N[variable] - 1))))
            interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
        except:
            interval[variable] = ''

        #Add the t-statistic dictionary to the dictionary
        data_values[variable].update({"interval": interval[variable]})

        try:
            high_tier[variable] = round((average[variable] + interval[variable]), 3)
            low_tier[variable] = round((average[variable] - interval[variable]), 3)
        except:
            high_tier[variable] = ''
            low_tier[variable] = ''

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        try:
            COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
            data_values[variable].update({"COV": COV[variable]})
        except:
            COV[variable] = ''
            data_values[variable].update({"COV": COV[variable]})


        CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})

    #Write data values dictionary to output path
    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        #Add the header to the outputfile
        writer.writerow(header)
        #Write units, values, and comparative data for all varaibles in all tests
        for variable in data_values:
            writer.writerow([variable, data_values[variable]["units"]]
                            + data_values[variable]["values"]
                            + [data_values[variable]["average"]]
                            + [data_values[variable]["N"]]
                            + [data_values[variable]["stdev"]]
                            + [data_values[variable]["interval"]]
                            + [data_values[variable]["high_tier"]]
                            + [data_values[variable]["low_tier"]]
                            + [data_values[variable]["COV"]]
                            + [data_values[variable]["CI"]])
        csvfile.close()

    # drop keys not in copied values
    copied_dict = {key: data_values[key] for key in copied_values if key in data_values}

    # convert to pandas dataframe
    df = pd.DataFrame.from_dict(data=copied_dict, orient='index')

    try:
        # Rearrange columns to align with the provided header
        df = df[['units', 'values', 'average', 'N', 'stdev', 'interval', 'high_tier', 'low_tier', 'COV', 'CI']]

        # create second dataframe to format values list
        df2 = pd.DataFrame(df['values'].tolist(), columns=testname_list)
        df2.index = copied_values
        df = df.drop(columns='values')  # drop the values column from first dataframe

        for name in testname_list:
            col = df2[name]
            try:
                col = col.astype(float).round(3)
            except:
                pass
            df[name] = col #join to origional dataframe

        # reorder the columns according to the header
        header.remove(header[0])
        df = df[header]
    except:
        pass

    df.name = 'Variable'

    writer = pd.ExcelWriter(outputexcel, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Formatted')
    worksheet.set_column(0, 0, 30)  # adjust width of first column
    writer.sheets['Formatted'] = worksheet

    # Create a cell format with heading font
    heading_format = writer.book.add_format({
        'bold': True,
        'font_name': 'Arial',  # Customize the font name as needed
        'font_size': 12,  # Customize the font size as needed
        'align': 'center',  # Center-align the text
        'valign': 'vcenter'  # Vertically center-align the text
    })

    worksheet.write_string(0, 0, df.name, heading_format)
    df.to_excel(writer, sheet_name='Formatted', startrow=1, startcol=0)
    writer.save()

    line = 'created: ' + outputexcel
    print(line)
    logs.append(line)

    line = 'Custom table created: ' + outputpath
    print(line)
    logs.append(line)
    line = 'To change custom table outputs open: ' + csvpath + ' and edit parameters. Save and rerun menu option.'
    print(line)