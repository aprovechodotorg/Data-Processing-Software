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
import os.path
from datetime import datetime as dt
from datetime import datetime, timedelta

import easygui

import LEMS_DataProcessing_IO as io

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_SenserionRawData.txt"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_FormattedSenserionData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_log.txt"

def LEMS_Senserion(inputpath, outputpath, seninputs, logpath, inputmethod):
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
    temps = []
    idx = []
    for n, name in enumerate(names):
        if 'Flow' in name:  # find flow channels
            flows.append(name)
            idx.append(n)
        if 'TC' in name: # fine temp channels
            temps.append(name)

    # Check if flow and temperature assignment file exists
    if os.path.isfile(seninputs):
        [snames, sunits, sval, sunc, suval] = io.load_constant_inputs(seninputs)
    else:
        snames = []  # list of variable names
        sunits = {}  # Dictionary of units, key is names
        sval = {}  # Dictionary of values, key is names
        sunc = {}  # Dictionary of uncertainties, key is names
        suval = {}  # Dictionary of values and uncertianties as ufloats, key is names

        #make a header
        name = 'variable'
        snames.append(name)
        sunits[name] = 'units'
        sval[name] = 'value'

        for name in flows:
            snames.append(name)
            sunits[name] = 'Primary/Secondary'
            sval[name] = 'Primary'

        for name in temps:
            snames.append(name)
            sunits[name] = 'text'
            sval[name] = ''

    if inputmethod == '1':
        fieldnames = []
        defaults = []
        for name in snames[1:]:
            fieldnames.append(name)
            defaults.append(sval[name])
        # Easy gui to prompt for inputs
        msg = f"Designate fan flows as either Primary or Secondary to calculate primary and secondary total flows.\n" \
              f"Describe the location of each thermocouple."
        title = 'Define Fans and Thermocouples'
        newvals = easygui.multenterbox(msg, title, fieldnames, values=defaults)
        if newvals:
            if newvals != defaults:  # If user entered new values
                defaults = newvals
                for n, name in enumerate(snames[1:]):
                    sval[name] = defaults[n]
        else:
            line = 'Error: Undefined variables'
            print(line)
            logs.append(line)

        # Record values
        io.write_constant_outputs(seninputs, snames, sunits, sval, sunc, suval)
        line = f'Created sensor designation file: {seninputs}'
        print(line)
        logs.append(line)

    # Calculate Primary flow
    name = 'PrimaryFlow'
    names.append(name)
    units[name] = units[flows[0]]
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if sval[flow] == 'Primary' or sval[flow] == 'primary' or sval[flow] == 'PRIMARY' and data[flow][n] != 999:
                # 999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

    # Calculate Secondary flow
    name = 'SecondaryFlow'
    names.append(name)
    units[name] = units[flows[0]]
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if sval[flow] == 'Secondary' or sval[flow] == 'secondary' or sval[flow] == 'SECONDARY' and \
                    data[flow][n] != 999:  # 999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

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

    name = 'SenO2Percent'
    names.append(name)
    data[name] = []
    units[name] = '%'
    for val in data['Lambda']:
        data[name].append((val - 1) / ((1/3) + 4.77 * val))

    # write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    return logs

# run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_Senserion(inputpath, outputpath, logpath)

