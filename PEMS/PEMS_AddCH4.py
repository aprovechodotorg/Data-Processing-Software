#v 2.0  python 3

#    Copyright (C) 2023 Mountain Air Engineering 
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
import numpy as np
from numpy import math
import matplotlib.pyplot as plt
import math
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import copy

#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\Projects\Brick_kilns\Data\Colombia\Event0\Event0_RawData_LinesRemoved.csv'
#output data file to be created:
outputpath='C:\Mountain Air\Projects\Brick_kilns\Data\Colombia\Event0\Event0_RawData_ReCalced.csv'
#input file of Ratnoze output header to be used for the recalculation
matrixpath='C:\Mountain Air\Projects\Brick_kilns\Data\Colombia\Event0\Inputs\Event0_Header.csv'
logpath='C:\Mountain Air\Projects\Brick_kilns\Data\Colombia\Event0\Event0_log.txt'
var=3
##########################################

#Corrects sensor signals for cross-sensitivities
#Reads in times series data from csv file 
#Reads in sensor cross-sensitivity matrix
#Writes recalculated data to the output csv file

def PEMS_AddCH4(inputpath,outputpath,matrixpath,logpath):

    ver = '2.0'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_AddCH4 v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    plot_channels=[]    #list of calculated channels to plot at the end to check the changes that were made to the data. Sensor signals will get added later in the code if they are modified
    
    Tstd=float(293)     #define standard temperature in Kelvin
    Pstd=float(101325)   #define standard pressure in Pascals
    
    #################################################
    # load time series data input file 
    [names,units,data_old] = io.load_timeseries(inputpath) 
    line = 'loaded time series input file: '+inputpath
    print(line)
    logs.append(line)
    
    ##############################################
    #give instructions
    @@@@@@@@@@@@@@@@@@@@@@@@@@@
    firstline='Open the matrix input file and edit the desired calibration parameters:\n\n'
    secondline=matrixpath
    thirdline='\n\nSave and close the matrix input file then click OK to continue'
    boxstring=firstline+secondline+thirdline
    msgtitle='gitrdun'
    easygui.msgbox(msg=boxstring,title=msgtitle)
    
    ######################################################
    
    #load matrix input file
    [matrixnames,matrixunits,matrixval,matrixunc,matrixuval]=io.load_constant_inputs(matrixpath)
    matrixnames=matrixnames[1:] #remove the first name because it is the header
    
    line = 'Loaded matrix input file:'+matrixpath
    print(line)
    logs.append(line)
    #end of read in matrix
    ##############################################################
    #create the output data series
    #channels without calculations are copied straight from the old sheet 
    #channels with calculations are recalculated using the values from the new header

    data_new = copy.deepcopy(data_old)
    
    for name in matrixnames:
        spot = name.index('_')
        yvar = name[:spot]
        xvar = name[spot+1:]
        corrected=[]
        for n,val in enumerate(data_new[yvar]):
            newval = val - data_new[xvar][n]*float(matrixval[name])
            corrected.append(newval)
        data_new[yvar] = corrected
        plot_channels.append(yvar)

    ###############################################################
    #print updated time series data file
    io.write_timeseries(outputpath,names,units,data_new)
    
    line = 'created: '+outputpath
    print(line)
    logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)

    ##################################################   
     #plot the old and new data series to inspect the differences 
    
    firstline='The following plots show the corrections. Close the plots to continue.'
    msgtitle='gitrdun'
    easygui.msgbox(msg=firstline,title=msgtitle)

    for (fignum,name) in enumerate(plot_channels): #for each plot channel
        for n in range(len(data_old[name])):
            data_old[name][n]=float(data_old[name][n])          # convert old and new data series to floats 
            data_new[name][n]=float(data_new[name][n])      # to remove strings so they will plot
        plt.figure(fignum+1)
        old=plt.plot(data_old[name], label=name + ' old')
        new=plt.plot(data_new[name], label=name + ' new')
        plt.xlabel('data points')
        plt.ylabel(units[name])
        plt.legend()
    plt.show()
    #end of figure
    #end of function
#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_AddCH4(inputpath,outputpath,matrixpath,logpath)