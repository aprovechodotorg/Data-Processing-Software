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
import statistics
from scipy import stats
import pandas as pd
import subprocess

# inputs (which files are being pulled and written) #############
inputpath = ['foldername1_AllOutputs.csv', 'foldername2_AllOutputs.csv']  # read
outputpath = 'foldername_CustomCutTable_L2.csv'  # write
outputexcel = 'foldername_CustomCutTable_L2.xlsx'  # write
csvpath = 'foldername_CutTableParameters.csv'  # read/write
logger = 'logging Python package'
##################################################################


def LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logger):
    # Function purpose: Created a shortened output table in csv and excel output according to user selection for all
    # tests in level 2 analysis and gives statistics between test values

    # Inputs:
    # List of paths to outputs from all calculations in all menu steps
    # Selected metrics to include in cut table (if exists)
    # Python logging function

    # Outputs:
    # csv file of cut table
    # Excel file of cut table
    # csv file of user selected metrics

    # Called by LEMS_DataEntry_L2, LEMS_DataEntry_IDC_L2,
    # LEMSDataCruncher_L2_ISO, LEMSDataCruncher_L2

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
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath[0])
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
        for path in inputpath:
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)
            # make a complete list of all variable names from all tests
            for n, name in enumerate(new_names):
                units[name] = new_units[name]
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        un = ['Units']

        for path in inputpath:
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

            # make a complete list of all variable names from all tests
            for n, name in enumerate(new_names):
                if name not in var:  # If this is a new name, insert it into the list of names
                    var.insert(n, name)
                    un.insert(n, new_units[name])
                    units[name] = new_units[name]
        on = [0] * len(var)  # Create a row to specify if that value is being plotted default is off (0)
        on.insert(0, 'Included')

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

    copied_values = []  # Run through names in csvpath csv to see what the user wants in cut table
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
        [names, new_units, values, unc, uval] = io.load_constant_inputs(path)

        phases = ['_hp', '_mp', '_lp']

        # load in first input file to check if IDC
        [pnames, punits, pvalues, punc, puval] = io.load_constant_inputs(inputpath[0])
        if 'start_time_L1' in pnames:
            phases.insert(0, '_L1')
        if 'start_time_L5' in pnames:
            phases.append('_L5')

        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add dictionary
        if x == 0:
            for name in copied_values:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]]}
                except KeyError:
                    try:
                        data_values[name] = {"units": units[name], "values": ['']}
                    except KeyError:
                        data_values[name] = {"units": '', "values": ['']}
        else:
            for name in copied_values:
                try:
                    data_values[name]["values"].append(values[name])
                except KeyError:
                    data_values[name]["values"].append('')
        x += 1

    # Add headers for additional columns of comparative data
    header.append("average")
    header.append("N")
    header.append("stdev")
    header.append("interval")
    header.append("high_tier")
    header.append("low_tier")
    header.append("COV")
    header.append("CI")

    # Add dictionaries for additional columns of comparative data
    average = {}
    N = {}
    stadev = {}
    interval = {}
    high_tier = {}
    low_tier = {}
    COV = {}
    CI = {}

    # loop through each variable the user selected
    for variable in copied_values:
        num_list = []

        # Loop through each value for the variable.
        # This loop is needed to sort through data entries that are blank and ignore them instead of throwing errors
        for value in data_values[variable]["values"]:
            # If the vaule is blank, do nothing (error is a throw away variable)
            if value == '':
                pass
            # Otherwise, the value is a number, add it to list of values that have numbers
            # Note: Could add to if loop to sort out str values right now those throw errors although there may not
            # be str values
            else:
                try:
                    num_list.append(float(value))
                except ValueError:
                    num_list.append(value)

        # Try averaging the list of numbered values
        try:
            average[variable] = round(sum(num_list) / len(num_list), 3)

        # If the list of number values is blank (you try dividing by 0) make average nan
        except ZeroDivisionError:
            average[variable] = ''

        # Update dictionary to add average dictionary
        data_values[variable].update({"average": average[variable]})

        # Count the number of tests done for this value
        N[variable] = len(num_list)
        # Add the count dictionary to the dictionary
        data_values[variable].update({"N": N[variable]})

        try:
            # Standard deviation of numbered values
            stadev[variable] = round(statistics.stdev(num_list), 3)
        except (statistics.StatisticsError, TypeError):
            stadev[variable] = ''

        # Add the standard deviation dictionary to the dictionary
        data_values[variable].update({"stdev": stadev[variable]})

        # t-statistic
        # p<0.1, 2-tail, n-1
        try:
            interval[variable] = (stats.t.ppf(1 - 0.05, (N[variable] - 1)))
            interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
        except (KeyError, ValueError, ZeroDivisionError, TypeError):
            interval[variable] = ''

        # Add the t-statistic dictionary to the dictionary
        data_values[variable].update({"interval": interval[variable]})

        try:
            high_tier[variable] = round((average[variable] + interval[variable]), 3)
            low_tier[variable] = round((average[variable] - interval[variable]), 3)
        except (ValueError, TypeError):
            high_tier[variable] = ''
            low_tier[variable] = ''

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        try:
            COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
            data_values[variable].update({"COV": COV[variable]})
        except (ValueError, TypeError, ZeroDivisionError):
            COV[variable] = ''
            data_values[variable].update({"COV": COV[variable]})

        CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})

    # Write data values dictionary to output path
    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Add the header to the outputfile
        writer.writerow(header)
        # Write units, values, and comparative data for all varaibles in all tests
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

    line = 'Created CSV cut table: ' + outputpath
    print(line)
    logger.info(line)
    logs.append(line)

    # Write Excel file #########################################3
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
            except ValueError:
                pass
            df[name] = col  # join to origional dataframe

        # reorder the columns according to the header
        header.remove(header[0])
        df = df[header]
    except KeyError:
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

    # Write to excel
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

    return data_values, units

########################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logger)
