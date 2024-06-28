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

# calculates PM mass concentration by gravimetric method
# inputs gravimetric filter weights
# determines which test phases and which flow trains by reading which variable names are present in the grav input file
# inputs phase times input file to calculate phase time length
# outputs filter net mass, flow, duration, and concentration for each phase
# outputs report to terminal and log file

#do:
#add plot of PM scat and grav flows with phase markers as a visual check
# create grav input file to interface with filter log database

import LEMS_DataProcessing_IO as io
import easygui
#import matplotlib.pyplot as plt
#import matplotlib
from datetime import datetime as dt
from uncertainties import ufloat
import os

#########      inputs      ##############
#gravimetric filter masses input file:
gravinputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_GravInputs.csv'
#phase averages input data file:
aveinputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
#gravimetric output metrics data file:
gravoutputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_GravOutputs.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,energypath,gravoutputpath,logpath, inputmethod):

    ver = '0.3'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_GravCalcs v'+ver+'   '+timestampstring
    print(line)
    logs=[line]

    outnames=[] #initialize list of variable names for grav output metrics
    outuval={} #initialize dictionary for grav output metrics (type: ufloats)
    outunits={} #dict of units for grav output metrics
    outval={}       #only used for output file header 
    outunc={}      #only used for output file header 

    #list of phases for filter inputs
    phases = ['_hp', '_mp', '_lp']
    #define flow sensor channel names 
    gravtrain={}
    gravtrain['A']='GravFlo1'   
    gravtrain['B']='GravFlo2'
    gravtrain['SB3002']='GravFlo1'
    gravtrain['SB3001']='GravFlo1'
    gravtrain['Possum2'] = 'GravFlo1'

    ##################
    # need to create grav input file here
    # potential options:
    #   1. run io function to create from 2d data entry form
    ##################

    # load phase averages data file
    [names, units, ave, aveunc, aveuval] = io.load_constant_inputs(aveinputpath)

    line = 'Loaded phase averages:' + aveinputpath
    print(line)
    logs.append(line)

    # load phase times input file
    [timenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(timespath)

    line = 'Loaded input file of phase start and end times:' + timespath
    print(line)
    logs.append(line)

    ###Check if running IDC test or not
    if 'start_time_L1' in timenames:
        phases.insert(0, '_L1')
    if 'start_time_L5' in timenames:
        phases.append('_L5')

    check = 0
    choice = []
    #check for grav path
    if os.path.isfile(gravinputpath):
        # load grav filter weights input file
        [gravnames, gravunits, gravval, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
        #check if input file is correct current version
        if 'start_time_A_L1' in gravnames or 'start_time_A_hp' in gravnames or 'start_time_A_mp' in gravnames or 'start_time_A_lp' in gravnames:
            line = '\nGrav input file already exists with chanel A: ' + gravinputpath
            print(line)
            logs.append(line)
            choice.append('A')
        elif 'start_time_B_L1' in gravnames or 'start_time_B_hp' in gravnames or 'start_time_B_mp' in gravnames or 'start_time_B_lp' in gravnames:
            line = '\nGrav input file already exists with chanel B: ' + gravinputpath
            print(line)
            logs.append(line)
            choice.append('B')
        elif 'start_time_SB3002_L1' in gravnames or 'start_time_SB3002_hp' in gravnames or 'start_time_SB3002_mp' in gravnames or 'start_time_SB3002_lp' in gravnames:
            line = '\nGrav input file already exists for SB3002: ' + gravinputpath
            print(line)
            logs.append(line)
            choice.append('SB3002')
        elif 'start_time_SB3001_L1' in gravnames or 'start_time_SB3001_hp' in gravnames or 'start_time_SB3001_mp' in gravnames or 'start_time_SB3001_lp' in gravnames:
            line = '\nGrav input file already exists for SB3001: ' + gravinputpath
            print(line)
            logs.append(line)
            choice.append('SB3001')
        elif 'start_time_Possum2_L1' in gravnames or 'start_time_Possum2_hp' in gravnames or 'start_time_Possum2_mp' in gravnames or 'start_time_Possum2_lp' in gravnames:
            line = '\nGrav input file already exists for Possum2: ' + gravinputpath
            print(line)
            logs.append(line)
            choice.append('Possum2')
        else:
            check = 1

        if check != 1 and inputmethod == '1':
            # GUI box to edit grav inputs
            zeroline = 'Enter grav input data (g)\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit'
            msg = zeroline + secondline + thirdline
            title = 'Gitdone'
            fieldNames = gravnames[1:]
            defaults=[]
            for name in gravnames[1:]:
                defaults.append(gravval[name])
            newvals = easygui.multenterbox(msg, title, fieldNames, values=defaults)  # , height = height)
            if newvals:
                if newvals != defaults:
                    defaults = newvals
                    for n, name in enumerate(gravnames[1:]):
                        gravval[name] = defaults[n]
            else:
                line = 'Error: Undefined variables'
                print(line)
                logs.append(line)

            io.write_constant_outputs(gravinputpath, gravnames, gravunits, gravval, gravunc, gravuval)
            line = '\nCreated phase times input file: ' + gravinputpath
            print(line)
            logs.append(line)
    else:
        check = 1

    if check == 1: #Create input file if does not exist or correct version does not exist
        gravnames = ['variable']
        gravunits={}
        gravval={}
        gravunc={}
        gravuval={}

        msg = "Select Grav Channels Used" #check for cannels used in grav filter
        title = 'Gitdone'
        channels = ['A', 'B', 'SB3002', 'SB3001', 'Possum2']
        choice = easygui.multchoicebox(msg, title, channels) #Can choose both

        defaults = []
        for c in choice: #for each channel choice
            for phase in phases:
                name = 'filterID_' + c + phase
                gravnames.append(name)
                gravunits[name] = 'text'
                defaults.append('')
                name = 'taremass_' + c + phase
                gravnames.append(name)
                gravunits[name] = 'g'
                defaults.append('')
                name = 'grossmass_' + c + phase
                gravnames.append(name)
                gravunits[name] = 'g'
                defaults.append('')
                name = 'start_time_' + c + phase
                gravnames.append(name)
                gravunits[name] = 'yyyymmdd hh:mm:ss'
                start = 'start_time' + phase
                defaults.append(timestring[start])
                name = 'end_time_' + c + phase
                gravnames.append(name)
                gravunits[name] = 'yyyymmdd hh:mm:ss'
                end = 'end_time' + phase
                defaults.append(timestring[end])

        if 'SB3002' in choice: #3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if 'GravFlo1' in enames: #if data entry sheet has default flow value, grab that
                defaults.append(euval['GravFlo1'])
            else: #assign default value (can be changed later during csv creation
                defaults.append(16.7)
        if 'SB3001' in choice: #3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if 'GravFlo1' in enames: #if data entry sheet has default flow value, grab that
                defaults.append(euval['GravFlo1'])
            else: #assign default value (can be changed later during csv creation
                defaults.append(16.7)
        if 'Possum2' in choice: #3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if 'GravFlo1' in enames: #if data entry sheet has default flow value, grab that
                defaults.append(euval['GravFlo1'])
            else: #assign default value (can be changed later during csv creation
                defaults.append(16.7)
        #make header
        name = 'variable'
        gravunits[name] = 'units'
        gravval[name] = 'value'
        gravunc[name] = 'uncertainty'

        #GUI box to edit grav inputs
        zeroline = 'Enter grav input data (g)\n'
        secondline = 'Click OK to continue\n'
        thirdline = 'Click Cancel to exit'
        msg = zeroline + secondline + thirdline
        title = 'Gitdone'
        fieldNames = gravnames[1:]
        height = len(fieldNames)
        width = max(len(fieldNames) for message in fieldNames)
        #currentvals=['', '', '', data['time'][0], data['time'][-1]]
        newvals = easygui.multenterbox(msg, title, fieldNames, values=defaults)#, height = height)
        if newvals:
            if newvals != defaults:
                defaults = newvals
                for n, name in enumerate(gravnames[1:]):
                    gravval[name] = defaults[n]
        else:
            line = 'Error: Undefined variables'
            print(line)
            logs.append(line)

        io.write_constant_outputs(gravinputpath, gravnames, gravunits, gravval, gravunc, gravuval)
        line = '\nCreated phase times input file: ' + gravinputpath
        print(line)
        logs.append(line)

    ##################################

    #load grav filter weights input file
    [gravnames,gravunits,gravval,gravunc,gravuval]=io.load_constant_inputs(gravinputpath)
    gravnames=gravnames[1:] #remove the first name because it is the header
    
    line = 'Loaded input file of gravimetric filter weights:' + gravinputpath
    print(line)
    logs.append(line)
    
    #define test phases by reading the variable names in the grav input file
    phases=[] #initialize a list of test phases (low power, med power, high power)    
    for name in gravnames:
        if gravval[name] != '':           #if the value is not blank
            try:
                spot=name.rindex('_')           #locate the last underscore
                phase=name[spot+1:]         #grab the string after the last underscore
                if phase not in phases:             #if it is a new phase
                    phases.append(phase)            #add to the list of phases
            except:
                pass #for GravFlo1
    
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

        if 'A' in choice:
            #phase duration in minutes
            startname='start_time_A_'+phase   #variable name of the phase start time from the phase times input file
            endname='end_time_A_'+phase       #variable name of the phase end time from the phase times input file
            starttime=gravval[startname]     #variable value (string) of the phase start time from the phase times input file
            endtime=gravval[endname]         #variable value (string) of the phase end time from the phase times input file
            duration=timeperiod(starttime,endtime)  #phase length in minutes
        elif 'B' in choice:
            #phase duration in minutes
            startname='start_time_B_'+phase   #variable name of the phase start time from the phase times input file
            endname='end_time_B_'+phase       #variable name of the phase end time from the phase times input file
            starttime=gravval[startname]     #variable value (string) of the phase start time from the phase times input file
            endtime=gravval[endname]         #variable value (string) of the phase end time from the phase times input file
            try:
                duration=timeperiod(starttime,endtime)  #phase length in minutes
            except:
                duration=''
        elif 'SB3002' in choice:
            # phase duration in minutes
            startname = 'start_time_SB3002_' + phase  # variable name of the phase start time from the phase times input file
            endname = 'end_time_SB3002_' + phase  # variable name of the phase end time from the phase times input file
            starttime = gravval[startname]  # variable value (string) of the phase start time from the phase times input file
            endtime = gravval[endname]  # variable value (string) of the phase end time from the phase times input file
            duration = timeperiod(starttime, endtime)  # phase length in minutes
        elif 'SB3001' in choice:
            # phase duration in minutes
            startname = 'start_time_SB3001_' + phase  # variable name of the phase start time from the phase times input file
            endname = 'end_time_SB3001_' + phase  # variable name of the phase end time from the phase times input file
            starttime = gravval[startname]  # variable value (string) of the phase start time from the phase times input file
            endtime = gravval[endname]  # variable value (string) of the phase end time from the phase times input file
            duration = timeperiod(starttime, endtime)  # phase length in minutes
        elif 'Possum2' in choice:
            # phase duration in minutes
            startname = 'start_time_Possum2_' + phase  # variable name of the phase start time from the phase times input file
            endname = 'end_time_Possum2_' + phase  # variable name of the phase end time from the phase times input file
            starttime = gravval[startname]  # variable value (string) of the phase start time from the phase times input file
            endtime = gravval[endname]  # variable value (string) of the phase end time from the phase times input file
            duration = timeperiod(starttime, endtime)  # phase length in minutes
        else:
            #phase duration in minutes
            startname='start_time_'+phase   #variable name of the phase start time from the phase times input file
            endname='end_time_'+phase       #variable name of the phase end time from the phase times input file
            starttime=gravval[startname]     #variable value (string) of the phase start time from the phase times input file
            endtime=gravval[endname]         #variable value (string) of the phase end time from the phase times input file
            duration=timeperiod(starttime,endtime)  #phase length in minutes
        
        for train in ['A','B', 'SB3002', 'SB3001', 'Possum2']: #for each grav flow train
            line=(train+':').ljust(12)
            
            tarename = 'taremass_'+train+'_'+phase          #variable name of tare mass from the grav inputs file
            grossname = 'grossmass_'+train+'_'+phase    #variable name of gross mass from the grav inputs file
            try:
                avename = gravtrain[train]+'_'+phase               #variable name of the flow channel from the averages input file
            except:
                pass #for SB3002

            try:
                netmass[train]=gravuval[grossname]-gravuval[tarename]  #grams
                if train == 'SB3002':
                    flow[train]=gravuval['GravFlo1'] #liters per minute - constant
                elif train == 'SB3001':
                    flow[train] = gravuval['GravFlo1']  # liters per minute - constant
                elif train == 'Possum2':
                    flow[train] = gravuval['GravFlo1']  # liters per minute - constant
                else:
                    flow[train]=aveuval[avename]   #liters per minute
                conc[train]=calcPMconc(netmass[train],flow[train],duration)     #PM conc (ug/m^3)
                goodtrains.append(train)                #if no errors then mark as successful calculation
                
                line=line+gravtrain[train].ljust(12)
                line=line+(str(round(netmass[train].n,6))+'+/-'+str(round(netmass[train].s,6))).ljust(20)
                line=line+(str(round(flow[train].n,3))+'+/-'+str(round(flow[train].s,3))).ljust(20)
                line=line+str(round(duration,2)).ljust(18)+str(round(conc[train].n,1))+'+/-'+str(round(conc[train].s,1))

            except:     #if errors in calculation then print blanks in the report
                line=line+'---'.ljust(12)+'---'.ljust(20)+'---'.ljust(20)+'---'.ljust(18)+'---'
            
            print(line)
            logs.append(line)
            
        #define which flow trains are used for the total calculation
        if 'A' in goodtrains and 'B' in goodtrains:
            chan='both'
        elif 'A' in goodtrains:
            chan=gravtrain['A']
        elif 'B' in goodtrains:
            chan=gravtrain['B']
        elif 'SB3002' in goodtrains:
            chan=gravtrain['SB3002']
        elif 'SB3001' in goodtrains:
            chan=gravtrain['SB3001']
        elif 'Possum2' in goodtrains:
            chan=gravtrain['Possum2']
        else:
            chan=''
            
        #calculate total concentration from both flow trains 
        totalnetmass=sum(netmass.values())      
        name='PMsample_mass_'+phase                #variable name for PM filter net mass
        outuval[name]=totalnetmass
        outnames.append(name)
        outunits[name]='g'
        
        totalflow=sum(flow.values())
        name='Qsample_'+phase                                #variable name for grav train flow rate
        outuval[name]=totalflow
        outnames.append(name)
        outunits[name]='l/min'
        
        name='phase_time_'+phase                        #variable name for phase time length 
        outuval[name]=duration
        outnames.append(name)
        outunits[name]='min'
        
        name='PMmass_'+phase                              #variable name for the average PM concentration 
        outuval[name]=calcPMconc(totalnetmass,totalflow,duration)
        outnames.append(name)
        outunits[name]='ug/m^3'

        try:
            line='total:'.ljust(12)+chan.ljust(12)+(str(round(totalnetmass.n,6))+'+/-'+str(round(totalnetmass.s,6))).ljust(20)
        except:
            line = 'total:'.ljust(12) + chan.ljust(12) + (str(round(totalnetmass, 6)))
        try:
            line=line+(str(round(totalflow.n,3))+'+/-'+str(round(totalflow.s,3))).ljust(20)
        except:
            line = line + (str(round(totalflow, 3))).ljust(20)
        try:
            line=line+str(round(duration,2)).ljust(18)+str(round(outuval[name].n,1))+'+/-'+str(round(outuval[name].s,1))
        except:
            line = line + str(duration).ljust(18) + str(outuval[name])
        print(line)
        logs.append(line)
        
    #make header for output file
    name='variable_name'    
    outnames=[name]+outnames
    outunits[name]='units'
    outval[name]='value'
    outunc[name]='uncertainty'
    
    #print grav output metrics data file
    io.write_constant_outputs(gravoutputpath,outnames,outunits,outval,outunc,outuval)
    
    line='\ncreated gravimetric PM output file:\n'+gravoutputpath
    print(line)
    logs.append(line)    
    
    #print to log file
    io.write_logfile(logpath,logs)

    return logs, gravval, outval, gravunits, outunits

def calcPMconc(Netmass,Flow,Duration):
    #function calculates PM mass concentration 
    #inputs: Netmass (g), Flow (l/min), Duration (minutes)
    try:
        PMconc=Netmass/Flow/Duration*1000000*1000  #(ug/m^3), correction factors = 1,000,000 ug/g    and   1,000 liters/m^3
    except:
        try:
            PMconc = Netmass.n / Flow / Duration * 1000000 * 1000
        except:
            PMconc = ''
    return PMconc
    
def timeperiod(StartTime,EndTime):
    #function calculates time difference in minutes
    #Inputs start and end times as strings and converts to time objects
    try:
        start_object=dt.strptime(StartTime, '%Y%m%d %H:%M:%S')       #convert the start time string to date object
        end_object=dt.strptime(EndTime, '%Y%m%d %H:%M:%S')          #convert the end time string to date object
    except:
        start_object=dt.strptime(StartTime, '%H:%M:%S')
        end_object=dt.strptime(EndTime, '%H:%M:%S')
    delta_object=end_object-start_object                           #time difference as date object
    Time=delta_object.total_seconds()/60                         #time difference as minutes
    return Time
    
#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,gravoutputpath,logpath)