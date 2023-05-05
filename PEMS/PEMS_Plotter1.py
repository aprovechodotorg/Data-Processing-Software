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

#########      inputs      ##############
#raw data input file:
inputpath = 'PEMS/Data/hh12/hh12_test2/hh12_test2_TimeSeries.csv'
plotpath = 'PEMS/Data/hh12/hh12_test2/hh12_test2_plots.csv'
#can be raw data file from sensor box with full raw data header, or processed data file with only channel names and units for header
##################################

##################################################################        

# Error handling function that prints the error and keeps the terminal open so the user can read the error
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)
    #For launcher. If error, holds terminal open so user knows what to fix

sys.excepthook = show_exception_and_exit
####################################################
'''
line = 'Select time series data file:'
print(line)
inputpath = easygui.fileopenbox()
line=inputpath
print(line)
'''
def PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig):
    try: #if the data file has a raw data header
        [names,units,data,A,B,C,D,const] = io.load_timeseries_with_header(inputpath)
        print('raw data file with header = A,B,C,D,units,names')
    except: #if the data file does not have a raw data header
        [names,units,data] = io.load_timeseries(inputpath)
        print('processed data file with header = names, units')

    #time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name]='date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name]=[]
    try:
        for n,val in enumerate(data['time']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
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

    ################
    #looking for or creating a file to designate what plots will be made and their scales

    '''
    #split inputpath to find testname and directory
    directory,filename=os.path.split(inputpath)
    datadirectory,testname=os.path.split(directory)
    
    #designate plotpath direction
    plotpath = os.path.join(directory, testname + '_plots.csv')
    '''
    #Check if plot csv already exists
    if os.path.isfile(plotpath):
        print('Plot file already exists:')
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
        print('Plot file created:')



    PEMS_PlotTimeSeries(names,units,data, plotpath, savefig)    #send data to plot function

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_Plotter(inputpath, plotpath)