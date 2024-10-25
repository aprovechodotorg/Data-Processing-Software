#v0.0 Python3

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
import math
import statistics
from scipy import stats

################################
inputpath =['Data/CrappieCooker/CrappieCooker_test1/CrappieCooker_test1_EnergyOutputs.csv',
            'Data/CrappieCooker/CrappieCooker_test3/CrappieCooker_test3_EnergyOutputs.csv',
            'Data/CrappieCooker/CrappieCooker_test4/CrappieCooker_test4_EnergyOutputs.csv']

outputpath ='Data/CrappieCooker/CrappieCooker_L2_FormattedData.csv'

testname = ['yatzo_test1', 'yatzo_test2', 'yatzo_test3', 'yatzo_test4', 'yatzo_test5']
###############################

#def LEMS_EnergyCalcs_L2(inputpath,outputpath):

#Change Here 
def LEMS_EnergyCalcs_L2(energyinputpath, emissioninputpath, outputpath, testname):
    
    #print(outputpath)
    #List of headers
    header = []
    #dictionary of data for each test run
    data_values = {}

    #CHANGE START HERE 
    trial = {} # to try out keeping track of data for each test 
    #CHANGE END HERE 

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
    
    #CHANGE HERE 
    y=0
    #CHANGE END 
    
    #Run through all tests entered
    for path in energyinputpath:
        #Pull each test name/number. Add to header
        #directory, filename = os.path.split(path)
        #datadirectory, testname = os.path.split(directory)
        #header.append(testname)

        #CHANGE HERE 
        header.append(testname[y])
        #END CHANGE
        
        #load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)


        #Add dictionaries for additional columns of comparative data
        average = {}
        N = {}
        stadev = {}
        interval = {}
        high_tier = {}
        low_tier = {}
        COV = {}
        CI = {}
        
        #CHANGE START HERE 
        trial[testname[y]]= {}
        #CHANGE END HERE 

        ###########################################
        # Run calculations
        #All calcs have the same formula so loops through formula for each value that will be calculated
        t = 0

        phases = ['_hp', '_mp', '_lp']

        # load in first input file to check if IDC
        [names, units, values, unc, uval] = io.load_constant_inputs(energyinputpath[0])
        if 'start_time_L1' in names:
            phases.insert(0, '_L1')
        if 'start_time_L5' in names:
            phases.append('_L5')

        for each in copied_values:

            #Add name and unit of calculation to dictionary
            name = each
            names.append(name)
            units[name] = var_units[t]
            #print(values['weight_total'])

            sum_list = []
            for phase in phases:
                try:
                    sum.append(float(values[var_name[t] + phase]))
                except:
                    pass

            total = sum(sum_list)
            cal = round((total / float(values['weight_total'])) , 3)
            '''
            if float(values['weight_total']) == 3:
                try:
                    #Run through formula. If any value cells are blank, leave value cell blank
                        cal = round((((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                                +(float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                                +(float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                / float(values['weight_total'])), 3)
                except:
                    cal = ''

            elif float(values['weight_total']) == 2:
                try:
                    cal = round((((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                            +(float(values[var_name[t] + '_mp']) * float(values['weight_mp'])))
                            / float(values['weight_total'])), 3)
                    try:
                        cal = round((((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                                + (float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                / float(values['weight_total'])), 3)
                        try:
                            cal = round(((+ (float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                                    + (float(values[var_name[t] + '_lp']) * float(values['weight_lp'])))
                                   / float(values['weight_total'])), 3)
                        except:
                            cal = ''
                    except:
                        cal = ''
                except:
                    cal = ''
            elif float(values['weight_total']) == 1:
                print('wtf')
                try:
                    cal = round(((float(values[var_name[t] + '_hp']) * float(values['weight_hp']))
                            / float(values['weight_total'])), 3)
                    try:
                        cal = round(((float(values[var_name[t] + '_mp']) * float(values['weight_mp']))
                            / float(values['weight_total'])), 3)
                        try:
                            cal = round(((float(values[var_name[t] + '_lp']) * float(values['weight_lp']))
                                / float(values['weight_total'])), 3)
                        except:
                            cal = ''
                    except:
                        cal = ''
                except:
                    cal = ''

            else:
                cal = 'enter weights for data'
            '''

            #add value to dictionary
            values[name] = cal
            t += 1

        #Loop through dictionary and add to data values dictionary wanted definitions
        #If this is the first row,add dictionary
        if (x == 0):
            for name in copied_values:
                #print(name)
                try:
                    data_values[name] = {"units" : units[name], "values" : [values[name]]}
                except:
                    data_values[name] = {"units": '', "values": ['']}
        else:
            for name in copied_values:
                try:
                    data_values[name]["values"].append(values[name])
                except:
                    data_values[name]["values"].append('')
        x += 1
        #print(data_values)
        
        #CHANGE START HERE 
        trial[testname[y]] = values
        y += 1
        #CHANGE END HERE

    ###############################################
    #Adding Emission Metrics if avalible
    copied_values = ['CO_useful_eng_deliver',
                     'CO2_useful_eng_deliver',
                     'CO_mass_time',
                     'CO2_mass_time',
                     'PM_mass_time']

    x = 0
    edata_values = {}
    for path in emissioninputpath:
        if os.path.isfile(path):
            # load in inputs from each emissionoutput file
            [enames, eunits, evalues, eunc, euval] = io.load_constant_inputs(path)

            for each in copied_values:

                # Add name and unit of calculation to dictionary
                name = each
                names.append(name)
                enames.append(name)
                try:
                    eunits[name] = eunits[name + '_hp']
                except:
                    pass

                if float(values['weight_total']) == 3:
                    try:
                        cal = round((float(evalues[each + '_hp'])+float(evalues[each + '_mp'])+float(evalues[each + '_lp']))/
                              float(values['weight_total']))
                    except:
                        cal = ''

                #add value to dictionary
                evalues[each] = cal

            # Loop through dictionary and add to data values dictionary wanted definitions
             # If this is the first row,add dictionary
            if (x == 0):
                for name in copied_values:
                     # print(name)
                    try:
                        edata_values[name] = {"units": eunits[name], "values": [evalues[name]]}
                    except:
                        edata_values[name] = {"units": '', "values": ['']}
            else:
                for name in copied_values:
                    try:
                        edata_values[name]["values"].append(evalues[name])
                    except:
                        edata_values[name]["values"].append('')
            x += 1

        #merge dictionaries
        data_values.update(edata_values)

    #Add headers for additional columns of comparative data
    header.append("average")
    header.append("N")
    header.append("stdev")
    header.append("Interval")
    header.append("High Tier Estimate")
    header.append("Low Tier Estimate")
    header.append("COV")
    header.append("CI")


    #loop through each variable in the dictionary
    for variable in data_values:
        num_list = []

        #Loop through each value for the variable.
        #This loop is needed to sort through data entries that are blank and ignore them instead of throwing errors
        for value in data_values[variable]["values"]:
            #If the vaule is blank, do nothing (error is a throw away variable)
            if value == '':
                error = 1
            #Otherwise, the value is a number, add it to list of values that have numbers
            #Note: Could add to if loop to sort out str values right now those throw errors although there may not be str values
            else:
                num_list.append(float(value))

        #Try averaging the list of numbered values
        try:
            #print(data_values[variable]["values"])
            #print(len(data_values[variable]["values"]))
            average[variable] = round(sum(num_list)/len(num_list), 3)
            #average[variable] = float((sum(data_values[variable]["values"]))) / (len(data_values[variable]["values"]))
            #avg.append(average[variable])

        #If the list of number values is blank (you try dividing by 0) make average nan
        except:
            average[variable] = math.nan
            #avg.append(average[variable])


        #Update dictionary to add average dictionary
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



        #t-statistic
        #p<0.1, 2-tail, n-1
        interval[variable] = ((stats.t.ppf(1-0.05, (N[variable] - 1))))
                      # * stadev[variable] / N[variable] ^ 0.5)
        interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)


        #Add the t-statistic dictionary to the dictionary
        data_values[variable].update({"interval": interval[variable]})

        high_tier[variable] = round((average[variable] + interval[variable]), 3)
        low_tier[variable] = round((average[variable] - interval[variable]), 3)

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        try:
            COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
            data_values[variable].update({"COV": COV[variable]})
        except:
            COV[variable] = math.nan
            data_values[variable].update({"COV": COV[variable]})


        CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})


        #print(data_values)
    #Write data values dictionary to output path
    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        #Add the header to the outputfile
        writer.writerow(header)
        #Write units, values, and comparative data for all varaibles in all tests
        for variable in data_values:
            #print(data_values[variable]["average"])
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


    #Change here 
    return trial,average, data_values, N, stadev, interval, high_tier, low_tier, COV 

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_EnergyCalcs_L2(inputpath, outputpath)