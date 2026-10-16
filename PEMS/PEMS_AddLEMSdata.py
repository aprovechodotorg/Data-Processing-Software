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

import PEMS_DataProcessing_IO as io
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
inputpath='...testname_TimeSeriesStackFlow.csv'
#output data file to be created:
outputpath='...testname_TimeSeriesStackFlow_wLEMS.csv'
#input file of LEMS data
LEMSpath='...testname_LEMSTimeSeriesMetric_full.csv'
logpath='...testname_log.txt'
##########################################
def nominal(vals):
    #return nominal values from a list that may contain ufloats, floats, or nan
    return np.array([v.nominal_value if hasattr(v, 'nominal_value') else v for v in vals], dtype=float)

def stdev(vals):
    #return standard deviations from a list that may contain ufloats (0 for plain floats)
    return np.array([v.std_dev if hasattr(v, 'std_dev') else 0 for v in vals], dtype=float)


def PEMS_AddLEMSdata(inputpath,outputpath,LEMSpath,logpath):
    ver = '1.0'
    
    timeshift = 0 #shift timestamps _ hours sooner (if clocks are not synced or wrong time zone)
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_AddLEMSdata v'+ver+'   '+timestampstring
    print(line)
    logs=[line]

    #################################################
    
    #read in time series file
    [names,units,data] = io.load_timeseries_with_uncertainty(inputpath)
    
    #read in LEMS data file
    [LEMSnames,LEMSunits,LEMSdata] = io.load_timeseries(LEMSpath)
    
    #time channel: convert LEMS date strings to date objects
    name = 'dateobjects'
    LEMSunits[name]='date'
    LEMSdata[name]=[]
    for n,val in enumerate(LEMSdata['time']):
        dateobject=dt.strptime(val, '%Y%m%d %H:%M:%S')
        if timeshift > 0:       #shift time zone
            dateobject = dateobject - timedelta(hours=timeshift)
        LEMSdata[name].append(dateobject)   
        
    delta=[1]
    for n,val in enumerate(LEMSdata['dateobjects'][1:]):
        diff = LEMSdata['dateobjects'][n+1] - LEMSdata['dateobjects'][n]
        diff = diff.total_seconds()
        delta.append(diff)
    plt.plot(delta)
    plt.title('LEMS data time steps')
    plt.xlabel('data points')
    plt.ylabel('delta t (sec)')
    plt.show()

    #add LEMS data to data dict
    for LEMSname in LEMSnames:
        #if LEMSname != 'MIU_DESC': #add if statement here to skip channels
        name = LEMSname+'_LEMS'
        data[name] = [np.nan]*len(data['time'])
        units[name] = LEMSunits[LEMSname]
        names.append(name)
        
    #time channel: convert date strings to date numbers
    name = 'dateobjects'
    units[name]='date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name]=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)
        
    print('meshing LEMS timestamps to Possum timestamps')
    print('N='+str(len(data['dateobjects'])))
    for n,val in enumerate(data['dateobjects']):
        #find the closest LEMS index
        dateobject=min(LEMSdata['dateobjects'],key=lambda x: abs(x - val))
        #print(val)
        #print(dateobject)
        i=LEMSdata['dateobjects'].index(dateobject)
        #print(i)
        #define data dict values
        for LEMSname in LEMSnames:
            #if LEMSname != 'MIU_DESC': #add if statement here to skip channels
            name=LEMSname+'_LEMS'
            data[name][n] = LEMSdata[LEMSname][i]
        if n % 1000 == 0:
            print('n='+str(n))

    #add stack flow by COhi
    name='StakFlowbyCOhi'
    names.append(name)
    units[name] = units['StakFlow']
    data[name] = []
    for n,val in enumerate(data['dateobjects']):
        flow = data['CO_ER_LEMS'][n]/data['COhistakconc'][n]
        data[name].append(flow)
    
    #add stack flow by diluted CO
    name='StakFlowbyCO'
    names.append(name)
    units[name] = units['StakFlow']
    data[name] = []
    for n,val in enumerate(data['dateobjects']):
        flow = data['CO_ER_LEMS'][n]/data['COstakconc'][n]
        data[name].append(flow)
    
    #add stack flow by CO2hi
    name='StakFlowbyCO2hi'
    names.append(name)
    units[name] = units['StakFlow']
    data[name] = []
    for n,val in enumerate(data['dateobjects']):
        flow = data['CO2_ER_LEMS'][n]/data['CO2histakconc'][n]
        data[name].append(flow)
    
    #add stack flow by diluted CO2
    name='StakFlowbyCO2'
    names.append(name)
    units[name] = units['StakFlow']
    data[name] = []
    for n,val in enumerate(data['dateobjects']):
        flow = data['CO2_ER_LEMS'][n]/data['CO2stakconc'][n]
        data[name].append(flow)

    io.write_timeseries_with_uncertainty2(outputpath,names,units,data)    
 
    line='created time series data file with LEMS channels:\n'+outputpath
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
        
    LEMSunits[name]='date'
    #names.append(name)
    datenums=matplotlib.dates.date2num(LEMSdata['dateobjects'])
    datenums=list(datenums)     #convert ndarray to a list in order to use index function
    LEMSdata['datenumbers']=datenums
        
    plt.ion()  #turn on interactive plot mode

    f1, (ax1, ax2) = plt.subplots(2, sharex=True) # subplots sharing x axis

    ax1.plot(LEMSdata['datenumbers'], nominal(LEMSdata['CO_ER']), color='black', marker='.', label='LEMS time')
    ax1.plot(nominal(data['datenumbers']), nominal(data['CO_ER_LEMS']), color='red', marker='.', label='Possum time')
    ax2.plot(LEMSdata['datenumbers'], nominal(LEMSdata['CO2_ER']), color='black', marker='.', label='LEMS time')
    ax2.plot(nominal(data['datenumbers']), nominal(data['CO2_ER_LEMS']), color='blue', marker='.', label='Possum time')

    
    ax1.set_ylabel(units['CO_ER_LEMS'])
    ax1.set_title('CO_ER')
    ax1.grid(visible=True, which='major', axis='y')
    
    ax2.set_ylabel(units['CO2_ER_LEMS'])
    ax2.set_title('CO2_ER')
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
    
    plt.show()
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_AddLEMSdata(inputpath,outputpath,LEMSpath,logpath)

