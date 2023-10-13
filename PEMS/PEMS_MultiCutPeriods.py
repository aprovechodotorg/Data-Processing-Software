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

inputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_TimeSeries_test.csv"
energypath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_EnergyOutputs.csv"
gravinputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_GravOutputs.csv"
empath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_EmissionOutputs.csv"
stakpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_TimeSeriesStakFlow.csv"
fuelpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_FuelMetrics.csv"
cutpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_CutTimes.csv"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_RealtimeOutputs.csv"
averageoutputpath ="C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_AveragingPeriodOutputs.csv"
averagecalcoutputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_AveragingPeriodCalcs.csv"
fullaverageoutputpath = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_RealtimeAverages.csv"
savefig = "C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_averagingperiod.png"
logpath ="C:\\Users\\Jaden\\Documents\\DOE-stak\\test\\3.21.23\\3.21.23_log.txt"

def PEMS_MultiCutPeriods(inputpath, energypath, gravinputpath, empath, stakpath, fuelpath, cutpath, outputpath,
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
    # load in stak velocity timeseries data
    try:
        [snames, sunits, sdata] = io.load_timeseries(stakpath)
        plots = 4
    except:
        plots = 1
    ####################################################

    if os.path.isfile(cutpath): #If cut times file already exists
        line = 'Cut times input file already exists: ' + cutpath
        print(line)
        logs.append(line)
    elif os.path.isfile(fuelpath): #if fuel cut times are avalible, make file based on those
        fnames = []  # list of variable names
        fval = {}  # dictionary keys are variable names, values are variable values

        # load input file
        stuff = []
        with open(fuelpath) as f:
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
            writer.writerow({'Label': f"end time {len(fval['time'])}", 'Units': 'yyyymmdd HH:MM:SS', 'Time': eval['end_time_test']}) #end of test from datasheet

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



#####################################################################
# the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    PEMS_MultiCutPeriods(inputpath, energypath, gravinputpath, empath, stakpath, fuelpath, cutpath, outputpath,
                         averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, savefig, logpath)

