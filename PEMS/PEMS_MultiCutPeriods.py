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
# determines which Unit Tests phases and which flow trains by reading which variable names are present in the grav input file
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

inputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_TimeSeries_test.csv"
energypath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_EnergyOutputs.csv"
gravinputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_GravOutputs.csv"
empath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_EmissionOutputs.csv"
stakpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_TimeSeriesStackFlow.csv"
stakempath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_StackFlowEmissionOutputs.csv"
fuelmetricpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_FuelMetrics.csv"
fuelpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_FuelDataCut.csv"
cutpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_CutTimes.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_RealtimeOutputs.csv"
averageoutputpath ="C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_AveragingPeriodOutputs.csv"
averagecalcoutputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_AveragingPeriodCalcs.csv"
fullaverageoutputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_RealtimeAverages.csv"
savefig = "C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_averagingperiod.png"
logpath ="C:\\Users\\Jaden\\Documents\\DOE-stak\\Unit Tests\\3.21.23\\3.21.23_log.txt"

def PEMS_MultiCutPeriods(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, fuelmetricpath, fuelpath, cutpath, outputpath,
                         averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, savefig, logpath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]
    #################################################

    # flow = 'F1Flow' #Able to change flow chanel for stakvel calcs

    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    line = 'loaded: ' + inputpath  # add to log
    print(line)
    logs.append(line)

    emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'PM']  # emission species that will get metric calculations

    for em in emissions:  # Test if emissions is in data dictionary
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

    metric = {}  # Dictionary for storing calculated values

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
            val = 0.0
        conc.append(val / float(gravval['MSC']) / 1000)
    data['conc'] = conc
    ################################################
    # calculate metrics

    # mass concentration

    # SOME CO AND CO2 VALUES ARE NEGATIVE AND START AND END. CHANGED TO 0
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
                # if val < 0:
                # val = 0.00001
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
            values.append(
                val * MW['C'] / MW['CO'] + metric['CO2hiconc'][n] * MW['C'] / MW['CO2'])  # ISO19869 Formula 60
        metric[name] = values
        data[name] = values

    # MCE
    values = []
    name = 'MCE'
    names.append(name)
    units[name] = 'mol/mol'
    for n, val in enumerate(data['CO2']):
        try:
            values.append(val / (data['CO'][n] + val))  # ISO 19869 Formula 61
        except:
            values.append(val / 0.0000001)  # for the off chance that it would have been zero
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

    # carbon emission ratio
    for em in emissions:
        name = 'CER_' + em
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
        for n, val in enumerate(metric[em + 'conc']):
            try:
                values.append(val / metric[cconc][n])  # ISO 19869 Formula 63
            except:
                values.append(val / 0.0000001)  # ISO 19869 Formula 63
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

    # Emission factor, dry fuel mass based, not  an ISO 19869 metric
    for em in emissions:
        name = 'EFmass_dry_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/kg'
        else:
            units[name] = 'g/kg'
        values = []
        for val in metric['CER_' + em]:
            values.append(val * emetric['fuel_Cfrac_db'].nominal_value * 1000)
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
    # Emission rate
    for em in emissions:
        name = 'ER_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/min'
        else:
            units[name] = 'g/min'
        values = []
        for val in metric['EFenergy_' + em]:
            values.append(val * emetric['fuel_energy'].nominal_value / emetric[
                'phase_time_test'].nominal_value)  # ISO 19869 Formula 74-77
        metric[name] = values
        data[name] = values

    name = 'ER_PM_heat'  # PM ISO emission rate g/hr
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['ER_PM']:
        if float(val) < 0.0:
            values.append(0.0)
        else:
            values.append(val * 60 / 1000)
    metric[name] = values
    data[name] = values

    #######################Constant FLOWRATE PM

    # volflowPM = emmetric['ER_PM_heat'].nominal_value / gravmetric['PMconc_tot'].nominal_value  # m^3/hr
    volflowPM = emmetric['ER_PM_heat'].nominal_value / gravmetric['PMconc_tot'].nominal_value / 1000  # m^3/hr
    volflowCO = emmetric['ER_CO'].nominal_value / emmetric['COconc'].n  # m^3/min
    volflowCO2 = emmetric['ER_CO2'].nominal_value / emmetric['CO2conc'].n  # m^3/min
    print('volflowPM=' + str(volflowPM))
    print('volflowCO=' + str(volflowCO))
    print('volflowCO2=' + str(volflowCO2))

    name = 'Realtime_conc_PM'
    names.append(name)
    units[name] = 'mg/m^3'
    values = []
    for val in data['PM']:
        values.append(val / gravmetric['MSC'].nominal_value)  # ug/m^3 realtime concentration
    metric[name] = values
    data[name] = values

    name = 'Realtime_conc_CO'
    names.append(name)
    units[name] = 'g/m^3'
    values = []
    for val in data['CO']:  # ppm
        values.append(val * MW['CO'] * Pstd / Tstd / 1000000 / R)  # g/m^3 realtime concentration

    metric[name] = values
    data[name] = values

    name = 'Realtime_conc_CO2'
    names.append(name)
    units[name] = 'g/m^3'
    values = []
    for val in data['CO2']:
        values.append(val * MW['CO2'] * Pstd / Tstd / 1000000 / R)  # g/m^3 realtime concentration

    metric[name] = values
    data[name] = values

    name = 'PM_flowrate'  # Emission rate based on constant flowrate
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['Realtime_conc_PM']:
        values.append((val * volflowPM))
    metric[name] = values
    data[name] = values

    name = 'CO_flowrate'  # Emission rate based on constant flowrate
    names.append(name)
    units[name] = 'g/min'
    values = []
    for val in metric['Realtime_conc_CO']:
        values.append((val * volflowCO))  # different flow rate because different uncertainty
    metric[name] = values
    data[name] = values

    name = 'CO2_flowrate'  # Emission rate based on constant flowrate
    names.append(name)
    units[name] = 'g/min'
    values = []
    for val in metric['Realtime_conc_CO2']:
        values.append((val * volflowCO2))
    metric[name] = values
    data[name] = values

    #####################################################################
    # Volumetric flow rate/stack flow rate for PM
    # Not working for PC

    # load in stak velocity timeseries data
    try:
        [snames, sunits, sdata] = io.load_timeseries(stakpath)
        plots = 4
    except:
        plots = 1
        # Create full averages
    fullavg = {}
    unc = {}
    uval = {}
    emweightavg = ['MCE', 'MCEhi', 'CER_CO', 'CER_COhi', 'CER_CO2', 'CER_CO2hi', 'CER_PM', 'EFmass_CO', 'EFmass_COhi',
                   'EFmass_CO2', 'EFmass_CO2hi', 'EFmass_PM', 'EFmass_dry_CO', 'EFmass_dry_COhi', 'EFmass_dry_CO2',
                   'EFmass_dry_CO2hi', 'EFmass_dry_PM', 'EFenergy_CO', 'EFenergy_COhi', 'EFenergy_CO2',
                   'EFenergy_CO2hi',
                   'EFenergy_PM']
    for name in names:
        if name not in emweightavg:  # only for series needing time weighted data
            if name == 'seconds':
                fullavg[name] = data['seconds'][-1] - data['seconds'][0]
            else:
                # Try creating averages of values, nan value if can't
                try:
                    fullavg[name] = sum(data[name]) / len(data[name])  # time weighted average
                except:
                    fullavg[name] = ''
                ####Currently not handling uncertainties
            unc[name] = ''
            uval[name] = ''
    for name in names:
        if name in emweightavg:  # only for series needing emission weighted data
            top = 0
            try:
                for n, val in enumerate(data[name]):
                    top = (val * (data['Cconc'][n] / fullavg['Cconc'])) + top
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
        coname = 'ER_COCB_volratio'
        co2name = 'ER_CO2CB_volratio'
        snames.append(name)
        snames.append(coname)
        snames.append(co2name)
        sunits[name] = 'g/hr'
        sunits[coname] = 'g/min'
        sunits[co2name] = 'g/min'
        sdata[name] = []
        sdata[coname] = []
        sdata[co2name] = []
        sdata['volflow_norm_PM'] = []
        sdata['volflow_norm_CO'] = []
        sdata['volflow_norm_CO2'] = []
        #sdata[coname] = []
        #sdata[co2name] = []
        for n, val in enumerate(data['PM_flowrate']):
            ratio = sdata['StakFlow'][n] / fullavg['StakFlow']
            sdata['volflow_norm_PM'].append(volflowPM * ratio)
            sdata['volflow_norm_CO'].append(volflowCO/60 * ratio)
            sdata['volflow_norm_CO2'].append(volflowCO2 / 60 * ratio)
            #sdata[name].append(val * ratio)


        #name = 'PM_flowrate'  # Emission rate based on flowrate
        #snames.append(name)
        #units[name] = 'g/hr'
        values = []
        covalues = []
        co2values = []
        for n, val in enumerate(metric['Realtime_conc_PM']):
            values.append((val * sdata['volflow_norm_PM'][n]))
            #covalues.append()
        sdata['ER_PMCB_volratio'] = values
        #data[name] = values

        for n, val in enumerate(metric['Realtime_conc_CO']):
            covalues.append((val * sdata['volflow_norm_CO'][n] * 60))
        sdata['ER_COCB_volratio'] = covalues
        #data[name] = values

        for n, val in enumerate(metric['Realtime_conc_CO2']):
            co2values.append((val * sdata['volflow_norm_CO2'][n] * 60))
        sdata['ER_CO2CB_volratio'] = co2values
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
        CO_heat = emmetric['ER_CO']
        ratio = CO_heat / fullavg['ERCOstak']
        for n, val in enumerate(sdata['ERCOstak']):
            sdata[name].append(ratio.n * val)

        name = 'ER_CO2_ERratio'
        snames.append(name)
        sunits[name] = 'g/hr'
        sdata[name] = []
        CO_heat = emmetric['ER_CO2']
        ratio = CO_heat / fullavg['ERCO2stak']
        for n, val in enumerate(sdata['ERCO2stak']):
            sdata[name].append(ratio.n * val)

        addnames = []
        for sname in snames: #go through stak velocity outputs
            if 'ER' in sname: #we only care about ER right now
                if sname not in names:
                    try:
                        fullavg[sname] = sum(sdata[sname]) / len(sdata[sname]) #time weighted average
                    except:
                        fullavg[name] = ''
                    units[sname] = sunits[sname]
                    addnames.append(sname)
                    unc[name] = ''
                    uval[name] = ''
            elif sname == 'Firepower':
                try:
                    fullavg[sname] = sum(sdata[sname]) / len(sdata[sname]) #time weighted average
                except:
                    fullavg[name] = ''
                units[sname] = sunits[sname]
                addnames.append(sname)
                unc[name] = ''
                uval[name] = ''
            elif sname == 'UsefulPower':
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
    ####################################################

    if os.path.isfile(cutpath): #If cut times file already exists
        line = 'Cut times input file already exists: ' + cutpath
        print(line)
        logs.append(line)
    elif os.path.isfile(fuelmetricpath): #if fuel cut times are avalible, make file based on those
        fnames = []  # list of variable names
        fval = {}  # dictionary keys are variable names, values are variable values

        # load input file
        stuff = []
        with open(fuelmetricpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        namesrow = stuff[0]
        for n, name in enumerate(namesrow):
            fnames.append(name)
            fval[name] =[x[n] for x in stuff[1:]]
            for m, value in enumerate(fval[name]):
                try:
                    if name == 'time':
                        fval[name][m] = fval[name][m].replace("-", "") #remove - from date
                    else:
                        fval[name][m] = float(fval[name][m])
                except:
                    pass

        with open(cutpath, 'w', newline='') as csvfile:
            fieldnames = ['Label', 'Units', 'Time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for i in range(len(fval['time'])-1):
                start_time = f"start time {i+1}"
                end_time = f"end time {i + 1}"
                writer.writerow({'Label': start_time, 'Units': 'yyyymmdd HH:MM:SS', 'Time': fval['time'][i]})
                writer.writerow({'Label': end_time, 'Units': 'yyyymmdd HH:MM:SS', 'Time': fval['time'][i+1]})

            # Write the last start and end time
            writer.writerow({'Label': f"start time {len(fval['time'])}",'Units': 'yyyymmdd HH:MM:SS', 'Time': fval['time'][-1]}) #last removal time
            writer.writerow({'Label': f"end time {len(fval['time'])}", 'Units': 'yyyymmdd HH:MM:SS', 'Time': eval['end_time_test']}) #end of Unit Tests from datasheet

        line = 'Created cut times based on fuel loading times: ' + cutpath
        print(line)
        logs.append(line)

    else: #if there's no existing file and no loading times, ask user to input phase times
        data = []
        num_phases = easygui.integerbox("Enter how many phases you would like evaluated:")
        if num_phases is not None:
            phase_times = []
            #for i in range(num_phases):
                #start_time = easygui.enterbox(f"Enter start time for Phase {i + 1} (yyyymmdd HH:MM:SS):",
                                              #f"Phase {i + 1}")
                #end_time = easygui.enterbox(f"Enter end time for Phase {i + 1} (yyyymmdd HH:MM:SS):", f"Phase {i + 1}")
                #phase_times.append((start_time, end_time))
            zeroline = "Enter start and end times for each phase period\n"
            firstline = "Time format = yyyymmdd HH:MM:SS\n"
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit\n'
            msg = zeroline + firstline + secondline + thirdline
            title = "Gitrdone"
            fieldnames = []
            currentvals = []
            phase = 1
            while phase <= num_phases:
                fieldnames.append('start time ' + str(phase))
                currentvals.append('')
                fieldnames.append('end time ' + str(phase))
                currentvals.append('')
                phase += 1
            phase_times = easygui.multenterbox(msg, title, fieldnames, currentvals)
            if phase_times:
                if phase_times != currentvals:
                    currentvals = phase_times

            with open(cutpath, 'w', newline='') as csvfile:
                fieldnames = ['Label', 'Units', 'Time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i, name in enumerate(fieldnames):
                    writer.writerow({'Label': name, "Units": 'yyyymmdd HH:MM:SS', "Time": currentvals[i]})

            line = "Created cut times based on inputs: " + cutpath
            print(line)
            logs.append(line)
        else:
            line = "Not a number, no cut times created"
            print(line)
            logs.append(line)

    #########################################
    #read in fuel data for graphing later.
    if os.path.isfile(fuelpath):
        [fuelnames, fuelunits, fuelvals] = io.load_timeseries(fuelpath)

    name = 'dateobjects'
    fuelunits[name] = 'date'
    #names.append(name) #don't add to print list because time object cant print to csv
    fuelvals[name] = []
    try:
        for n,val in enumerate(fuelvals['time']):
            dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S') #Convert time to readble datetime object
            fuelvals[name].append(dateobject)
    except:
        try:
            for n,val in enumerate(fuelvals['time']):
                dateobject=dt.strptime(val, '%Y-%m-%d  %H:%M:%S') #Convert time to readble datetime object
                fuelvals[name].append(dateobject)
        except:
            for n, val in enumerate(fuelvals['time']):
                dateobject = dt.strptime(val, '%Y/%m/%d  %H:%M:%S')  # Convert time to readble datetime object
                fuelvals[name].append(dateobject)

    name='datenumbers'
    fuelunits[name]='date'
    #names.append(name)
    datenums=matplotlib.dates.date2num(fuelvals['dateobjects'])
    datenums=list(datenums)     #convert ndarray to a list in order to use index function
    fuelvals['datenumbers']=datenums

    ##########################################################################
    #get the date from the time series data
    date=data['time'][0][:8]
    print(len(data['time']))

    # time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name] = 'date'
    # names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    for n, val in enumerate(data['time']):
        try:
            dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
            data[name].append(dateobject)
        except:
            print(n)

    name = 'datenumbers'
    units[name] = 'date'
    names.append(name)
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)  # convert ndarray to a list in order to use index function
    data['datenumbers'] = datenums

    # add phase column to time series data
    name = 'phase'
    names.append(name)
    units[name] = 'text'
    data[name] = ['none'] * len(data['time'])

    # read in input file of phase start and end times
    [timenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(cutpath)

    #read in measurement uncertainty file
    #[ucnames,ucunits,ucinputs] = io.load_timeseries(ucpath)

    [validnames, timeobject] = makeTimeObjects(timenames, timestring, date)  # convert time strings to time objects
    print(validnames)

    phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase

    phaseindices = findIndices(validnames,timeobject,datenums)  #find the indices in the time data series for the start and stop times of each phase

    [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,phases,phaseindices)#,ucinputs)   #define phase data series for each channel


    #plot data to check periods
    plt.ion() #turn on interactive plot mode

    lw=float(5)    #define the linewidth for the data series
    plw=float(2)    #define the linewidth for the bkg and sample period marker
    msize=30        #marker size for start and end pints of each period

    #create consistent phase colors based on rgb values
    start_r = 1
    start_g = 0
    start_b = 0
    r = []
    g = []
    b = []
    #count = 'down'
    colors = []

    #count_r = 'down'
    #count_g = 'down'
    #count_b = 'up'

    for phase in phases:
        #count = 'down'
        if start_r == 1:
            count_r = 'down'
            start_r = start_r - .1
            if start_r < 0:
                r.append(0)
            else:
                r.append(start_r)
        elif start_r > 0 and count_r == 'down':
            start_r = start_r - .1
            if start_r < 0:
                r.append(0)
            else:
                r.append(start_r)
        elif start_r == 0:
            count_r = 'up'
            start_r = start_r + .1
            if start_r > 1:
                r.append(1)
            else:
                r.append(start_r)
        elif start_r < 1 and count_r == 'up':
            start_r = start_r + .1
            if start_r > 1:
                r.append(1)
            else:
                r.append(start_r)
        else:
            start_r = 0.5
            count_r = 'up'
            r.append(abs(start_r))

        #count = 'down'
        if start_g == 1:
            count_g = 'down'
            start_g = start_g - .2
            if start_g < 0:
                g.append(0)
            else:
                g.append(start_g)
        elif start_g > 0 and count_g == 'down':
            start_g = start_g - .2
            if start_g < 0:
                g.append(0)
            else:
                g.append(start_g)
        elif start_g == 0:
            count_g = 'up'
            start_g = start_g + .2
            if start_g > 1:
                g.append(1)
            else:
                g.append(start_g)
        elif start_g < 1 and count_g == 'up':
            start_g = start_g + .2
            if start_g > 1:
                g.append(1)
            else:
                g.append(start_g)
        else:
            start_g = 0.5
            count_g = 'up'
            g.append(abs(start_g))

        #count = 'up'
        if start_b == 1:
            count_b = 'down'
            start_b = start_b - .25
            if start_b < 0:
                b.append(0)
            else:
                b.append(start_b)
        elif start_b > 0 and count_b == 'down':
            start_b = start_b - .25
            if start_b < 0:
                b.append(0)
            else:
                b.append(start_b)
        elif start_b == 0:
            count_b = 'up'
            start_b = start_b + .25
            if start_b > 1:
                b.append(1)
            else:
                b.append(start_b)
        elif start_b < 1 and count_b == 'up':
            start_b = start_b + .25
            if start_b > 1:
                b.append(1)
            else:
                b.append(start_b)
        else:
            start_b = 0.5
            count_b = 'up'
            b.append(abs(start_b))

    for n in range(len(phases)):
        c = []
        c.append(r[n])
        c.append(g[n])
        c.append(b[n])
        colors.append(tuple(c))

    if plots == 1:
        fig, axs = plt.subplots(1, plots)
    else:
        fig, axs = plt.subplots(2, 1)

    scalar = 1/10
    try:
        scaleTC= [x * scalar for x in data['TC']]
        fullname = 'TC (' + str(scalar) + ')'
    except:
        scaleTCnoz = [x * scalar for x in data['TCnoz']]
        fullname = 'TCnoz(C) (X' + str(scalar) + ')'

    shift = 30
    scalar = 10
    try:
        scalefuel = [(x *scalar) + shift for x in fuelvals['firewood']]
    except:
        pass

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

        # plot full data and averaging period in same subplot
        axs[0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
        axs[0].set_title('Realtime Flowrate ER PM')
        axs[0].set(ylabel='Emission Rate(g/hr)')
        try:
            axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
        except:
            axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
        axs[0].legend()
        for n, phase in enumerate(phases):
            axs[0].plot(phasedatenums[phase], phasedata['PM_flowrate_test'], color=colors[n], linewidth=plw,label=phase)

    else:
        y = []
        for val in metric['PM_flowrate']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)
        # plot full data and averaging period in same subplot
        axs[0].plot(data['datenumbers'], data['PM_flowrate'], color='blue', label='Full constant flowrate ER')
        axs[0].set_title('Realtime Constant Flowrate ER PM')
        axs[0].set(ylabel='Emission Rate(g/hr)')
        try:
            axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
        except:
            axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
        try:
            axs[0].plot(fuelvals['datenumbers'], scalefuel, color='brown', label='Fuel(kg) (X' + str(scalar) + ')')
        except:
            pass

        for n, phase in enumerate(phases):
            axs[0].plot(phasedatenums[phase], phasedata['PM_flowrate ' + phase], color=colors[n], linewidth=plw,label=phase)
            axs[0].plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata['PM_flowrate ' + phase][0], phasedata['ERPMstak_heat ' + phase][-1]], color=colors[n],linestyle='none', marker='|', markersize=msize)

        axs[0].legend()

        # plot full data and averaging period in same subplot
        axs[1].plot(data['datenumbers'], data['ERPMstak_heat'], color='blue', label='Full stak flowrate ER')
        axs[1].set_title('Realtime Stack Flowrate ER PM')
        axs[1].set(ylabel='Emission Rate(g/hr)')
        try:
            axs[1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
        except:
            axs[1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
        try:
            axs[1].plot(fuelvals['datenumbers'], scalefuel, color='brown', label='Fuel(kg) (X' + str(scalar) + ')')
        except:
            pass

        for n, phase in enumerate(phases):
            axs[1].plot(phasedatenums[phase], phasedata['ERPMstak_heat ' + phase], color=colors[n], linewidth=plw,label=phase)
            axs[1].plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata['ERPMstak_heat ' + phase][0], phasedata['ERPMstak_heat ' + phase][-1]], color=colors[n],linestyle='none', marker='|', markersize=msize)

        axs[1].legend()

    # Format x axis to readable times
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
    axs[1].xaxis.set_major_formatter(xfmt)
    for tick in axs[1].get_xticklabels():
        tick.set_rotation(30)
    #for i, ax in enumerate(fig.axes):
        #ax.xaxis.set_major_formatter(xfmt)
        #for tick in ax.get_xticklabels():
            #tick.set_rotation(30)

    ##########################################################
    #REplot for new inputs
    running = 'fun'
    while running == 'fun':
            #GUI box to edit input times

        zeroline = 'Edit averaging period\n'
        firstline = 'Time format = yyyymmdd HH:MM:SS\n'
        secondline = 'Click OK to update plot\n'
        thirdline = 'Click Cancel to exit\n'
        msg = zeroline + firstline + secondline + thirdline
        title = "Gitrdone"

        fieldnames = timenames
        currentvals = []

        for name in timenames:
            currentvals.append(timestring[name])

        newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)
        if newvals:
            if newvals != currentvals:  # If new values are entered
                currentvals = newvals
                for n, name in enumerate(fieldnames):
                    timestring[name] = currentvals[n]
                    eval[name] = currentvals[n]  # update to new values

                # record new values in averagingperiod for next time
                io.write_constant_outputs(cutpath, timenames, timeunits, timestring, timeunc, timeuval)
                line = 'Updated averaging period file:' + cutpath
                print(line)
                logs.append(line)
        else:
            running = 'not fun'
            savefig = os.path.join(savefig + '_averagingperiod.png')
            plt.savefig(savefig, bbox_inches='tight')
            plt.ioff()  # turn off interactive plot
            plt.close()  # close plot

        ##################################################################
        # Convert datetime str to readable value time objects
        [validnames, timeobject] = makeTimeObjects(timenames, timestring, date)

        # Find 'phase' averging period
        phases = definePhases(validnames)
        # find indicieds in the data for start and end
        indices = findIndices(validnames, timeobject, datenums)

        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

        # add names and units
        avgnames = []
        avgunits = {}
        for phase in phases:
            for name in names:
                testname = name + ' ' + phase
                avgnames.append(testname)
                avgunits[testname] = units[name]

        for name in timenames:
            try:
                avgnames.remove(name)  # temoprarliy remove start and end names
            except:
                pass

        #################################################################
        # Create period averages
        calcavg = {}
        unc = {}
        uval = {}
        for name in avgnames:
            for phase in phases:
                if name == 'seconds ' + phase:
                    calcavg[name] = avgdata['seconds ' + phase][-1] - avgdata['seconds ' + phase][0]
                else:
                    # Try creating averages of values, nan value if can't
                    try:
                        calcavg[name] = sum(avgdata[name]) / len(avgdata[name])
                    except:
                        calcavg[name] = 'nan'
            ####Currently not handling uncertainties
            unc[name] = ''
            uval[name] = ''
        for n, name in enumerate(timenames): #Add start and end time
            avgnames.insert(n, name)
            calcavg[name] = timestring[name]
            avgunits[name] = 'yyyymmdd hh:mm:ss'

        # output time series data file for each phase
        for phase in phases:
            phaseoutputpath = averagecalcoutputpath[
                              :-4] + '_' + phase + '.csv'  # name the output file by inserting the phase name into the outputpath
            #Record updated averaged
            avgphasenames = []
            for name in avgnames:
                if name.endswith(phase):
                    avgphasenames.append(name)
            io.write_constant_outputs(phaseoutputpath, avgphasenames, avgunits, calcavg, unc, uval)
            line = 'updated average calculations file: ' + phaseoutputpath
            print(line)
            logs.append(line)
        phaseoutputpath = averagecalcoutputpath[
                          :-4] + '_allphases.csv'  # name the output file by inserting the phase name into the outputpath
        io.write_constant_outputs(phaseoutputpath, avgnames, avgunits, calcavg, unc, uval)
        line = 'updated average calculations file: ' + phaseoutputpath
        print(line)
        logs.append(line)

        # update the data series column named phase
        name = 'phase'
        data[name] = ['none'] * len(data['time'])  # clear all values to none
        for phase in phases:
            for n, val in enumerate(data['time']):
                if n >= indices['start time ' + phase] and n <= indices['end time ' + phase]:
                    if data[name][n] == 'none':
                        data[name][n] = phase
                    else:
                        data[name][n] = data[name][n] + ',' + phase

        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

        ###################################################################
        #update plot
        axs[0].cla()
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

            # plot full data and averaging period in same subplot
            axs[0].plot(data['datenumbers'], y, color='blue', label='Full constant flowrate ER')
            axs[0].set_title('Realtime Flowrate ER PM')
            axs[0].set(ylabel='Emission Rate(g/hr)')
            try:
                axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            except:
                axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            axs[0].legend()
            for n, phase in enumerate(phases):
                axs[0].plot(phasedatenums[phase], phasedata['PM_flowrate_test'], color=colors[n], linewidth=plw,
                            label=phase)

        else:
            y = []
            for val in metric['PM_flowrate']:
                try:
                    if float(val) < 0.0:
                        y.append(0.0)
                    else:
                        y.append(val)
                except:
                    y.append(val)
            # plot full data and averaging period in same subplot
            #plt.Artist.remove(axs[0].lines[0])
            axs[0].plot(data['datenumbers'], data['PM_flowrate'], color='blue', label='Full constant flowrate ER')
            axs[0].set_title('Realtime Constant Flowrate ER PM')
            axs[0].set(ylabel='Emission Rate(g/hr)')
            try:
                axs[0].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            except:
                axs[0].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            try:
                axs[0].plot(fuelvals['datenumbers'], scalefuel, color='brown',
                            label='Fuel(kg) (X' + str(scalar) + ')')
            except:
                pass

            for n, phase in enumerate(phases):
                axs[0].plot(avgdatenums[phase], avgdata['PM_flowrate ' + phase], color=colors[n], linewidth=plw,
                            label=phase)
                axs[0].plot([avgdatenums[phase][0], avgdatenums[phase][-1]],
                            [avgdata['PM_flowrate ' + phase][0], avgdata['ERPMstak_heat ' + phase][-1]],
                            color=colors[n], linestyle='none', marker='|', markersize=msize)

            axs[0].legend()
            axs[1].cla()
            # plot full data and averaging period in same subplot
            axs[1].plot(data['datenumbers'], data['ERPMstak_heat'], color='blue', label='Full stak flowrate ER')
            axs[1].set_title('Realtime Stack Flowrate ER PM')
            axs[1].set(ylabel='Emission Rate(g/hr)')
            try:
                axs[1].plot(data['datenumbers'], scaleTC, color='yellow', label=fullname)
            except:
                axs[1].plot(data['datenumbers'], scaleTCnoz, color='yellow', label=fullname)
            try:
                axs[1].plot(fuelvals['datenumbers'], scalefuel, color='brown',
                            label='Fuel(kg) (X' + str(scalar) + ')')
            except:
                pass

            for n, phase in enumerate(phases):
                axs[1].plot(avgdatenums[phase], avgdata['ERPMstak_heat ' + phase], color=colors[n],
                            linewidth=plw, label=phase)
                axs[1].plot([avgdatenums[phase][0], avgdatenums[phase][-1]],
                            [avgdata['ERPMstak_heat ' + phase][0], avgdata['ERPMstak_heat ' + phase][-1]],
                            color=colors[n], linestyle='none', marker='|', markersize=msize)

            axs[1].legend()

        # Format x axis to readable times
        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
        axs[1].xaxis.set_major_formatter(xfmt)
        for tick in axs[1].get_xticklabels():
            tick.set_rotation(30)
        #for i, ax in enumerate(fig.axes):
            #ax.xaxis.set_major_formatter(xfmt)
            #for tick in ax.get_xticklabels():
                #tick.set_rotation(30)

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)

