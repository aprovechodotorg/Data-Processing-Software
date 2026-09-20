# Python3

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

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os
from uncertainties import ufloat

#########      inputs      ##############
#raw data input file:
inputpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_RawData.csv'
#output data file to be created:
outputpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_RawData_wH2Oppm.csv'
logpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def PEMS_CalcH2Oppm(inputpath,outputpath,logpath):
    # calculates H2O channel from RH signal
    # ver = '2.0' # renamed H2O to H2Orh
    ver = '3.0' # added legend
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CalcH2Oppm v'+ver+'   '+timestampstring
    print(line)
    logs=[line]

    #################################################
    
    #read in time series file
    [names,units,data] = io.load_timeseries(inputpath)
    
    #time channel: convert date strings to date numbers
    name = 'dateobjects'
    units[name]='date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name]=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)
     
    ###########################################################
    # H2O in diluted sample from RH signal
    
    # vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    # P=10^(a-b/(c+T))
    # P = vapor pressure (mmHg)
    # T = temperature (C)
    a = 8.07131  # constant
    b = 1730.63  # constant
    c = 233.426  # constant
    
    name = 'Psat'  # saturation pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name]=[]
    try:
        T = data['RHtemp']
    except:
        T = data['COtemp']
    for n,t in enumerate(T):
        psat = np.power(10, (a - b / (c + t))) / .0075  # 1 Pa = 0.0075 mmHg
        data[name].append(psat)
        
    
    name = 'PH2O'  # partial pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name]=[]
    for n,p in enumerate(data['Psat']):
        ph2o = p * data['RH'][n] / 100
        data[name].append(ph2o)
    
    name = 'H2Orh'  # H2O concentration
    names.append(name)
    units[name] = 'ppm'
    data[name]=[]
    for n,ph2o in enumerate(data['PH2O']):
        h2o = ph2o / data['Pamb'][n] * 1000000  # ppm
        data[name].append(h2o)

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated H2O concentration ' + timestampstring)

    io.write_timeseries(outputpath,names,units,data)    
 
    line='created time series data file with H2O channels:\n'+outputpath
    print(line)
    logs.append(line)
    
    #print to log file
    io.write_logfile(logpath,logs)
    
    #plot data to check bkg and test periods
    
    #first create datenumbers for plot
    name='datenumbers'
    if name not in names:   #if datenumbers series is not already there (may have been created by CorrectDrift)
        units[name]='date'
        #names.append(name)
        datenums=matplotlib.dates.date2num(data['dateobjects'])
        datenums=list(datenums)     #convert ndarray to a list in order to use index function
        data['datenumbers']=datenums
        
    plt.ion()  #turn on interactive plot mode

    f1, (ax1, ax2) = plt.subplots(2, sharex=True) # subplots sharing x axis

    ax1.plot(data['datenumbers'],data['H2Orh'],color='blue',label='H2O Possum')   #
    try:
        ax1.plot(data['datenumbers'],data['H2Ogm'],color='purple', label='H2O LGR')   #
    except:
        line = 'no LGR data'
        print(line)
        logs.append(line)
    ax2.plot(data['datenumbers'],data['RH'],color='black',label='RH')   #
    ax2.plot(data['datenumbers'],data['RHtemp'],color='orange', label='RH temp')   #   
    
    ax1.set_ylabel(units['H2Orh'])
    ax1.set_title('H2O')
    ax1.grid(visible=True, which='major', axis='y')
    
    ax2.set_ylabel(units['RH'])
    ax2.set_title('RH')
    ax2.grid(visible=True, which='major', axis='y')
    
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax2.xaxis.set_major_formatter(xfmt)
    for tick in ax2.get_xticklabels():
        tick.set_rotation(30)
    #plt.xlabel('time')
    #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
    #plt.legend(fontsize=10).draggable()
    box = ax2.get_position()
    ax2.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
    plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it verically to make room for the long x axis data labels
    ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
    ax2.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax2
    
    plt.show()
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_CalcH2Oppm(inputpath,outputpath,logpath)

