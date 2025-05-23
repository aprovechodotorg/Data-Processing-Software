# v0.6 Python3
#   v0.1: for Apro
#   v0.2: faster
#   v0.3: added firepower
#   v0.5: input DR to calc stack H2O instead of using DR_flows
#   v0.6: added energy calcs from CAN B415.1

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
from uncertainties import unumpy
from datetime import datetime as dt
import os
import easygui
import matplotlib.pyplot as plt
import matplotlib
import time

#########      inputs      ##############
# input file of all time series data
inputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_TimeSeriesPitot.csv'
# input file for stack flow calculations
stackinputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_StackFlowInputs.csv'
# uncertainty inputs file
ucpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_UCInputs.csv'
# input file of gravimetric outputs
gravpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_GravOutputs.csv'
# input file of carbon balance test average output metrics
metricpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_EmissionOutputs.csv'
# output file of time series data
outputpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_TimeSeriesStackFlow.csv'
# log file
logpath = 'C:\Mountain Air\Projects\AproDOE\Data\collocated\PEMS\8.23.23\8.23.23_log.txt'


##########################################

def PEMS_StackFlowCalcs(inputpath, stackinputpath, ucpath, gravpath, metricpath, energypath, dilratinputpath,
                        outputpath, logpath, savefig3):
    interactive = 1  # set to 1 for interactive mode
    ver = '0.6'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_StackFlowCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    particles = ['PM']  # measured particles in the dilution train
    possible_diluted_gases = ['CO', 'CO2', 'SO2', 'NO', 'NO2', 'HC', 'VOC', 'CH4',
                              'H2O']  # possible measured gases in the dilution train, depending on sensor box
    undiluted_gases = ['COhi', 'CO2hi', 'O2']  # measured gases in the undiluted train
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
    diluted_gases.append('H2O')  # calculated from RH
    stack_gases = diluted_gases + undiluted_gases  # all measured gases
    ERgases = diluted_gases + undiluted_gases + ['N2', 'C']  # gases that will get emission rate calcs

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
        if name in ucnames:
            if name == 'time' or name == 'seconds' or name == 'ID':
                pass
            else:
                unc = abs(data[name] * ucinputs[name][1]) + abs(ucinputs[name][
                                                                    0])  # uncertainty is combination of relative and absolute from the uncertainty input file
                data[name] = unumpy.uarray(data[name], unc)
        if name == 'CH4':  # use HC uncertainty inputs for CH4
            unc = abs(data[name] * ucinputs['HC'][1]) + abs(ucinputs['HC'][
                                                                0])  # uncertainty is combination of relative and absolute from the uncertainty input file
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
    staktempname = 'TCnoz'  # define name of default stack temperature channel
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
    '''
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
    '''

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
    # H2O in diluted sample
    name = 'Psat'  # saturation pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    # data[name]=[]
    name = 'PH2O'  # partial pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    # data[name]=[]
    name = 'H2O'  # H2O concentration
    names.append(name)
    units[name] = 'ppm'
    # data[name]=[]

    # vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    # P=10^(A-B/(C+T))
    # P = vapor pressure (mmHg)
    # T = temperature (C)
    A = 8.07131  # constant
    B = 1730.63  # constant
    C = 233.426  # constant

    data['Psat'] = np.power(10, (A - B / (C + data['COtemp']))) / .0075  # 1 Pa = 0.0075 mmHg
    data['PH2O'] = data['Psat'] * data['RH'] / 100  # ufloat
    data['H2O'] = data['PH2O'] / data['Pamb'] * 1000000  # ufloat ppm
    '''
    for n in range(len(data['RH'])):
        Tval = data['COtemp'][n]
        Psatval = pow(10,(A-B/(C+Tval)))/.0075 # 1 Pa = 0.0075 mmHg
        PH2Oval = Psatval*data['RH'][n]/100 #ufloat
        H2Oval = PH2Oval/data['Pamb'][n]*1000000 #ufloat ppm

        data['Psat'].append(Psatval)
        data['PH2O'].append(PH2Oval)
        data['H2O'].append(H2Oval)
    '''
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

    name = 'DilRat_Flow_smooth'
    names.append(name)
    units[name] = units['DilRat']
    # data[name] = movingaverage(data['DilRat_Flow'],100)
    data[name] = running_mean(data['DilRat_Flow'], 100)

    '''
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
    '''

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('calculated dilution ratio from flows ' + timestampstring)
    line = '    DilRat_Flow = DilFlow/(FiltFlow+SampFlow-DilFlow)'
    print(line)
    logs.append(line)

    ####################################
    ####################################
    ########## Note on calculating dilution ratio from gas sensors ############3
    # We need to know the undiluted stack concentrations of CO and CO2 on a wet basis (the actual concentrations in the stack)
    # COhi and CO2hi are measured on dry basis and they need to be converted to wet basis
    # The stack H2O concentration is currently calculated from the measured H2O in the diluted sample and the dilution ratio
    # Problem: We need the stack H2O concentration to calculate the dilution ratio...
    #   but we need the dilution ratio to calculate the stack H2O concentration.
    # Solution: Input value for dilution ratio (a best estimate) to estimate the stack H2O concentration
    #       to calculate CO and CO2 wet basis for the dilution ratio calculation.
    #       Then, after the best dilution ratio series is chosen, stack concentrations will be recalculated using that dilution ratio for outputs
    #       If the final dilution ratio is much different than the estimated DR you first entered,
    #       you may need to repeat the process a few times to converge on the best DR.
    #       Each time entering a DR at the start that is closer to the final calculated DR.
    # Better solution:
    #       define dilution ratio on a dry basis,
    #       then use it to calculate stack concentrations on a dry basis, including H2O on a dry basis
    #       then calc stack concentrations on wet basis
    # Or measure stack moisture using EPA inpinger method instead of deriving it from RH
    # Another possible solution: Calculate theoretical stack moisture using CANB415
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

        name = 'H2O'
        stakname = name + 'stak'
        # names.append(stakname)
        # units[stakname] = '%vol'
        data[stakname] = (DR + 1) * data[name] / 1000000 * 100  # convert ppm to %vol

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
        #   It can be calculated from SubtractBkg function output as the background-subtracted stack concentration plus the background value that was subtracted
        # Csamp is the diluted sample concentration before background subtraction
        #   It can be calculated from SubtractBkg function output as the background-subtracted diluted sample concentration plus the background value that was subtracted
        # The denominator (Csamp-Cdil) is the background-subtracted diluted sample concentration if we assume
        #   the dilution air concentration is same as the background air concentration.
        #   For CO this assumption should be fine because both background and dilution air concentrations should be close to 0  ppm.
        #   For CO2 this assumption should be fine for high concentrations that are not very sensitive to the background subtraction,
        #   but may add artifact to the dilution ratio for low concentrations that are sensitive to the background subtraction
        #########calculate dilution ratio from CO2 ######################
        name = 'DilRat_CO2'
        names.append(name)
        units[name] = units['DilRat']
        denominator = []
        for val in data['CO2']:
            if val.n == 0:  # change any zero values to 1 ppm +/- absolute unc to prevent div 0 error
                denominator.append(ufloat(1, ucinputs['CO2'][0]))
            else:
                denominator.append(val)
        data[name] = (data['CO2hiwb'] + data['CO2hi_bkgwb'] - data['CO2'] - data['CO2_bkg']) / denominator

        # smooth
        name = 'DilRat_CO2_smooth'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = running_mean(data['DilRat_CO2'], 100)

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilution ratio from CO2 ' + timestampstring)
        #########calculate dilution ratio from CO ######################
        name = 'DilRat_CO'
        names.append(name)
        units[name] = units['DilRat']
        denominator = []
        for val in data['CO']:
            if val.n == 0:  # change any zero values to 1 ppm +/- absolute unc to prevent div 0 error
                denominator.append(ufloat(1, ucinputs['CO'][0]))
            else:
                denominator.append(val)
        data[name] = (data['COhiwb'] + data['COhi_bkgwb'] - data['CO'] - data['CO_bkg']) / denominator

        # smooth
        name = 'DilRat_CO_smooth'
        names.append(name)
        units[name] = units['DilRat']
        data[name] = running_mean(data['DilRat_CO'], 100)

        timestampobject = dt.now()  # get timestamp from operating system for log file
        timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
        print('calculated dilution ratio from CO ' + timestampstring)
        #################################################
        # calculate dilution ratio from constant averages

        # take average values of each dilution ratio time series
        for name in ['DilRat', 'DilRat_Flow', 'DilRat_CO2', 'DilRat_CO']:
            metric[name] = np.mean(data[name])

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
            for name in DRnames:
                y = unumpy.nominal_values(data[name])  # make a list of nominal values from ufloats for plotting
                ax1.plot(data['datenumbers'], y, label=name)

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
        data[stakname] = (DR + 1) * data[name] / 1000000 * 100

    for name in undiluted_gases:
        stakname = name + 'stak'
        names.append(stakname)
        units[stakname] = '%vol'
        data[stakname] = data[name] * (1 - data['H2Ostak'] / 100)  # wb = db*(1-mc)
        if name != 'O2':
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
        data[concname] = data[stakname] / 100 * MW[name] * data['Pamb'] / (
                    Tstak + 273) / R  # mass concentration (g/m^3)

    # calculate PM concentration
    name = 'PMconc'
    units[name] = 'mgm^-3'
    names.append(name)
    msc = gravmetric[
        'MSC']  # ufloat, PM is a direct measurement that gets uncertainty from the UC input file, MSC is a calculated value with a calculated uncertainty
    data[name] = data['PM'] / msc / 1000  # at standard conditions

    name = 'PMstakconcstd'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name] = (DR + 1) * data['PMconc']

    name = 'PMstakconc'
    units[name] = 'mgm^-3'
    names.append(name)
    data[name] = data['PMstakconcstd'] * Tstd / (Tstak + 273) * data[
        'Pamb'] / Pstd  # ideal gas law temperature and pressure correction : Cstak = Cstd x Tstd/Tstak x Pstak/Pstd

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
    # calculate volumetric flow rate

    # first calculate area
    stack_area = np.pi * (stackinputuval['stack_diameter'] / 100) * (stackinputuval['stack_diameter'] / 100) / 4  # m^2

    name = 'StakFlow'
    units[name] = 'm^3/s'
    names.append(name)
    data[name] = data['StakVelCor'] * stack_area * stackinputuval['Cprofile']

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

    ###########################################################################
    ###########################################################################

    name = 'ERCstak'
    units[name] = 'g/hr'
    names.append(name)
    data[name] = data['ERCOhistak'] * MW['C'] / MW['CO'] + data['ERCO2histak'] * MW['C'] / MW['CO2']
        
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

    # calculate emission rate for PM
    name = 'ERPMstak'
    concname = 'PMstakconc'
    units[name] = 'mg/hr'
    names.append(name)
    data[name] = data['StakFlow'] * data[concname] * 3600  # mg/hr

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")
    print('Calculated emission rates ' + timestampstring)
    
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
    io.write_timeseries_with_uncertainty(outputpath, names, units, data)  # use this one, but it is slow
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
    