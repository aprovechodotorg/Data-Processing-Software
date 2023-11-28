#v0.3 Python3

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

# Subtracts background values from time series data
# GUI to edit start and end times of each test period, including the background periods
#  Plot to visualize the affects of background adjustment and subtraction
# Outputs:
#    1. Background subtracted time series data file, full length (all phases)
#    2. For each phase, background subtracted time series data file
#    3. For each phase, averages data file of average values of all data channels
#    4. Background subtraction report to terminal and log file

#do: 
#accept date formats in the phase times input file
#allow other background subtraction methods: pre,post,offset,realtime
# allow for individual channel bkg start and end time adjustments
#move plots to plot library
#add 1 more figure for CH4 and VOC
#add uncertainty for averages

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os

#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_RawData2.csv'
#output data file to be created:
energyinputpath ='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test1\CrappieCooker_test2_EnergyInputs.csv'
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_TimeSeriesData.csv'
#output file of average values for each phase:
aveoutputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def LEMS_TEOM_SubtractBkg(inputpath,outputpath,aveoutputpath,timespath,logpath):
    ver = '0.3'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_TEOM_SubtractBkg v'+ver+'   '+timestampstring
    print(line)
    logs=[line]

    #################################################
    
    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)

    sample_rate = data['seconds'][1] - data['seconds'][0] #check the sample rate (time between seconds)
    
    #time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name]='date'
    data[name]=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        data[name].append(dateobject)   
    
    name='datenumbers'
    units[name]='date'
    names.append(name)
    datenums=matplotlib.dates.date2num(data['dateobjects'])
    datenums=list(datenums)     #convert ndarray to a list in order to use index function
    data['datenumbers']=datenums #float number
    
    #add phase column to time series data
    name='phase'
    names.append(name)
    units[name]='text'
    data[name]=['none']*len(data['time'])

    #read in input file of phase start and end times
    [timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)
    
    ###############################################

    [validnames,timeobject]=makeTimeObjects(timenames,timestring)  #convert time strings to time objects
    
    phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase
    
    phaseindices = findIndices(validnames,timeobject,datenums, sample_rate, data['time'])  #find the indices in the time data series for the start and stop times of each phase
    
    [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,phases,phaseindices)   #define phase data series for each channel
    
    #bkgvalue = calcBkgValue(bkgnames,phasemean)     #calculate the background value for each channel that will get background subtraction

    #data_new = bkgSubtraction(names,data,bkgnames,bkgvalue) #subtract the background
    
    #[phasedatenums,phasedata_new,phasemean_new] = definePhaseData(names,data_new,phases,phaseindices)   #define phase data series after background subtraction

    #output time series data file for each phase
    for phase in phases:
        phaseoutputpath=outputpath[:-4]+'_'+phase+'.csv'    #name the output file by inserting the phase name into the outputpath
        phasedataoutput={}  #initialize a dictionary of phase time series data for the output file
        for name in names:
            phasename=name+'_'+phase      
            phasedataoutput[name]=phasedata[phasename]
        io.write_timeseries(phaseoutputpath,names,units,phasedataoutput)
    
        line='created background-corrected time series data file:\n'+phaseoutputpath
        print(line)
        logs.append(line)
        
    # output average values  #####################
    phasenames=[]  
    phaseunits={}
    uvals={}
    unc={}
    
    for phase in phases:
        for name in names:
            phasename=name+'_'+phase     
            phasenames.append(phasename)
            if name=='time':
                phaseunits[phasename]='yyyymmdd hh:mm:ss'
            else:
                phaseunits[phasename]=units[name]
    
    #make header for averages file
    name='variable_name'    
    phasenames = [name]+phasenames
    phaseunits[name]='units'
    phasemean[name]='average'
    unc[name]='uncertainty'
            
    io.write_constant_outputs(aveoutputpath,phasenames,phaseunits,phasemean,unc,uvals)
    
    line='created phase averages data file:\n'+aveoutputpath
    print(line)
    logs.append(line)    
    #############################################

    #print to log file
    io.write_logfile(logpath,logs)
    
