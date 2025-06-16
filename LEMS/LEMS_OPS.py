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
from datetime import datetime, timedelta
import re
import LEMS_DataProcessing_IO as io

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_OPSRawData.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_FormattedOPSData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_log.txt"

def LEMS_OPS(inputpath, outputpath, logpath):
    #Function takes in OSP data and reformats to be readable for the rest of the program

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_OSP v' + ver + '   ' + timestampstring  # Add to log
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
            if 'Elapsed' in row[0]:
                namesrow = n
            elif 'Start Time' in row[0]:
                timerow = n
            elif 'Start Date' in row[0]:
                daterow = n
            elif 'Offset' in row[0]:
                offrow = n
        except:
            pass

    datarow = namesrow + 1
    tempnames = stuff[namesrow]
    for n, name in enumerate(tempnames):
        if 'Elapsed' in name:
            names.append('seconds')
            units['seconds'] = 's'
            data['seconds'] = [x[n] for x in stuff[datarow:]]
        else:
            try:
                u = re.findall((r'\(.*?\)', name)) #check for units in name
                units[name] = u[0]
            except:
                units[name] = ''
            names.append(name)
            data[name] = [x[n] for x in stuff[datarow:]]

    try:
        offset = float(stuff[offrow][1])
    except UnboundLocalError:
        offset = 0

    timestamp = stuff[daterow][1] + ' ' + stuff[timerow][1]
    try:
        convertnum = datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")
    except:
        convertnum = datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S')

    data['time'] = []
    names.insert(0, 'time')
    units['time'] = 'yyyymmdd hh:mm:ss'
    for n, num in enumerate(data['seconds']):
        elapsed = int(num) + offset
        data['time'].append(convertnum + timedelta(seconds=elapsed)) #add elapsed seconds with included offset

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
    LEMS_OPS(inputpath, outputpath, logpath)