def makeTimeObjects(Timenames,Timestring,Date):
    Timeobject={}   #initialize a dictionary of time objects
    Validnames=[] #initialize a list of time names that have a valid time entered
    for Name in Timenames:
        if len(Timestring[Name]) == 8:  #if time format
            Datestring=Date+' '+Timestring[Name]    #add the date to the time string
        else:   #if already date format
            Datestring = Timestring[Name]   #use it as is
        try:
            Timeobject[Name]=dt.strptime(Datestring, '%Y%m%d %H:%M:%S')                #convert the time string to date object
            Validnames.append(Name)
        except:
            pass
    return Validnames,Timeobject


def definePhases(Timenames):
    Phases = []  # initialize a list of Unit Tests phases (prebkg, low power, med power, high power, post bkg)
    for Name in Timenames:
        spot = Name.rindex(' ')  # locate the last space
        Phase = Name[spot + 1:]  # grab the string after the last underscore
        if Phase not in Phases:  # if it is a new phase
            Phases.append(Phase)  # add to the list of phases
    return Phases


def findIndices(InputTimeNames, InputTimeObject, Datenums):
    InputTimeDatenums = {}
    Indices = {}
    for Name in InputTimeNames:
        InputTimeDatenums[Name] = matplotlib.dates.date2num(InputTimeObject[Name])
        Indices[Name] = Datenums.index(InputTimeDatenums[Name])
    return Indices


