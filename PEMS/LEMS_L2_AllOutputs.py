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
import json
import pandas as pd
import numpy as np
from datetime import datetime as dt

def LEMS_L2_AllOutputs(energyinputpath, outputpath, logpath):
    #Function intakes list of inputpaths and creates comparission between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_L2_AllOutputs v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]
    #################################################

    ############################################################
    #ENERGY OUTPUTS
    # List of headers
    header = []
    # dictionary of data for each Unit Tests run
    data_values = {}

    header = ['Energy Outputs', 'units']

    x = 0
    # Run through all tests entered
    for path in energyinputpath:
        # Pull each Unit Tests name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)

        # load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)

        line = 'loaded: ' + path
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
            for name in names:
                data_values[name] = {"units": units[name], "values": [values[name]]}
        else:
                for name in names:
                    data_values[name]["values"].append(values[name])
        x += 1

    #add headers for comparative data
    header.append('average')
    header.append('N')
    header.append('stdev')
    header.append('Interval')
    header.append("High Tier Estimate")
    header.append("Low Tier Estimate")
    header.append("COV")
    header.append("CI")

    # Loop through each variable
    for variable in data_values:
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

        #Add high and low tier estimates
        high_tier[variable] = round((average[variable] + interval[variable]), 3)
        low_tier[variable] = round((average[variable] - interval[variable]), 3)

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        #Add COV
        try:
            COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
        except:
            COV[variable] = math.nan

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

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)
