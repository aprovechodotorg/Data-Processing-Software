#v0.0 Python3

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


#do:
#add plot of PM scat and grav flows with phase markers as a visual check

import LEMS_DataProcessing_IO as io
#import easygui
#import matplotlib.pyplot as plt
#import matplotlib
from datetime import datetime as dt
from uncertainties import ufloat
#import numpy as np

#########      inputs      ##############
#raw data input file:
gravinputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_GravInputs.csv'
#phase averages input data file:
aveinputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
#phase averages output data file:
aveoutputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_AveragesWithPM.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,aveoutputpath,logpath):

    logs=[]
    
    #define flow sensor channel names 
    gravtrain={}
    gravtrain['A']='GravFlo1'   
    gravtrain['B']='GravFlo2'
    
    #load grav filter weights input file
    [gravnames,gravunits,gravval,gravunc,gravuval]=io.load_constant_inputs(gravinputpath)
    gravnames=gravnames[1:] #remove the first name because it is the header
    
    line = 'Loaded input file of gravimetric filter weights:'+gravinputpath
    print(line)
    logs.append(line)
    
    #load phase averages data file
    [names,units,ave,aveunc,aveuval]=io.load_constant_inputs(aveinputpath)
    
    line = 'Loaded phase averages:'+aveinputpath
    print(line)
    logs.append(line)
    
    #load phase times input file
    [timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)   
    
    line = 'Loaded input file of phase start and end times:'+timespath
    print(line)
    logs.append(line)
    
    #define test phases by reading the variable names in the grav input file
    phases=[] #initialize a list of test phases (low power, med power, high power)    
    for name in gravnames:
        if gravval[name] != '':           #if the value is not blank
            spot=name.rindex('_')           #locate the last underscore
            phase=name[spot+1:]         #grab the string after the last underscore
            if phase not in phases:             #if it is a new phase
                phases.append(phase)            #add to the list of phases
    
    line= '\nGravimetric PM mass concentration report:'
    print(line)
    logs.append(line)
    
    for phase in phases:
        line='\nPhase:'+phase
        print(line)
        logs.append(line)
        
        line='Grav train'.ljust(12)+'channel'.ljust(12)+'net mass (g)'.ljust(20)+'flow (lpm)'.ljust(20)+'phase time (min)'.ljust(18)+'PM conc (ug/m^3)'
        print(line)
        logs.append(line)
        
        line='..........'.ljust(12)+'.......'.ljust(12)+'............'.ljust(20)+'..........'.ljust(20)+'................'.ljust(18)+'................'
        print(line)
        logs.append(line)
        
        #initialize dictionaries to calculate concentration
        flow={}
        netmass={}
        conc={}
        goodtrains=[]
        phasename='PMmass_'+phase   #variable name for the average PM concentration 
        
        #phase duration in minutes
        startname='start_time_'+phase   #variable name of the phase start time from the phase times input file
        endname='end_time_'+phase       #variable name of the phase end time from the phase times input file
        starttime=timestring[startname]     #variable value (string) of the phase start time from the phase times input file
        endtime=timestring[endname]         #variable value (string) of the phase end time from the phase times input file
        duration=timeperiod(starttime,endtime)  #phase length in minutes
        
        for train in ['A','B']: #for each grav flow train
            line=(train+':').ljust(12)
            
            tarename = 'taremass_'+train+'_'+phase          #variable name of tare mass from the grav inputs file
            grossname = 'grossmass_'+train+'_'+phase    #variable name of gross mass from the grav inputs file
            avename = gravtrain[train]+'_'+phase               #variable name of the flow channel from the averages input file
                
            try:
                netmass[train]=gravuval[grossname]-gravuval[tarename]  #grams
                flow[train]=aveuval[avename]   #liters per minute
                conc[train]=netmass[train]/flow[train]/duration*1000000*1000  #ug/m^3, conversion factors = 1,000,000 ug/g    and      1,000 liters/m^3
                goodtrains.append(train)                #if no errors then mark as successful calculation
                
                line=line+gravtrain[train].ljust(12)
                line=line+(str(round(netmass[train].n,6))+'+/-'+str(round(netmass[train].s,6))).ljust(20)
                line=line+(str(round(flow[train].n,3))+'+/-'+str(round(flow[train].s,3))).ljust(20)
                line=line+str(round(duration,2)).ljust(18)+str(round(conc[train].n,1))+'+/-'+str(round(conc[train].s,1))

            except:     #if errors in calculation then print blanks in the report
                line=line+'---'.ljust(12)+'---'.ljust(20)+'---'.ljust(20)+'---'.ljust(18)+'---'
            
            print(line)
            logs.append(line)
            
        #calculate total concentration from both flow trains    
        totalnetmass=sum(netmass.values())
        totalflow=sum(flow.values())
        aveuval[phasename]=totalnetmass/totalflow/duration*1000000*1000  #(ug/m^3), correction factors = 1,000,000 ug/g    and   1,000 liters/m^3
        names.append(phasename)
        units[phasename]='ug/m^3'
        
        #define which flow trains were used for the total calculation
        if 'A' in goodtrains and 'B' in goodtrains:
            chan='both'
        elif 'A' in goodtrains:
            chan=gravtrain['A']
        elif 'B' in goodtrains:
            chan=gravtrain['B']
        else:
            chan=''
        
        line='total:'.ljust(12)+chan.ljust(12)+(str(round(totalnetmass.n,6))+'+/-'+str(round(totalnetmass.s,6))).ljust(20)
        line=line+(str(round(totalflow.n,3))+'+/-'+str(round(totalflow.s,3))).ljust(20)
        line=line+str(round(duration,2)).ljust(18)+str(round(aveuval[phasename].n,1))+'+/-'+str(round(aveuval[phasename].s,1))
        print(line)
        logs.append(line)
    
    #print new phase averages data file with PM concentration added
    io.write_constant_outputs(aveoutputpath,names,units,ave,aveunc,aveuval)
    
    line='\ncreated new phase averages data file with PM concentration:\n'+aveoutputpath
    print(line)
    logs.append(line)    
    
    #print to log file
    io.write_logfile(logpath,logs)
    
def timeperiod(StartTime,EndTime):             
    #function calculates time difference in minutes
    #Inputs start and end times as strings and converts to time objects
    start_object=dt.strptime(StartTime, '%H:%M:%S')       #convert the start time string to date object
    end_object=dt.strptime(EndTime, '%H:%M:%S')          #convert the end time string to date object
    delta_object=end_object-start_object                           #time difference as date object
    Time=delta_object.total_seconds()/60                         #time difference as minutes
    return Time
    
#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,aveoutputpath,logpath)