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
import pandas as pd

def LEMS_FormattedL1(inputpath, outputpath, outputpathexcel, testname):

    #List of values that will appear in the output
    #Note: Improvment can make this into an excel/txt list that is read in for easy edits
    copied_values = ['eff_w_char',
                    'eff_wo_char',
                    'char_mass_productivity',
                    'char_energy_productivity',
                    'cooking_power',
                    'burn_rate',
                    'CO_useful_eng_deliver',
                    'CO2_useful_eng_deliver',
                    'CO_mass_time',
                    'CO2_mass_time',
                    'PM_mass_time']

    # Populate header
    header = ['ISO Performance Metrics (Weighted Mean)', 'units']
    header.append(testname)

    phases = ['_hp', '_mp', '_lp']

    # load in inputs from each energyoutput file
    [names, units, values, unc, uval] = io.load_constant_inputs(inputpath)

    #check if IDC test
    if 'start_time_L1' in names:
        phases.insert(0, '_L1')
    if 'start_time_L5' in names:
        phases.append('_L5')

    for each in copied_values:
        #add name and unit to dictionary for calculation
        name = each
        names.append(name)
        try:
            units[name] = units[name + '_hp']
        except:
            units[name] = ''

        sum_list = []
        for phase in phases:
            try:
                sum_list.append(float(values[each + phase]))
            except:
                pass

        #find the averages of all the phases
        total = sum(sum_list)
        try:
            cal = round((total/len(sum_list)), 3)
        except:
            cal = ''
        values[name] = cal


    output = []
    for name in copied_values:
        row = []
        row.append(name)
        row.append(units[name])
        row.append(values[name])
        output.append(row)

        # print to the output file
    with open(outputpath, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # add header
        writer.writerow(header)
        writer.writerows(output)

    #######################################
    '''
    #Excel output file
    df = pd.DataFrame.from_dict(data=values, orient='index')
    df.columns=['variable_name', 'values']
    for col in df.columns:
        print(col)
    #print(df.head())
    df2 = pd.DataFrame.from_dict(data=units, orient='index')
    #print(df2.head())
    #join dataframes
    df =df.merge(df2, on='variable_name', how='left')
    print(df)
    '''


    #rearrange cols to align with header
