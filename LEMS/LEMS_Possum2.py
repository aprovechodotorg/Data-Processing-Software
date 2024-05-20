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

import csv
from datetime import datetime, timedelta
from datetime import  datetime as dt
import LEMS_DataProcessing_IO as io

def LEMS_Possum2(inputpath, outputpath, logpath):

    # This function was made for PEMS Possum2. Raw data from SB is taken in and reformatted into a readable
    # Format for the rest of the functions to take in

    ver = '0.1'

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Possum2 v'+ver+'   '+timestampstring #add to log
    print(line)
    logs=[line]

    line = 'firmware version = Possum2, reformatting raw data input'
    print(line)
    logs.append(line)

    names = [] #list of variable names
    units = {} #dictionary of units. Key is names
    multi = {} #Dictionary of multipliers. Key is name
    data = {} #dictionary of data point. Key is names
    metric = {} #Recalcualted corrected data. Key is names

    #FOR MORE CHANNELS, CHANGE HERE - NAMES MUST MATCH NAMES FROM LEMS 4003 DATA - NAME ORDER IS HOW COLUMNS ARE WRITTEN
    names_new = [] #New list for names

    # load input file
    stuff = []
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    line = 'loaded: ' + inputpath
    print(line)
    logs.append(line)

    # put inputs in a dictionary
    for n, row in enumerate(stuff):
        try:
            if 'time' in row[0]:
                names_row = n
            if row[0] == '#units:':
                units_row = n
        except:
            pass

    data_row = names_row + 1  # Data starts right after names

    for name in stuff[names_row]:
        if name == '':
            pass
        else:
            names.append(name)  # Assign names

    for n, name in enumerate(names):
        data[name]=[x[n] for x in stuff[data_row:]] #Grab all the data for each named row
        for m,val in enumerate(data[name]): #Convert data to floats
            try:
                units[name] = stuff[units_row][n]  # second row is units
                data[name][m]=float(data[name][m])
            except:
                pass

    #FOR OTHER CHANNELS OR CHANNELS NAMED DIFFERENTLY, CHANGE HERE
    for name in names: #Different variables have different calculations with their multipliers
        values = []
        if name == 'Pitot':
            for val in data[name]:
                calc = val / 9.80665 #Pa to mmH20
                values.append(calc)
            names_new.append('Flow')
            units['Flow'] = 'mmH2O'
            metric['Flow'] = values
        elif name == 'Pamb':
            for val in data[name]:
                calc = val * 0.01 #Pa to hPa
                values.append(calc)
            names_new.append('AmbPres')
            units['AmbPres'] = 'hPa'
            metric['AmbPres'] = values
        elif name == 'FlueTemp':
            for val in data[name]:
                values.append(val)
            names_new.append('FLUEtemp')
            units['FLUEtemp'] = 'C'
            metric['FLUEtemp'] = values
        else:
            for val in data[name]:
                values.append(val)
            names_new.append(name)
            metric[name] = values

    ######################################################################
    # Write cut data to outputpath - Data isn't recalibrated just named that for next steps
    io.write_timeseries(outputpath, names_new, units, metric)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
