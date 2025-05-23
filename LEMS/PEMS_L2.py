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
import pandas as pd
import numpy as np
from datetime import datetime as dt
import traceback

def PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath):
    #Function intakes list of inputpaths and creates comparission between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_L2 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]
    #################################################
    ####ALL OUTPUTS
    all = True
    if len(allpath) != 0:
        for path in allpath:
            if os.path.isfile(path):
                good = '1'
            else:
                all = False
    else:
        all = False

    if all == True:
        # List of headers
        header = []
        # dictionary of data for each test run
        data_values = {}
        units = {}
        names = []  # list of variable names

        header = ['All Outputs', 'units']

        x = 0
        # Run through all tests entered
        for path in allpath:
            # Pull each test name/number. Add to header
            directory, filename = os.path.split(path)
            datadirectory, testname = os.path.split(directory)
            header.append(testname)

            # load in inputs from each energyoutput file
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

            # Make a complete list of all variable names from all tests
            for n, name in enumerate(new_names):
                if name not in names:  # If this is a new name, insert it into the ist of names
                    names.insert(n, name)
                    units[name] = new_units[name]

        for path in allpath:
            # load in inputs from each energyoutput file
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

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
                    try:
                        data_values[name] = {"units": units[name], "values": [values[name]]}
                    except:
                        try:
                            data_values[name] = {"units": units[name], "values": ['']}
                        except:
                            data_values[name] = {"units": '', "values": ['']}
            else:
                for name in names:
                    try:
                        data_values[name]["values"].append(values[name])
                    except:
                        data_values[name]["values"].append('')
            x += 1

        # add headers for comparative data
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
                        if 'Tier' in value:
                            num_list.append(0)
                        else:
                            num_list.append(float(value))
                            # Filter out NaN values from num_list
                            filtered_list = [num for num in num_list if not math.isnan(num)]
                            filtered_list = [num for num in filtered_list if not num == 'nan']
                            num_list = filtered_list
                    except:
                        pass
            if variable == 'tier_CO_useful_eng_deliver':
                if data_values['CO_useful_eng_deliver_weighted']['low_tier'] > 18.3:
                    average[variable] = 'Tier 0'
                elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 18.3 and data_values[
                    'CO_useful_eng_deliver_weighted']['low_tier'] > 11.5:
                    average[variable] = 'Tier 1'
                elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 11.5 and data_values[
                    'CO_useful_eng_deliver_weighted']['low_tier'] > 7.2:
                    average[variable] = 'Tier 2'
                elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 7.2 and data_values[
                    'CO_useful_eng_deliver_weighted']['low_tier'] > 4.4:
                    average[variable] = 'Tier 3'
                elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 4.4 and data_values[
                    'CO_useful_eng_deliver_weighted']['low_tier'] > 3:
                    average[variable] = 'Tier 4'
                elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 3:
                    average[variable] = 'Tier 5'
                else:
                    average[variable] = 'nan'
            elif variable == 'tier_PM_useful_eng_deliver':
                if data_values['PM_useful_eng_deliver_weighted']['low_tier'] > 1030:
                    average[variable] = 'Tier 0'
                elif data_values['PM_useful_eng_deliver_weighted']['low_tier'] <= 1030 and data_values[
                    'PM_useful_eng_deliver_weighted']['low_tier'] > 481:
                    average[variable] = 'Tier 1'
                elif data_values['PM_useful_eng_deliver_weighted']['low_tier'] <= 481 and data_values[
                    'PM_useful_eng_deliver_weighted']['low_tier'] > 218:
                    average[variable] = 'Tier 2'
                elif data_values['PM_useful_eng_deliver_weighted']['low_tier'] <= 218 and data_values[
                    'PM_useful_eng_deliver_weighted']['low_tier'] > 62:
                    average[variable] = 'Tier 3'
                elif data_values['PM_useful_eng_deliver_weighted']['low_tier'] <= 62 and data_values[
                    'PM_useful_eng_deliver_weighted']['low_tier'] > 5:
                    average[variable] = 'Tier 4'
                elif data_values['PM_useful_eng_deliver_weighted']['low_tier'] <= 5:
                    average[variable] = 'Tier 5'
                else:
                    average[variable] = 'nan'
            elif variable == 'tier_eff_wo_char':
                if data_values['eff_wo_char_weighted']['low_tier'] < 10:
                    average[variable] = 'Tier 0'
                elif data_values['eff_wo_char_weighted']['low_tier']  >= 10 and data_values['eff_wo_char_weighted']['low_tier']  < 20:
                    average[variable] = 'Tier 1'
                elif data_values['eff_wo_char_weighted']['low_tier']  >= 20 and data_values['eff_wo_char_weighted']['low_tier']  < 30:
                    average[variable] = 'Tier 2'
                elif data_values['eff_wo_char_weighted']['low_tier']  >= 30 and data_values['eff_wo_char_weighted']['low_tier']  < 40:
                    average[variable] = 'Tier 3'
                elif data_values['eff_wo_char_weighted']['low_tier']  >= 40 and data_values['eff_wo_char_weighted']['low_tier']  < 50:
                    average[variable] = 'Tier 4'
                elif data_values['eff_wo_char_weighted']['low_tier']  >= 50:
                    average[variable] = 'Tier 5'
                else:
                    average[variable] = 'nan'
            elif variable == 'tier_eff_w_char':
                if data_values['eff_w_char_weighted']['low_tier'] < 10:
                    average[variable] = 'Tier 0'
                elif data_values['eff_w_char_weighted']['low_tier'] >= 10 and data_values['eff_w_char_weighted']['low_tier'] < 20:
                    average[variable] = 'Tier 1'
                elif data_values['eff_w_char_weighted']['low_tier'] >= 20 and data_values['eff_w_char_weighted']['low_tier'] < 30:
                    average[variable] = 'Tier 2'
                elif data_values['eff_w_char_weighted']['low_tier'] >= 30 and data_values['eff_w_char_weighted']['low_tier'] < 40:
                    average[variable] = 'Tier 3'
                elif data_values['eff_w_char_weighted']['low_tier'] >= 40 and data_values['eff_w_char_weighted']['low_tier'] < 50:
                    average[variable] = 'Tier 4'
                elif data_values['eff_w_char_weighted']['low_tier'] >= 50:
                    average[variable] = 'Tier 5'
                else:
                    average[variable] = 'nan'
            else:
                # Filter out NaN values from num_list
                filtered_list = [num for num in num_list if not math.isnan(num)]
                filtered_list = [num for num in filtered_list if not num == 'nan']

                if filtered_list:
                    # Calculate the average of the filtered list
                    average[variable] = round(sum(filtered_list) / len(filtered_list), 3)
                else:
                    # If all values are NaN, assign NaN to the average
                    average[variable] = math.nan

            if variable not in data_values:
                data_values[variable] = {}
            # Add the average dictionary to the dictionary
            data_values[variable].update({"average": average[variable]})

            # Count the number of tests done for this value
            N[variable] = len(num_list)
            # Add the count dictionary to the dictionary
            data_values[variable].update({"N": N[variable]})

            if variable == 'PM_useful_eng_deliver_weighted':
                test = 1
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

            # Add high and low tier estimates
            try:
                high_tier[variable] = round((average[variable] + interval[variable]), 3)
            except:
                high_tier[variable] = 'nan'
            try:
                low_tier[variable] = round((average[variable] - interval[variable]), 3)
            except:
                low_tier[variable] = 'nan'

            data_values[variable].update({"high_tier": high_tier[variable]})
            data_values[variable].update({"low_tier": low_tier[variable]})

            # Add COV
            try:
                COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
            except:
                COV[variable] = math.nan

            data_values[variable].update({"COV": COV[variable]})

            # Add confidence interval
            CI[variable] = str(low_tier[variable]) + '-' + str(high_tier[variable])
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

        full_values = data_values
        full_units = units
        return full_values, full_units, logs
    else:
        ############################################################
        #ENERGY OUTPUTS
        # List of headers
        header = []
        # dictionary of data for each test run
        data_values = {}
        units = {}
        names = [] #list of variable names

        header = ['Energy Outputs', 'units']

        x = 0
        # Run through all tests entered
        for path in energyinputpath:
            # Pull each test name/number. Add to header
            directory, filename = os.path.split(path)
            datadirectory, testname = os.path.split(directory)
            header.append(testname)

            # load in inputs from each energyoutput file
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

            #Make a complete list of all variable names from all tests
            for n, name in enumerate(new_names):
                if name not in names: #If this is a new name, insert it into the ist of names
                    names.insert(n, name)
                    units[name] = new_units[name]

        for path in energyinputpath:
            # load in inputs from each energyoutput file
            [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

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
                    try:
                        data_values[name] = {"units": units[name], "values": [values[name]]}
                    except:
                        data_values[name] = {"units": '', "values": ['']}
            else:
                    for name in names:
                        try:
                            data_values[name]["values"].append(values[name])
                        except:
                            data_values[name]["values"].append('')
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
            CI[variable] = str(low_tier[variable]) + '-' + str(high_tier[variable])
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

        full_values = data_values
        full_units = units

        ####################################################
        #EMISSION OUTPUTS

        # List of headers
        header = []
        # dictionary of data for each test run
        data_values = {}
        units = {}
        names = [] #list of variable names

        header = ['Emissions Outputs', 'units']

        realpaths = []
        for path in emissionsinputpath:

            if os.path.isfile(path): #check if emissions paths are real
                realpaths.append(path)
            else:
                line = 'Emissions path: ' + path + ' does not exist and will not be compared'
                print(line)
        emissionsinputpath = realpaths

        if len(emissionsinputpath) != 0: #only run code if the list of real emissions paths has one or more entries
            x = 0
            # Run through all tests entered
            for path in emissionsinputpath:
                # Pull each test name/number. Add to header
                directory, filename = os.path.split(path)
                datadirectory, testname = os.path.split(directory)
                header.append(testname)

                # load in inputs from each energyoutput file
                [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

                # Make a complete list of all variable names from all tests
                for n, name in enumerate(new_names):
                    if name not in names:  # If this is a new name, insert it into the ist of names
                        names.insert(n, name)
                        units[name] = new_units[name]
            for path in emissionsinputpath:
                # load in inputs from each energyoutput file
                [new_names, new_units, values, unc, uval] = io.load_constant_inputs(path)

                line = 'loaded: ' + path
                print(line)
                logs.append(line)

                phases = []
                for name in names: #check if emission data is in phases or not
                    if '_L1' in name: #record what phases are present
                        phases.append('_L1')
                        continue
                    if '_hp' in name:
                        phases.append('_hp')
                        continue
                    if '_mp' in name:
                        phases.append('_mp')
                        continue
                    if '_lp' in name:
                        phases.append('_lp')
                        continue
                    if '_full' in name:
                        phases.append('_full')
                        continue

                if len(phases) != 0: #if there are phases
                    temp_names = []
                    for name in names:
                        if phases[0] in name: #get the 'raw' name without the identifier
                            size = len(name)
                            #remove phase identifier
                            name = name[:size - 3]
                            temp_names.append(name)

                    phaselist = ['_hp', '_mp', '_lp', '_full']

                    if '_L1' in phases: #Check if IDC test
                        phaselist.insert(0, '_L1')

                    all_names = []
                    for phase in phaselist: #add al phases to all names so it has to loop through all
                        for name in temp_names:
                            new_name = name + phase
                            all_names.append(new_name)

                    names = all_names    #reassign names list


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
                        try:
                            data_values[name] = {"units": units[name], "values": [values[name]]}
                        except:
                            data_values[name] = {"units": '', "values": ['']}
                else:
                    for name in names:
                        try:
                            data_values[name]["values"].append(values[name])
                        except:
                            data_values[name]["values"].append('')
                x += 1

            # add headers for comparative data
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

                if variable == 'tier_CO_useful_eng_deliver':
                    if data_values['CO_useful_eng_deliver_weighted']['low_tier'] > 18.3:
                        average[variable] = 'Tier 0'
                    elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 18.3 and data_values[
                        'CO_useful_eng_deliver_weighted']['low_tier'] > 11.5:
                        average[variable] = 'Tier 1'
                    elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 11.5 and data_values[
                        'CO_useful_eng_deliver_weighted']['low_tier'] > 7.2:
                        average[variable] = 'Tier 2'
                    elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 7.2 and data_values[
                        'CO_useful_eng_deliver_weighted']['low_tier'] > 4.4:
                        average[variable] = 'Tier 3'
                    elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 4.4 and data_values[
                        'CO_useful_eng_deliver_weighted']['low_tier'] > 3:
                        average[variable] = 'Tier 4'
                    elif data_values['CO_useful_eng_deliver_weighted']['low_tier'] <= 3:
                        average[variable] = 'Tier 5'
                    else:
                        average[variable] = 'nan'
                else:
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

                #add high and low tier
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


            try:
                # Open existing output and append values to it. This will not overwrite previous values
                with open(outputpath, 'a', newline='') as csvfile:
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
                line = 'Added emissions to file: ' + outputpath
                print(line)
                logs.append(line)
            except:
                pass

        return full_values, full_units, data_values, units, logs
    #print to log file
    io.write_logfile(logpath,logs)
