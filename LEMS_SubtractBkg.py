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

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
import numpy as np

#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData2.csv'
#output data file to be created:
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TimeSeries_BkgSubtracted.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TimesInputs.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_log.txt'
##########################################

def LEMS_SubtractBkg(inputpath,outpath,timespath,logpath):

    timeobject={}
    datenumbers={}
    datenumseries={}
    indices={}
    phasedata={}
    phasemean={}
    bkgvalue={}
    logs=[]
    
    data_new={}
    phasedata_new={}
    phasemean_new={}
    
    potentialBkgNames=['CO','CO2','PM','VOC','CH4'] #define potential channel names that will get background subtraction
    bkgnames=[] #initialize list of actual channel names that will get background subtraction

    #################################################
    #read in raw data file
    
    [names,units,data] = io.load_timeseries(inputpath)
    
     ##############################################
    #read in input file of start and end times
    [timenames,timeunits,timenom,timeunc,timeval] = io.load_constant_inputs(timespath)

    line = 'Loaded input file of start and end times:'+timespath
    print(line)
    logs.append(line)
    
    ###############################################
    #prep the data for background subtraction
    
    #choose which channels will get background subtraction
    #could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)
    
    #get the date from the time series data
    date=data['time'][0][:8]
    
    goodnames=[] #initialize a list of time names that have a valid time entered
    for name in timenames:
        datestring=date+' '+timenom[name] #add the date to the time string
        #convert the time strings to date objects   
        try:
            timeobject[name]=dt.strptime(datestring, '%Y%m%d  %H:%M:%S')
            goodnames.append(name)
        except:
            pass
        
    for name in goodnames:
        #convert the start and stop date objects to date numbers for plotting
        datenumbers[name]=matplotlib.dates.date2num(timeobject[name])
        
    #convert date strings from the time data series to date numbers for plotting
    dateobjects=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
        dateobjects.append(dateobject)   
    datenums=matplotlib.dates.date2num(dateobjects)
    datenums=list(datenums)     #convert ndarray to a list in order to use index function

    phases=[] #initialize a list of test phases (prebkg, low power, med power, high power, post bkg)
    for name in goodnames:
        #find the data series indices of the start and stop times
        indices[name]=datenums.index(datenumbers[name]) 
        
        #define the phases
        spot=name.rindex('_')
        phase=name[spot+1:]
        if phase not in phases:
            phases.append(phase)
    

    for phase in phases: #for each test phase
        #make data series of date numbers
        key='start_time_'+phase
        startindex=indices[key]
        key='end_time_'+phase
        endindex=indices[key]
        datenumseries[phase]=datenums[startindex:endindex+1]

        #make data series for each data channel
        for name in names:
            keyname=name+'_'+phase
            phasedata[keyname]=data[name][startindex:endindex+1]
            
            #calculate average value
            if name != 'time':
                if all(np.isnan(phasedata[keyname])):
                    phasemean[keyname]=np.nan
                else:
                    phasemean[keyname]=np.nanmean(phasedata[keyname])
            
    #end of data preparation for background subtraction
    #########################################################  
    #subtract the background
    for name in bkgnames:    #for each channel that will get background subtraction
        data_new[name]=[]
        bkgvalue[name]=np.mean([phasemean[name+'_prebkg'],phasemean[name+'_postbkg']])         #pre-post method
        for n,val in enumerate(data[name]):
            newval=val-bkgvalue[name]
            data_new[name].append(newval)   

    for phase in phases:   
        #make new background subtracted data series for each data channel
        for name in bkgnames:
            keyname=name+'_'+phase
            phasedata_new[keyname]=data_new[name][startindex:endindex+1]
            
            #calculate average value
            if name != 'time':
                if all(np.isnan(phasedata_new[keyname])):
                    phasemean_new[keyname]=np.nan
                else:
                    phasemean_new[keyname]=np.nanmean(phasedata_new[keyname])            

    ##########################################
    #print report
    
    #plot

    #GUI box to edit input times
    firstline='Time format = '+timeunits['start_time_prebkg']
    msg=firstline
    title = "Gitrdone"
    fieldNames = timenames[1:]
    currentvals=[]
    for name in timenames[1:]:
        currentvals.append(timenom[name])
    newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
            for n,name in enumerate(timenames[1:]):
                timenom[name]=currentvals[n]
            io.write_constant_outputs(timespath,timenames,timeunits,timenom,timeunc,timeval)
            line = 'Updated input file of start and end times:'+timespath
            print(line)
            logs.append(line)
    
    #output new background subtracted time series data file 
    
    #print final report to logs
    
    #print to log file
    io.write_logfile(logpath,logs)
    
        #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_SubtractBkg(inputpath,outputpath,timespath,logpath)

