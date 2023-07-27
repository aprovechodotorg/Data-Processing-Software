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

def LEMS_Emissions_L2(inputpath, outputpath):

    # List of headers
    header = []
    # dictionary of data for each test run
    data_values = {}

    header = ['Total Emissions', 'units']

    copied_values = ['MCE',
                     'CO_total_mass',
                     'CO2_total_mass',
                     'PM_total_mass',
                     'PM_heat_mass_time']

    phases = ['_hp', '_mp', '_lp']

    # load in first input file to check if IDC
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath[0])
    if 'CO_L1' in names:
        phases.insert(0, '_L1')

    realpaths = []
    for path in inputpath:

        if os.path.isfile(path): #check if emissions paths are real
            realpaths.append(path)
        else:
            line = 'Emissions path: ' + path + ' does not exist and will not be compared'
            print(line)

    inputpath = realpaths

    if len(inputpath) != 0: #only run code if the list of real emissions paths has one or more entries
        x = 0
        # Run through all tests entered
        for path in inputpath:
            # Pull each test name/number. Add to header
            directory, filename = os.path.split(path)
            datadirectory, testname = os.path.split(directory)
            header.append(testname)

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
                for phase in phases:
                    for name in copied_values:
                        name = name + phase
                        #print(name)
                        try:
                            data_values[name] = {"units": units[name], "values": [values[name]]}
                        except:
                            data_values[name] = {"units": '', "values": ['']}
            else:
                for phase in phases:
                    for name in copied_values:
                        name = name+phase
                        try:
                            data_values[name]["values"].append(values[name])
                        except:
                            data_values[name]["values"].append('')
            x += 1

        # Write data values dictionary to output path
        y = 0
        avg = []

        #add headers for comparative data
        header.append('average')
        header.append('N')
        header.append('stdev')
        header.append('Interval')
        header.append("High Tier Estimate")
        header.append("Low Tier Estimate")
        header.append("COV")
        header.append("CI")

        #print(data_values)

        #Loop through each variable
        for variable in data_values:
            num_list = []

            # Loop through each value for the variable.
            # This loop is needed to sort through data entries that are blank and ignore them instead of throwing errors
            for value in data_values[variable]["values"]:
                #p = 0

                # If the vaule is blank, do nothing (error is a throw away variable)
                if value == '':

                    #print(p)
                    #data_values[variable]["values"[p]] = 0
                    #data_values[variable]["values"].append(values[variable])
                    error = 1
                    #p += 1

                # Otherwise, the value is a number, add it to list of values that have numbers
                # Note: Could add to if loop to sort out str values right now those throw errors although there may not be str values
                else:
                    num_list.append(float(value))
                    #p += 1

            #print(num_list)
            #print(data_values[variable]["values"])

            #Try averaging the list of numbered values
            try:
                average[variable] = round(sum(num_list)/len(num_list), 3)
                #avg.append(average[variable])

            except:
                average[variable] = math.nan
                #avg.append(average[variable])

            #Add the average dictionary to the dictionary
            data_values[variable].update({"average": average[variable]})

            #Count the number of tests done for this value
            N[variable] = len(num_list)
            #Add the count dictionary to the dictionary
            data_values[variable].update({"N" : N[variable]})

            try:
                #Standard deviation of numbered values
                stadev[variable] = round(statistics.stdev(num_list), 3)
            except:
                stadev[variable] = math.nan
            #Add the standard deviation dictionary to the dictionary
            data_values[variable].update({"stdev" : stadev[variable]})

            try:
                #t-statistic
                #p<0.1, 2-tail, n-1
                interval[variable] = ((stats.t.ppf(1-0.05, (N[variable] - 1))))
                              # * stadev[variable] / N[variable] ^ 0.5)
                interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
            except:
                interval[variable] = math.nan

            #Add the t-statistic dictionary to the dictionary
            data_values[variable].update({"interval" : interval[variable]})

            high_tier[variable] = round((average[variable] + interval[variable]), 3)
            low_tier[variable] = round((average[variable] - interval[variable]), 3)

            data_values[variable].update({"high_tier": high_tier[variable]})
            data_values[variable].update({"low_tier": low_tier[variable]})

            try:
                COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
            except:
                COV[variable] = math.nan

            data_values[variable].update({"COV": COV[variable]})

            CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
            data_values[variable].update({"CI": CI[variable]})

            #y += 1
            #print(data_values[variable])
        #Open existing output and append values to it. This will not overwrite previous values
        with open(outputpath, 'a', newline='') as csvfile:
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
