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
import LEMS_DataProcessing_IO as io

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_SenserionRawData.txt"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_FormattedSenserionData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_log.txt"

def LEMS_Senserion(inputpath, outputpath, logpath):
    #Function takes in senserion data and reformats to be readable for the rest of the program and adds total flow

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Senserion v' + ver + '   ' + timestampstring  # Add to log
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

    computer = 0
    for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start
        #try:
        #print(row[0])
        if 'Timestamp' in row[0] and computer == 0: #there's two timestamps, computer and sensor box
            computertimelist = row[0].split(" ")
            try:
                computertime = datetime.strptime(computertimelist[2], "%Y%m%d%H%M%S")  # convert str to datetime object
            except:
                computertime = datetime.strptime(computertimelist[1],"%Y%m%d%H%M%S")  # convert str to datetime object
            computer = 1
        elif 'Timestamp' in row[0] and computer == 1:
            sensortimelist = row[0].split(" ")
            #try:
            sensortime = datetime.strptime(sensortimelist[1] + ' '  + sensortimelist[2],"%Y%m%d %H:%M:%S")
            #except:
                #sensortime = datetime.strptime(sensortimelist[2], "%y%m%d %H:%M:%S")
            computer = 2
        if 'time' in row[0]:
            namesrow = n
        if 'units' in row[0]:
            unitsrow = n
        #except:
            #pass

    datarow = namesrow + 1
    names=stuff[namesrow]
    for n, name in enumerate(names):
        if name == 'time':
            units[name] = 'yyyymmdd HH:MM:SS'
            data['temptime'] = [x[n] for x in stuff[datarow:]]
        else:
            units[name] = stuff[unitsrow][n]
            data[name] = [x[n] for x in stuff[datarow:]]
            for m,val in enumerate(data[name]):
                try:
                    data[name][m]=float(data[name][m])
                except:
                    pass

    timeoffset = computertime - sensortime
    data['time'] = []
    for temptime in data['temptime']: #correct time to match computer (LEMS time)
        convertedtime = datetime.strptime(temptime, '%Y%m%d %H:%M:%S')
        correctedtime = convertedtime + timedelta(seconds=timeoffset.total_seconds())
        data['time'].append(correctedtime)

    flows = []
    idx = []
    for n, name in enumerate(names): #find flow channels
        if 'Flow' in name:
            flows.append(name)
            idx.append(n)

    name = 'TotalPrimaryFlow'
    names.append(name)
    data[name] = []
    units[name] = units[flows[0]]
    for n, row in enumerate(data['time']):
        data[name].append(data['Flow1'][n] + data['Flow2'][n] + data['Flow3'][n] + data['Flow4'][n] + data['Flow5'][n] +
                          data['Flow7'][n])

    name = 'TotalSecondaryFlow'
    names.append(name)
    data[name] = []
    units[name] = units[flows[0]]
    for n, row in enumerate(data['time']):
        data[name].append(data['Flow6'][n] + data['Flow8'][n])

    name = 'TotalFlow' #caculate total from all sensors
    names.append(name)
    data[name] = []
    units[name] = units[flows[0]]
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if data[flow][n] != 999: #999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

    # write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

# run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_Senserion(inputpath, outputpath, logpath)

