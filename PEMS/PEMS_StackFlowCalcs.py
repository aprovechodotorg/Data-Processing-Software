# v0.6 Python3
#   v0.1: for Apro
#   v0.2: faster
#   v0.3: added firepower
#   v0.5: input DR to calc stack H2O instead of using DR_flows
#   v0.6: added energy calcs from CAN B415.1

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
import numpy as np
from uncertainties import ufloat
from uncertainties import ufloat_fromstr
from uncertainties import umath
from uncertainties import unumpy
from datetime import datetime as dt
import os
import easygui
import matplotlib.pyplot as plt
import matplotlib
import math
import time

#########      inputs      ##############
# input file of all time series data
inputpath = '...\8.23.23_TimeSeriesPitot.csv'
# input file for stack flow calculations
stackinputpath = '...\8.23.23\8.23.23_StackFlowInputs.csv'
# uncertainty inputs file
ucpath = '...\8.23.23\8.23.23_UCInputs.csv'
# input file of gravimetric outputs
gravpath = '...\8.23.23\8.23.23_GravOutputs.csv'
# input file of carbon balance test average output metrics
metricpath = '...\8.23.23\8.23.23_EmissionOutputs.csv'
# output file of time series data
outputpath = '...\8.23.23\8.23.23_TimeSeriesStackFlow.csv'
# log file
logpath = '...\8.23.23\8.23.23_log.txt'


##########################################

