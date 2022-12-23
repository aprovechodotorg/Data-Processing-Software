inputpath =['Data/yatzo alcohol/yatzo_test1/yatzo_test1_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test2/yatzo_test2_EnergyOutputs.csv']
outputpath ='Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

import pandas as pd
import LEMS_DataProcessing_IO as io
import csv

def process_files(inputpath,outputpath):

    #List of headers
    header = []
    #dictionary of data for each test run
    data_values = {}

    #List of values that will appear in the output
    #Note: Improvment can make this into an excel/txt list that is read in for easy edits
    copied_values = ['thermal_efficiency_w_char',
                     'thermal_efficiency_wo_char',
                     'char_mass_productivity',
                     'char_energy_productivity',
                     'avg_cooking_power',
                     'burning_rate']

    phases = ['_hp', '_mp', '_lp']

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

    #Populate header
    header = ['variable name', 'units']

    x=0
    #Run through all tests entered
    for path in inputpath:
        #Pull each test name/number. Add to header
        test_name = path
        header.append(test_name)

        #load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)

        ###########################################
        # Run calculations
        t = 0
        for each in copied_values:
            name = each
            names.append(name)
            units[name] = var_units[t]

            try:
                cal = (((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                        +(float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                        +(float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                        / float(values['weight_total']))
            except:
                cal = ''

            values[name] = cal
            t += 1
        print(values)
        '''
        #thermal efficiency. Pull values from energyoutput, calculate results
        name = 'thermal_efficiency_w_char'
        names.append(name)
        units[name] = '%'
        #Set up function to handle when value cells are blank
        try:
            TE_w = (((float(values['eff_w_char_hp']) * float(values['weight_hp']))
                    + (float(values['eff_w_char_mp']) * float(values['weight_mp']))
                    + (float(values['eff_w_char_lp']) * float(values['weight_lp'])))
                    / float(values['weight_total']))
        except:
            TE_w = ''
        values[name] = TE_w

        name = 'thermal_efficiency_wo_char'
        names.append(name)
        units[name] = '%'

        # Set up function to handle when value cells are blank
        try:
            TE_wo = (((float(values['eff_wo_char_hp']) * float(values['weight_hp']))
                     + (float(values['eff_wo_char_mp']) * float(values['weight_mp']))
                     + (float(values['eff_wo_char_lp']) * float(values['weight_lp'])))
                     / float(values['weight_total']))
        except:
            TE_wo = ''

        values[name] = TE_wo

        #char mass productivity
        name = 'char_mass_productivity'
        names.append(name)
        units[name] = '%'
        try:
            CM = (((float(values['char_mass_productivity_hp']) * float(values['weight_hp']))
                  + (float(values['char_mass_productivity_mp']) * float(values['weight_mp']))
                  + (float(values['char_mass_productivity_lp']) * float(values['weight_lp'])))
                  / float(values['weight_total']))
        except:

            CM = ''
        values[name] = CM

        #char energy productivity
        name = 'char_energy_productivity'
        names.append(name)
        units[name] = '%'

        # Set up function to handle when value cells are blank
        try:
            CE = (((float(values['char_energy_productivity_hp']) * float(values['weight_hp']))
                  + (float(values['char_energy_productivity_mp']) * float(values['weight_mp']))
                  + (float(values['char_energy_productivity_lp']) * float(values['weight_lp'])))
                  / float(values['weight_total']))
        except:
            CE = ''

        values[name] = CE

        #Average cooking power
        name = 'avg_cooking_power'
        names.append(name)
        units[name] = 'watts'
        try:
            ACP = (((float(values['cooking_power_hp']) * float(values['weight_hp']))
                    + (float(values['cooking_power_mp']) * float(values['weight_mp']))
                    + (float(values['cooking_power_lp']) * float(values['weight_lp'])))
                    / float(values['weight_total']))
        except:
            ACP = ''

        values[name] = ACP
        '''
        if (x == 0):
            for name in copied_values:
                print(name)
                data_values[name] = {"units" : units[name], "values" : [values[name]]}
        else:
            for name in copied_values:
                data_values[name]["values"].append(values[name])
        x += 1

    print(header)
    print(data_values)
    with open(outputpath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for variable in data_values:
            print(variable)
            writer.writerow([variable, data_values[variable]["units"]] + data_values[variable]["values"])
        csvfile.close()
#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    process_files(inputpath,outputpath)