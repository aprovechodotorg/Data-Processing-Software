#v0.1 Python3

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

import LEMS_DataProcessing_IO as io
import numpy as np
from uncertainties import ufloat
from uncertainties import ufloat_fromstr
from uncertainties import umath
from datetime import datetime as dt
import os
import easygui
import matplotlib.pyplot as plt
import matplotlib
import time

#########      inputs      ##############
#input file of all time series data
inputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_TimeSeriesPitot.csv'
#input file for stack flow calculations
stackinputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_StackFlowInputs.csv'
#uncertainty inputs file
ucpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_UCInputs.csv'
#input file of gravimetric outputs
gravpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_GravOutputs.csv'
#input file of carbon balance test average output metrics
metricpath='C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_EmissionOutputs.csv'
#output file of time series data 
outputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_TimeSeriesStackFlow.csv'
#log file
logpath='C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_log.txt'

##########################################

def PEMS_StackFlowCalcs(inputpath,stackinputpath,ucpath,gravpath,metricpath,dilratinputpath,outputpath,logpath):
    
    ver = '0.1' #for Aprovecho
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_StackFlowCalcs v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    particles = ['PM']    #measured particles in the dilution train
    possible_diluted_gases = ['CO','CO2','SO2','NO','NO2','HC','VOC','CH4','H2O']    #possible measured gases in the dilution train, depending on sensor box
    undiluted_gases = ['COhi','CO2hi','O2'] #measured gases in the undiluted train
    MWgases = ['COhi','CO2hi','H2O','O2','N2']  #gases used to calculate flue gas molecular weight
    
    #emission species that will get defined after reading the channel names of the data file
    diluted_gases = []    #measured gases in the dilution train
    stack_gases = [] #all measured gases
    ERgases = [] #gases that will get emission rate calcs
    
    Tstd=float(293)     #define standard temperature in Kelvin
    Pstd=float(101325)   #define standard pressure in Pascals
    Cp = ufloat(1,0.1) #J/g/K  heat capacity of flue gas. good enough for now. update as a function of flue gas composition and temperature
    R=float(8.314)     #universal gas constant (m^3Pa/mol/K)
    
    MW={}
    MW['C']=float(12.01)    # molecular weight of carbon (g/mol)
    MW['CO']=float(28.01)   # molecular weight of carbon monoxide (g/mol)
    MW['COhi']=float(28.01)   # molecular weight of carbon monoxide (g/mol)
    MW['CO2']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['CO2hi']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['SO2']=float(64.07)   # molecular weight of sulfur dioxide (g/mol)
    MW['NO']=float(30.01)   # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2']=float(46.01)   # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S']=float(34.1)   # molecular weight of hydrogen sulfide (g/mol)
    MW['HxCy']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['HC']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['VOC']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['CH4']=float(16.04) # molecular weight of methane (g/mol)
    MW['air']=float(29) #molecular weight of air (g/mol)
    MW['O2'] = float(32)   # molecular weight of oxygen (g/mol)
    MW['N2'] = float(28.01)   # molecular weight of nitrogen (g/mol)
    MW['H2O'] = float(18.02)   # molecular weight of water (g/mol)
    
    #load time series data file (full length with all phases because this file has the bkg subtraction series)
    [names,units,alldata]=io.load_timeseries(inputpath) 
    
    line = 'Loaded time series data:'+inputpath
    print(line)
    logs.append(line)

    #define the test phase data series
    data={}
    for name in names:
        data[name] = []
    for n,val in enumerate(alldata['phase']):
        if 'test' in val:
            for name in names:
                data[name].append(alldata[name][n])
    ##############################################
    #define emission species to use in the calculations
    for name in names:
        if name in possible_diluted_gases:
            diluted_gases.append(name)                          #measured gases in the dilution train
    diluted_gases.append('H2O') #calculated from RH       
    stack_gases = diluted_gases + undiluted_gases   #all measured gases
    ERgases = diluted_gases+undiluted_gases+['N2','C']    #gases that will get emission rate calcs
 
    ###############################################  
    #read in carbon balance emission metrics file
    [metricnames,metricunits,metricval,metricunc,metric]=io.load_constant_inputs(metricpath)
    line = 'Loaded carbon balance emission metrics:'+metricpath
    print(line)
    logs.append(line)

    ##############################################
      
    #read in measurement uncertainty file
    [ucnames,ucunits,ucinputs] = io.load_timeseries(ucpath)
    line = 'Loaded measurement uncertainty input file :'+ucpath
    print(line)
    logs.append(line)
    
    #######################################
    
    #apply measurement uncertainty to time series data
    for name in names:
        for n,val in enumerate(data[name]):
            try:
                float(val)  #if a number
                if name in ucnames:
                    unc = val*ucinputs[name][1]+ucinputs[name][0] #uncertainty is combination of relative and absolute from the uncertainty input file
                    data[name][n]=ufloat(val,unc)
                elif name =='datenumbers': #plot x axis, must be float, not ufloat
                    data[name][n]=val
                else:
                    data[name][n]=ufloat(val,0)
            except:             #if not a number, but rather a string
                pass            #don't change it   
    
    line = 'Added measurement uncertainty to time series data'
    print(line)
    logs.append(line)    
                
    ##########################################
    #add dateobects data series for plotting
    name = 'dateobjects'
    units[name] = 'date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    try:
        for n,val in enumerate(data['time']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S') #Convert time to readable datetime object
            data[name].append(dateobject)
    except: #some files have different name convention
        for n,val in enumerate(data['time_test']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
            data[name].append(dateobject)
            
    ###########################################################
    #define stack temperature channel name

    #check which TC channels exist
    TCchans = []
    for name in names:
        if 'TC' in name: # or name == 'FlueTemp' or name == 'H2Otemp':
            TCchans.append(name)
            
    #Plot TC channels and choose stack temp

    plt.ion()
    f1, (ax1) = plt.subplots()
    for chan in TCchans:
        y=nomvals(data[chan])    #make a list of nominal values from ufloats for plotting
        ax1.plot(data['datenumbers'], y, label=chan)

    ax1.set_ylabel('Temperature (C)')

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    #plt.savefig(savefig, bbox_inches='tight')
    #plt.show()

    running = 'fun'
    staktempname = 'TCnoz' #define name of default stack temperature channel

    while running == 'fun':
        #Ask user which one they want
        text = 'Select stack temperature channel'
        title = 'Gitrdone'
        choices = TCchans
        output = easygui.choicebox(text, title, choices)
        if output:
            staktempname = output
            running = 'not fun'
            
    plt.ioff()
    plt.close()

    Tstak = data[staktempname]
    line = 'Using '+staktempname+' channel for stack temperature (Tstak)'
    print(line)
    logs.append(line)  
    ################################################3
    #load grav metrics data file
    try:
        [gravnames,gravunits,gravval,gravunc,gravmetric]=io.load_constant_inputs(gravpath)
        line = 'Loaded gravimetric PM metrics:'+gravpath
        print(line)
        logs.append(line)
    except:
        line = 'No gravimetric data'
        print(line)
        logs.append(line)
        
    ###########################################
    #check for stack flow input file
    if os.path.isfile(stackinputpath):
        line='\nStack flow input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        stackinputnames = []
        stackinputunits = {}
        stackinputuval = {}
        stackinputval = {}
        stackinputunc = {}
        name = 'Cpitot'
        stackinputnames.append(name)
        stackinputunits[name] = '-'
        stackinputuval[name] = ufloat(0.84,0.01)      
        name = 'Cprofile'
        stackinputnames.append(name)
        stackinputunits[name] = '-'
        stackinputuval[name] = ufloat(1.0,0.0)       
        name = 'stack_diameter'
        stackinputnames.append(name)
        stackinputunits[name] = 'cm'
        stackinputuval[name] = ufloat(15.24,0.5)      
        stackinputnames =['variable_name']+stackinputnames   #add header
        stackinputunits['variable_name']='units'  #add header
        stackinputval['variable_name']='value'      #add header
        stackinputunc['variable_name']='uncertainty'       #add header
        io.write_constant_outputs(stackinputpath,stackinputnames,stackinputunits,stackinputval,stackinputunc,stackinputuval)
        line = '\nCreated stack flow input file: '
        print(line)
        logs.append(line)
    line=stackinputpath
    print(line)
    logs.append(line)
    
    [stackinputnames,stackinputunits,stackinputval,stackinputunc,stackinputuval] = io.load_constant_inputs(stackinputpath) #open input file

    #GUI box to edit inputs 
    zeroline='Enter stack flow inputs\n\n'
    secondline='Click OK to continue\n'
    thirdline='Click Cancel to exit\n'
    msg=zeroline+secondline+thirdline
    title = "inputs for stack flow calculations"
    fieldNames = []
    currentvals=[]
    for n,name in enumerate(stackinputnames[1:]):
        fieldname = name+' ('+stackinputunits[name]+')'
        fieldNames.append(fieldname) 
        currentvals.append(stackinputuval[name])
    newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
    else:
        line = 'Error: Undefined inputs'
        print(line)
        logs.append(line)
    for n,name in enumerate(stackinputnames[1:]):
        stackinputuval[name]=ufloat_fromstr(currentvals[n])
        print(name+' '+currentvals[n])
        
        #for n,name in enumerate(fieldNames[1:]):    #for each channel
        #    spot=currentvals[n].index(',')    #locate the comma
        #    methods[name]=currentvals[n][:spot]  #grab the string before the comma
        #    offsets[name] = currentvals[n][spot+1:]  #grab the string after the comma
        #    blank[name] = ''    
    stackinputval = {}
    stackinputunc = {}
    io.write_constant_outputs(stackinputpath,stackinputnames,stackinputunits,stackinputval,stackinputunc,stackinputuval)
    line = '\nUpdated stack flow input file:'
    print(line)
    logs.append(line)
    line=stackinputpath
    print(line)
    logs.append(line)
    
    #####smooth Pitot data series
    #maybe use boxcar centered on value
    #this boxcar average trails the value
    n = 10  #boxcar length
    name = 'Pitot_smooth'
    names.append(name)
    units[name]='Pa'
    data[name] = []
    for m,val in enumerate(data['Pitot']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['Pitot'][m-n:m]
            else:
                boxcar = data['Pitot'][:m]
            newval=sum(boxcar)/len(boxcar)
        data[name].append(newval)
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")    
    print('smoothed pitot '+timestampstring)
    
    ###########################################################
    #H2O in diluted sample
    name='Psat' #saturation pressure of H2O
    names.append(name)
    units[name]='Pa'
    data[name]=[]
    name='PH2O' #partial pressure of H2O
    names.append(name)
    units[name]='Pa'
    data[name]=[]
    name='H2O' # H2O concentration
    names.append(name)
    units[name]='ppm'
    data[name]=[]
    
    #vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    # P=10^(A-B/(C+T))
    #P = vapor pressure (mmHg) 
    #T = temperature (C)
    A = 8.07131 #constant
    B = 1730.63 #constant
    C = 233.426 #constant
    
    for n in range(len(data['RH'])):
        Tval = data['COtemp'][n]
        Psatval = pow(10,(A-B/(C+Tval)))/.0075 # 1 Pa = 0.0075 mmHg
        PH2Oval = Psatval*data['RH'][n]/100 #ufloat
        H2Oval = PH2Oval/data['Pamb'][n]*1000000 #ufloat ppm

        data['Psat'].append(Psatval);
        data['PH2O'].append(PH2Oval);
        data['H2O'].append(H2Oval);
        
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")  
    print('calculated H2O concentration '+timestampstring)
    
    #########calculate dilution ratio from flows ######################  
    # this may be different than the firmware calculation if some flow trains are not connected to the probe
    #for Possum1 check F2Flow and TAPflow
    
    #define filterflow channel name
    for name in names:
        if name == 'F1Flow':    #Possum1 during DOE field measurements Jan 2023
            filterflow = name
        if name == 'FiltFlow':   #Possum2
            filterflow = name

    name = 'DilRat_Flow'
    names.append(name)
    units[name] = units['DilRat']
    data[name]=[]
    for n,val in enumerate(data['time']):
        try:
            #this formula is for Possum2 
            #and for Possum1 if F2flow and TAPflow were not used
            dilrat = data['DilFlow'][n]/(data[filterflow][n]+data['SampFlow'][n]-data['DilFlow'][n])
        except:
            dilrat = 0.003
        data[name].append(dilrat)
        
    n = 100  #boxcar length
    #maybe use boxcar centered on value
    #this boxcar average trails the value
    name = 'DilRat_Flow_smooth'
    names.append(name)
    units[name]=units['DilRat']    
    data[name] = []
    for m,val in enumerate(data['DilRat_Flow']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['DilRat_Flow'][m-n:m]
            else:
                boxcar = data['DilRat_Flow'][:m]
            newval=sum(boxcar)/len(boxcar)
        data[name].append(newval)
     
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")  
    print('calculated dilution ratio from flows '+timestampstring) 
    line = '    DilRat_Flow = DilFlow/(FiltFlow+SampFlow-DilFlow)'
    print(line)
    logs.append(line)
    
    ####################################
    ########## Note on calculating dilution ratio from gas sensors ############3
    # We need to know the undiluted stack concentrations of CO and CO2 on a wet basis (the actual concentrations in the stack)
    # COhi and CO2hi are measured on dry basis and they need to be converted to wet basis 
    # The stack H2O concentration is currently calculated from the measured H2O in the diluted sample and the dilution ratio
    # Problem: We need the stack H2O concentration to calculate the dilution ratio...
    #   but we need the dilution ratio to calculate the stack H2O concentration.
    # Solution: Use the dilution ratio calculated by flows (DilRat_Flow) to estimate the stack H2O concentration 
    #   and use this to calculate CO and CO2 wet basis for the dilution ratio calculation.
    #   Then, after the best dilution ratio series is chosen, stack concentrations will be recalculated using that dilution ratio for outputs
    # Better solution: measure stack moisture using EPA inpinger method instead of deriving it from RH 
    # Another possible solution: Calculate theoretical stack moisture using CANB415
    #
    #Calculate stack moisture concentration from diluted H2O and DilRat_Flow
    #don't add data channel names to output because they are calculated again later with better dilution ratio
    
    DR = data['DilRat_Flow']
    
    name = 'H2O'
    stakname = name + 'stak'
    #names.append(stakname)
    #units[stakname] = '%vol'
    data[stakname] = []
    for n in range(len(data[name])):
        stack_conc = (DR[n]+1)*data[name][n]/1000000*100    #convert ppm to %vol
        data[stakname].append(stack_conc)
        
    #calculate stack concentrations on web basis        
    for name in ['COhi','COhi_bkg','CO2hi','CO2hi_bkg']:
        wbname = name+'wb'  #wet basis
        data[wbname] = []
        for n in range(len(data[name])):    
            db = data[name][n]
            mc = data['H2Ostak'][n]/100 # decimal fraction
            wb = db*(1-mc)
            data[wbname].append(wb)
    
    ############# More notes on calculating dilution ratio from gas sensors  ##########
    #starting with 3 fundamental equations:
    #1. VstakCstak + VdilCdil = VsampCsamp
    #2. Vstak + Vdil = Vsamp
    #3. DR = Vdil/Vstak
    # where:
    # Vstak = undiluted sample flow rate from the stack
    # Cstak = undiluted stack concentration
    # Vdil = dilution air flow rate
    # Cdil = dilution air concentration
    # Vsamp = diluted sample flow rate
    # Csamp = diluted sample concentration  
    #
    # the dilution ratio formula can be rearranged to:
    # DR=(Cstak-Csamp)/(Csamp-Cdil) 
    #
    #Cstak is the undiluted stack concentration before background subtraction. 
    #   It can be calculated from SubtractBkg function output as the background-subtracted stack concentration plus the background value that was subtracted
    #Csamp is the diluted sample concentration before background subtraction
    #   It can be calculated from SubtractBkg function output as the background-subtracted diluted sample concentration plus the background value that was subtracted
    #The denominator (Csamp-Cdil) is the background-subtracted diluted sample concentration if we assume
    #   the dilution air concentration is same as the background air concentration.
    #   For CO this assumption should be fine because both background and dilution air concentrations should be close to 0 ppm.
    #   For CO2 this assumption should be fine for high concentrations that are not very sensitive to the background subtraction,
    #   but may add artifact to the dilution ratio for low concentrations that are sensitive to the background subtraction
    #########calculate dilution ratio from CO2 ######################
    name = 'DilRat_CO2'
    names.append(name)
    units[name] = units['DilRat']
    data[name]=[]
    for n,val in enumerate(data['time']):
        try:
            dilrat = (data['CO2hiwb'][n]+data['CO2hi_bkgwb'][n]-data['CO2'][n]-data['CO2_bkg'][n])/(data['CO2'][n])
        except:
            dilrat = 0.001
        data[name].append(dilrat)
    
    n = 100  #boxcar length
    #maybe use boxcar centered on value
    #this boxcar average trails the value
    name = 'DilRat_CO2_smooth'
    names.append(name)
    units[name]=units['DilRat']    
    data[name] = []
    for m,val in enumerate(data['DilRat_CO2']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['DilRat_CO2'][m-n:m]
            else:
                boxcar = data['DilRat_CO2'][:m]
            newval=sum(boxcar)/len(boxcar)
        data[name].append(newval)

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")      
    print('calculated dilution ratio from CO2 '+timestampstring)
    #########calculate dilution ratio from CO ######################
    name = 'DilRat_CO'
    names.append(name)
    units[name] = units['DilRat']
    data[name]=[]
    for n,val in enumerate(data['time']):
        try:
            dilrat = (data['COhiwb'][n]+data['COhi_bkgwb'][n]-data['CO'][n]-data['CO_bkg'][n])/(data['CO'][n])
        except:
            dilrat = 0.002
        data[name].append(dilrat)
        
    n = 100  #boxcar length
    #maybe use boxcar centered on value
    #this boxcar average trails the value
    name = 'DilRat_CO_smooth'
    names.append(name)
    units[name]=units['DilRat']    
    data[name] = []
    for m,val in enumerate(data['DilRat_CO']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['DilRat_CO'][m-n:m]
            else:
                boxcar = data['DilRat_CO'][:m]
            newval=sum(boxcar)/len(boxcar)
        data[name].append(newval)  

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")      
    print('calculated dilution ratio from CO '+timestampstring)
    #################################################
    #calculate dilution ratio from constant
    
    #take average values of each dilution ratio time series
    for name in ['DilRat','DilRat_Flow','DilRat_CO2','DilRat_CO']:
        metric[name]=sum(data[name])/len(data[name])
    
    name = 'DilRat_Ave'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = [metric['DilRat']]*len(data['DilRat'])

    name = 'DilRat_Flow_Ave'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = [metric['DilRat_Flow']]*len(data['DilRat']) 

    name = 'DilRat_CO2_Ave'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = [metric['DilRat_CO2']]*len(data['DilRat']) 
    
    name = 'DilRat_CO_Ave'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = [metric['DilRat_CO']]*len(data['DilRat']) 
   
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")     
    print('calculated dilution ratio from constant '+timestampstring)
    #################################################
    #choose dilution ratio to use
    
    #create list of all available dilution ratio series
    DRnames=[]
    for name in names:
        if 'DilRat' in name:
            DRnames.append(name)
    
    #plot dilution ratio series
    plt.ion()
    f1, (ax1, ax2) = plt.subplots(2, sharex=True) # subplots sharing x axis
    for name in DRnames:
        y=nomvals(data[name])    #make a list of nominal values from ufloats for plotting
        ax1.plot(data['datenumbers'], y, label=name)
    
    #plot CO and CO2 to check when you can trust the dilution ratio series
    # steady concentrations produce higher quality dilution ratios
    # rapid fluctuations in concentrations produce incorrect dilution ratios because of sensor response time differences
    # higher concentrations produce higher quality dilution ratios because they are less sensitive to background concentrations
    # lower concentrations have higher relative uncertainty from background concentrations which propagates to dilution ratio
    for name in ['CO','COhi','CO2','CO2hi']:
        y=nomvals(data[name])    #make a list of nominal values from ufloats for plotting
        ax2.plot(data['datenumbers'],y, label=name)

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    ax2.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax2
    # plt.savefig(savefig, bbox_inches='tight')
    plt.show()
    
    #draw your own dilution ratio series
    name = 'DilRat_Drawn'
    names.append(name)
    DRnames.append(name)
    units[name]=units['DilRat']  
    data[name] = []
    
    #check for dilrat input file
    if os.path.isfile(dilratinputpath):
        line='\ndilrat input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        inputnames = []
        inputunits = {}
        inputuval = {}
        inputval = {}
        inputunc = {}
        inputname = 'ycoord'
        inputnames.append(inputname)
        inputunits[inputname] = '-'
        inputuval[inputname] = ufloat(0.00,0.00)      
        #name = 'Cprofile'
        #inputnames.append(name)
        #inputunits[name] = '-'
        #inputuval[name] = ufloat(1.0,0.0)       
        #name = 'stack_diameter'
        #inputnames.append(name)
        #inputunits[name] = 'cm'
        #inputuval[name] = ufloat(15.24,0.5)      
        inputnames =['variable_name']+inputnames   #add header
        inputunits['variable_name']='units'  #add header
        inputval['variable_name']='value'      #add header
        inputunc['variable_name']='uncertainty'       #add header
        io.write_constant_outputs(dilratinputpath,inputnames,inputunits,inputval,inputunc,inputuval)
        line = '\nCreated dilrat input file: '
        print(line)
        logs.append(line)
    line=dilratinputpath
    print(line)
    logs.append(line)
    
    [inputnames,inputunits,inputval,inputunc,inputuval] = io.load_constant_inputs(dilratinputpath) #open input file
    line='loaded'
    print(line)
    logs.append(line)
    
    
    # GUI box to enter a value for a constant dilution ratio series
    # This can be replaced with a more complex function to draw a custom dilution ratio series on the plot
    # could use a GUI cursor drawing tool
    # or input a table of points to create a line by connecting the dots
    
    point = inputuval['ycoord']  #first and only value of series
    text = 'Create a constant dilution ratio series. Enter value:\n\nThis is just a placeholder for a more complex function to draw a series'
    title = 'Gitrdone'
    output = easygui.enterbox(text, title, str(point))
    if output:
        point = ufloat_fromstr(output)
        inputval['ycoord'] = point.n
        inputunc['ycoord'] = point.s
        inputuval['ycoord'] = point
        io.write_constant_outputs(dilratinputpath,inputnames,inputunits,inputval,inputunc,inputuval)    #save the value to input file
        line='updated dilrat input file'
        print(line)
        logs.append(line)
        line=dilratinputpath
        print(line)
        logs.append(line)
        
    #define data series
    data[name]=[inputuval['ycoord']]*len(data['time'])
    #data[name]=[]
    #for n,val in enumerate(data['DilRat']):
    #    data[name].append(point)

    #add the new drawn dilrat series to the plot
    ax1.get_legend().remove()
    y=nomvals(data[name])    #name = DilRat_Drawn, make a list of nominal values from ufloats for plotting
    ax1.plot(data['datenumbers'], y, label=name)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    f1.canvas.draw()

    running = 'fun'
    DRname='DilRat' # default dilrat is firmware dilrat

    while running == 'fun':
        #Select which dilution ratio to use
        text = "Select a dilution ratio method"
        title = 'Gitrdone'
        choices = DRnames
        output = easygui.choicebox(text, title, choices)

        if output:
            DRname = output #get dilution ratio from output of sensor box
            running = 'not fun'

    plt.close()

    DR = data[DRname]
    
    line='dilution ratio series chosen for the calculations: '+DRname
    print(line)
    logs.append(line)
    ##########################################################
    #calculate stack volume concentrations
    
    for name in diluted_gases:
        stakname = name + 'stak'
        names.append(stakname)
        units[stakname] = '%vol'
        data[stakname] = []
        for n in range(len(data[name])):
            stack_conc = (DR[n]+1)*data[name][n]/1000000*100
            data[stakname].append(stack_conc)
        
    for name in undiluted_gases:
        stakname = name + 'stak'
        names.append(stakname)
        units[stakname] = '%vol'
        data[stakname] = []
        for n in range(len(data[name])):    
            db = data[name][n]
            mc = data['H2Ostak'][n]/100
            wb = db*(1-mc)
            if name != 'O2':
                wb = wb/1000000*100
            data[stakname].append(wb)
    
    #balance stack composition is nitrogen
    stakname = 'N2stak'
    names.append(stakname)
    units[stakname] = '%vol'
    data[stakname]=[]
    for n in range(len(data['O2'])):
        val = ufloat(100,0)
        for name in MWgases:
            sname = name+'stak'
            if name != 'N2':
                val = val - data[sname][n]
        data[stakname].append(val)   
        
    #carbon concentration (CO + CO2)
    name = 'Cstak'
    units[name] = '%vol'
    names.append(name)
    data[name]=[]
    for n,val in enumerate(data['COhistak']):
        cconc = val+data['CO2histak'][n]
        data[name].append(cconc)
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")  
    print('calculated stack concentrations '+timestampstring)
    ##########################################
    #flue gas molecular weight
    stakname='MWstak'
    names.append(stakname)
    units[stakname] = 'g/mol'
    data[stakname] = []

    for n in range(len(data['O2'])):
        mw = ufloat(0,0)
        for name in MWgases:
            sname = name + 'stak'
            mw = mw + MW[name]*data[sname][n]/100
         #     if n < 100:
         #           print stakname + '   ' +str(mw) + '   '+ str(molwt[name]) + '   '+ str(data[stakname][n]) + '   '+ str(data[stakname+'_uc'][n])
        data[stakname].append(mw)
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")  
    print('calculated molecular weight '+timestampstring)
    ##############################################
    #recalculate stack velocity
    
    name='StakVelCor'
    #StakVel=Cp*Kp*sqrt(Pitot*(TCnoz+273)/Pamb/MW)
    names.append(name)
    units[name]='m/s'
    data[name]=[]

    Kp=float(129)
    Cpitot = stackinputuval['Cpitot']
    for n in range(len(data['time'])):
        Pitotval=data['Pitot_smooth'][n]
        if Tstak[n]=='nan':
            newval='nan'
        else:
            if  Pitotval < 0:
                Pitotval = -Pitotval
                inside = Pitotval*(Tstak[n]+273.15)/data['Pamb'][n]/data['MWstak'][n]
                newval=-Cpitot*Kp*umath.sqrt(inside)
            else:
                inside = Pitotval*(Tstak[n]+273.15)/data['Pamb'][n]/data['MWstak'][n]
                newval=Cpitot*Kp*umath.sqrt(inside)
 #           if abs(newval.n)<0.00001:   #added because really small numbers give huge uc value
 #               newval = ufloat(0,0)
        data[name].append(newval)

    line = 'StakVel recalculated using MW time series, zeroed and smooth Pitot delta P'
    print(line)
    logs.append(line)   
    
    ##################################################################
    #calculate mass concentration
    for name in ERgases:
        stakname = name +'stak'
        concname = stakname+'conc'
        names.append(concname)
        units[concname] = 'gm^-3'
        data[concname] = []
        for n,vconc in enumerate(data[stakname]):
            mconc = vconc/100*MW[name]*data['Pamb'][n]/(Tstak[n]+273)/R #mass concentration (g/m^3)      
            data[concname].append(mconc)
        
    #calculate PM concentration
    name = 'PMconc'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name]=[]  
    msc = gravmetric['MSC'].n #ufloat, don't include uncertainty here because already included in PMscat below
    for n,val in enumerate(data['PM']):
        pmconc = val/msc/1000 #at standard conditions
        data[name].append(pmconc)
    
    name = 'PMstakconcstd'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name]=[]  
    for n,val in enumerate(data['PMconc']):
        stack_conc = (DR[n]+1)*val
        data[name].append(stack_conc)
        
    name = 'PMstakconc'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name]=[]  
    for n,val in enumerate(data['PMstakconcstd']): 
        pmconc = val*Tstd/(Tstak[n]+273)*data['Pamb'][n]/Pstd    #ideal gas law temperature and pressure correction : Cstak = Cstd x Tstd/Tstak x Pstak/Pstd
        data[name].append(pmconc)
   
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")     
    print('Calculated mass concentrations '+timestampstring)
    ###########################################################################   
    #calculate density 
    name = 'StakDensity'
    units[name] = 'g/m^3'
    names.append(name)
    data[name]=[]
    for n,val in enumerate(data['MWstak']):
        dens = val*data['Pamb'][n]/(Tstak[n]+273)/R
        data[name].append(dens)

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")      
    print('Calculated density '+timestampstring)
    ###########################################################################   
    #calculate volumetric flow rate
    
    #first calculate area
    stack_area = np.pi*(stackinputuval['stack_diameter']/100)*(stackinputuval['stack_diameter']/100)/4  #m^2
    
    name = 'StakFlow'
    units[name] = 'm^3/s'
    names.append(name)
    data[name]=[]
    for n,val in enumerate(data['StakVelCor']):
        flow = val*stack_area*stackinputuval['Cprofile']
        data[name].append(flow)    

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")          
    print('Calculated stack volumetric flow rate '+timestampstring)    
    ###########################################################################   
    #calculate mass flow (g/s) = volflow (m^3/s) x density (g/m^3)
    name = 'MassFlow'
    units[name] = 'g/s'
    names.append(name)
    data[name]=[] 
    for n,val in enumerate(data['StakFlow']):
        mflow = val*data['StakDensity'][n]
        data[name].append(mflow)
       
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")        
    print('Calculated stack mass flow rate '+timestampstring)    
    ###########################################################################   
    #calculate energy flow (Watts)  = Cp (J/g/K) x massflow (g/s) x dT (K)
    name = 'EnergyFlow'
    units[name] = 'W'
    names.append(name)
    data[name]=[]     
    for n,val in enumerate(data['MassFlow']):
        #use Tsamp for Tamb
        qdot = Cp*val*(Tstak[n]-data['COtemp'][n])
        data[name].append(qdot)

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")                     
    print('Calculated energy flow rate '+timestampstring)                   
    ###########################################################################   
    #calculate emission rates for gases
    for gas in ERgases:
        stakname = gas+'stak'
        concname = stakname+'conc'
        ername = 'ER'+stakname
        units[ername] = 'g/hr'
        names.append(ername)
        data[ername]=[]      
        for n,val in enumerate(data['StakFlow']):        
            er = val*data[concname][n]*3600       #g/hr
            data[ername].append(er)
        
    ###########################################################################   
    #calculate emission rate for PM
    name = 'ERPMstak'
    concname = 'PMstakconc'
    units[name] = 'mg/hr'
    names.append(name)
    data[name]=[]
    for n,val in enumerate(data['StakFlow']):        
        er = val*data[concname][n]*3600    #mg/hr  
        data[name].append(er)

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")          
    print('Calculated emission rates '+timestampstring) 
    #####################################################
    
    ##################################################################### 
    #   output times series data file
    io.write_timeseries_with_uncertainty(outputpath,names,units,data)  #use this one, but it is slow
    #io.write_timeseries_without_uncertainty(outputpath,names,units,data)   #use this one to write fast and ignore uncertainty value
    #io.write_timeseries(outputpath,names,units,data)       #don't use: writes entire ufloat to 1 cell but not enough sig figs
    line = '\nCreated stack flow time series data file: '
    print(line)
    logs.append(line)
    line=outputpath
    print(line)
    logs.append(line)
    
    #print to log file
    io.write_logfile(logpath,logs)
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")  
    line='finally done '+timestampstring
    
#####################################
#this function makes a list of nominal values from a list of ufloats for plotting
#input:   ufloat_series = list of ufloats
def nomvals(ufloat_series):
    noms=[]    #initialize a list of nominal values
    for val in ufloat_series:
        try:    #try to read the nominal value if it is a ufloat
            noms.append(val.n)
        except: #if not a ufloat
            noms.append(val)  
    return noms


#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_StackFlowCalcs(inputpath,stackinputpath,ucpath,gravpath,metricpath,dilratinputpath,outputpath,logpath)