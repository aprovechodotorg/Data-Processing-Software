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

#########      inputs      ##############
#raw data input file:
#inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_TimeSeriesShifted.csv'
#can be raw data file from sensor box with full raw data header, or processed data file with only channel names and units for header
##################################

line = 'Select time series data file:'
print(line)
inputpath = easygui.fileopenbox()
line=inputpath
print(line)

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
for n,val in enumerate(data['time']):
    dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
    data[name].append(dateobject)   
    
name='datenumbers'
units[name]='date'
#names.append(name)
datenums=matplotlib.dates.date2num(data['dateobjects'])
datenums=list(datenums)     #convert ndarray to a list in order to use index function
data['datenumbers']=datenums


PEMS_PlotTimeSeries(names,units,data)    #send data to plot function