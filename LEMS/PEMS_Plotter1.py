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

#gui to select time series csv data file
# converts time strings to date numbers for plotting
# passes data

from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import matplotlib
import easygui
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
import sys
import os
import csv
from datetime import datetime as dt
import re

#########      inputs      ##############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#raw data input file:
inputpath = 'TimeSeries.csv'
fuelpath = 'FuelDataCut.csv'
fuelmetricpath = 'FuelMetric.csv'
exactpath = 'ExactDataCut.csv'
scalepath = 'FormattedScaleData.csv'
intscalepath = 'FormattedIntScaleData.csv'
nanopath = 'FormattedNanoscanData.csv'
TEOMpath = 'FormattedTEOMData.csv'
senserionpath = 'FormattedSenserionData.csv'
OPSpath = 'FormattedOPSData.csv'
plotpath = 'plots.csv'
savefig = 'fullperiodplot.png'
logpath = 'log.txt'
#can be raw data file from sensor box with full raw data header, or processed data file with only channel names and units for header
##################################


def PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, nanopath, TEOMpath,
                 senserionpath, OPSpath,
                 Picopath, plotpath, savefig, logpath):
    #Take in data files and check if plotfile exists. If not create csv to specify variables to be plotted, scale, and color

    #Function intakes list of inputpaths and creates comparission between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_Plotter v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    fnames = []
    fcnames = []
    exnames =[]
    snames = []
    isnames = []
    anames = []
    nnames = []
    tnames = []
    sennames = []
    opsnames = []
    pnames = []

    try: #if the data file has a raw data header
        [names,units,data,A,B,C,D,const] = io.load_timeseries_with_header(inputpath)
        line = 'loaded raw data file with header = A,B,C,D,units,names: ' + inputpath
        print(line)
        logs.append(line)
    except: #if the data file does not have a raw data header
        [names,units,data] = io.load_timeseries(inputpath)
        line = 'loaded processed data file without header = names, units: ' +inputpath
        print(line)
        logs.append(line)

    #time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name] = 'date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    try:
        for n,val in enumerate(data['time']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S') #Convert time to readble datetime object
            data[name].append(dateobject)
    except: #some files have different name convention
        for n,val in enumerate(data['time_test']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
            data[name].append(dateobject)

    name='datenumbers'
    units[name]='date'
    #names.append(name)
    datenums=matplotlib.dates.date2num(data['dateobjects'])
    datenums=list(datenums)     #convert ndarray to a list in order to use index function
    data['datenumbers']=datenums

    if os.path.isfile(fuelpath):
        #Read in fuel data if it exists
        [fnames, funits, fdata] =io.load_timeseries(fuelpath)

        fnames.remove('Temperature')

        type = 'f'
        names, units, data = loaddatastream(fnames, funits, fdata, names, units, data, type)

    if os.path.isfile(fuelmetricpath):
        #Read in exact temp data if file exists
        [fcnames, fcunits, fcdata] = io.load_timeseries(fuelmetricpath)
        type = 'fc'
        names, units, data = loaddatastream(fcnames, fcunits, fcdata, names, units, data, type)

    if os.path.isfile(exactpath):
        #Read in exact temp data if file exists
        [exnames, exunits, exdata] = io.load_timeseries(exactpath)
        type = 'ex'
        names, units, data = loaddatastream(exnames, exunits, exdata, names, units, data, type)

    if os.path.isfile(scalepath):
        #Read in lems adam scale data if file exists
        [snames, sunits, sdata] = io.load_timeseries(scalepath)
        type = 's'
        names, units, data = loaddatastream(snames, sunits, sdata, names, units, data, type)

    if os.path.isfile(intscalepath):
        #Read in intelligent scale  data if file exists
        [isnames, isunits, isdata] = io.load_timeseries(intscalepath)
        type = 'is'
        names, units, data = loaddatastream(isnames, isunits, isdata, names, units, data, type)

    if os.path.isfile(ascalepath):
        #Read in osprey adam scale data if file exists
        [anames, aunits, adata] = io.load_timeseries(ascalepath)
        type = 'a'
        names, units, data = loaddatastream(anames, aunits, adata, names, units, data, type)

    if os.path.isfile(nanopath):
        #Read in exact temp data if file exists
        [nnames, nunits, ndata] = io.load_timeseries(nanopath)
        type = 'n'
        names, units, data = loaddatastream(nnames, nunits, ndata, names, units, data, type)

    if os.path.isfile(TEOMpath):
        #Read in teom data if file exists
        [tnames, tunits, tdata] = io.load_timeseries(TEOMpath)
        type = 't'
        names, units, data = loaddatastream(tnames, tunits, tdata, names, units, data, type)

    if os.path.isfile(senserionpath):
        #Read in exact temp data if file exists
        [sennames, senunits, sendata] = io.load_timeseries(senserionpath)
        type = 'sen'
        names, units, data = loaddatastream(sennames, senunits, sendata, names, units, data, type)
        for n, name in enumerate(sennames): #TC channels already exist, rename to avoid confusion
            if 'TC' in name:
                sennames[n] = 'S' + name

    if os.path.isfile(OPSpath):
        #Read in exact temp data if file exists
        [opsnames, opsunits, opsdata] = io.load_timeseries(OPSpath)
        type = 'ops'
        names, units, data = loaddatastream(opsnames, opsunits, opsdata, names, units, data, type)

    if os.path.isfile(Picopath):
        #Read in exact temp data if file exists
        [pnames, punits, pdata] = io.load_timeseries(Picopath)
        type = 'p'
        names, units, data = loaddatastream(pnames, punits, pdata, names, units, data, type)


    ################
    #looking for or creating a file to designate what plots will be made and their scales

    #Check if plot csv already exists
    if os.path.isfile(plotpath):
        line = 'Plot file already exists: ' + plotpath
        print(line)
        logs.append(line)
    else:  # if plot file is not there then create it by printing the names
        var = ['Variable']
        for name in names: #create new names list with header that won't interfere with other calcs later
            print(name)
            if name != 'time' and name != 'seconds' and name != 'ID' and name != 'ftime' and name!= 'fseconds' \
                    and name != 'extime' and name != 'exseconds' and name != 'stime' and name != 'sseconds' and name != 'isseconds' and name != 'aseconds'\
                    and name != 'ntime' and name != 'nseconds' and name != 'ttime' and name != 'tseconds'\
                    and name != 'sentime' and name != 'senseconds' and '_uc' not in name and name != 'fctime' \
                    and 'fctime' not in name: #Don't add these values as plottable variables
                var.append(name)
        on = [0] * len(var) #Create a row to specify if that value is being plotted default is off (0)
        on[0] = 'Plotted'
        scale = [1] * len(var) #Create a row to specify scale default is 1
        scale[0] = 'Scale'
        colors = [''] * len(var) #Create a row of random colors
        colors[0] = 'Colors'
        order = [''] * len(var) #Create a row of order
        order[0] = 'Order'

        output = zip(var, on, scale, colors, order) #list of lists to be written switched to columns
        with open(plotpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row in output:
                writer.writerow(row)
        line = 'Plot file created: ' +plotpath
        print(line)
        logs.append(line)

    return names, units, data, fnames, fcnames, exnames, snames, isnames, anames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig
    #PEMS_PlotTimeSeries(names,units,data, plotpath, savefig)    #send data to plot function

    #print to log file
    io.write_logfile(logpath,logs)

def loaddatastream(new_names, new_units, new_data, names, units, data, type):
    for name in new_names:
        # add new values to dictionary
        # Time is already in dictionary, rename to not overwrite data
        if name == 'time':
            newname = type + 'time'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # seconds is already in dictionary, rename to not overwrite data
        elif name == 'seconds':
            newname = type + 'seconds'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # all other data can be added without ov
        elif 'TC' in name: #senserion data also has TC channels - rename so they don't get mixed up
            newname = 'S' + name
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        else:
            names.append(name)
            data[name] = new_data[name]
            units[name] = new_units[name]

    # Convert date strings to date numbers for plotting
    name = type + 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data[type + 'time']):
        try:
            dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        except:
            dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)

    name = type + 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data[type + 'dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    return names, units, data

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, nanopath, TEOMpath, senserionpath, OPSpath, plotpath, savefig, logpath)
