#v0.2 Python3

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

# do: 
# add plot
# fix easygui for SB4003: channel list is too long to fit on screen

import os
import LEMS_DataProcessing_IO as io
import easygui
from datetime import datetime as dt


#########      inputs      ##############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#raw data input file:
inputpath='RawData.csv'
#output data file to be created:
outputpath='TimeSeriesShifted.csv'
#input file of time shifts for each data channel
timespath='TimeShifts.csv'
logpath='log.txt'
##########################################

def LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath):
    #This function shifts time series data channels forward or backward in time (sensor response time correction)

    ver = '0.2'
    shiftunits={}
    val = {}
    unc = {}
    uval={}
    shift = {}
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_ShiftTimeSeries v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    #################################################
    #read in raw data file
    
    [names,units,data] = io.load_timeseries(inputpath)
    
    line = 'Loaded time series data file:'+inputpath
    print(line)
    logs.append(line)
       
 ##############################################
    #read in TimeShifts input file
    
    #check for input file
    if os.path.isfile(timespath):
        line='\nTimeShifts input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        for name in names:
            if name == 'time':
                shiftunits[name]='units'
                shift[name]='value'
            else:
                shiftunits[name] = 'sec'
                shift[name] = 0
        io.write_constant_outputs(timespath,names,shiftunits,shift,unc,uval)
        line='\nTimeShifts input file created:'
        print(line)
        logs.append(line)
    line=timespath
    print(line)
    logs.append(line)
    
    ##give instructions to manually edit the input file
    #firstline='Open the TimeShifts input file and edit the values:\n\n'
    #secondline=timespath
    #thirdline='\n\nNegative values shift time series back in time'
    #forthline='\n\nPositive values shift time series forward in time'
    #boxstring=firstline+secondline+thirdline+forthline
    #msgtitle='gitrdone'
    #easygui.msgbox(msg=boxstring,title=msgtitle)
    
    #open input file and load time shift values into dictionary
    [shiftnames,shiftunits,shift,unc,uval] = io.load_constant_inputs(timespath)
    
    #edit time shift values in input file
    firstline='Enter the seconds to shift each data series'
    thirdline='\nNegative values shift the series back in time'
    forthline='\nPositive values shift the series forward in time'
    fifthline='\n(Omitted light sensor channels)'
    msg=firstline+thirdline+forthline+fifthline
    title = "Gitrdone"
    fieldNames = []
    for name in names[3:]:
        if 'AS' not in name:                    #skip the light sensor channels because the easygui box is too long
        #if 'AS' not in name and 'TC' not in name:                    #skip the TCs and light sensor channels because the easygui box is too long
            fieldNames.append(name) 
        
    currentvals=[]
    for name in names[3:]:
        currentvals.append(shift[name])
    newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
            for n,name in enumerate(fieldNames):
                shift[name]=currentvals[n]
            io.write_constant_outputs(timespath,names,shiftunits,shift,unc,uval)
            
            line='\nTimeShifts input file edited:\n'+timespath
            print(line)
            logs.append(line)
    ###################################################################
    # shift the data series
    for name in names[1:]: #skip the first name ('time') because shift[time] is a string ('units')
        shift[name]=int(shift[name]) #shift dictionary was loaded as strings. convert to int
        if shift[name] < 0:
            pad = shift[name]*-1
            data[name][:pad]=[]                                #delete the first data points
            tailend=[data[name][-1]]*pad            #stretch the last data point to make end pad
            data[name]=data[name]+tailend       #put the pad on the end of the series
            
            line='shifted '+name+' '+str(pad)+' seconds up (back in time)'
            print(line)
            logs.append(line)
            
        if shift[name] > 0:
            pad=shift[name]
            data[name][-pad:]=[]                           #delete the last data points
            frontpad=[data[name][0]]*pad            #stretch the first data point to make pad
            data[name]=frontpad+data[name]      #put the pad on the front of the series
            
            line='shifted '+name+' '+str(pad)+' seconds down (forward in time)'
            print(line)
            logs.append(line)
         
    ##############################################
    #print the time series output file
    io.write_timeseries(outputpath,names,units,data)
    
    line='created new shifted time series data file:\n'+outputpath
    print(line)
    logs.append(line)    
    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
    ##############################################    
    #plot old and new time series
    
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath)