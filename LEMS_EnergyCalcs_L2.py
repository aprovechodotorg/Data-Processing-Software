




import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os

################################
inputpath =['Data/yatzo alcohol/yatzo_test1/yatzo_test1_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test2/yatzo_test2_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test3/yatzo_test3_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test4/yatzo_test4_EnergyOutputs.csv',
            'Data/yatzo alcohol/yatzo_test5/yatzo_test5_EnergyOutputs.csv']

outputpath ='Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

testname = ['yatzo_test1', 'yatzo_test2', 'yatzo_test3', 'yatzo_test4', 'yatzo_test5']
###############################

def LEMS_EnergyCalcs_L2(inputpath,outputpath):

    print(outputpath)
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
    header = ['ISO Performance Metrics (Weighted Mean)', 'units']

    x=0
    #Run through all tests entered
    for path in inputpath:
        #Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)

        #load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)

        ###########################################
        # Run calculations
        #All calcs have the same formula so loops through formula for each value that will be calculated
        t = 0
        for each in copied_values:


            #Add name and unit of calculation to dictionary
            name = each
            names.append(name)
            units[name] = var_units[t]
            print(values['weight_total'])

            if float(values['weight_total']) == 3:
                try:
                    #Run through formula. If any value cells are blank, leave value cell blank
                        cal = (((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                                +(float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                                +(float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                / float(values['weight_total']))
                except:
                    cal = ''

            elif values['weight_total'] == 2:
                try:
                    cal = (((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                            +(float(values[var_name[t] + '_mp']) * float(values['weight_mp'])))
                            / float(values['weight_total']))
                    try:
                        cal = (((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                                + (float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                / float(values['weight_total']))
                        try:
                            cal = ((+ (float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                                    + (float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                   / float(values['weight_total']))
                        except:
                            cal = ''
                    except:
                        cal = ''
                except:
                    cal = ''
            elif values['weight_total'] == 1:
                try:
                    cal = ((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                            / float(values['weight_total']))
                    try:
                        cal = ((float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                            / float(values['weight_total']))
                        try:
                            cal = ((float(values[var_name[t] + '_lp']) * float(values['weight_lp']))
                                / float(values['weight_total']))
                        except:
                            cal = ''
                    except:
                        cal = ''
                except:
                    cal = ''

            else:
                cal = 'enter weights for data'

            #add value to dictionary
            values[name] = cal
            t += 1

        #Loop through dictionary and add to data values dictionary wanted definitions
        #If this is the first row,add headers
        if (x == 0):
            for name in copied_values:
                print(name)
                data_values[name] = {"units" : units[name], "values" : [values[name]]}
        else:
            for name in copied_values:
                data_values[name]["values"].append(values[name])
        x += 1

    #Write data values dictionary to output path
    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for variable in data_values:
            print(variable)
            writer.writerow([variable, data_values[variable]["units"]] + data_values[variable]["values"])
        csvfile.close()




#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_EnergyCalcs_L2(inputpath, outputpath)