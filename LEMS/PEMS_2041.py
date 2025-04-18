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

##################____Inputs________###############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#Raw data input file
inputpath = 'RawData.csv'
#Created output
outputpath = 'RawData_Recalibrated.csv'
#log
logpath = 'log.txt'
#################################################

def PEMS_2041(Inputpath, outputpath, logpath):

    # This function was made for PC sensor box(not possum). Raw data from PC is taken in and reformatted into a readable
    # Format for the rest of the functions to take in

    ver = '0.1'

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_2041 v'+ver+'   '+timestampstring #add to log
    print(line)
    logs=[line]

    line = 'firmware version = 2041, reformatting raw data input'
    print(line)
    logs.append(line)

    #Read in partial capture data, output correctly formatted data

    names = [] #list of variable names
    units = {} #dictionary of units. Key is names
    multi = {} #Dictionary of multipliers. Key is name
    data = {} #dictionary of data point. Key is names
    metric = {} #Recalcualted corrected data. Key is names
    names_new = ['time', 'seconds', 'CO', 'ChipTemp', 'PM', 'Flow', 'FlueTemp', 'TC', 'F1Flow', 'DilFlow', 'CO2', 'PM_RH'] #New list for names

    # load input file
    stuff = []
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    line = 'loaded: ' + inputpath
    print(line)
    logs.append(line)

    # put inputs in a dictionary
    for n, row in enumerate(stuff):
        if row[0] == '##': #Find start time and data
            start_row = n - 1
            date_row = n - 2
        if row[0] == '#0': #Find multiplier row
            multi_row = n
        if row[0] == 'seconds':
            names_row = n

    data_row = names_row + 1 #Data starts right after names

    for name in stuff[names_row]:
        if name == '':
            pass
        else:
            names.append(name) #Assign names

    for n,name in enumerate(names):
        try:
            multi[name]=float(stuff[multi_row][n]) #Grab the multiplier for each named row
        except:
            multi[name] = stuff[multi_row][n]
        data[name]=[x[n] for x in stuff[data_row:]] #Grab all the data for each named row
        for m,val in enumerate(data[name]): #Convert data to floats
            try:
                data[name][m]=float(data[name][m])
            except:
                pass

    for name in names_new: #Different variables have different calculations with their multipliers
        values = []
        if name == 'CO' or name == 'ChipTemp' or name == 'FlueTemp' or name == 'TC':
            for val in data[name]:
                calc = val * multi[name]
                values.append(calc)
        elif name == 'seconds' or name == 'Flow' or name == 'CO2' or name == 'PM_RH':
            for val in data[name]:
                values.append(val)
        elif name == 'PM':
            for val in data[name]:
                calc = val * multi[name] / 3
                values.append(calc)
        elif name == 'F1Flow':
            for val in data['grav']:
                calc = val * multi['grav'] * 1000
                values.append(calc)
        elif name == 'DilFlow':
            for val in data['dilution']:
                calc = val * multi['dilution'] * 1000
                values.append(calc)
        metric[name] = values

    #Calculate time row
    try:
        start_time = stuff[start_row][1] #Find start time for time data
    except:
        pass


    try:
        date = stuff[date_row][1] #Find date for time data
    except:
        pass

    try:
        #Format data
        x = date.split("-") #split at "-", when the file is opened it excel it displays as split with "/", but in notebook it has - with the zeroes
        if len(x[0]) == 1: #if one number of month
            x[0] = '0' + x[0] #add 0 at start
        if len(x[1]) == 1: #if one numer of day
            x[1] = '0' + x[1]
    except:
        #Format data
        x = date.split("/") #split at "/", when the file is opened it excel it displays as split with "/", but in notebook it has - with the zeroes
        if len(x[0]) == 1: #if one number of month
            x[0] = '0' + x[0] #add 0 at start
        if len(x[1]) == 1: #if one numer of day
            x[1] = '0' + x[1]

    try:
        date = x[0] + x[1] + x[2] #yyyymmdd notepad has the correct order from the beginning
        date_time = date + ' ' + start_time #Combine into one datetime

        con_date_time = datetime.strptime(date_time, '%Y%m%d %H:%M:%S') #convert str to readable datetime
    except:
        date = x[2] + x[0] + x[1]  # yyyymmdd notepad has the correct order from the beginning
        date_time = date + ' ' + start_time  # Combine into one datetime

        con_date_time = datetime.strptime(date_time, '%Y%m%d %H:%M:%S')  # convert str to readable datetime

    timetemp = []
    for sec in data['seconds']: #Add seconds to time for each second point
        timetemp.append(con_date_time + timedelta(seconds=sec))

    time = []
    for val in timetemp:
        temp = str(val).replace("-","") #convert format from yyyy-mm-dd to yyyymmdd
        time.append(temp)

    names.append('time') #Add to dictionaries
    data['time'] = time
    metric['time'] = time
    units['time'] = 'yyyymmdd hhmmss'

    #Add units to names - not given in file
    units['seconds'] = 's'
    units['CO'] = 'ppm'
    units['ChipTemp'] = 'degC'
    units['PM'] = 'Mm^-1'
    units['Flow'] = ''
    units['FlueTemp'] = 'degC'
    units['TC'] = 'degC'
    units['F1Flow'] = 'ccm'
    units['DilFlow'] = 'ccm'
    units['CO2'] = 'ppm'
    units['PM_RH'] = '%'

    ######################################################################
    # Write cut data to outputpath - Data isn't recalibrated just named that for next steps
    io.write_timeseries(outputpath, names_new, units, metric)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)

    #######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_2041(inputpath,outputpath, logpath)


