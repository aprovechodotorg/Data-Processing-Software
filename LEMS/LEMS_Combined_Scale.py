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

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_FormattedScaleData.csv"
inputpath2 = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_FormattedAdamScaleData.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_FormattedCombinedScaleData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\scale\\sacle_log.txt"


def LEMS_Combined_Scale(inputpath, inputpath2, outputpath, logpath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Combined_Scale v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    [snames, sunits, sdata] = io.load_timeseries(inputpath)

    line = 'Loaded scale time series data:' + inputpath
    print(line)
    logs.append(line)

    [anames, aunits, adata] = io.load_timeseries(inputpath2)

    line = 'Loaded Adam scale time series data:' + inputpath2
    print(line)
    logs.append(line)

    names = []
    units = {}
    data = {}

    sdata['datetime'] = []
    adata['datetime'] = []

    for time in sdata['time']:
        sdata['datetime'].append(datetime.strptime(time, "%Y%m%d %H:%M:%S"))

    for time in adata['time']:
        adata['datetime'].append(datetime.strptime(time, "%Y%m%d %H:%M:%S"))

    sdownsampled = {}
    for time, weight in zip(sdata['datetime'], sdata['weight']):
        sec = time.replace(microsecond=0)
        if sec not in sdownsampled:
            sdownsampled[sec] = weight  # Keep the first weight in each second

    adownsampled = {}
    for time, weight in zip(adata['datetime'], adata['weight']):
        sec = time.replace(microsecond=0)
        if sec not in adownsampled:
            adownsampled[sec] = weight  # Keep the first weight in each second

    # Determine overlapping time range (starting from the later start time)
    start_time = max(min(sdownsampled), min(adownsampled))
    end_time = min(max(sdownsampled), max(adownsampled))

    name = 'time'
    names.append(name)
    units[name] = 'yyyymmdd hh:mm:ss'
    data[name] = []

    name = 'seconds'
    names.append(name)
    units[name] = 's'
    data[name] = []

    name = 'weight1'
    names.append(name)
    units[name] = sunits['weight']
    data[name] = []

    name = 'weight2'
    names.append(name)
    units[name] = aunits['weight']
    data[name] = []

    name = 'weight'
    names.append(name)
    units[name] = sunits['weight']
    data[name] = []

    current = start_time
    seconds = 1
    while current < end_time:
        w1 = sdownsampled.get(current, 0.0)
        w2 = adownsampled.get(current, 0.0)
        data['time'].append(current.strftime("%Y%m%d %H:%M:%S"))
        data['weight1'].append(w1)
        data['weight2'].append(w2)
        data['weight'].append(w1 + w2)
        data['seconds'].append(seconds)

        seconds += 1
        current += timedelta(seconds=1)

    #write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)


    #print to log file
    io.write_logfile(logpath, logs)

    return logs

