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
from datetime import datetime as dt

def LEMS_FormattedL1(inputpath, outputpath, outputexcel, testname, logpath):
    #function takes in file and creates a set cut table with hard coded parameters
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_FormattedL1 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

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
                     'PM_mass_time',
                     'PM_heat_mass_time']

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

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    # Create dictionary of combined units and values
    copied_dict = {}
    for key in names:
        copied_dict[key] = {'values': values[key],
                            'units': units.get(key, "")}

    # convert to pandas dataframe
    df = pd.DataFrame.from_dict(data=copied_dict, orient='index')

    df = df[['units', 'values']]

    df.name = 'Variable'

    writer = pd.ExcelWriter(outputexcel, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Formatted')
    worksheet.set_column(0, 0, 30)  # adjust width of first column
    writer.sheets['Formatted'] = worksheet

    # Create a cell format with heading font
    heading_format = writer.book.add_format({
        'bold': True,
        'font_name': 'Arial',  # Customize the font name as needed
        'font_size': 12,  # Customize the font size as needed
        'align': 'center',  # Center-align the text
        'valign': 'vcenter'  # Vertically center-align the text
    })

    worksheet.write_string(0, 0, df.name, heading_format)
    df.to_excel(writer, sheet_name='Formatted', startrow=1, startcol=0)
    writer.save()

    line = 'created: ' + outputexcel
    print(line)
    logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