def PEMS_StackFlowCalcs(inputpath, stackinputpath, ucpath, gravpath, metricpath, energypath, dilratinputpath,
                        outputpath, logpath, savefig3,pmunit):
    interactive = 1  # set to 1 for interactive mode
    ver = '0.6'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_StackFlowCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    particles = ['PM']  # measured particles in the dilution train
    possible_diluted_gases = ['CO', 'CO2', 'SO2', 'NO', 'NO2', 'HC', 'VOC', 'CH4',
                              'H2Orh']  # possible measured gases in the dilution train, depending on sensor box
    undiluted_gases = ['COhi', 'CO2hi', 'O2','H2O']  # measured gases in the undiluted train
    MWgases = ['COhi', 'CO2hi', 'H2O', 'O2', 'N2']  # gases used to calculate flue gas molecular weight

    # emission species that will get defined after reading the channel names of the data file
    diluted_gases = []  # measured gases in the dilution train
    stack_gases = []  # all measured gases
    ERgases = []  # gases that will get emission rate calcs

    Tstd = float(293)  # define standard temperature in Kelvin
    Pstd = float(101325)  # define standard pressure in Pascals
    Cp = ufloat(1,
                0.1)  # J/g/K  heat capacity of flue gas. good enough for now. update as a function of flue gas composition and temperature
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    MW = {}
    MW['C'] = float(12.01)  # molecular weight of carbon (g/mol)
    MW['Chi'] = float(12.01)  # molecular weight of carbon (g/mol)
    MW['CO'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['COhi'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['CO2'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['CO2hi'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['SO2'] = float(64.07)  # molecular weight of sulfur dioxide (g/mol)
    MW['NO'] = float(30.01)  # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2'] = float(46.01)  # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S'] = float(34.1)  # molecular weight of hydrogen sulfide (g/mol)
    MW['HxCy'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['HC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['VOC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['CH4'] = float(16.04)  # molecular weight of methane (g/mol)
    MW['air'] = float(29)  # molecular weight of air (g/mol)
    MW['O2'] = float(32)  # molecular weight of oxygen (g/mol)
    MW['N2'] = float(28.01)  # molecular weight of nitrogen (g/mol)
    MW['H2O'] = float(18.02)  # molecular weight of water (g/mol)
    MW['H2Orh'] = float(18.02)  # molecular weight of water (g/mol)

    # load time series data file (full length with all phases because this file has the bkg subtraction series)
    [names, units, alldata] = io.load_timeseries(inputpath)

    line = 'Loaded time series data:' + inputpath
    print(line)
    logs.append(line)

    # define the test phase data series
    data = {}
    for name in names:
        data[name] = []
    for n, val in enumerate(alldata['phase']):
        if 'test' in val:
            for name in names:
                data[name].append(alldata[name][n])
    ##############################################
    # define emission species to use in the calculations
    for name in names:
        if name in possible_diluted_gases:
            diluted_gases.append(name)  # measured gases in the dilution train


    ERgases = diluted_gases + undiluted_gases + ['N2', 'C', 'Chi']  # gases that will get emission rate calcs

    ###############################################
    # read in carbon balance emission metrics file
    [metricnames, metricunits, metricval, metricunc, metric] = io.load_constant_inputs(metricpath)
    line = 'Loaded carbon balance emission metrics:' + metricpath
    print(line)
    logs.append(line)

    ##############################################

    # read in measurement uncertainty file
    [ucnames, ucunits, ucinputs] = io.load_timeseries(ucpath)
    line = 'Loaded measurement uncertainty input file :' + ucpath
    print(line)
    logs.append(line)

    #######################################
    # apply measurement uncertainty to time series data
    for name in names:
        data[name] = np.array(data[name])
        if name == 'time' or name == 'seconds' or name == 'ID' or name == 'datenumbers' or name == 'Timegm' or name == 'phase':
            pass
        else:
            if name in ucnames:
                unc = abs(data[name] * ucinputs[name][1]) + abs(ucinputs[name][0])  # uncertainty is combination of relative and absolute from the uncertainty input file
            else:
                unc = [0]*len(data[name])
            data[name] = unumpy.uarray(data[name], unc)
        if name == 'CH4':  # use HC uncertainty inputs for CH4
            unc = abs(data[name] * ucinputs['HC'][1]) + abs(ucinputs['HC'][0])  # uncertainty is combination of relative and absolute from the uncertainty input file
            data[name] = unumpy.uarray(data[name], unc)

    line = 'Added measurement uncertainty to time series data'
    print(line)
    logs.append(line)

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print(timestampstring)

    ##########################################
    # add dateobects data series for plotting
    name = 'dateobjects'
    units[name] = 'date'
    # names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    try:
        for n, val in enumerate(data['time']):
            dateobject = dt.strptime(val, '%Y%m%d  %H:%M:%S')  # Convert time to readable datetime object
            data[name].append(dateobject)
    except:  # some files have different name convention
        for n, val in enumerate(data['time_test']):
            dateobject = dt.strptime(val, '%Y%m%d  %H:%M:%S')
            data[name].append(dateobject)

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('added dateobjects ' + timestampstring)
    ###########################################################
    # define stack temperature channel name
    '''
    #check which TC channels exist
    TCchans = []
    for name in names:
        if 'TC' in name: # or name == 'FlueTemp' or name == 'H2Otemp':
            TCchans.append(name)

    #Plot TC channels and choose stack temp

    plt.ion()
    f1, (ax1) = plt.subplots()
    for chan in TCchans:
        y=unumpy.nominal_values(data[chan])
        #y=nomvals(data[chan])    #make a list of nominal values from ufloats for plotting
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
    '''
    #staktempname = 'TCnoz'  # define name of default stack temperature channel
    staktempname = 'FlueTemp'  # define name of default stack temperature channel
    '''
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
    '''
    Tstak = data[staktempname]
    line = 'Using ' + staktempname + ' channel for stack temperature (Tstak)'
    print(line)
    logs.append(line)
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print(timestampstring)
    ################################################3
    # load grav metrics data file
    try:
        [gravnames, gravunits, gravval, gravunc, gravmetric] = io.load_constant_inputs(gravpath)
        line = 'Loaded gravimetric PM metrics:' + gravpath
        print(line)
        logs.append(line)
    except:
        line = 'No gravimetric data'
        print(line)
        logs.append(line)

    ###########################################
    # check for stack flow input file
    if os.path.isfile(stackinputpath):
        line = '\nStack flow input file already exists:'
        print(line)
        logs.append(line)
    else:  # if input file is not there then create it
        stackinputnames = []
        stackinputunits = {}
        stackinputuval = {}
        stackinputval = {}
        stackinputunc = {}
        name = 'Cpitot'
        stackinputnames.append(name)
        stackinputunits[name] = '-'
        stackinputuval[name] = ufloat(0.84, 0.01)
        name = 'Cprofile'
        stackinputnames.append(name)
        stackinputunits[name] = '-'
        stackinputuval[name] = ufloat(1.0, 0.0)
        name = 'stack_diameter'
        stackinputnames.append(name)
        stackinputunits[name] = 'cm'
        stackinputuval[name] = ufloat(15.24, 0.5)
        name = 'air_moisture_content'
        stackinputnames.append(name)
        stackinputunits[name] = 'ppm'
        stackinputuval[name] = ufloat(10000, 500)  
        name = 'water_mass_collected'
        stackinputnames.append(name)
        stackinputunits[name] = 'g'
        stackinputuval[name] = ''        
        stackinputnames = ['variable_name'] + stackinputnames  # add header
        stackinputunits['variable_name'] = 'units'  # add header
        stackinputval['variable_name'] = 'value'  # add header
        stackinputunc['variable_name'] = 'uncertainty'  # add header
        io.write_constant_outputs(stackinputpath, stackinputnames, stackinputunits, stackinputval, stackinputunc,
                                  stackinputuval)
        line = '\nCreated stack flow input file: '
        print(line)
        logs.append(line)
    line = stackinputpath
    print(line)
    logs.append(line)

    [stackinputnames, stackinputunits, stackinputval, stackinputunc, stackinputuval] = io.load_constant_inputs(
        stackinputpath)  # open input file
    
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
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")    
    print(timestampstring)
    

    #####smooth Pitot data series
    # maybe use boxcar centered on value
    # this boxcar average trails the value
    n = 10  # boxcar length
    name = 'Pitot_smooth'
    names.append(name)
    units[name] = 'Pa'
    data[name] = []
    for m, val in enumerate(data['Pitot']):
        if m == 0:
            newval = val
        else:
            if m >= n:
                boxcar = data['Pitot'][m - n:m]
            else:
                boxcar = data['Pitot'][:m]
            newval = sum(boxcar) / len(boxcar)
        data[name].append(newval)

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('smoothed pitot ' + timestampstring)

    ###########################################################
    # Calculate stack water vapor by EPA Method 4
    
    #H2O saturation stack concentration (partial pressure)
    #This is a quality control check. Actual H2Ostak should be below this but not always because there could be water droplets. 
                   
                                            
                      
    name = 'H2Osatstak'
    units[name] = '%vol'
                                     
    names.append(name)
    data[name] = []
                   

    # vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    # P=10^(a-b/(c+T))
    # P = vapor pressure (mmHg)
    # T = temperature (C)
    
    for T in Tstak:
        if T < 100: # deg C
            a = 8.07131  # imperical constant
            b = 1730.63  # imperical constant
            c = 233.426  # imperical constant
        else: # 100 < T < 374 deg C
            a = 8.14019  # imperical constant
            b = 1810.94  # imperical constant
            c = 244.485  # imperical constant
        psat = np.power(10, (a - b / (c + T))) / .0075  # 1 Pa = 0.0075 mmHg
        data[name].append(psat/101325)
    
    # water mass collected in condenser (grams), from the stack flow input file
    if stackinputuval['water_mass_collected'] != '' and stackinputuval['water_mass_collected'] is not None:
        H2Omethod = 'EPA Method 4'
        wm = stackinputuval['water_mass_collected']   #water mass (g)
        H2Ovol = wm*R*Tstd/Pstd/MW['H2O']  #Eq. 4.2 water vapor volume at standard conditions (m^3)
        line = 'H2Ovol = ' + str(H2Ovol) + ' m^3'
        print(line)
        logs.append(line)
        #Undiluted sample train volume (m^3), integrated flow over the sampling duration
        y = unumpy.nominal_values(data['USampFlow'])  # make a list of nominal values from ufloats
        u = unumpy.std_devs(data['USampFlow'])  
        Usampvol = ufloat(y.sum(),u.sum())/60000000 #ccm to m^3/s  #remove the correlations
        #Usampvol = data['USampFlow'].sum()/60000000 #ccm to m^3/s
        #Usampvol = ufloat(Usampvol.nominal_value,Usampvol.std_dev) 
 
        line = 'Usampvol = ' + str(Usampvol) + ' m^3'
        print(line)
        logs.append(line)
        H2Ostakave = H2Ovol/(H2Ovol+Usampvol)*100  #%vol
        line = 'H2Ostakave = ' + str(H2Ostakave) + ' %vol'
        print(line)
        logs.append(line)
        H2Orhave = data['H2Orh'].mean()
        H2Orhave = ufloat(H2Orhave.nominal_value,H2Orhave.std_dev)  #remove the correlations
        line = 'H2Orhave = ' + str(H2Orhave) + ' ppm'
        print(line)
        logs.append(line)
        data['H2Ostak'] = data['H2Orh']/H2Orhave*H2Ostakave
    else:
        H2Omethod = 'estimate'
        line = 'No water mass collected. H2Ostak determined from RH.'
        print(line)
        logs.append(line)
        # data['H2Ostak'] will be defined after dilution ratio input
    
    units['H2Ostak'] = '%vol'
    names.append('H2Ostak')





    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated H2O concentration ' + timestampstring)

    #########calculate dilution ratio from flows ######################
    # this may be different than the firmware calculation if some flow trains are not connected to the probe
    # for Possum1 check F2Flow and TAPflow

    # define filterflow channel name
    for name in names:
        if name == 'F1Flow':  # Possum1 during DOE field measurements Jan 2023
            filterflow = name
        if name == 'FiltFlow':  # Possum2
            filterflow = name

    name = 'DilRat_Flow'
    names.append(name)
    units[name] = units['DilRat']
    # this formula is for Possum2 and for Possum1 if F2flow and TAPflow were not used
    data[name] = data['DilFlow'] / (data[filterflow] + data['SampFlow'] - data['DilFlow'])

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated DilRat_Flow ' + timestampstring)


    ####################################
    ####################################
    ########## Note on calculating dilution ratio from gas sensors ############3
    # We need to know the undiluted stack concentrations of CO and CO2 on a wet basis (the actual concentrations in the stack)
    # COhi and CO2hi are measured on dry basis and they need to be converted to wet basis
    # If the stack H2O concentration is measured gravimetrically,then CO and CO2 wet basis are calculated
    # If the stack H2O concentration is calculated from the measured H2O in the diluted sample and the dilution ratio then guess and check:
    #   1. Input value for dilution ratio (a best estimate) to estimate the stack H2O concentration
    #   2. Calculate CO and CO2 wet basis for the dilution ratio calculation.
    #   3. Plot and choose the best dilution ratio series
    #   4. If the updated dilution ratio is different than the previous dilution ratio from step 1, iterate until converge
  #





















    # check for dilrat input file
    if os.path.isfile(dilratinputpath):
        line = '\ndilrat input file already exists:'
        print(line)
        logs.append(line)
    else:  # if input file is not there then create it
        inputnames = []
        inputunits = {}
        inputuval = {}
        inputval = {}
        inputunc = {}
        inputname = 'DR_estimate'
        inputnames.append(inputname)
        inputunits[inputname] = '-'
        inputuval[inputname] = ufloat(0.00, 0.00)
        inputname = 'DR_drawn'
        inputnames.append(inputname)
        inputunits[inputname] = '-'
        inputuval[inputname] = ufloat(0.00, 0.00)
        inputnames = ['variable_name'] + inputnames  # add header
        inputunits['variable_name'] = 'units'  # add header
        inputval['variable_name'] = 'value'  # add header
        inputunc['variable_name'] = 'uncertainty'  # add header
        io.write_constant_outputs(dilratinputpath, inputnames, inputunits, inputval, inputunc, inputuval)
        line = '\nCreated dilrat input file: '
        print(line)
        logs.append(line)
    line = dilratinputpath
    print(line)
    logs.append(line)

    [inputnames, inputunits, inputval, inputunc, inputuval] = io.load_constant_inputs(
        dilratinputpath)  # open input file
    line = 'loaded'
    print(line)
    logs.append(line)

    fish = 'trout'

    interactive = 1

    while fish == 'trout':
        if interactive == 1:
            # GUI box to enter a value for the dilution ratio estimate
            point = inputuval['DR_estimate']  #
            text = 'Enter value for DR_estimate to calculate stack H2O concentration'
            title = 'Gitrdone'
            output = easygui.enterbox(text, title, str(point))
            if output:
                point = ufloat_fromstr(output)
                inputval['DR_estimate'] = point.n
                inputunc['DR_estimate'] = point.s
                inputuval['DR_estimate'] = point
                io.write_constant_outputs(dilratinputpath, inputnames, inputunits, inputval, inputunc,
                                          inputuval)  # save the value to input file
                line = 'updated dilrat input file'
                print(line)
                logs.append(line)
                line = dilratinputpath
                print(line)
                logs.append(line)

        # define data series
        data['DilRat_Estimate'] = np.array([inputuval['DR_estimate']] * len(data['time']))

        # Calculate stack moisture concentration from diluted H2O and DilRat_Estimate
        # don't add data channel names to output because they are calculated again later with better dilution ratio

        DR = data['DilRat_Estimate']

        if H2Omethod == 'estimate': #if not EPA Method 4, estimate H2O stack concentration from diluted H2O
            #H2Ostak already added to names, and units already defined 
            data['H2Ostak'] = (DR + 1) * data['H2Orh'] / 1000000 * 100  # convert ppm to %vol 

        # calculate stack concentrations on web basis
        for name in ['COhi', 'COhi_bkg', 'CO2hi', 'CO2hi_bkg']:
            wbname = name + 'wb'  # wet basis
            data[wbname] = data[name] * (1 - data['H2Ostak'] / 100)  # wb = db*(1-mc)

        ############# More notes on calculating dilution ratio from gas sensors  ##########
        # starting with 3 fundamental equations:
        # 1. VstakCstak + VdilCdil = VsampCsamp
        # 2. Vstak + Vdil = Vsamp
        # 3. DR = Vdil/Vstak
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
        # Cstak is the undiluted stack concentration before background subtraction.
        # Csamp is the diluted sample concentration before background subtraction
        # Cdil is the dilution air concentration  It can be calculated from SubtractBkg function output as the background-subtracted diluted sample concentration plus the background value that was subtracted
        
        #########calculate dilution ratio from CO2 ######################
        name = 'DilRat_CO2'
        names.append(name)
        units[name] = units['DilRat']
        denominator = []
        for i,val in enumerate(data['CO2']):
            Cdil = data['CO2bkg'][i]
            den = val.n - Cdil.n
            if den == 0:  # change any zero values to 1 ppm +/- absolute unc to prevent div 0 error
                denominator.append(ufloat(1, ucinputs['CO2'][0]))
            else:
                denominator.append(den)
        data[name] = (data['CO2hiwb'] - data['CO2']) / denominator

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilution ratio from CO2 ' + timestampstring)
        #########calculate dilution ratio from CO ######################
        name = 'DilRat_CO'
        names.append(name)
        units[name] = units['DilRat']
        denominator = []
        for i,val in enumerate(data['CO']):
            Cdil = data['CObkg'][i]
            den = val.n - Cdil.n
            if den == 0:  # change any zero values to 1 ppm +/- absolute unc to prevent div 0 error
                denominator.append(ufloat(1, ucinputs['CO'][0]))
            else:
                denominator.append(den)
        data[name] = (data['COhiwb'] - data['CO']) / denominator

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilution ratio from CO ' + timestampstring)
        #################################################
        # calculate dilution ratio from constant averages

        # take average values of each dilution ratio time series
        for name in ['DilRat', 'DilRat_Flow', 'DilRat_CO2', 'DilRat_CO']:
            metric[name] = np.mean(data[name])
            metric[name] = ufloat(metric[name].nominal_value,metric[name].std_dev)  #clear the correlation matrix                          

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilrat averages ' + timestampstring)

        name = 'DilRat_Ave'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = [metric['DilRat']] * len(data['DilRat'])

        name = 'DilRat_Flow_Ave'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = [metric['DilRat_Flow']] * len(data['DilRat'])

        name = 'DilRat_CO2_Ave'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = [metric['DilRat_CO2']] * len(data['DilRat'])

        name = 'DilRat_CO_Ave'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = [metric['DilRat_CO']] * len(data['DilRat'])

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilution ratio from average ' + timestampstring)
        #################################################
        DRnames = []
        if interactive == 1:
            # choose dilution ratio to use
            # create list of all available dilution ratio series
            for name in names:
                if 'DilRat' in name:
                    DRnames.append(name)

            # plot dilution ratio series
            plt.ion()
            f1, (ax1, ax2) = plt.subplots(2, sharex=True)  # subplots sharing x axis
            #for name in DRnames:
            colors={}
            colors['DilRat_Flow']='green'
            colors['DilRat_CO']='red'
            colors['DilRat_CO2'] = 'blue'
            colors['DilRat_Estimate'] = 'black'
            for name in ['DilRat_Flow','DilRat_CO','DilRat_CO2','DilRat_Estimate']:
                y = unumpy.nominal_values(data[name])  # make a list of nominal values from ufloats for plotting
                u = unumpy.std_devs(data[name])
                ub = y+u
                lb = y-u
                ax1.plot(data['datenumbers'], ub, alpha=0.25, color=colors[name])
                ax1.plot(data['datenumbers'], lb, alpha=0.25, color=colors[name])
                ax1.plot(data['datenumbers'], y, color=colors[name], label=name)            

            # plot CO and CO2 to check when you can trust the dilution ratio series
            # steady concentrations produce higher quality dilution ratios
            # rapid fluctuations in concentrations produce incorrect dilution ratios because of sensor response time differences
            # higher concentrations produce higher quality dilution ratios because they are less sensitive to background concentrations
            # lower concentrations have higher relative uncertainty from background concentrations which propagates to dilution ratio
            for name in ['CO', 'COhi', 'CO2', 'CO2hi']:
                y = unumpy.nominal_values(data[name])  # make a list of nominal values from ufloats for plotting
                ax2.plot(data['datenumbers'], y, label=name)

            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
            # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
            ax1.xaxis.set_major_formatter(xfmt)
            for tick in ax1.get_xticklabels():
                tick.set_rotation(30)
            ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
            ax2.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax2
            # plt.savefig(savefig, bbox_inches='tight')
            plt.show()

        # draw your own dilution ratio series
        name = 'DilRat_Drawn'
        names.append(name)
        DRnames.append(name)
        units[name] = units['DilRat']
        point = inputuval['DR_drawn']
        if interactive == 1:
            # GUI box to enter a value for a constant dilution ratio series
            # This can be replaced with a more complex function to draw a custom dilution ratio series on the plot
            # could use a GUI cursor drawing tool
            # or input a table of points to create a line by connecting the dots

            text = 'Create a constant dilution ratio series. Enter value:\n\nThis is just a placeholder for a more complex function to draw a series'
            title = 'Gitrdone'
            output = easygui.enterbox(text, title, str(point))
            if output:
                point = ufloat_fromstr(output)
                inputval['DR_drawn'] = point.n
                inputunc['DR_drawn'] = point.s
                inputuval['DR_drawn'] = point
                io.write_constant_outputs(dilratinputpath, inputnames, inputunits, inputval, inputunc,
                                          inputuval)  # save the value to input file
                line = 'updated dilrat input file'
                print(line)
                logs.append(line)
                line = dilratinputpath
                print(line)
                logs.append(line)

        # define data series
        data[name] = np.array([inputuval['DR_drawn']] * len(data['time']))
        # data[name]=[]
        # for n,val in enumerate(data['DilRat']):
        #    data[name].append(point)

        if interactive == 1:
            # add the new drawn dilrat series to the plot
            ax1.get_legend().remove()
            y = unumpy.nominal_values(
                data[name])  # name = DilRat_Drawn, make a list of nominal values from ufloats for plotting
            ax1.plot(data['datenumbers'], y, label=name)
            ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
            f1.canvas.draw()

            running = 'fun'
            DRname = 'DilRat'  # default dilrat is firmware dilrat

            while running == 'fun':
                # Select which dilution ratio to use
                text = "Select a dilution ratio method"
                title = 'Gitrdone'
                choices = DRnames
                output = easygui.choicebox(text, title, choices)

                if output:
                    DRname = output  # get dilution ratio from output of sensor box
                    running = 'not fun'

            plt.savefig(savefig3, bbox_inches='tight')
            plt.close()

            # message  box
            message = 'DilRat_Estimate = ' + str(inputuval['DR_estimate']) + '\nDilRat_Drawn = ' + str(
                inputuval['DR_drawn']) + '\nDo you want to update DilRat_Estimate?'
            title = 'Gitrdone'
            output = easygui.ynbox(message, title)
            if output:  # if user pressed yes
                pass
            else:  # if user pressed No
                fish = 'pike'  # exit out of the while loop
        else:  # if interactive mode is off
            DRname = name  # define DR to use for stack flow calculations
            fish = 'shad'  # exit out of the while loop

    DR = data[DRname]

    line = 'dilution ratio series chosen for the calculations: ' + DRname
    print(line)
    logs.append(line)
    ##########################################################
    # calculate stack volume concentrations

    for name in diluted_gases:
        stakname = name + 'stak'
        names.append(stakname)
        units[stakname] = '%vol'
        try:    #try subtracting dilution train data series
            bkgname = name+'bkg'
            data[stakname] = (DR*(data[name] - data[bkgname])+data[name])/ 1000000 * 100
        except: 
            try:    #try subtracting background data series
                bkgname = name+'_bkg'
                data[stakname] = (DR*(data[name] - data[bkgname])+data[name])/ 1000000 * 100
            except: #assume background = 0
                data[stakname] = (DR*data[name]+data[name])/ 1000000 * 100
    for name in undiluted_gases:
        if name != 'H2O':   #H2Ostak is already defined
            stakname = name + 'stak'
            names.append(stakname)
            units[stakname] = '%vol'
            data[stakname] = data[name] * (1 - data['H2Ostak'] / 100)  # wb = db*(1-mc)
            if name in ['COhi','CO2hi']:    #
                data[stakname] = data[stakname] / 1000000 * 100

    # balance stack composition is nitrogen
    stakname = 'N2stak'
    names.append(stakname)
    units[stakname] = '%vol'
    data[stakname] = np.array([ufloat(100, 0)] * len(data['O2']))
    for name in MWgases:
        sname = name + 'stak'
        if name != 'N2':
            data[stakname] = data[stakname] - data[sname]

    # carbon concentration (CO + CO2)
    name = 'Cstak'
    units[name] = '%vol'
    names.append(name)
    data[name] = data['COstak'] + data['CO2stak']                                        
  
    # carbon concentration (COhi + CO2hi)
    name = 'Chistak'
    units[name] = '%vol'
    names.append(name)
    data[name] = data['COhistak'] + data['CO2histak']

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated stack concentrations ' + timestampstring)
    ##########################################
    # flue gas molecular weight
    stakname = 'MWstak'
    names.append(stakname)
    units[stakname] = 'g/mol'
    data[stakname] = np.array([ufloat(0, 0)] * len(data['O2']))
    for name in MWgases:
        sname = name + 'stak'
        data[stakname] = data[stakname] + MW[name] * data[sname] / 100
    '''
    for n in range(len(data['O2'])):
        mw = ufloat(0,0)
        for name in MWgases:
            sname = name + 'stak'
            mw = mw + MW[name]*data[sname][n]/100
         #     if n < 100:
         #           print stakname + '   ' +str(mw) + '   '+ str(molwt[name]) + '   '+ str(data[stakname][n]) + '   '+ str(data[stakname+'_uc'][n])
        data[stakname].append(mw)
    '''
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated molecular weight ' + timestampstring)
    ##############################################
    # recalculate stack velocity

    name = 'StakVelCor'
    # StakVel=Cp*Kp*sqrt(Pitot*(TCnoz+273)/Pamb/MW)
    names.append(name)
    units[name] = 'm/s'

    Kp = float(129)
    Cpitot = stackinputuval['Cpitot']

    noms = []  # initialize list of nominal vlues
    uncs = []  # initialize list of uncertainty values
    for n, val in enumerate(data['Pitot_smooth']):
        if val > 0:
            inside = val * (Tstak[n] + 273.15) / data['Pamb'][n] / data['MWstak'][n]
            vel = Cpitot * Kp * umath.sqrt(inside)
            noms.append(vel.nominal_value)
            uncs.append(vel.std_dev)
        else:  # force negative pitot values to zero to prevent sqrt error
            noms.append(float(0))
            uncs.append(float(0.1))  # negative dP values forced to vel =  0.00 +/- 0.10 m/s
    data[name] = unumpy.uarray(noms, uncs)  # make it an array to allow array operations
    '''
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
    '''
    line = 'StakVel recalculated using MW time series, zeroed and smooth Pitot delta P'
    print(line)
    logs.append(line)

    ##################################################################
    # calculate mass concentration
    for name in ERgases:
        stakname = name + 'stak'
        concname = stakname + 'conc'
        names.append(concname)
        units[concname] = 'gm^-3'
        try:
            data[concname] = data[stakname] / 100 * MW[name] * data['Pamb'] / (
                    Tstak + 273) / R  # mass concentration (g/m^3)
        except:
            data[concname] = data[stakname] / 100 * MW[name] * 100000 / (
                    Tstak + 273) / R  # mass concentration (g/m^3)

    # calculate PM concentration
    name = 'PMconc'
    names.append(name)
    msc = gravmetric[
        'MSC']  # ufloat, PM is a direct measurement that gets uncertainty from the UC input file, MSC is a calculated value with a calculated uncertainty
    if pmunit == 'g':
        units[name] = 'gm^-3'
        data[name] = data['PM'] / msc / 1000/1000  # at standard conditions, mg to g
    if pmunit == 'mg':
        units[name] = 'mgm^-3'
        data[name] = data['PM'] / msc / 1000  # at standard conditions, mg                                                  

    name = 'PMstakconcstd'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name] = (DR + 1) * data['PMconc']

    name = 'PMstakconc'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name] = data['PMstakconcstd'] * Tstd / (Tstak + 273) * data['Pamb'] / Pstd  # ideal gas law temperature and pressure correction : Cstak = Cstd x Tstd/Tstak x Pstak/Pstd
        
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated mass concentrations ' + timestampstring)
    ###########################################################################
    # calculate density
    name = 'StakDensity'
    units[name] = 'g/m^3'
    names.append(name)
    data[name] = data['MWstak'] * data['Pamb'] / (Tstak + 273) / R

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated density ' + timestampstring)
    ###########################################################################
    #Reynold's number and velcocity profile
    name = 'Re'
    names.append(name)
    units[name] = ''
    data[name] = []

    visname = 'Viscocity'
    names.append(visname)
    units[visname] = 'N s/m^2'
    data[visname] = []
    #Re = (density * velocity * hydraulic diameter) / dynamic viscocity
    stack_dia = stackinputuval['stack_diameter'] / 100 #cm to m
    for n, val in enumerate(data['StakVelCor']):
        #viscocity is temeperature dependent. Regressions were run on each species at different  temps to find viscocity at any temp
        #origional values from: https://www.engineeringtoolbox.com/gases-absolute-dynamic-viscosity-d_1888.html
        temperature = data['TCnoz'][n]
        CO2vis = ((0.004 * temperature) + 1.4305) * pow(10, -5)
        COvis = ((0.0037 * temperature) + 1.7107) * pow(10, -5)
        #N2vis = ((0.0035 * temperature) + 1.7291) * pow(10, -5)
        #NOvis = ((0.0039 * temperature) + 1.4317) * pow(10, -5)
        O2vis = ((0.0043 * temperature) + 1.9988) * pow(10, -5)
        #SO2vis = ((0.0041 * temperature) + 1.2103) * pow(10, -5)
        try:
            H2Ovis = (0.0011 * math.exp(-0.01 * temperature))
        except:
            H2Ovis = (0.0011 * math.exp(-0.01 * temperature.n))

        #weighted average of species based on concentration
        CO2weight = CO2vis * data['CO2histakconc'][n]
        COweight = COvis * data['COhistakconc'][n]
        #N2weight = N2vis * data['N2stakconc'][n]
        #NOweight = NOvis * data['NOstakconc'][n]
        O2weight = O2vis * data['O2stakconc'][n]
       # SO2weight = SO2vis * data['SO2stakconc'][n]
        H2Oweight = H2Ovis * data['H2Ostakconc'][n]

        #WeightSum = CO2weight + COweight + N2weight + NOweight + O2weight + SO2weight + H2Oweight

        #ConcSum = (data['CO2stakconc'][n] + data['COstakconc'][n] + data['N2stakconc'][n] + data['NOstakconc'][n] +
        #           data['O2stakconc'][n] + data['SO2stakconc'][n] + data['H2Ostakconc'][n])
        WeightSum = CO2weight + COweight + O2weight + H2Oweight

        ConcSum = (data['CO2stakconc'][n] + data['COstakconc'][n] +
                   data['O2stakconc'][n] + data['H2Ostakconc'][n])
        viscocity = WeightSum / ConcSum

        data[visname].append(viscocity)

        top = (val * (data['StakDensity'][n]/ 1000) * stack_dia) #m/s * kg/m^3 * m

        Re = top / viscocity

        data[name].append(Re)

    name = 'Cprofile'
    names.append(name)
    units[name] = ''
    data[name] = []
    for n, val in enumerate(data['Re']):
        if val < 2300: #laminar
            unc = 0.5 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.5, unc))
        elif 2300 <= val < 4000: #transient
            value = (0.0001705882 * val) + 0.107647 #assuming linear transition between (2300, 0.5) and (4000, 0.79)
            absunc = value.s
            relunc = value.n * 0.15 #15% relative uncertainty
            unc = absunc + relunc
            data[name].append(ufloat(value.n, unc))
        elif 4000 <= val < 10000: #turbulent
            unc = 0.79 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.79, unc))
        elif 10000 <= val < 100000: #turbulent
            unc = 0.811 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.811, unc))
        elif 100000 <= val < 1000000: #turbulent
            unc = 0.849 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.849, unc))
        elif 1000000 <= val < 10000000: #turbulent
            unc = 0.875 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.875, unc))
        elif 10000000 <= val < 100000000: #turbulent
            unc = 0.893 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.893, unc))
        elif 10000000 <= val: #turbulent
            unc = 0.907 * 0.15 #15% relative uncertainty
            data[name].append(ufloat(0.907, unc))
    #################################################################################33
    # calculate volumetric flow rate

    # first calculate area
    stack_area = np.pi * (stackinputuval['stack_diameter'] / 100) * (stackinputuval['stack_diameter'] / 100) / 4  # m^2

    name = 'StakFlow'
    units[name] = 'm^3/s'
    names.append(name)
    data[name] = []
    for n, val in enumerate(data['StakVelCor']):
        data[name].append(val * stack_area * data['Cprofile'][n])

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated stack volumetric flow rate ' + timestampstring)
    ###########################################################################
    # calculate mass flow (g/s) = volflow (m^3/s) x density (g/m^3)
    name = 'MassFlow'
    units[name] = 'g/s'
    names.append(name)
    data[name] = data['StakFlow'] * data['StakDensity']

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated stack mass flow rate ' + timestampstring)
    ###########################################################################
    # calculate energy flow (Watts)  = Cp (J/g/K) x massflow (g/s) x dT (K)
    name = 'EnergyFlow'
    units[name] = 'W'
    names.append(name)
    data[name] = Cp * data['MassFlow'] * (Tstak - data['COtemp'])

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated energy flow rate ' + timestampstring)

    # calculate emission rates for gases
    for gas in ERgases:
        stakname = gas + 'stak'
        concname = stakname + 'conc'
        ername = 'ER' + stakname
        units[ername] = 'g/hr'
        names.append(ername)
        data[ername] = data['StakFlow'] * data[concname] * 3600  # g/hr
    # calculate emission rate for PM
    name = 'ERPMstak'
    concname = 'PMstakconc'
    units[name] = pmunit+'/hr'
    names.append(name)
    data[name] = data['StakFlow'] * data[concname] * 3600  # g/hr or mg/hr

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated emission rates ' + timestampstring)    
    #################################################################
    
    #flow rate of combustion air
    
    # background combustion air composition, volume concentrations
    air_moisture_content = stackinputuval['air_moisture_content']
    name = 'H2Oair' #background air H2O concentration
    units[name] = '%vol'
    names.append(name)
    data[name] = np.array([air_moisture_content/10000] * len(data['time']))
    name = 'CO2air' #background air CO2 concentration
    units[name] = '%vol'
    names.append(name)
    data[name] = data['CO2hi_bkg']/10000*(1-data['H2Oair']/100)
    balance = 100-data['H2Oair']-data['CO2air']
    name = 'O2air' #background air O2 concentration
    units[name] = '%vol'
    names.append(name)
    data[name] = 0.21*balance   #assume balance air is 21% O2 and 79% N2
    name = 'N2air' #background air N2 concentration
    units[name] = '%vol'
    names.append(name)
    data[name] = 0.79*balance   #assume balance air is 21% O2 and 79% N2

    #background combustion air composition, mass concentration
    name='airconc'
    names.append(name)
    units[name] =  'gm^-3'
    data[name] = np.array([ufloat(0,0)] * len(data['time']))
    for name in ['N2','O2','CO2','H2O']:
        airname = name + 'air'
        concname = airname + 'conc'
        names.append(concname)
        units[concname] = 'gm^-3'
        data[concname] = data[airname] / 100 * MW[name] * data['Pamb'] / (Tstak + 273) / R  # mass concentration (g/m^3)
        data['airconc'] = data['airconc']+data[concname]
        
    name='Cairconc'
    names.append(name)
    units[name] =  'gm^-3'
    data[name] = data['CO2air'] / 100 * MW['C'] * data['Pamb'] / (Tstak + 273) / R  # mass concentration (g/m^3)
        
    #background combustion air emission rate
    name = 'ERCO2stak_bkg' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERN2stak']*data['CO2airconc']/data['N2airconc']
    
    name = 'ERCstak_bkg' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERN2stak']*data['Cairconc']/data['N2airconc']
    
    name = 'ERH2Ostak_bkg' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERN2stak']*data['H2Oairconc']/data['N2airconc']
    
    name = 'ERairstak_bkg' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERN2stak']*data['airconc']/data['N2airconc']
    
    #background subtracted emission rates
    name = 'ERCO2stak_bs' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERCO2stak']-data['ERCO2stak_bkg']
    
    name = 'ERCO2histak_bs' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERCO2histak']-data['ERCO2stak_bkg']
    
    name = 'ERCstak_bs' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERCstak']-data['ERCstak_bkg']
    
    name = 'ERChistak_bs' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERChistak']-data['ERCstak_bkg']
    
    name = 'ERH2Ostak_bs' 
    names.append(name)
    units[name] = 'g/hr'
    data[name] = data['ERH2Ostak']-data['ERH2Ostak_bkg']                          

    ###########################################################################
    ###########################################################################
    # calculate firepower (Watts)
    # simple case is carbon emission rate converted to fuel and energy using carbon balance
    # improve by using Can B.415 method accounting for flue gas composition and energy lost to CO formation

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    name = 'Firepower'
    units[name] = 'W'
    names.append(name)
    data[name] = []
    for n, val in enumerate(data['ERCstak']):
        if val < 0: #for negative values make them 0. Used for when the stove is off
            val = ufloat(0, val.s)
        data[name].append((val / 3600) / emetric['fuel_Cfrac_db'] * emetric[
            'fuel_EHV'] * 1000)  # metric['CER_CO']/metric['EFenergy_CO']*1000000) data['ERCstak']/3600 *metric['CER_CO']/metric['EFenergy_CO']*1000000

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated firepower ' + timestampstring)
    ###########################################################################
    # calculate useful energy (Watts)
    name = 'UsefulPower'
    units[name] = 'W'
    names.append(name)
    data[name] = []
    for n, val in enumerate(data['Firepower']):
        if data['EnergyFlow'][n] < 0: #For when the values is negative, when stove is off
            data[name].append(ufloat(0, 0))
        else:
            data[name].append(val - data['EnergyFlow'][n])  # =data['Firepower']-data['EnergyFlow']

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated useful power ' + timestampstring)
    
    ###########################################################################
    # calculate thermal efficieny(%)
    name = 'ThermalEfficiency'
    units[name] = '%'
    names.append(name)
    data[name] = []
    for n, val in enumerate(data['Firepower']):
        if val.n == 0:  # change to avoid div by 0 error
            val = ufloat(0.1, 0)
        if data['UsefulPower'][n].n == 0: #avoiding large uncertainties at 0s
            top = ufloat(0, 0)
        else:
            top = data['UsefulPower'][n]
        data[name].append((top / val) * 100)
    
    ####################################################
    ####################################################
    ####################################################
    
    #energy calculations from CAN B415.1
    
    #energy input
    # in CAN B415.1 the fuel burn rate is determined from measuring fuel consumption with the scale
    # but here we calculate it from the carbon emission rate
    name = 'I_CAN'
    units[name] = 'W'
    names.append(name)
    data[name] = data['ERCstak']/ 3600 / emetric['fuel_Cfrac_db'] * emetric['fuel_HHV'] * 1000 
    for n,val in enumerate(data[name]):
        if val < 0: #for negative values make them 0. Used for when the stove is off
            data[name][n] = ufloat(0, val.s)
    
    #molar flow rate
    # in CAN B415.1 the molar rate is calculated from the chemical mass balance
    # but here we calculate it from the measured stack flow rate
    for name in MWgases:
        concname = name+'stakconc'
        molname = 'MR'+name
        units[molname] = 'mol/s'
        names.append(molname)
        data[molname] = data['StakFlow']*data[concname]/MW[name] # m3/s * g/m3 * mol/g = mol/s
        
    #heat capacity of 'gas' at temperature 'T' (K), Cp (KJ/mol*K)   (clause 13.7.7)
    def CalcCp(gas, T):
        #define dictionary of heat capacity linear approximation values 
        #CP_lin['gas'] = [a (J/mol*K^2), b (J/mol*K)]
        #CP = a * T + b
        Cp_lin = {}
        Cp_lin['CO'] = [0.0056,27.162]
        Cp_lin['COhi'] = [0.0056,27.162]
        Cp_lin['CO2'] = [0.029,29.54]
        Cp_lin['CO2hi'] = [0.029,29.54]
        Cp_lin['H2O'] = [0.0057,32.859]
        Cp_lin['O2'] = [0.009,26.782]
        Cp_lin['N2'] = [0.0062,26.626]
        Cp_lin['CH4'] = [0.056,18.471]
  
        Cp = T*Cp_lin[gas][0]+Cp_lin[gas][1] #(J/mol*K)        
        return Cp
        
    #sensible energy loss out the chimney
    # CAN B415.1 uses 6 gases but we are only using the 5 gases defined in MWgases list (omitting CH4)
    # COtemp (sensor box temp) is used here in place of room temp because we did not measure room temp
    name = 'L_sen_CAN'
    units[name] = 'W'
    names.append(name)
    data[name] = np.array([ufloat(0,0)]*len(Tstak))   #initialize data series as 0 array
    for n,val in enumerate(Tstak):
        Lsen = float(0)
        for gasname in MWgases:
            molname = 'MR'+gasname  #mol rate (mol/s)
            Lsen = Lsen + data[molname][n]*(CalcCp(gasname,Tstak[n]+273)+CalcCp(gasname,data['COtemp'][n]+273))/2 * (Tstak[n]-data['COtemp'][n])
        data[name][n] = Lsen
    
    #latent energy loss out the chimney
    #in CAN B415.1 this uses the moles of H20 from combustion (the moles of H2O that changed phase)
    # here we use the total moles of H2O in the chimney from fuel and including moisture in intake air (room air)
    # we did not measure intake air temperature or humidity in order to quantify the background moisture and subtract it from the total stack moisture
    # so it is an overestimate of latent energy loss
    # because only H2O from fuel changed phase. H2O in intake air was already a gas. 
    name = 'L_lat_CAN'
    units[name] = 'W'
    names.append(name)
    data[name] = 43969 * data['MRH2O']
   
    #chemical energy loss out the chimney
    name = 'L_chem_CAN'
    units[name] = 'W'
    names.append(name)
    if 'CH4' in MWgases:
        data[name] = data['MRCOhi']*282993 + data['CH4']*890156
    else:
        data[name] = data['MRCOhi']*282993
    
    # overall heat output (claue 13.7.9.1)
    name = 'E_out_CAN'
    units[name] = 'W'
    names.append(name)
    data[name] = data['I_CAN'] - data['L_sen_CAN'] - data['L_lat_CAN'] - data['L_chem_CAN']
    
    #combustion efficiency (clause 13.7.9.2)
    name = 'CE_CAN'
    units[name] = '%'
    names.append(name)
    data[name] = np.array([ufloat(0,0)]*len(Tstak))  #initialize data series as 0 array
    for n,val in enumerate(data['I_CAN']):
        if val.n <= 0:
            data[name][n] = np.nan  #to avoid divide by 0 error
        else:
            data[name][n] = (data['I_CAN'][n]-data['L_chem_CAN'][n])/data['I_CAN'][n]*100
            if data[name][n] > 99.5:
                data[name][n] = ufloat(99.5,val.s)
    
    #overall efficiency  (clause 13.7.9.3)
    name = 'OE_CAN'
    units[name] = '%'
    names.append(name)
    data[name] = np.array([ufloat(0,0)]*len(Tstak))  #initialize data series as 0 array
    for n,val in enumerate(data['I_CAN']):
        if val.n <= 0:
            data[name][n] = np.nan  #to avoid divide by 0 error
        else:
            if data['E_out_CAN'][n] <= 0:       #if negative efficiency
                data[name][n] = ufloat(0,0)     #force to 0
            else:  
                data[name][n] = data['E_out_CAN'][n]/data['I_CAN'][n]*100   #if not negative efficiency
    
    #heat transfer efficiency (clause 13.7.9.4)
    name = 'HTE_CAN'
    units[name] = '%'
    names.append(name)
    data[name] = data['OE_CAN']/data['CE_CAN']*100
    
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated CAN B415.1 energy metrics ' + timestampstring)

    #####################################################################
    #   output times series data file
    #io.write_timeseries_with_uncertainty(outputpath, names, units, data)  # this one is too slow
    io.write_timeseries_with_uncertainty2(outputpath, names, units, data) #fast                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    # io.write_timeseries_without_uncertainty(outputpath,names,units,data)   #use this one to write fast and ignore uncertainty value
    # io.write_timeseries(outputpath,names,units,data)       #don't use: writes entire ufloat to 1 cell but not enough sig figs
    line = '\nCreated stack flow time series data file: '
    print(line)
    logs.append(line)
    line = outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    line = 'finally done ' + timestampstring


#####################################
#####################################
# moving average function
# dont use! too slow
# def movingaverage(interval, window_size):
#        window = np.ones(int(window_size))/float(window_size)
#        return np.convolve(interval, window, 'same')

# moving average function
# use this one, very fast
# averaging window is in front of the data point, edit to make centered on data point
def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    short = (cumsum[N:] - cumsum[:-N]) / float(N)  # the length of this smooth array == len(x)-N+1
    pad = [short[-1]] * (N - 1)  # stretch the last value to make it the same length as x
    return np.insert(short, -1, pad)


# this function makes a list of nominal values from a list of ufloats for plotting
# input:   ufloat_series = list of ufloats
# using the function unumpy.nominal_values(ufloat_series) is faster
def nomvals(ufloat_series):
    noms = []  # initialize a list of nominal values
    for val in ufloat_series:
        try:  # try to read the nominal value if it is a ufloat
            noms.append(val.n)
        except:  # if not a ufloat
            noms.append(val)
    return noms


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_StackFlowCalcs(inputpath, stackinputpath, ucpath, gravpath, metricpath, dilratinputpath, outputpath, logpath)
    