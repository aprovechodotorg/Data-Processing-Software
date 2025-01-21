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
# determines which Unit Tests phases and which flow trains by reading which variable names are present in the grav input file
# inputs phase times input file to calculate phase time length
# outputs filter net mass, flow, duration, and concentration for each phase
# outputs report to terminal and log file


import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os
import math
import statistics
from scipy import stats
from datetime import datetime as dt

def PEMS_CSVFormatted_L2(energyinputpath, emissioninputpath, outputpath, outputexcel, csvpath, logpath):
    #Function intakes list of inputpaths and creates comparission between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CSVFormatted_L2 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #load in inputs
    [enames, eunits, evalues, eunc, euval] = io.load_constant_inputs(energyinputpath[0])
    line = 'loaded processed data file without = names, units: ' + energyinputpath[0]
    print(line)
    logs.append(line)

    enames.remove(enames[0])

    [emnames, emunits, emvalues, emunc, emuval] = io.load_constant_inputs(emissioninputpath[0])
    line = 'loaded processed data file without = names, units: ' + emissioninputpath[0]
    print(line)
    logs.append(line)

    emnames.remove(emnames[0])

    #Create lists/dictionaries of combined emissions and energy output variables
    names = []
    units = {}

    for name in enames:
        names.append(name)
        units[name] = eunits[name]
    for name in emnames:
        names.append(name)
        units[name] = emunits[name]

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

    # dictionary of data for each Unit Tests run
    data_values = {}

    # Populate header
    header = ['variable', 'units']
    testname_list = []

    x = 0
    y = 0
    # Run through all tests entered
    for n, path in enumerate(energyinputpath):
        # Pull each Unit Tests name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        testname_list.append(testname)

        # load in inputs from each energyoutput file
        [enames, eunits, evalues, eunc, euval] = io.load_constant_inputs(path)

        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        try:
            # load in inputs from each emissionoutput file
            [emnames, emunits, emvalues, emunc, emuval] = io.load_constant_inputs(emissioninputpath[n])
            q = 1
        except:
            q = 0

        line = 'loaded: ' + emissioninputpath[0]
        print(line)
        logs.append(line)

        # Add dictionaries for additional columns of comparative data
        average = {}
        N = {}
        stadev = {}
        interval = {}
        high_tier = {}
        low_tier = {}
        COV = {}
        CI = {}

        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add headers
        if (x == 0):
            for name in enames:
                data_values[name] = {"units": eunits[name], "values": [evalues[name]]}
        else:
                for name in enames:
                    data_values[name]["values"].append(evalues[name])
        x += 1

        if y == 0 and q == 1:
            for name in emnames:
                data_values[name] = {"units": emunits[name], "values": [emvalues[name]]}
        else:
                for name in emnames:
                    data_values[name]["values"].append(emvalues[name])
        y += 1

    #add headers for comparative data
    header.append('average')
    header.append('N')
    header.append('stdev')
    header.append('interval')
    header.append("high_tier")
    header.append("low_tier")
    header.append("COV")
    header.append("CI")

    # Loop through each variable
    for variable in copied_values:
        num_list = []

        # Loop through each value for the variable.
        # This loop is needed to sort through data entries that are blank and ignore them instead of throwing errors
        for value in data_values[variable]["values"]:
            # p = 0

            # If the vaule is blank, do nothing
            if value == '':
                pass
            # Otherwise, the value is a number, add it to list of values that have numbers
            # Note: Could add to if loop to sort out str values right now those throw errors although there may not be str values
            else:
                try:
                    num_list.append(float(value))
                except:
                    pass

        # Try averaging the list of numbered values
        try:
            average[variable] = round(sum(num_list) / len(num_list), 3)
        except:
            average[variable] = ''

        # Add the average dictionary to the dictionary
        data_values[variable].update({"average": average[variable]})

        # Count the number of tests done for this value
        N[variable] = len(num_list)
        # Add the count dictionary to the dictionary
        data_values[variable].update({"N": N[variable]})

        try:
            # Standard deviation of numbered values
            stadev[variable] = round(statistics.stdev(num_list), 3)
        except:
            stadev[variable] = ''
        # Add the standard deviation dictionary to the dictionary
        data_values[variable].update({"stdev": stadev[variable]})

        try:
            # t-statistic
            # p<0.1, 2-tail, n-1
            interval[variable] = ((stats.t.ppf(1 - 0.05, (N[variable] - 1))))
            interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
        except:
            interval[variable] = ''

        # Add the t-statistic dictionary to the dictionary
        data_values[variable].update({"interval": interval[variable]})

        #Add high and low tier estimates
        try:
            high_tier[variable] = round((average[variable] + interval[variable]), 3)
            low_tier[variable] = round((average[variable] - interval[variable]), 3)
        except:
            high_tier[variable] = ''
            low_tier[variable] = ''

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        #Add COV
        try:
            COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
        except:
            COV[variable] = ''

        data_values[variable].update({"COV": COV[variable]})

        #Add confidence interval
        CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})

    # Create new file with outputs
    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Reprint header to specify section (really you just need the section title but having the other column callouts
        # repeated makes it easier to read
        writer.writerow(header)
        # Write units, values, and comparative data for all varaibles in all tests
        for variable in copied_values:
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

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    #drop keys not in copied values
    copied_dict = {key: data_values[key] for key in copied_values if key in data_values}

    #convert to pandas dataframe
    df = pd.DataFrame.from_dict(data=copied_dict, orient='index')

    try:
        # Rearrange columns to align with the provided header
        df = df[['units', 'values', 'average', 'N', 'stdev', 'interval', 'high_tier', 'low_tier', 'COV', 'CI']]
        #create second dataframe to format values list
        df2 = pd.DataFrame(df['values'].tolist(), columns=testname_list)
        df2.index = copied_values
        df = df.drop(columns='values') #drop the values column from first dataframe

        for name in testname_list:
            col = df2[name]
            try:
                col = col.astype(float).round(3)
            except:
                pass
            df[name] = col

        #reorder the columns according to the header
        header.remove(header[0])
        df = df[header]

    except:
        pass

    df.name = 'Variable'

    writer = pd.ExcelWriter(outputexcel, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Formatted')
    worksheet.set_column(0, 0, 30) #adjust width of first column
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

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
