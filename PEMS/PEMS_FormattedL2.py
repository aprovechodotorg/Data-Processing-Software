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

import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os
import math
import statistics
from scipy import stats
import json

def PEMS_FormattedL2(inputpath, outputpath, outputexcel):
    #dictionary of data for each test run
    data_values = {}

    #CHANGE START HERE
    trial = {} # to try out keeping track of data for each test
    #CHANGE END HERE

    #List of values that will appear in the output
    #Note: Improvment can make this into an excel/txt list that is read in for easy edits
    copied_values = ['seconds',
                     'TC2',
                     'EFenergy_CO',
                     'EFenergy_CO2',
                     'EFenergy_PM',
                     'ER_PM_heat',
                     'ER_CO',
                     'ER_CO2',
                     'PM_flowrate']

    '''
    #example of dictionary setup. Dictionary contains dictionaries with names, units, and val list.
    data_values = {
        "variable_name": {
            "units" : "example unit",
            "values" : [1,2,3,4]
        }
        "variable_name": {
            "units" : "example unit",
            "values" : [1,2,3,4]
        }
        "variable_name": {
            "units" : "example unit",
            "values" : [1,2,3,4]
        }
    }
    '''

    # load in input file one for checking if IDC tet
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath[0])
    if 'CO_test' in names: #check if this is a cut test or full test
        phase_values = []
        for name in copied_values:
            phase_name = name + '_test'
            phase_values.append(phase_name)
        copied_values = phase_values
        # Populate header
        header = ['Cut Period', 'units']
    else:
        # Populate header
        header = ['Full Period', 'units']

    x = 0
    # Run through all tests entered
    testname_list = []
    for path in inputpath:
        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        testname_list.append(testname)

        # load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)
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
    # Write data values dictionary to output path
    y = 0
    avg = []

    # add headers for comparative data
    header.append('average')
    header.append('N')
    header.append('stdev')
    header.append('interval')
    header.append("high_tier")
    header.append("low_tier")
    header.append("COV")
    header.append("CI")

    #Loop through each variable
    for variable in data_values:
        num_list = []

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
            average[variable] = math.nan

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
            stadev[variable] = math.nan
        # Add the standard deviation dictionary to the dictionary
        data_values[variable].update({"stdev": stadev[variable]})

        try:
            # t-statistic
            # p<0.1, 2-tail, n-1
            interval[variable] = ((stats.t.ppf(1 - 0.05, (N[variable] - 1))))
            # * stadev[variable] / N[variable] ^ 0.5)
            interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
        except:
            interval[variable] = math.nan

        # Add the t-statistic dictionary to the dictionary
        data_values[variable].update({"interval": interval[variable]})

        high_tier[variable] = round((average[variable] + interval[variable]), 3)
        low_tier[variable] = round((average[variable] - interval[variable]), 3)

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)

        data_values[variable].update({"COV": COV[variable]})

        CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})

    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        #Reprint header to specify section (really you just need the section title but having the other column callouts
        #repeated makes it easier to read
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

    df = pd.DataFrame.from_dict(data=data_values, orient = 'index')

    # Rearrange columns to align with the provided header
    df = df[['units', 'values', 'average', 'N', 'stdev', 'interval', 'high_tier', 'low_tier', 'COV', 'CI']]

    # Add the 'Full Period' column to the DataFrame
    #df['Full Period'] = df['values'].apply(', '.join)

    #for name in testname_list:
    df2 = pd.DataFrame(df['values'].tolist(), columns = testname_list)
    df2.index = copied_values
    # Drop the 'values' column since it's no longer needed
    df = df.drop(columns='values')

    for name in testname_list:
        col = df2[name]
        df = df.join(col)

    # Transpose the DataFrame to have '3.21.23', '3.22.23', '3.23.23' as columns
    #df = df.T

    # Reorder the columns according to the header
    header.remove(header[0])
    df = df[header]

    # Write DataFrame to Excel file
    df.to_excel(outputexcel, index_label='Data', sheet_name='Sheet1')