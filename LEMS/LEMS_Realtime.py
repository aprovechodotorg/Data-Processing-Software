#v0.4  Python3

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


import os
import csv
import numpy as np
import math
import uncertainties as unumpy
import matplotlib
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg

########### inputs (only used if this script is run as executable) #############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
inputpath='TimeSeries.csv'
energypath='EnergyOutputs.csv'
graninputpath = 'GravOutputs.csv'
empath = 'EmissionOutputs.csv'
periodpath = 'AveragingPeriod.csv'
outputpath = 'RealtimeOutputs.csv'
averageoutputpath = 'AveragingPeriodOutputs.csv' #Will contain avg for each phase and for cut period
averagecalcoutputpath = 'AveragingPeriodCalcs.csv'
fullaverageoutputpath = 'RealtimeAveragesOutputs.csv'
phasepath = 'PhaseTimes.csv'
savefig = 'averagingperiod.png'
logpath='log.txt'
##################################

def LEMS_Realtime(inputpath, energypath, gravinputpath, empath, periodpath, outputpath, averageoutputpath, averagecalcoutputpath, fullaverageoutputpath, phasepath, savefig, logpath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]
    #################################################

    #Assumptions and values
    pm_coef = 1 #(ug/m^3)/logunit
    scat_cx = 3 #m^2 / g scattering cross-section

    ##############################
    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    line = 'loaded: ' + inputpath #add to log
    print(line)
    logs.append(line)

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'loaded: ' + energypath
    print(line)
    logs.append(line)

    # load emissions data file
    [emnames, emunits, emval, emunc, emmetric] = io.load_constant_inputs(empath)

    line = 'loaded: ' + empath
    print(line)
    logs.append(line)

    metric = {} #Dictionary for storing calculated values
    phases = ['_hp', '_mp', '_lp']
    if 'start_time_L1' in enames:
        phases.insert('_L1', 0)
    if 'start_time_L5' in enames:
        phases.insert('_L5', 0)

    ###################################
    #Mass flow rate
    name = 'Mass_Flow'
    names.append(name)
    units[name] = 'g/s'
    data[name] = []

    p_amb = eval['initial_pressure'] * 3386 #in Hg to Pa
    for n, val in enumerate(data['FLUEtemp']):
        temp = val * 15.3 * math.sqrt(data['Flow'][n] * (p_amb / (val + 273.15))) #May need to change to P_duct
        data[name].append(temp)

    #Mole flow rate
    name = 'Mole_Flow'
    names.append(name)
    units[name] = 'mol / s'
    data[name] = []

    for val in data['Mass_flow']:
        mole = val / 29
        data[name].append(mole)

    #CO2 flow rate
    name = 'CO2_Flow'
    names.append(name)
    units[name] = 'mol/s'
    data[name] = []

    for n, val in enumerate(data['CO2']):
        co2 = val * data['Mole_Flow'][n] / 1000000
        data[name].append(co2)

    #CO flow rate
    name = 'CO_Flow'
    names.append(name)
    units[name] = 'mol/s'
    data[name] = []

    for n, val in enumerate(data['CO']):
        co = val * data['Mole_Flow'][n] / 1000000
        data[name].append(co)

    #Density
    name = 'Density'
    names.append(name)
    units[name] = 'g/m^3'
    data[name] = []

    for val in data['FLUEtemp']:
        den = 29 * p_amb / 8.314 / (val + 273)
        data[name].append(den)

    #PM scat coef
    name = 'PM_scat_coef'
    names.append(name)
    units[name] = '1/Mm'
    data[name] = []

    for val in data['PM']:
        coef = val * pm_coef * scat_cx
        data[name].append(coef)

    ################################################################
    # Read in averaging period start and end times (phase start and end time)
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(phasepath)

    line = 'loaded: ' + phasepath
    print(line)
    logs.append(line)

    ##################################################################
    # Convert datetime str to readable value time objects
    date = data['time'][0][:8] #pull date

    [validnames, timeobject] = bkg.makeTimeObjects(titlenames, timestring, date)

    # Find 'phase' averging period
    phases = bkg.definePhases(validnames)
    # find indicieds in the data for start and end
    indices = bkg.findIndices(validnames, timeobject, datenums)

    # Define averaging data series
    [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

    #PM conc
    name = 'PM_Conc'
    names.append(name)
    units[name] = 'ug/m^3'
    data[name] = []

    #PM mass scat CX
    mass_scat_cx = []
    for phase in phases:
        coefname = 'PM_scat_coef' + phase
        cx = avgmean[coefname] /




    for phase in phases:
        for n, val in enumerate

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