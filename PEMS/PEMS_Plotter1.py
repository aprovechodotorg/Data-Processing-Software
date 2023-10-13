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
exactpath = 'ExactDataCut.csv'
plotpath = 'plots.csv'
savefig = 'fullperiodplot.png'
logpath = 'log.txt'
#can be raw data file from sensor box with full raw data header, or processed data file with only channel names and units for header
##################################

def PEMS_Plotter(inputpath, fuelpath, exactpath, fuelmetricpath, plotpath, savefig, logpath):
    #Take in data files and check if plotfile exists. If not create csv to specify variables to be plotted, scale, and color

    #Function intakes list of inputpaths and creates comparission between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_Plotter v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    try: #if the data file has a raw data header
        [names,units,data,A,B,C,D,const] = io.load_timeseries_with_header(inputpath)
        line = 'loaded raw data file with header = A,B,C,D,units,names: ' + inputpath
        print(line)
        logs.append(line)
    except: #if the data file does not have a raw data header
        [names,units,data] = io.load_timeseries(inputpath)
        line = 'loaded processed data file with header = names, units: ' +inputpath
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

        #add new values to dictionary
        for name in fnames:
            #Time is already in dictionary, rename to not overwrite data
            if name == 'time':
                fname = 'ftime'
                names.append(fname)
                units[fname] = funits[name]
                data[fname] = fdata[name]
            #seconds is already in dictionary, rename to not overwrite data
            elif name == 'seconds':
                fname = 'fseconds'
                names.append(fname)
                units[fname] = funits[name]
                data[fname] = fdata[name]
            #all other data can be added without overwriting current dictionary items
            else:
                names.append(name)
                units[name] = funits[name]
                data[name] = fdata[name]

        #Convert date strings to date numbers for plotting
        name = 'fdateobjects'
        units[name] = 'date'
        data[name] = []
        for n,val in enumerate(data['ftime']):
            dateobject=dt.strptime(val, '%Y-%m-%d %H:%M:%S')
            data[name].append(dateobject)

        name = 'fdatenumbers'
        units[name] = 'date'
        datenums = matplotlib.dates.date2num(data['fdateobjects'])
        datenums = list(datenums)
        data[name] = datenums

    if os.path.isfile(exactpath):
        #Read in exact temp data if file exists
        [exnames, exunits, exdata] = io.load_timeseries(exactpath)

        # add new values to dictionary
        for name in exnames:
            # Time is already in dictionary, rename to not overwrite data
            if name == 'time':
                exname = 'extime'
                names.append(exname)
                units[exname] = exunits[name]
                data[exname] = exdata[name]
            # seconds is already in dictionary, rename to not overwrite data
            elif name == 'seconds':
                exname = 'exseconds'
                names.append(exname)
                units[exname] = exunits[name]
                data[exname] = exdata[name]
            # all other data can be added without overwriting current dictionary items
            else:
                names.append(name)
                units[name] = exunits[name]
                data[name] = exdata[name]
        # Convert date strings to date numbers for plotting
        name = 'exdateobjects'
        units[name] = 'date'
        data[name] = []
        for n, val in enumerate(data['extime']):
            dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
            data[name].append(dateobject)

        name = 'exdatenumbers'
        units[name] = 'date'
        datenums = matplotlib.dates.date2num(data['exdateobjects'])
        datenums = list(datenums)
        data[name] = datenums

    if os.path.isfile(fuelmetricpath):
        stuff = []
        with open(fuelmetricpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        #find the row inex for the data
        for n, row in enumerate(stuff[:100]): #interate through first 101 rows
            if 'time' in row:
                namesrow = n #assign name row
        datarow = namesrow + 1 #data is one below names

        tempnames = []
        for name in stuff[namesrow]:
            tempnames.append(name)

        rnames = []
        runits = {}
        rdata = {}
        q = 0
        for n, name in enumerate(tempnames):
            # Define a regular expression pattern to capture text inside parentheses
            pattern = r'\((.*?)\)'

            # Use the re.search function to find the first match of the pattern
            unit_match = re.search(pattern, name)

            # Extract the units if found
            unit = unit_match.group(1) if unit_match else ""

            # Remove the units from the input string
            cleaned_string = re.sub(pattern, '', name).strip()
            if cleaned_string == 'Loading Frequency':
                if q == 0:
                    cleaned_string = 'Hour Loading Frequency'
                    q += 1
                if q == 1:
                    cleaned_string = 'Minute Loading Frequency'
                    q += 1
                if q == 2:
                    cleaned_string = 'Second Loading Frequency'
                    q += 1

            rnames.append(cleaned_string)
            runits[cleaned_string] = unit
            rdata[cleaned_string] = [x[n] for x in stuff[datarow:]]

        # add new values to dictionary
        for name in rnames:
            # Time is already in dictionary, rename to not overwrite data
            if name == 'time':
                rname = 'rtime'
                names.append(rname)
                units[rname] = runits[name]
                data[rname] = rdata[name]
            # seconds is already in dictionary, rename to not overwrite data
            elif name == 'seconds':
                rname = 'rseconds'
                names.append(rname)
                units[rname] = runits[name]
                data[rname] = rdata[name]
            # all other data can be added without overwriting current dictionary items
            else:
                names.append(name)
                units[name] = runits[name]
                data[name] = rdata[name]
        # Convert date strings to date numbers for plotting
        name = 'rdateobjects'
        units[name] = 'date'
        data[name] = []
        for n, val in enumerate(data['rtime']):
            try:
                dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
            except:
                print(val)
                dateobject = dt.strptime(val, '%Y%m%d %H%M%S')
            data[name].append(dateobject)

        name = 'rdatenumbers'
        units[name] = 'date'
        datenums = matplotlib.dates.date2num(data['rdateobjects'])
        datenums = list(datenums)
        data[name] = datenums
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
            if name != 'time' and name != 'seconds' and name != 'ID' and name != 'ftime' and name!= 'fseconds' and name != 'extime' and name != 'exseconds': #Don't add these values as plottable variables
                var.append(name)
        on = [0] * len(var) #Create a row to specify if that value is being plotted default is off (0)
        on[0] = 'Plotted'
        scale = [1] * len(var) #Create a row to specify scale default is 1
        scale[0] = 'Scale'
        colors = [''] * len(var) #Create a row of random colors
        colors[0] = 'Colors'

        output = zip(var, on, scale, colors) #list of lists to be written switched to columns
        with open(plotpath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row in output:
                writer.writerow(row)
        line = 'Plot file created: ' +plotpath
        print(line)
        logs.append(line)

    PEMS_PlotTimeSeries(names,units,data, plotpath, savefig)    #send data to plot function

    #print to log file
    io.write_logfile(logpath,logs)

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig, logpath)