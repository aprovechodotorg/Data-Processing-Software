




import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os
import math
import statistics
import pandas as pd
import numpy as np

inputpath = ['Data/yatzo alcohol/yatzo_test1/yatzo_test1_EnergyOutputs.csv',
             'Data/yatzo alcohol/yatzo_test2/yatzo_test2_EnergyOutputs.csv',
             'Data/yatzo alcohol/yatzo_test3/yatzo_test3_EnergyOutputs.csv',
             'Data/yatzo alcohol/yatzo_test4/yatzo_test4_EnergyOutputs.csv',
             'Data/yatzo alcohol/yatzo_test5/yatzo_test5_EnergyOutputs.csv']

outputpath = 'Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

testname = ['yatzo_test1', 'yatzo_test2', 'yatzo_test3', 'yatzo_test4', 'yatzo_test5']


def LEMS_BasicOP_L2 (inputpath, outputpath):

    # List of headers
    header = []
    # dictionary of data for each test run
    data_values = {}

    # List of values that will appear in the output
    # Note: Improvment can make this into an excel/txt list that is read in for easy edits
    copied_values = ['time_to_boil',
                     'phase_time',
                     'eff_w_char',
                     'eff_wo_char',
                     'fuel_mass',
                     'burn_rate',
                     'firepower',
                     'cooking_power',
                     'char_energy_productivity',
                     'char_mass_productivity']
    phases = ['_hp', '_mp', '_lp']
    '''
    var_name = ['eff_w_char',
                'eff_wo_char',
                'char_mass_productivity',
                'char_energy_productivity',
                'cooking_power',
                'burn_rate']
    var_units = ['%',
                 '%',
                 '%',
                 '%',
                 'watts',
                 'g/min']
    '''
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

    # Populate header
    header = ['Basic Operation', 'units']

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


        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add headers
        if (x == 0):
            for phase in phases:
                for name in copied_values:
                    name = name + phase
                    #print(name)
                    data_values[name] = {"units": units[name], "values": [values[name]]}
        else:
            for phase in phases:
                for name in copied_values:
                    name = name+phase
                    data_values[name]["values"].append(values[name])
        x += 1
    # Write data values dictionary to output path
    y = 0
    avg = []

    #add headers for comparative data
    header.append('average')
    header.append('N')
    header.append('stdev')

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
            average[variable] = sum(num_list)/len(num_list)
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
            stadev[variable] = statistics.stdev(num_list)
        except:
            stadev[variable] = math.nan
        #Add the standard deviation dictionary to the dictionary
        data_values[variable].update({"stdev" : stadev[variable]})

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
                            + [data_values[variable]["stdev"]])
        csvfile.close()


#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_BasicOP_L2(inputpath,outputpath)