#v0 Python3

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

import os
import LEMS_DataProcessing_IO as io
import easygui

#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData2.csv'
#output data file to be created:
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TimeSeries_Shifted.csv'
#input file of time shifts for each data channel
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TimeShifts.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_log.txt'
##########################################

def LEMS_ShiftTimeSeries(inputpath,outpath,timespath,logpath):

    shiftunits={}
    nom = {}
    unc = {}
    shift = {}

    line = 'LEMS_ShiftTimeSeries'
    print(line)
    logs=[line]
    
    #################################################
    #read in raw data file
    
    [names,units,data] = io.load_timeseries(inputpath)
       
 ##############################################
    #read in TimeShifts input file
    
    #check for input file
    if os.path.isfile(timespath):
        print('TimeShifts input file already exists:')
    else:   #if input file is not there then create it
        for name in names:
            if name == 'time':
                shiftunits[name]='units'
                shift[name]='value'
            else:
                shiftunits[name] = 'sec'
                shift[name] = 0
        io.write_constant_outputs(timespath,names,shiftunits,nom,unc,shift)
        print('TimeShifts input file created:')
    print('')
    print(timespath)
    print('')
    
    ##give instructions to manually edit the input file
    #firstline='Open the TimeShifts input file and edit the values:\n\n'
    #secondline=timespath
    #thirdline='\n\nNegative values shift time series back in time'
    #forthline='\n\nPositive values shift time series forward in time'
    #boxstring=firstline+secondline+thirdline+forthline
    #msgtitle='gitrdone'
    #easygui.msgbox(msg=boxstring,title=msgtitle)
    
    #open input file and load time shift values into dictionary
    [shiftnames,shiftunits,shift,unc,val] = io.load_constant_inputs(timespath)
    
    #edit time shift values in input file
    firstline='Enter the seconds to shift each data series'
    thirdline='\nNegative values shift the series back in time'
    forthline='\nPositive values shift the series forward in time'
    msg=firstline+thirdline+forthline
    title = "Gitrdone"
    fieldNames = names[3:]
    currentvals=[]
    for name in names[3:]:
        currentvals.append(shift[name])
    newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
            for n,name in enumerate(names[3:]):
                shift[name]=currentvals[n]
            io.write_constant_outputs(timespath,names,shiftunits,shift,unc,val)
            print('TimeShifts input file edited:')
            print('')
            print(timespath)
            print('')
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
    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
    ##############################################    
    #plot old and new time series
    
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath)