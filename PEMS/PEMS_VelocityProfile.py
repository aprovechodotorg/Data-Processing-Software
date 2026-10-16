

#    Copyright (C) 2026 Mountain Air Engineering 
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
#    Contact: ryan@mtnaireng.com   

import os
import csv
import matplotlib.pyplot as plt
import numpy as np
import copy
import math
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import sys
import matplotlib

#########      inputs (only used if this script is run as executable)     ######################
#input file of raw data:
inputpath='Test1_TimeSeriesStackFlow.csv'
#output file with TAP data patches that will be created:
outputpath='Test1_VelocityProfileOutputs.csv'
#input file with a table of start and stop times for each TAP data patch:
timespath='Test1_VelocityProfileInputs.csv'
#event log pile:
logpath='Test1_log.txt'
######################################################################

def PEMS_VelocityProfile(inputpath,outputpath,timespath,logpath):
    print(inputpath)
    ver = '0.1'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'VelocityProfile v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    #initialize dictionaries 
    data_old={}
    units={}
    

    ########################################################
    #read in time series file
    
    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)
  
    #check for times input file
    
    if os.path.isfile(timespath):
        print('start stop times input file already exists:')
    else:   #If the times input file is not there then create it with a blank table
    
        with open(timespath, 'w',newline='') as csvfile: 
            writer = csv.writer(csvfile)
            writer.writerow(['point','starttime','endtime'])
        print('start stop times input file created:')
    
    ##################################################################
    print('')
    print(timespath)
    print('')
    
    ######################################################################
    #read in the start and stop times file
    [pointlist,starttime,endtime,blank,blank] = io.load_constant_inputs(timespath)
        
    points = pointlist[1:]
            
    ##############################################################
    #define velocity channel from input time series file
    #stakvel = 'StakVel'
    stakvel = 'StakVelCor'
    
    #get the date from the time series data
    date=data['time'][0][:8]
    
    startdatestring={}
    starttimeobject={}
    startdatenum = {}
    startindex={}
    enddatestring = {}
    endtimeobject = {}
    enddatenum = {}
    endindex = {}
    datenums = {}
    vel={}
    v={}
    for point in points:
        print(point)
        startdatestring[point] = date+' '+starttime[point]
        starttimeobject[point] = dt.strptime(startdatestring[point], '%Y%m%d %H:%M:%S')                #convert the time string to date object
        startdatenum[point] = matplotlib.dates.date2num(starttimeobject[point])
        startindex[point]=data['datenumbers'].index(startdatenum[point])
        enddatestring[point] = date+' '+endtime[point]
        endtimeobject[point] = dt.strptime(enddatestring[point], '%Y%m%d %H:%M:%S')                #convert the time string to date object
        enddatenum[point] = matplotlib.dates.date2num(endtimeobject[point])
        endindex[point]=data['datenumbers'].index(enddatenum[point])
        datenums[point] = data['datenumbers'][startindex[point]:endindex[point]+1]   
        vel[point] = data[stakvel][startindex[point]:endindex[point]+1] 
        v[point] = np.nanmean(vel[point])
    
    v['point'] = 'v'
    io.write_constant_outputs(outputpath,pointlist,starttime,endtime,v,blank)
    
    #print to log file
    io.write_logfile(logpath,logs)

#####################################################################    
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_VelocityProfile(inputpath,outputpath,timespath,logpath)
     