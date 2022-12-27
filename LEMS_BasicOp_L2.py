


inputpath =['Data/yatzo alcohol/yatzo_test1/yatzo_test1_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test2/yatzo_test2_EnergyOutputs.csv']
outputpath ='Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

import pandas as pd
import LEMS_DataProcessing_IO as io
import csv



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
        test_name = path
        header.append(test_name)

        # load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)


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
    with open(outputpath, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for variable in data_values:
            print(variable)
            writer.writerow([variable, data_values[variable]["units"]] + data_values[variable]["values"])
        csvfile.close()

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_BasicOP_L2(inputpath,outputpath)