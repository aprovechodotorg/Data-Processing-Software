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


import os
import csv
import math
import numpy as np
from scipy.signal import savgol_filter
import uncertainties as unumpy
import matplotlib
#matplotlib.use('QtAgg')
#matplotlib.use('TkAgg', force=True)
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg
from PEMS_StakVel import PEMS_StakVel
from PEMS_StakEmissions import PEMS_StakEmissions
import traceback

########### inputs (only used if this script is run as executable) #############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
inputpath='TimeSeries_test.csv'
energypath='EnergyOutputs.csv'
graninputpath = 'GravOutputs.csv'
empath = 'EmissionOutputs.csv'
periodpath = 'AveragingPeriod.csv'
outputpath = 'RealtimeOutputs.csv'
averageoutputpath = 'AveragingPeriodOutputs.csv'
averagecalcoutputpath = 'AveragingPeriodCalcs.csv'
fullaverageoutputpath = 'RealtimeAveragesOutputs.csv'
savefig = 'averagingperiod.png'
logpath='log.txt'
##################################

def PEMS_Realtime(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, periodpath, outputpath, averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, savefig, logpath):
    # Function takes in data and outputs realtime calculations for certain metric
    # Function allows user to cut data at different time periods and outputs averages over cut time period

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]
    #################################################

    #flow = 'F1Flow' #Able to change flow chanel for stakvel calcs

    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    line = 'loaded: ' + inputpath #add to log
    print(line)
    logs.append(line)

    emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'PM']  # emission species that will get metric calculations

    for em in emissions: #Test if emissions is in data dictionary
        try:
            data[em]
        except:
            emissions.remove(em)

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'loaded: ' + energypath
    print(line)
    logs.append(line)

    # load grav metrics data file
    [gravnames, gravunits, gravval, gravunc, gravmetric] = io.load_constant_inputs(gravinputpath)

    line = 'loaded: ' + gravinputpath
    print(line)
    logs.append(line)

    # load emissions data file
    [emnames, emunits, emval, emunc, emmetric] = io.load_constant_inputs(empath)

    line = 'loaded: ' + empath
    print(line)
    logs.append(line)

    metric = {} #Dictionary for storing calculated values

    #################################CARBON BALANCE

    Tstd = float(293)  # define standard temperature in Kelvin
    Pstd = float(101325)  # define standard pressure in Pascals

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
    MW['CH4'] = float(16.04)  # molecular weight of methane (g/mol)
    MW['air'] = float(29)  # molecular weight of air (g/mol)
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    # SOME PM VALUES ARE NEGATIVE AND START AND END. CHANGED TO 0
    conc = []
    for n, val in enumerate(data['PM']):
        if val < 0.0:
            val =0.0
        conc.append(val / float(gravval['MSC']) / 1000)
    data['conc'] = conc
    ################################################
    # calculate metrics


    # mass concentration

    #SOME CO AND CO2 VALUES ARE NEGATIVE AND START AND END. CHANGED TO 0
    for em in emissions:
        name = em + 'conc'
        names.append(name)
        values = []
        if em == 'PM':
            units[name] = 'mgm^-3'
            for val in conc:
                values.append(val)
            metric[name] = values
            data[name] = values
        else:
            units[name] = 'gm^-3'
            for val in data[em]:
                #if val < 0:
                    #val = 0.00001
                F = MW[em] * Pstd / Tstd / 1000000 / R  # ISO19869 Formula 28
                values.append(F * val)
            metric[name] = values
            data[name] = values

    # total carbon concentration
    values = []
    name = 'Cconc'
    names.append(name)
    units[name] = 'gm^-3'
    for n, val in enumerate(metric['COconc']):
        values.append(val * MW['C'] / MW['CO'] + metric['CO2conc'][n] * MW['C'] / MW['CO2'])  # ISO19869 Formula 60
    metric[name] = values
    data[name] = values

    # total carbon concentration hi range
    if 'COhi' in emissions:
        values = []
        name = 'Cconchi'
        names.append(name)
        units[name] = 'gm^-3'
        for n, val in enumerate(metric['COhiconc']):
            values.append(val * MW['C'] / MW['CO'] + metric['CO2hiconc'][n] * MW['C'] / MW['CO2'])  # ISO19869 Formula 60
        metric[name] = values
        data[name] = values

    # MCE
    values = []
    name = 'MCE'
    names.append(name)
    units[name] = 'mol/mol'
    for n, val in enumerate(data['CO2']):
        values.append(val / (data['CO'][n] + val))  # ISO 19869 Formula 61
    metric[name] = values
    data[name] = values

    # MCEhi
    if 'COhi' in emissions:
        values = []
        name = 'MCEhi'
        names.append(name)
        units[name] = 'mol/mol'
        for n, val in enumerate(data['CO2hi']):
            values.append(val / (data['COhi'][n] + val))  # ISO 19869 Formula 61
        metric[name] = values
        data[name] = values

    #carbon emission ratio
    for em in emissions:
        name = 'CER_'+em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/g'
        else:
            units[name] = 'g/g'
        if 'hi' in em:
            cconc = 'Cconchi'
        else:
            cconc = 'Cconc'
        values = []
        for n, val in enumerate(metric[em+'conc']):
            values.append(val/metric[cconc][n])  #ISO 19869 Formula 63
        metric[name] = values
        data[name] = values

    # Emission factor, fuel mass based
    for em in emissions:
        name = 'EFmass_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/kg'
        else:
            units[name] = 'g/kg'
        values = []
        for val in metric['CER_' + em]:
            values.append(val * emetric['fuel_Cfrac'].nominal_value * 1000)  # ISO 19869 Formula 66-69
        metric[name] = values
        data[name] = values

    #Emission factor, dry fuel mass based, not  an ISO 19869 metric
    for em in emissions:
        name = 'EFmass_dry_'+em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/kg'
        else:
            units[name] = 'g/kg'
        values = []
        for val in metric['CER_' + em]:
            values.append(val*emetric['fuel_Cfrac_db'].nominal_value*1000)
        metric[name] = values
        data[name] = values

    # Emission factor, fuel energy based
    for em in emissions:
        name = 'EFenergy_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/MJ'
        else:
            units[name] = 'g/MJ'
        values = []
        for val in metric['EFmass_' + em]:
            values.append(val / emetric['fuel_EHV'].nominal_value)  # ISO 19869 Formula 70-73
        metric[name] = values
        data[name] = values
    #Emission rate
    for em in emissions:
        name = 'ER_'+em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/min'
        else:
            units[name] = 'g/min'
        values = []
        for val in metric['EFenergy_' + em]:
            values.append(val*emetric['fuel_energy'].nominal_value/emetric['phase_time_test'].nominal_value)  #ISO 19869 Formula 74-77
        metric[name] = values
        data[name] = values

    name = 'ER_PM_heat' #emission rate g/hr
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['ER_PM']:
        if float(val) < 0.0:
            values.append(0.0)
        else:
            values.append(val*60/1000)
    metric[name] = values
    data[name] = values

    #######################FLOWRATE PM

    #volflowPM = emmetric['ER_PM_heat'].nominal_value / gravmetric['PMconc_tot'].nominal_value  # m^3/hr
    volflowPM = emmetric['ER_PM_heat'].nominal_value / gravmetric['PMconc_tot'].nominal_value / 1000  # m^3/hr
    print('volflowPM='+str(volflowPM))

    name = 'Realtime_conc_PM'
    names.append(name)
    units[name] = 'mg/m^3'
    values = []
    for val in data['PM']:
        values.append(val / gravmetric['MSC'].nominal_value)  # ug/m^3 realtime concentration
    metric[name] = values
    data[name] = values

    name = 'PM_flowrate' #Emission rate based on flowrate
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['Realtime_conc_PM']:
        values.append((val * volflowPM))
    metric[name] = values
    data[name] = values

    #####################################################################
    #Volumetric flow rate/stack flow rate for PM
    #Not working for PC
    '''
    try:
        data, names, units, TC, dilrat = PEMS_StakVel(data, names, units, outputpath, savefig) #Recalculate stak velocity- To do: subtract background pitot
    except Exception as e:
        line = 'Error: ' + str(e)
        print(line)
        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
        logs.append(line)

    try:
        data, names, units = PEMS_StakEmissions(data, gravmetric, emetric, names, units, eunits, TC, dilrat) #Emissions, energy flow
    except Exception as e:
        line = 'Error: ' + str(e)
        print(line)
        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
        logs.append(line)

    #To do: handling different dillution ratio scenarios, figure out which is best for each test
    '''
    #load in stak velocity timeseries data
    try:
        [snames, sunits, sdata] = io.load_timeseries(stakpath)
        plots = 4
    except:
        plots = 1
    ####################################################
    '''
    #Firepower (from excel logger data equations)

    #mole flowrate
    name = 'MolFlow'
    names.append(name)
    units[name] = 'mol/s'
    data[name] = []
    for val in data['MassFlow']:
        mf = val / data['MW'][n]
        data[name].append(mf)

    #CO2 flow rate
    name = 'CO2Flow'
    names.append(name)
    units[name] = 'mol/s'
    data[name] = []
    for n, val in enumerate(data['CO2stak']):
        co2f = val * data['MolFlow'][n] / 1000
        data[name].append(co2f)

    #CO flow rate
    name = 'COFlow'
    names.append(name)
    units[name] = 'mol/s'
    data[name] = []
    for n, val in enumerate(data['COstak']):
        cof = val * data['MolFlow'][n] / 1000
        data[name].append(cof)

    #Carbon burn rate
    name = 'CBurnRate'
    names.append(name)
    units[name] = 'g/s'
    data[name] = []
    for n, val in enumerate(data['CO2Flow']):
        cbr = (data['COFlow'][n] + val) *12 #molecular weight of carbon (mass flow rate)
        data[name].append(cbr)

    #firepower
    name = 'FirePower'
    names.append(name)
    units[name] = 'watts'
    data[name] = []
    for n, val in enumerate(data['CBurnRate']):
        fp = val / emetric['fuel_Cfrac'] * emetric['fuel_EHV'] #excel uses net calorific value, can't find in data - Use GCV or LHV or use effective carbon fraction
        data[name].append((fp.n * 1000)) #kW to W
        #figure out what is being used for BTUs per hour in heating stove metrics and then match calorific value that is used there
        
    try:
        name = 'Stak_PM'
        names.append(name)
        units[name] = 'g/m^3'
        values = []
        for n, val in enumerate(data['DilFlow']):
            stak = gravmetric['PMconc_tot'] / (1 - (val / (data['SampFlow'][n] + data[flow][n])))
            values.append(stak.nominal_value / 1000)
        data[name] = values
        metric[name] = values

        name = 'StakFlow'
        names.append(name)
        units[name] = 'm^3/s'
        values = []

        rad = (emetric['stak_dia'] * 0.0254) / 2 #Inch to meter
        area = math.pi * pow(rad, 2) #m^2

        for val in data['StakVel']:
            flow = val * area * 0.8
            values.append(flow.nominal_value)
        data[name] = values
        metric[name] = values

        name = 'ER_stak' #Emission rate based on stak velocity
        names.append(name)
        units[name] = 'g/hr'
        values = []
        for n, val in enumerate(data['StakFlow']):
            newval = val * 60 * 60  #convert to m^3/hr
            stak = newval * data['Stak_PM'][n]
            values.append(stak)
        data[name] = values
        metric[name] = values
    except:
        pass
    '''
    '''
    if 'ERPMstak' in names: #PC Will not calculate stak velocity
        plots = 3
    else:
        plots = 2

    if plots == 2: #If PC, remove stak velocity from  names list
        try:
            names.remove('Stak_PM')
            names.remove('StakFlow')
            names.remove('ERPMstak')
        except:
            pass
    '''
    #################################################################
    # Convert datetime to readable dateobject
    date = data['time'][0][:8] #pull date

    name = 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data['time']):
        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)

    name = 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    ############################################################################
    #exponential Moving average to smooth data (currently does all variables)
    #calcualted by taking weighted mean of the observation at a time.
    #weight of obs decreases exponentially over time.
    #good for analyzing recent changes
    '''
    smoothing = ['ER_PM_heat', 'PM_flowrate', 'ERPMstak']
    window_size = 50

    for name in smoothing:
        values = np.array(data[name])
        moving_avg = np.convolve(values, np.ones(window_size) / window_size, mode='same')
        metric[name] = moving_avg.tolist()
        data[name] = metric[name]
    '''
    #Create full averages
    fullavg = {}
    unc={}
    uval={}
    emweightavg = ['MCE', 'MCEhi', 'CER_CO', 'CER_COhi', 'CER_CO2', 'CER_CO2hi','CER_PM','EFmass_CO', 'EFmass_COhi',
                   'EFmass_CO2', 'EFmass_CO2hi', 'EFmass_PM', 'EFmass_dry_CO', 'EFmass_dry_COhi', 'EFmass_dry_CO2',
                   'EFmass_dry_CO2hi', 'EFmass_dry_PM', 'EFenergy_CO', 'EFenergy_COhi', 'EFenergy_CO2', 'EFenergy_CO2hi',
                   'EFenergy_PM']
    for name in names:
        if name not in emweightavg: #only for series needing time weighted data
            if name == 'seconds':
                fullavg[name] = data['seconds'][-1] - data['seconds'][0]
            else:
                #Try creating averages of values, nan value if can't
                try:
                    fullavg[name] = sum(data[name]) / len(data[name]) #time weighted average
                except:
                    fullavg[name] = ''
                ####Currently not handling uncertainties
            unc[name] = ''
            uval[name] = ''
    for name in names:
        if name in emweightavg: #only for series needing emission weighted data
            top = 0
            try:
                for n, val in enumerate(data[name]):
                    top = (val * (data['Cconc'][n]/fullavg['Cconc'])) + top
                fullavg[name] = top / len(data[name])
            except:
                fullavg[name] = ''
            unc[name] = ''
            uval[name] = ''

    if plots == 4: #if stak velocity can be run
        name = 'ERPMstak_heat' #add g/hr ERPM
        snames.append(name)
        sunits[name] = 'g/hr'
        sdata[name] = []
        for val in sdata['ERPMstak']:
            sdata[name].append(val/1000) #mg/hr to g/hr

        [scnames, scunits, scval, scunc, scdata] = io.load_constant_inputs(stakempath)

        #normalize with carbon balanca
        name = 'ERPMstak_Carbonratio'
        coname = 'ERCOstak_Carbonratio'
        co2name = 'ERCO2stak_Carbonratio'
        snames.append(name)
        snames.append(coname)
        snames.append(co2name)
        sunits[name] = 'g/hr'
        sunits[coname] = 'g/hr'
        sunits[co2name] = 'g/hr'
        sdata[name] = []
        sdata[coname] = []
        sdata[co2name] = []
        ratio = scdata['Mass_C'] / emmetric['Mass_C']
        for n, val in enumerate(sdata['ERPMstak_heat']):
            sdata[name].append(val * ratio.n)
            sdata[coname].append(sdata['ERCOstak'][n] * ratio.n)
            sdata[co2name].append(sdata['ERCO2stak'][n] * ratio.n)


        fullavg['StakFlow'] = sum(sdata['StakFlow']) / len(sdata['StakFlow'])
        print(fullavg['StakFlow'])

        name = 'ER_PMCB_volratio'
        #coname = 'ER_COCB_volratio'
        #co2name = 'ER_CO2CB_volratio'
        snames.append(name)
        #snames.append(coname)
        #snames.append(co2name)
        sunits[name] = 'g/hr'
        #sunits[coname] = 'g/hr'
        #sunits[co2name] = 'g/hr'
        sdata[name] = []
        #sdata[coname] = []
        #sdata[co2name] = []
        sdata['volflow_norm'] = []
        #sdata[coname] = []
        #sdata[co2name] = []
        for n, val in enumerate(data['PM_flowrate']):
            ratio = sdata['StakFlow'][n] / fullavg['StakFlow']
            sdata['volflow_norm'].append(volflowPM * ratio)
            #sdata[name].append(val * ratio)

        name = 'Realtime_conc_PM'
        names.append(name)
        units[name] = 'mg/m^3'
        values = []
        for val in data['PM']:
            values.append(val / gravmetric['MSC'].nominal_value)  # mg/m^3 realtime concentration
        metric[name] = values
        data[name] = values

        #name = 'PM_flowrate'  # Emission rate based on flowrate
        #snames.append(name)
        #units[name] = 'g/hr'
        values = []
        covalues = []
        co2values = []
        for n, val in enumerate(metric['Realtime_conc_PM']):
            values.append((val * sdata['volflow_norm'][n]))
            #covalues.append()
        sdata['ER_PMCB_volratio'] = values
        #data[name] = values

        addnames = []
        for sname in snames: #go through stak velocity outputs
            if 'ER' in sname: #we only care about ER right now
                try:
                    fullavg[sname] = sum(sdata[sname]) / len(sdata[sname]) #time weighted average
                except:
                    fullavg[name] = ''
                units[sname] = sunits[sname]
                addnames.append(sname)
                unc[name] = ''
                uval[name] = ''

        for name in addnames:
            names.append(name)
            units[name] = sunits[name]
            data[name] = sdata[name]

        name = 'ER_PM_ERratio'
        snames.append(name)
        sunits[name] = 'g/hr'
        sdata[name] = []
        ratio = emmetric['ER_PM_heat'] / fullavg['ERPMstak_heat']
        for n, val in enumerate(sdata['ERPMstak_heat']):
            sdata[name].append(ratio.n * val)

        name = 'ER_CO_ERratio'
        snames.append(name)
        sunits[name] = 'g/hr'
        sdata[name] = []
        CO_heat = emmetric['ER_CO'] * 60
        ratio = CO_heat / fullavg['ERCOstak']
        for n, val in enumerate(sdata['ERCOstak']):
            sdata[name].append(ratio.n * val)

        name = 'ER_CO2_ERratio'
        snames.append(name)
        sunits[name] = 'g/hr'
        sdata[name] = []
        CO_heat = emmetric['ER_CO2'] * 60
        ratio = CO_heat / fullavg['ERCO2stak']
        for n, val in enumerate(sdata['ERCO2stak']):
            sdata[name].append(ratio.n * val)

        for sname in snames: #go through stak velocity outputs
            if 'ER' in sname: #we only care about ER right now
                try:
                    fullavg[sname] = sum(sdata[sname]) / len(sdata[sname]) #time weighted average
                except:
                    fullavg[name] = ''
                units[sname] = sunits[sname]
                addnames.append(sname)
                unc[name] = ''
                uval[name] = ''

        for name in addnames:
            names.append(name)
            units[name] = sunits[name]
            data[name] = sdata[name]

    #create file of full real-time averages
    io.write_constant_outputs(fullaverageoutputpath, names, units, fullavg, unc, uval)

    line = 'created: ' + fullaverageoutputpath #add to log
    print(line)
    logs.append(line)

    #################################################################
    # Defining averaging period for analysis

    # Check if average period times file exists
    if os.path.isfile(periodpath):
        line = 'Average Period time file already exists: ' + periodpath
        print(line)
        logs.append(line)
    else:  # If it doesn't exist, create it
        # Add start and end times from energy inputs as temp vals
        titlenames = []
        if 'start_time_test' in enames:
            starttime = eval['start_time_test']
            titlenames.append('start_time_test')
        if 'end_time_test' in enames:
            endtime = eval['end_time_test']
            titlenames.append('end_time_test')

        # GUI box to edit input times
        zeroline = 'Enter start and end times for averaging period\n'
        firstline = 'Time format =' + eunits['start_time_test'] + '\n\n'
        secondline = 'Click OK to confirm entered values\n'
        thirdline = 'Click Cancel to exit\n'
        msg = zeroline + firstline + secondline + thirdline
        title = "Gitrdone"
        fieldnames = titlenames
        currentvals = []
        for name in titlenames:
            currentvals.append(eval[name])
        newvals = easygui.multenterbox(msg, title, fieldnames, currentvals) #save new vals from user input
        if newvals:
            if newvals != currentvals: #reassign user input as new values
                currentvals = newvals
                for n, name in enumerate(titlenames):
                    eval[name] = currentvals[n]
            else:
                line = 'Undefined variables'
                print(line)
        #Create new file with start and end times
        io.write_constant_outputs(periodpath, titlenames, eunits, eval, eunc, emetric)
        line = 'Created averaging times input file: ' + periodpath
        print(line)
        logs.append(line)

    ################################################################
    # Read in averaging period start and end times
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

    line = 'loaded: ' + periodpath
    print(line)
    logs.append(line)

    ##################################################################
    # Convert datetime str to readable value time objects
    [validnames, timeobject] = bkg.makeTimeObjects(titlenames, timestring, date)

    # Find 'phase' averging period
    phases = bkg.definePhases(validnames)
    # find indicieds in the data for start and end
    indices = bkg.findIndices(validnames, timeobject, datenums)

    # Define averaging data series
    [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

    #add names and units
    avgnames = []
    avgunits ={}
    for name in names:
        testname = name + '_test'
        avgnames.append(testname)
        avgunits[testname] = units[name]

    #Write cut values into a file
    io.write_timeseries(averageoutputpath, avgnames, avgunits, avgdata)

    line = 'created: ' + averageoutputpath
    print(line)
    logs.append(line)

    #################### #############################################
    #Create period averages
    #total_seconds = avgdata['seconds_test'][-1] - avgdata['seconds_test'][0]
    calcavg = {}
    unc={}
    uval={}
    for name in avgnames:
        if name not in emweightavg:
            if name == 'seconds_test':
                calcavg[name] = avgdata['seconds_test'][-1] - avgdata['seconds_test'][0]
            else:
                #Try creating averages of values, nan value if can't
                try:
                    calcavg[name] = sum(avgdata[name]) / len(avgdata[name]) #time weighted avg
                except:
                    calcavg[name] = ''
                ####Currently not handling uncertainties
            unc[name] = ''
            uval[name] = ''
    for name in avgnames:
        if name in emweightavg:
            top = 0
            try:
                for n, val in enumerate(avgdata[name]):
                    top = (val * (avgdata['Cconc'][n] / calcavg['Cconc'])) + top
                calcavg[name] = top / len(avgdata[name])
            except:
                calcavg[name] = ''
            unc[name] = ''
            uval[name] = ''

    #add start and end time for reference
    for n, name in enumerate(titlenames):
        avgnames.insert(n, name)
        calcavg[name] = eval[name]
        avgunits[name] = 'yyyymmdd hh:mm:ss'

    #Print averages
    line = 'Average Carbon Balance ER PM ISO (Full dataset) ' + str(emmetric['ER_PM_heat'].nominal_value)
    print(line)
    line = ('Average Constant Flowrate ER PM (Averaging Period) ') + str(calcavg['PM_flowrate_test'])
    print(line)
    try:
        line = 'Average Stak Flowrate ER PM (Averaging Period) ' + str(calcavg['ERPMstak_heat_test'])
        print(line)
        line = 'Normalized Average Stak Flowrate ER PM (Averaging Period) ' +str(calcavg['ERPMstak_Carbonratio_test'])
        print(line)
        line = 'Normalize Average Constant Flowrate ER PM (Averaging Period) ' +str(calcavg['ER_PMCB_volratio_test'])
        print(line)
        line = 'Normalized by ER Stak Flowrate ER PM (Averaging Period) ' +str(calcavg['ER_PM_ERratio_test'])
        print(line)
    except:
        pass

    #create file of averages for averaging period
    io.write_constant_outputs(averagecalcoutputpath, avgnames, avgunits, calcavg, unc, uval)

    line = 'created: ' + averagecalcoutputpath
    print(line)
    logs.append(line)

###############################################################

    plt.ion() #Turn on interactive plot mode
    ylimit = (-5, 100)
    scalar = 1/10
    if plots == 1:
        fig, axs = plt.subplots(1, plots) #plot 1-4 plots depnding on number calculated ERs
    else:
        fig, axs = plt.subplots(2, 3)
    plt.setp(axs, ylim=ylimit)

    y = []
    #Remove 0s
    for val in metric['PM_flowrate']:
        try:
            if float(val) < 0.0:
                y.append(0.0)
            else:
                y.append(val)
        except:
            y.append(val)

    yavg = []
    for val in avgdata['PM_flowrate_test']:
        try:
            if float(val) < 0.0:
                yavg.append(0.0)
            else:
                yavg.append(val)
        except:
            yavg.append(val)

    '''
    #Plot full test and averaging period in same subplot
    axs[0].plot(data['datenumbers'], y, color = 'blue', label='Full CF ER')
    axs[0].plot(avgdatenums['test'], yavg, color = 'red', label='Cut CF ER')
    axs[0].set_title('Realtime Constant Flowrate ER PM')
    axs[0].set(ylabel='Emission Rate(g/hr)', xlabel='Time(s)')
    '''
    try:
        scaleTC= [x * scalar for x in data['TC']]
        avgscaleTC = [x * scalar for x in avgdata['TC_test']]
        fullname = 'Full TC (' + str(scalar) + ')'
        cutname = 'Cut TC (' + str(scalar) + ')'
        #axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
        #axs[0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
    except:
        scaleTCnoz = [x * scalar for x in data['TCnoz']]
        avgscaleTCnoz = [x * scalar for x in avgdata['TCnoz_test']]
        fullname = 'Full TCnoz (' + str(scalar) + ')'
        cutname = 'Cut TCnoz (' + str(scalar) + ')'
        #axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
        #axs[0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
    #axs[0].legend()


    if plots == 1:
        y = []
        for val in metric['PM_flowrate']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['PM_flowrate_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        #plot full data and averaging period in same subplot
        axs[0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
        axs[0].plot(avgdatenums['test'], yavg, color = 'red', label='Cut constant flowrate ER')
        axs[0].set_title('Realtime Flowrate ER PM')
        axs[0].set(ylabel='Emission Rate(g/hr)')
        try:
            axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[0].legend()

    #if there's a third ER method, plot it too
    if plots == 4:
        y = []
        for val in metric['PM_flowrate']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['PM_flowrate_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        # plot full data and averaging period in same subplot
        axs[0, 0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
        axs[0, 0].plot(avgdatenums['test'], yavg, color='red', label='Cut constant flowrate ER')
        axs[0, 0].set_title('Realtime Flowrate ER PM')
        axs[0, 0].set(ylabel='Emission Rate(g/hr)')
        try:
            axs[0, 0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[0, 0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[0, 0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[0, 0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[0, 0].legend()

        y = []
        for val in data['ERPMstak_heat']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['ERPMstak_heat_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        axs[1, 0].plot(data['datenumbers'], y, color='blue', label='Full stakvel ER')
        axs[1, 0].plot(avgdatenums['test'], yavg, color='red', label='Cut stakvel ER')
        axs[1, 0].set(ylabel='Emission Rate(g/hr)', title='Stak Velocity Emission Rate')
        try:
            axs[1, 0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[1, 0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[1, 0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[1, 0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[1, 0].legend()

        y = []
        for val in data['ERPMstak_Carbonratio']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['ERPMstak_Carbonratio_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        axs[1, 1].plot(data['datenumbers'], y, color='blue', label='Full normalized stakvel ER')
        axs[1, 1].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized stakvel ER')
        axs[1, 1].set(ylabel='Emission Rate(g/hr)', title='Normalized Stak Velocity Emission Rate')
        try:
            axs[1, 1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[1, 1].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[1, 1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[1, 1].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[1, 1].legend()

        y = []
        for val in data['ER_PMCB_volratio']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['ER_PMCB_volratio_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        axs[0, 1].plot(data['datenumbers'], y, color='blue', label='Full normalized CF ER')
        axs[0, 1].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized CF ER')
        axs[0, 1].set(ylabel='Emission Rate(g/hr)', title='Normalized by volratio Constant Flowrate Emission Rate')
        try:
            axs[0, 1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[0, 1].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[0, 1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[0, 1].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[0, 1].legend()

        y = []
        for val in data['ER_PM_ERratio']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['ER_PM_ERratio_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        axs[0, 2].plot(data['datenumbers'], y, color='blue', label='Full normalized CF ER')
        axs[0, 2].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized CF ER')
        axs[0, 2].set(ylabel='Emission Rate(g/hr)', title='Normalized by ER ratio Constant Flowrate Emission Rate')
        try:
            axs[0, 2].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            axs[0, 2].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            axs[0, 2].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[0, 2].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        axs[0, 2].legend()

    #Format x axis to readable times
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S') #pull and format time data
    for i, ax in enumerate(fig.axes):
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)

    ##########################################################
    #REplot for new inputs
    running = 'fun'
    while(running == 'fun'):
            #GUI box to edit input times

        zeroline = 'Edit averaging period\n'
        firstline = 'Time format = ' + timeunits['start_time_test'] + '\n\n'
        secondline = 'Click OK to update plot\n'
        thirdline = 'Click Cancel to exit\n'
        msg = zeroline + firstline + secondline + thirdline
        title = "Gitrdone"

        fieldnames = titlenames
        currentvals = []

        for name in titlenames:
            currentvals.append(timestring[name])

        newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)
        if newvals:
            if newvals != currentvals: #If new values are entered
                currentvals = newvals
                for n, name in enumerate(fieldnames):
                    timestring[name] = currentvals[n]
                    eval[name] = currentvals[n] #update to new values

                #record new values in averagingperiod for next time
                io.write_constant_outputs(periodpath, titlenames, eunits, eval, eunc, emetric)
                line = 'Updated averaging period file:' + periodpath
                print(line)
                logs.append(line)
        else:
            running = 'not fun'
            savefig = os.path.join(savefig + '_averagingperiod.png')
            plt.savefig(savefig, bbox_inches='tight')
            plt.ioff() #turn off interactive plot
            plt.close() #close plot

        ##################################################################
        # Convert datetime str to readable value time objects
        [validnames, timeobject] = bkg.makeTimeObjects(titlenames, timestring, date)

        # Find 'phase' averging period
        phases = bkg.definePhases(validnames)
        # find indicieds in the data for start and end
        indices = bkg.findIndices(validnames, timeobject, datenums)

        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

        for name in titlenames:
            avgnames.remove(name) #temoprarliy remove start and end names

        # Write cut values into a file
        io.write_timeseries(averageoutputpath, avgnames, avgunits, avgdata)

        line = 'updated averaging output file: ' + averageoutputpath
        print(line)
        logs.append(line)

        #################################################################
        # Create period averages
        calcavg = {}
        unc = {}
        uval = {}
        for name in avgnames:
            if name == 'seconds_test':
                calcavg[name] = avgdata['seconds_test'][-1] - avgdata['seconds_test'][0]
            else:
                # Try creating averages of values, nan value if can't
                try:
                    calcavg[name] = sum(avgdata[name]) / len(avgdata[name])
                except:
                    calcavg[name] = 'nan'
            ####Currently not handling uncertainties
            unc[name] = ''
            uval[name] = ''
        for n, name in enumerate(titlenames): #Add start and end time
            avgnames.insert(n, name)
            calcavg[name] = eval[name]
            avgunits[name] = 'yyyymmdd hh:mm:ss'

        #print averages over new values
        line = 'Average Carbon Balance ER PM ISO (Full dataset) ' + str(emmetric['ER_PM_heat'].nominal_value)
        print(line)
        line = 'Average Carbon Balance ER PM Realtime (Averaging period) ' + str(calcavg['ER_PM_heat_test'])
        print(line)
        try:
            line = 'Average Stak Flowrate ER PM (Averaging Period) ' + str(calcavg['ERPMstak_heat_test'])
            print(line)
            line = 'Normalized Average Stak Flowrate ER PM (Averaging Period) ' + str(
                calcavg['ERPMstak_Carbonratio_test'])
            print(line)
            line = 'Normalize Average Carbon Balance ER PM (Averaging Period) ' + str(calcavg['ER_PMCB_volratio_test'])
            print(line)
            line = 'Normalized by ER Stak Flowrate ER PM (Averaging Period) ' + str(calcavg['ER_PM_ERratio_test'])
            print(line)
        except:
            pass

        #Record updated averaged
        io.write_constant_outputs(averagecalcoutputpath, avgnames, avgunits, calcavg, unc, uval)
        line = 'updated average calculations file: ' + averagecalcoutputpath
        print(line)
        logs.append(line)

        # update the data series column named phase
        name = 'phase'
        data[name] = ['none'] * len(data['time'])  # clear all values to none
        for phase in phases:
            for n, val in enumerate(data['time']):
                if n >= indices['start_time_' + phase] and n <= indices['end_time_' + phase]:
                    if data[name][n] == 'none':
                        data[name][n] = phase
                    else:
                        data[name][n] = data[name][n] + ',' + phase

        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)



#############################################################
        #Update plot
        #plt.clf()
        '''
        y = []
        for val in metric['ER_PM_heat']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        yavg = []
        for val in avgdata['ER_PM_heat_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)

        axs[0].plot(data['datenumbers'], y, color = 'blue', label='Full CB ER')
        axs[0].plot(avgdatenums['test'], yavg, color = 'red', label='Cut CB ER')
        axs[0].set_title('Realtime Carbon Balance ER PM')
        axs[0].set(ylabel='Emission Rate(g/hr)', xlabel='Time(s)')
        '''
        try:
            scaleTC = [x * scalar for x in data['TC']]
            avgscaleTC = [x * scalar for x in avgdata['TC_test']]
            #axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            #axs[0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
        except:
            scaleTCnoz = [x * scalar for x in data['TCnoz']]
            avgscaleTCnoz = [x * scalar for x in avgdata['TCnoz_test']]
            #axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            #axs[0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)
        if plots == 0:
            y = []
            for val in metric['PM_flowrate']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['PM_flowrate_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
            axs[0].plot(avgdatenums['test'], yavg, color = 'red', label='Cut constant flowrate ER')
            axs[0].set_title('Realtime Flowrate ER PM')
            axs[0].set(ylabel='Emission Rate(g/hr)')
            try:
                axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

        if plots == 4:
            y = []
            for val in metric['PM_flowrate']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['PM_flowrate_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[0, 0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
            axs[0, 0].plot(avgdatenums['test'], yavg, color='red', label='Cut constant flowrate ER')
            axs[0, 0].set_title('Realtime Flowrate ER PM')
            axs[0, 0].set(ylabel='Emission Rate(g/hr)')
            try:
                axs[0, 0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[0, 0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[0, 0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[0, 0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

            y = []
            for val in data['ERPMstak']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['ERPMstak_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[1, 0].plot(data['datenumbers'], y, color='blue', label='Full stakvel ER')
            axs[1, 0].plot(avgdatenums['test'], yavg, color='red', label='Cut stakvel ER')
            axs[1, 0].set(ylabel='Emission Rate(g/hr)', title='Stak Velocity Emission Rate')
            try:
                axs[1, 0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[1, 0].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[1, 0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[1, 0].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

            y = []
            for val in data['ERPMstak_Carbonratio']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['ERPMstak_Carbonratio_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[1, 1].plot(data['datenumbers'], y, color='blue', label='Full normalized stakvel ER')
            axs[1, 1].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized stakvel ER')
            axs[1, 1].set(ylabel='Emission Rate(g/hr)', title='Normalized Stak Velocity Emission Rate')
            try:
                axs[1, 1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[1, 1].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[1, 1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[1, 1].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

            y = []
            for val in data['ER_PMCB_volratio']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['ER_PMCB_volratio_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[0, 1].plot(data['datenumbers'], y, color='blue', label='Full normalized CF ER')
            axs[0, 1].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized CF ER')
            axs[0, 1].set(ylabel='Emission Rate(g/hr)', title='Normalized by volratio Constant Flowrate Emission Rate')
            try:
                axs[0, 1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[0, 1].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[0, 1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[0, 1].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

            y = []
            for val in data['ER_PM_ERratio']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)

            yavg = []
            for val in avgdata['ER_PM_ERratio_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)

            axs[0, 2].plot(data['datenumbers'], y, color='blue', label='Full normalized CF ER')
            axs[0, 2].plot(avgdatenums['test'], yavg, color='red', label='Cut normalized CF ER')
            axs[0, 2].set(ylabel='Emission Rate(g/hr)', title='Normalized by ER ratio Constant Flowrate Emission Rate')
            try:
                axs[0, 2].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
                axs[0, 2].plot(avgdatenums['test'], avgscaleTC, color='orange', label=cutname)
            except:
                axs[0, 2].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
                axs[0, 2].plot(avgdatenums['test'], avgscaleTCnoz, color='orange', label=cutname)

        #plt.tight_layout(pad=0.4, w_pad=0.7, h_pad=1.0)

    #fig.canvas.draw()

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    
    #Record full test outputs
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)

def definePhaseData(Names, Data, Phases, Indices):
    Phasedatenums = {}
    Phasedata = {}
    Phasemean = {}
    for Phase in Phases:  # for each test phase
        # make data series of date numbers
        key = 'start_time_' + Phase
        startindex = Indices[key]
        key = 'end_time_' + Phase
        endindex = Indices[key]
        Phasedatenums[Phase] = Data['datenumbers'][startindex:endindex + 1]
        # make phase data series for each data channel
        for Name in Names:
            Phasename = Name + '_' + Phase
            Phasedata[Phasename] = Data[Name][startindex:endindex + 1]

            # calculate average value
            if Name != 'time' and Name != 'phase':
                if all(np.isnan(Phasedata[Phasename])):
                    Phasemean[Phasename] = np.nan
                else:
                    ave = np.nanmean(Phasedata[Phasename])
                    if Name == 'datenumbers':
                        Phasemean[Phasename] = ave


        # time channel: use the mid-point time string
        Phasename = 'datenumbers_' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean

#######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_Realtime(inputpath, energypath, gravinputpath, empath, periodpath, outputpath, averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, savefig, logpath)