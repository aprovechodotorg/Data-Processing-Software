# v0.0 Python3

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


# do:
# add time series for Volume flow QC, Flow RE, and Re QC
# add performance tiers
# add input for duct static pressure to calculate duct pressure instead of ambient pressure
# add input for flow grid calibration factor
# add firepower and carbon balance data series
# add other desired output metrics from old data processing spreadsheet Results tab
# Resolve emission metric name discrepancy with 'upload_template from christian.csv'
#  One metric is listed in the upload template that is not output by this script: CO2_useful_eng, CO_useful_eng, PM_useful_eng (not sure how to calculate it)

import LEMS_DataProcessing_IO as io
import numpy as np
from uncertainties import ufloat
from datetime import datetime as dt
import math

#########      inputs      ##############
# Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
# time series data file:
inputpath = 'TimeSeries.csv'
# energy metrics data file:
energypath = 'EnergyOutputs.csv'
# phase averages input data file:
aveinputpath = 'Averages.csv'
# gravimetric PM metrics data file:
gravinputpath = 'GravOutputs.csv'
# phase emission metrics output data file:
emisoutputpath = 'EmissionOutputs.csv'
# all metrics output data file:
alloutputpath = 'AllOutputs.csv'
# input file of start and end times for background and test phase periods
logpath = 'log.txt'


##########################################


def PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath):
    # Function calculates carbon balance calculations according to ISO standards
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CarbonBalanceCalcs v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    # Initialize dictionaries for output
    names = []
    units = {}
    val = {}
    unc = {}
    metric = {}

    #emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'PM', 'NO', 'NO2', 'VOC']  # emission species that will get metric calculations
    emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'PM', 'BC']  # emission species that will get metric calculations

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
    MW['VOC'] = float(96.95) #molecular weight of volatile organic compounds (g/mol)
    MW['HC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    # load test averages data file
    [avenames, aveunits, aveval, aveunc, ave] = io.load_constant_inputs(aveinputpath)

    line = 'Loaded test averages:' + aveinputpath  # Add to log
    print(line)
    logs.append(line)

    # Check that hi values exist in data set
    try:
        value = ave['COhi_test']
    except:
        # If it doesn't exist, remove it from possible calculations and outputs
        emissions.remove('COhi')

    try:
        value = ave['CO2hi_test']
    except:
        # If it doesn't exist, remove it from possible calculations and outputs
        emissions.remove('CO2hi')

    for em in emissions:
        for name in avenames:
            if em + '_' in name and 'test' in name:  # copy some of the averages to the metric dictionary
                names.append(em)
                units[em] = aveunits[name]
                metric[em] = ave[name]
        testname = em + '_test'

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'Loaded energy metrics:' + energypath  # add to log
    print(line)
    logs.append(line)

    # load grav metrics data file
    try:
        [gravnames, gravunits, gravval, gravunc, gravmetric] = io.load_constant_inputs(gravinputpath)

        line = 'Loaded gravimetric PM metrics:' + gravinputpath  # add to log
        print(line)
        logs.append(line)
    except:
        line = 'No gravimetric data'
        print(line)
        logs.append(line)

    ################################################
    # calculate metrics

    # mass concentration
    for em in emissions:
        name = em + 'conc'
        names.append(name)
        if em == 'PM':
            units[name] = 'mgm^-3'
            metric[name] = gravmetric[name + '_test']
        elif em == 'BC':
            units[name] = 'ugm^-3'
            try:
                filt_area = (math.pi * pow(gravmetric['filter_catch_diameter'], 2) / 4) / 100 #area = pi*d^2/2 covert to cm^2
                mass = gravmetric['BC_load'] * filt_area #mass of BC = BC loading * catch area (ug)
                metric[name] = mass * gravmetric['volume_tot'] #concentration = mass * flow volume
            except:
                metric[name] = ''
        else:
            units[name] = 'gm^-3'
            F = MW[em] * Pstd / Tstd / 1000000 / R  # ISO19869 Formula 28
            metric[name] = F * metric[em]

    if metric['BCconc'] == '':
        emissions.remove('BC')

    # total carbon concentration
    name = 'Cconc'
    names.append(name)
    units[name] = 'gm^-3'
    try:
        metric[name] = (metric['COconc'] * MW['C'] / MW['CO']) + (metric['CO2conc'] * MW['C'] / MW['CO2']) + (
            ((metric['BCconc']/1000) + (metric['PMconc'] - (metric['BCconc'] / 1000))) / 1000)  # ISO19869 Formula 60
    except: #no BC data
        metric[name] = (metric['COconc'] * MW['C'] / MW['CO']) + (metric['CO2conc'] * MW['C'] / MW['CO2'])
    #Cconc = CO2conc * MWc/MWco2 + COconc * MWC/MWco + (ECconc + OCconc)/1000

    # total carbon concentration hi range
    if 'COhi' in emissions:
        name = 'Cconchi'
        names.append(name)
        units[name] = 'gm^-3'
        metric[name] = metric['COhiconc'] * MW['C'] / MW['CO'] + metric['CO2hiconc'] * MW['C'] / MW[
            'CO2']  # ISO19869 Formula 60

    # MCE
    name = 'MCE'
    names.append(name)
    units[name] = 'mol/mol'
    metric[name] = metric['CO2'] / (metric['CO'] + metric['CO2'])  # ISO 19869 Formula 61

    if 'CO2hi' in emissions:
        # MCEhi
        name = 'MCEhi'
        names.append(name)
        units[name] = 'mol/mol'
        metric[name] = metric['CO2hi'] / (metric['COhi'] + metric['CO2hi'])  # ISO 19869 Formula 61

    # carbon emission ratio
    for em in emissions:
        name = 'CER_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/g'
        elif em == 'BC':
            units[name] = 'ug/g'
        else:
            units[name] = 'g/g'
        if 'hi' in em:
            cconc = 'Cconchi'
        else:
            cconc = 'Cconc'
        metric[name] = metric[em + 'conc'] / metric[cconc]  # ISO 19869 Formula 63

    # Emission factor, fuel mass based
    for em in emissions:
        name = 'EFmass_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/kg'
        elif em == 'BC':
            units[name] = 'ug/kg'
        else:
            units[name] = 'g/kg'
        metric[name] = metric['CER_' + em] * emetric['fuel_Cfrac'] * 1000  # ISO 19869 Formula 66-69

    # Emission factor, dry fuel mass based, not  an ISO 19869 metric
    for em in emissions:
        name = 'EFmass_dry_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/kg'
        elif em == 'BC':
            units[name] = 'ug/kg'
        else:
            units[name] = 'g/kg'
        metric[name] = metric['CER_' + em] * emetric['fuel_Cfrac_db'] * 1000

    # Emission factor, fuel energy based
    for em in emissions:
        name = 'EFenergy_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/MJ'
        elif em == 'BC':
            units[name] = 'ug/MJ'
        else:
            units[name] = 'g/MJ'
        metric[name] = metric['EFmass_' + em] / emetric['fuel_EHV']  # ISO 19869 Formula 70-73

    # Emission rate
    for em in emissions:
        name = 'ER_' + em
        names.append(name)
        if em == 'PM':
            units[name] = 'mg/min'
        elif em == 'BC':
            units[name] = 'ug/min'
        else:
            units[name] = 'g/min'
        metric[name] = metric['EFenergy_' + em] * emetric['fuel_energy'] / emetric[
            'phase_time_test']  # ISO 19869 Formula 74-77
    name = 'ER_PM_heat'
    names.append(name)
    units[name] = 'g/hr'
    metric[name] = metric['ER_PM'] * 60 / 1000

    try:
        name = 'ER_BC_heat'
        metric[name] = metric['ER_BC'] * 60 / 1000000
        names.append(name)
        units[name] = 'g/hr'


        name = 'BC_PM_ratio'
        metric[name] = metric['ER_BC_heat'] / metric['ER_PM_heat']
        names.append(name)
        units[name] = ''


        name = 'BC_OC_ratio'
        metric[name] = metric['ER_BC_heat'] / (metric['ER_PM_heat'] - metric['ER_BC_heat'])  # PM - BC = OC
        names.append(name)
        units[name] = ''
    except:
        pass


    # Total carbon
    name = 'Mass_C'
    names.append(name)
    units[name] = 'g'
    metric[name] = emetric['fuel_dry_mass'] * emetric['fuel_Cfrac_db'] * 1000

    # make header for output file:
    name = 'variable_name'
    names = [name] + names
    units[name] = 'units'
    val[name] = 'value'
    unc[name] = 'unc'

    # print metrics output file
    io.write_constant_outputs(metricpath, names, units, val, unc, metric)

    line = '\ncreated emission metrics output file:\n' + metricpath  # add to log
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath)
