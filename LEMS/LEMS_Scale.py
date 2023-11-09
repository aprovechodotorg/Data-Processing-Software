#v0.0  Python3

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
import re
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import datetime, timedelta
import LEMS_DataProcessing_IO as io
import os

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_ScaleRawData.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_FormattedScaleData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_log.txt"


def LEMS_Scale(inputpath, outputpath, logpath):
    #Function takes in scalet data and reformats to be readable for the rest of the program

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Scale v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    names = []  # list of variable names
    units = {}  # Dictionary keys are variable names, values are units
    data = {}  # Dictionary #keys are variable names, values are times series as a list

    sample_rate = 1/30 #set sample rate - 30 data points a second - measured from putting weights on every 30 seconds.

    # load input file
    stuff = []
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)
    line = 'loaded: ' + inputpath  # add to log
    print(line)
    logs.append(line)

    x = 0
    for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start
            if 'Timestamp' in row[0]:
                timerow = n
            if 'GROSS' in row[0] and x == 0: #only do this the first time gross is found
                datarow = n
                x = 1
    names.append('time') #add variables that will be tracked
    names.append('seconds')
    names.append('weight')
    units['time'] = 'yyyymmdd hhmmss'
    units['seconds'] = 's'

    tempdata = [x[0] for x in stuff[datarow:]] #assign first column as temporary data
    data['weight'] = []

    for row in tempdata:
        try:
            trash, weight, unit = row.split() #split at the spaces: data has format GROSS # unit
            data['weight'].append(float(weight)) #only add the data
        except:
            data['weight'].append('')
    units['weight'] = unit #grab the last unit to record

    #time conversion
    timestamp = stuff[timerow][0] #first col in timerow is the time stamp
    hashtag, label, info = timestamp.split()
    start_time = datetime.strptime(info, '%Y%m%d%H%M%S') #convert str to datetime object

    data['seconds'] = [] #track time and seconds elapsed since the timestamp
    data['time'] = []
    total = 0
    for n, row in enumerate(data['weight']):
        if n == 0:
            data['seconds'].append(0) #first row, no time has passed
            data['time'].append(start_time)
        else:
            total = total + sample_rate #add the measured sample rate
            data['seconds'].append(round(total, 2)) #round and add seconds
            new_time = start_time + timedelta(seconds=round(total,0)) #round to nearest second to avoid milliseonds
            data['time'].append(new_time)

    #write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'create: ' + outputpath
    print(line)
    logs.append(line)


    #print to log file
    io.write_logfile(logpath, logs)

#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_Scale(inputpath, outputpath, logpath)
