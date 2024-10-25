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
from datetime import datetime as dt
from datetime import datetime
import LEMS_DataProcessing_IO as io

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_NanoscanRawData.txt"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_FormattedNanoscanData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_log.txt"

def LEMS_Nanoscan(inputpath, outputpath, logpath):
    #Function takes in nanoscan data and reformats to be readable for the rest of the program

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Nanoscan v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    names = []  # list of variable names
    units = {}  # Dictionary keys are variable names, values are units
    data = {}  # Dictionary #keys are variable names, values are times series as a list

    # load input file
    stuff = []
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)
    line = 'loaded: ' + inputpath  # add to log
    print(line)
    logs.append(line)

    for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start
        try:
            if 'File Index' in row[0]:
                namesrow = n
        except:
            pass
    datarow = namesrow + 1
    tempnames=stuff[namesrow]
    for n, name in enumerate(tempnames):
        if name == 'Date Time':
            names.append('time')
            names.append('seconds')
            units['time'] = 'yyyymmdd HH:MM:SS'
            units['seconds'] = 's'
            data['temptime'] = [x[n] for x in stuff[datarow:]]
        else:
            names.append(name)
            units[name] = ''
            data[name] = [x[n] for x in stuff[datarow:]]

    time = []
    seconds = []
    for n, num in enumerate(data['temptime']):
        try:
            convertnum = datetime.strptime(num, "%m/%d/%Y %H:%M") #convert str to datetime object
            time.append(convertnum)
            dateform = "%m/%d/%Y %H:%M"
        except:
            try:
                convertnum = datetime.strptime(num, '%Y-%m-%d %H:%M:%S')  # convert str to datetime object
                time.append(convertnum)
                dateform = '%Y-%m-%d %H:%M:%S'
            except:
                convertnum = datetime.strptime(num, '%Y/%m/%d %H:%M:%S')  # convert str to datetime object
                time.append(convertnum)
                dateform = '%Y/%m/%d %H:%M:%S'

        if n == 0: #for first data point set at 60
            seconds.append(60)
        else:
            try:
                nextnum = datetime.strptime(data['temptime'][n+1], dateform)
                diff = nextnum - convertnum
                seconds.append(seconds[n-1] + diff.total_seconds()) #convert to seconds and add to previous value
            except:
                seconds.append(seconds[n - 1] + 60) #add 60 seconds as default sample rate
    data['time'] = time
    data['seconds'] = seconds

    #write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)


    #print to log file
    io.write_logfile(logpath, logs)

    return logs

#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_Nanoscan(inputpath, outputpath, logpath)