def definePhaseData(Names, Data, Phases, Indices):#, Ucinputs):
    Phasedatenums = {}
    Phasedata = {}
    Phasemean = {}
    for Phase in Phases:  # for each Unit Tests phase
        # make data series of date numbers
        key = 'start time ' + Phase
        startindex = Indices[key]
        key = 'end time ' + Phase
        endindex = Indices[key]
        Phasedatenums[Phase] = Data['datenumbers'][startindex:endindex + 1]
        # make phase data series for each data channel
        for Name in Names:
            Phasename = Name + ' ' + Phase
            Phasedata[Phasename] = Data[Name][startindex:endindex + 1]

            # calculate average value
            if Name != 'time' and Name != 'phase':
                if all(np.isnan(Phasedata[Phasename])):
                    Phasemean[Phasename] = np.nan
                else:
                    ave = np.nanmean(Phasedata[Phasename])
                    if Name == 'datenumbers':
                        Phasemean[Phasename] = ave
                    #else:
                        #uc = abs(float(Ucinputs[Name][0]) + ave * float(Ucinputs[Name][1]))
                        #Phasemean[Phasename] = ufloat(ave, uc)

        # time channel: use the mid-point time string
        Phasename = 'datenumbers ' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean
#####################################################################
# the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    PEMS_MultiCutPeriods(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, fuelmetricpath, fuelpath, cutpath, outputpath,
                         averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, savefig, logpath)
