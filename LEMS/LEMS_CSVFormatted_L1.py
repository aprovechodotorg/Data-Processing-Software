# v0.2 Python3

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

import LEMS_DataProcessing_IO as io
import csv
import os
from datetime import datetime as dt
import pandas as pd
import subprocess

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_AllOutputs.csv'  # read
outputpath = 'foldername_CustomCutTable.csv'  # write
outputexcel = 'foldername_CustomCutTable.xlsx'  # write
csvpath = 'foldername_CutTableParameters.csv'  # read/write
testname = 'folername'  # write
logger = 'logging Python package'


##################################################


def LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, testname, logger):
    # Function purpose: Created a shortened output table in csv and excel output according to user selection

    # Inputs:
    # Outputs from all calculations in all menu steps
    # Selected metrics to include in cut table (if exists)
    # Python logging function

    # Outputs:
    # csv file of cut table
    # Excel file of cut table
    # csv file of user selected metrics

    # Called by LEMS_DataEntry_L1, LEMS_DataEntry_IDC_L1, LEMS_DataEntry_L2, LEMS_DataEntry_IDC_L2,
    # LEMSDataCruncher_ISO, LEMS_DataCruncher_IDC, LEMSDataCruncher_L2_ISO, LEMSDataCruncher_L2

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

    # load in inputs
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath)
    line = 'Loaded all outputs file: ' + inputpath
    print(line)
    logger.info(line)
    logs.append(line)

    names.remove(names[0])

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
        on.insert(0, 'Included')

        output = zip(var, un, on)  # list of lists to be written switched to columns
        with open(csvpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row in output:
                writer.writerow(row)
        line = 'CSV file of metrics for table created: ' + csvpath
        print(line)
        logger.info(line)
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

    copied_values = []  # Run through names in csvpath csv to see what the user wants in cut table
    var.remove(var[0])
    for name in var:
        if on[name] != '0':
            copied_values.append(name)

    # Populate header
    header = ['Variable', 'units', testname]

    phases = ['_hp', '_mp', '_lp']
    # check if IDC test
    if 'start_time_L1' in names:
        phases.insert(0, '_L1')
    if 'start_time_L5' in names:
        phases.append('_L5')

    output = []
    for name in copied_values:
        row = [name, units[name], values[name]]
        output.append(row)

    # print to the output file
    with open(outputpath, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # add header
        writer.writerow(header)
        writer.writerows(output)

    line = 'Created CSV cut table: ' + outputpath
    print(line)
    logger.info(line)
    logs.append(line)

    # Create dictionary of combined units and values for copied values only
    copied_dict = {}
    for key in copied_values:
        copied_dict[key] = {'values': values[key],
                            'units': units.get(key, "")}

    # Excel writing ##################################
    # convert to pandas dataframe
    df = pd.DataFrame.from_dict(data=copied_dict, orient='index')

    try:
        df = df[['units', 'values']]
    except KeyError:
        pass

    df.name = 'Variable'

    # Create excel writer
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

    # Write excel format
    worksheet.write_string(0, 0, df.name, heading_format)
    df.to_excel(writer, sheet_name='Formatted', startrow=1, startcol=0)
    writer.close()

    line = 'Created Excel cut table: ' + outputexcel
    print(line)
    logger.info(line)
    logs.append(line)

    line = 'To change custom table outputs open: ' + csvpath + ' and edit parameters. Save and rerun menu option.'
    print(line)

    ##############################################
    end_time = dt.now()  # record function execution time
    log = f"Execution time: {end_time - func_start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

########################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, testname, logger)
