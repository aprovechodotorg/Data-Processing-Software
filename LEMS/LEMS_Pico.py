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

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_PicoRawData.csv"
lemspath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_RawData.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_FormattedPicoData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\scale_log.txt"

def LEMS_Pico(inputpath, lemspath, outputpath, logpath):
    #Function takes in nanoscan data and reformats to be readable for the rest of the program

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Pico v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    delta_for_seconds = 0 #TO SHIFT TIME SERIES DATA  CHANGE THIS VALUE - USE SECONDS

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
            if 'C' in row[1]:
                namesrow = n
        except:
            pass
    datarow = namesrow + 1
    tempnames = stuff[namesrow]
    tempnames[0] = 'seconds'
    names = []
    for n, name in enumerate(tempnames):
        if name == 'seconds':
            names.append(name)
            units['time'] = 'yyyymmdd HH:MM:SS'
            units['seconds'] = 's'
            data['tempseconds'] = [x[n] for x in stuff[datarow:]]
        elif name != '':
            names.append(name)
            units[name] = 'C'
            data[name] = [x[n] for x in stuff[datarow:]]
        elif name == '':
            break
    names.insert(0, 'time')

    first = data['tempseconds'][1].split(':') #split at :
    second = data['tempseconds'][2].split(':') #split at :
    sample_rate = int(second[2]) - int(first[2]) #find the sample rate of the sensor

    seconds = 0

    data['seconds'] = []
    for sec in data['tempseconds']:
        data['seconds'].append(seconds)
        seconds = seconds + sample_rate #add the sample rate for the next data point

    #assign LEMS timestamp to Pico (allow for time shift if Pico was turned on at a different time)
    try:
        [Lnames,Lunits,Ldata,A,B,C,D,const] = io.load_timeseries_with_header(lemspath)
    except:
        [Lnames,Lunits,Ldata] = io.load_timeseries(lemspath)

    start_time = Ldata['time'][0]
    convert_start = datetime.strptime(start_time, "%Y%m%d  %H:%M:%S")  # convert str to datetime object
    shift_start = convert_start + timedelta(seconds=delta_for_seconds)

    start_string = shift_start.strftime("%Y%m%d %H:%M:%S")
    line = ('A start time of ' + start_string + ' was assigned to the Pico dataset. This time was shifted by ' +
         str(delta_for_seconds) + ' seconds from the LEMS start time.')
    print(line)
    logs.append(line)

    data['time'] = []
    for num in data['seconds']:
        data['time'].append(shift_start)
        shift_start = shift_start + timedelta(seconds=sample_rate)

    # write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    return logs

#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_Pico(inputpath, lemspath, outputpath, logpath)
