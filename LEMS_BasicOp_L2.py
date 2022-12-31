




import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os
import math
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
        average = {}


        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add headers
        if (x == 0):
            for phase in phases:
                for name in copied_values:
                    name = name + phase
                    print(name)
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
    header.append('average')

    for variable in data_values:

        for value in data_values[variable]["values"]:
            print(value + 'test')
            if value == '':
                values[variable] = value
                data_values[variable]["values"].append(values[variable])
                print('done')
        print(variable)
        print(data_values[variable]["values"])
        total = float(sum(data_values[variable]["values"]))
        print(total)

        try:
            average[variable] = float((sum(data_values[variable]["values"]))) / (len(data_values[variable]["values"]))
            avg.append(average[variable])

        except:
            average[variable] = 'error'
            avg.append(average[variable])
        data_values[variable].update({"average": average[variable]})
        y += 1
        print(data_values[variable])
    with open(outputpath, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for variable in data_values:
            writer.writerow([variable, data_values[variable]["units"]] + data_values[variable]["values"] + [data_values[variable]["average"]])
        csvfile.close()


#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_BasicOP_L2(inputpath,outputpath)