def makeTimeObjects(Timenames,Timestring):
    Timeobject={}   #initialize a dictionary of time objects
    Validnames=[] #initialize a list of time names that have a valid time entered
    for Name in Timenames:
        Datestring=Timestring[Name]    #add the date to the time string
        try:
            Timeobject[Name]=dt.strptime(Datestring, '%Y%m%d  %H:%M:%S')                #convert the time string to date object
            Validnames.append(Name)
        except:
            pass
    return Validnames,Timeobject
        
def definePhases(Timenames):
    Phases=[] #initialize a list of test phases (prebkg, low power, med power, high power, post bkg)    
    for Name in Timenames:
        spot=Name.rindex('_')           #locate the last underscore
        Phase=Name[spot+1:]         #grab the string after the last underscore
        if Phase not in Phases:             #if it is a new phase
            Phases.append(Phase)            #add to the list of phases
    return Phases

def findIndices(InputTimeNames,InputTimeObject,Datenums, Sample_Rate, Time):
    InputTimeDatenums={}
    Indices={}
    for Name in InputTimeNames:
        m = 1
        ind = 0
        while m <= Sample_Rate + 1 and ind == 0:
            try:
                InputTimeDatenums[Name] = matplotlib.dates.date2num(InputTimeObject[Name])
                Indices[Name]=Datenums.index(InputTimeDatenums[Name])
                ind = 1
            except:
                print(InputTimeObject[Name])
                InputTimeObject[Name] = InputTimeObject[Name] + timedelta(seconds = 1)
                m += 1

        try:
            check = Indices[Name]
        except:
            m = 1
            ind = 0
            while m <= Sample_Rate + 1 and ind == 0:
                try:
                    InputTimeDatenums[Name] = matplotlib.dates.date2num(InputTimeObject[Name])
                    Indices[Name] = Datenums.index(InputTimeDatenums[Name])
                    ind = 1
                except:
                    print(InputTimeObject[Name])
                    InputTimeObject[Name] = InputTimeObject[Name] + timedelta(seconds=-1)
                    m += 1

        try:
            check = Indices[Name]
        except:
            print('Filter change may be in the middle of phase end/start time, please adjust phase times')

    return Indices

def definePhaseData(Names,Data,Phases,Indices):
    Phasedatenums={}
    Phasedata={}
    Phasemean={}
    for Phase in Phases: #for each test phase
        #make data series of date numbers
        key='start_time_'+Phase
        startindex=Indices[key]
        key='end_time_'+Phase
        endindex=Indices[key]
        Phasedatenums[Phase]=Data['datenumbers'][startindex:endindex+1]    
        
        #make phase data series for each data channel
        for Name in Names:
            Phasename=Name+'_'+Phase
            Phasedata[Phasename]=Data[Name][startindex:endindex+1]
            
            #calculate average value
            if Name != 'time' and Name != 'phase':
                if all(np.isnan(Phasedata[Phasename])):
                    Phasemean[Phasename]=np.nan
                else:
                    Phasemean[Phasename]=np.nanmean(Phasedata[Phasename])
        
        #time channel: use the mid-point time string
        Phasename='datenumbers_'+Phase
        Dateobject=matplotlib.dates.num2date(Phasemean[Phasename]) #convert mean date number to date object
        Phasename='time_'+Phase
        Phasemean[Phasename]=Dateobject.strftime('%Y%m%d  %H:%M:%S')  
        
        #phase channel: use phase name
        Phasename='phase_'+Phase
        Phasemean[Phasename]=Phase
        
    return Phasedatenums,Phasedata,Phasemean
    
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_SubtractBkg(inputpath,energyinputpath,outputpath,aveoutputpath,timespath,logpath)

