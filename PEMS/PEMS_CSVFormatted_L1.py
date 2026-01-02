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
#adds stack outputs

import PEMS_DataProcessing_IO as io
import csv
import os
from datetime import datetime as dt
import pandas as pd

def PEMS_CSVFormatted_L1(energyinputpath, emissioninputpath, stackinputpath, outputpath, outputexcel, csvpath, testname, logpath):
    #function takes in file and creates/reads csv file of wanted outputs and creates shortened output list.
    ver = '0.1'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CSVFormatted_L1 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #load in inputs
    [enames, eunits, evalues, eunc, euval] = io.load_constant_inputs(energyinputpath)
    line = 'loaded processed data file without = names, units: ' + energyinputpath
    print(line)
    logs.append(line)

    enames.remove(enames[0])

    [emnames, emunits, emvalues, emunc, emuval] = io.load_constant_inputs(emissioninputpath)
    line = 'loaded processed data file without = names, units: ' + emissioninputpath
    print(line)
    logs.append(line)

    emnames.remove(emnames[0])

    [stnames, stunits, stvalues, stunc, stuval] = io.load_constant_inputs(stackinputpath)
    line = 'loaded processed data file without = names, units: ' + stackinputpath
    print(line)
    logs.append(line)

    stnames.remove(stnames[0])

    #Create lists/dictionaries of combined emissions and energy output variables
    names = []
    units = {}

    for name in enames:
        names.append(name)
        units[name] = eunits[name]
    for name in emnames:
        names.append(name)
        units[name] = emunits[name]
    for name in stnames:
        names.append(name)
        units[name] = stunits[name]

    # Check if plot csv already exists
    if os.path.isfile(csvpath):
        line = 'CSV file already exists: ' + csvpath
        print(line)
        logs.append(line)
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        un = ['Units']
        for name in enames:  # create new names list with header that won't interfere with other calcs later
            var.append(name)
            un.append(eunits[name])
        for name in emnames:
            var.append(name)
            un.append(emunits[name])
        for name in stnames:
            var.append(name)
            un.append(stunits[name])
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

    output = []
    for name in copied_values:
        if name in enames:
            row = []
            row.append(name)
            row.append(eunits[name])
            row.append(evalues[name])
            output.append(row)
        elif name in emnames:
            row = []
            row.append(name)
            row.append(emunits[name])
            row.append(emvalues[name])
            output.append(row)
        elif name in stnames:
            row = []
            row.append(name)
            row.append(stunits[name])
            row.append(stvalues[name])
            output.append(row)


        # print to the output file
    with open(outputpath, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # add header
        writer.writerow(header)
        writer.writerows(output)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    #Create dictionary of combined units and values for copied values only
    copied_dict = {}
    for key in copied_values:
        if key in enames:
            copied_dict[key] = {'values': evalues[key],
                                'units': eunits.get(key, "")}
        elif key in emnames:
            copied_dict[key] = {'values': emvalues[key],
                                'units': emunits.get(key, "")}
        elif key in stnames:
            copied_dict[key] = {'values': stvalues[key],
                                'units': stunits.get(key, "")}

    #convert to pandas dataframe
    df = pd.DataFrame.from_dict(data=copied_dict, orient='index')

    try:
        df = df[['units', 'values']]
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
    writer._save()

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
