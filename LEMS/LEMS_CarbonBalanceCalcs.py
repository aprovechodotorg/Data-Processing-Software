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

#########      inputs      ##############
# Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
# time series data file:
inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_TimeSeries.csv"
# energy metrics data file:
energypath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_EnergyOutputs.csv"
# phase averages input data file:
aveinputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_Averages.csv"
# gravimetric PM metrics data file:
gravinputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_GravOutputs.csv"
# phase emission metrics output data file:
emisoutputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_EmissionOutputs.csv"
# all metrics output data file:
alloutputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_AllOutputs.csv"
metricpath = 'output.csv'
# input file of start and end times for background and test phase periods
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\5.31\\5.31_log.txt"


##########################################


def LEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath):
    # Function calculates carbon balance calculations according to ISO standards
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_CarbonBalanceCalcs v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    # Initialize dictionaries for output
    names = []
    units = {}
    val = {}
    unc = {}
    metric = {}

    emissions = ['CO', 'CO2', 'PM']  # emission species that will get metric calculations

    test_phases = ['hp', 'mp', 'lp']

    Tstd = float(293)  # define standard temperature in Kelvin
    Pstd = float(101325)  # define standard pressure in Pascals

    MW = {}
    MW['C'] = float(12.01)  # molecular weight of carbon (g/mol)
    MW['CO'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['COhi'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['CO2'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['CO2v'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['CO2hi'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['SO2'] = float(64.07)  # molecular weight of sulfur dioxide (g/mol)
    MW['NO'] = float(30.01)  # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2'] = float(46.01)  # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S'] = float(34.1)  # molecular weight of hydrogen sulfide (g/mol)
    MW['HxCy'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['CH4'] = float(16.04)  # molecular weight of methane (g/mol)
    MW['air'] = float(29)  # molecular weight of air (g/mol)
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    # load test averages data file
    [avenames, aveunits, aveval, aveunc, ave] = io.load_constant_inputs(aveinputpath)

    line = 'Loaded test averages:' + aveinputpath  # Add to log
    print(line)
    logs.append(line)

    phases = []
    for phase in test_phases: #check which phases exist
        name = 'time_' + phase
        if name in avenames:
            phases.append(phase)

    #check if IDC test
    if 'time_L1' in avenames:
        phases.insert(0, 'L1')
    if 'time_L5' in avenames:
        phases.append('L5')

    for em in emissions:
        for phase in phases:
            for name in avenames:
                if em+'_' in name and phase in name:   #copy some of the averages to the metric dictionary
                    names.append(em + '_' + phase)
                    units[em + '_' + phase] = aveunits[name]
                    metric[em + '_' + phase] = ave[name]

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'Loaded energy metrics:' + energypath  # add to log
    print(line)
    logs.append(line)

    # load energy metrics data file
    [emnames, emunits, emval, emunc, emmetric] = io.load_constant_inputs(emisoutputpath)

    line = 'Loaded emission metrics:' + emisoutputpath  # add to log
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
        for phase in phases:
            name = em + 'conc_' + phase
            names.append(name)
            if em == 'PM':
                units[name] = 'mgm^-3'
                metric[name] = gravmetric[em + 'mass_' + phase] / 1000 #ug/m^3 to mg/m^3
            else:
                units[name] = 'gm^-3'
                F = MW[em] * Pstd / Tstd / 1000000 / R  # ISO19869 Formula 28
                metric[name] = F * metric[em + '_' + phase]

    #total carbon concentration
    for phase in phases:
        name = 'Cconc_' + phase
        names.append(name)
        units[name] = 'gm^-3'
        metric[name] =metric['COconc_' + phase]*MW['C']/MW['CO']+metric['CO2conc_' + phase]*MW['C']/MW['CO2']    # ISO19869 Formula 60

    #MCE
    for phase in phases:
        name = 'MCE_' + phase
        names.append(name)
        units[name] = 'mol/mol'
        metric[name] = metric['CO2_' + phase]/(metric['CO_' + phase]+metric['CO2_' + phase])  #ISO 19869 Formula 61

    #carbon emission ratio
    for em in emissions:
        for phase in phases:
            name = 'CER_' + em + '_' + phase
            names.append(name)
            if em == 'PM':
                units[name] = 'mg/g'
            else:
                units[name] = 'g/g'
            cconc = 'Cconc_' + phase
            metric[name] = metric[em+'conc_' + phase]/metric[cconc]  #ISO 19869 Formula 63

    #Emission factor, fuel mass based
    wood_Cfrac = 0.5  # carbon fraction of fuel
    for em in emissions:
        for phase in phases:
            name = 'EFmass_'+em + '_' + phase
            names.append(name)
            if em == 'PM':
                units[name] = 'mg/kg'
            else:
                units[name] = 'g/kg'
            metric[name] = metric['CER_'+em + '_' + phase]*wood_Cfrac*1000  #ISO 19869 Formula 66-69 should be wet basis c frac though

    #Emission factor, dry fuel mass based, not  an ISO 19869 metric
    for em in emissions:
        for phase in phases
            name = 'EFmass_dry_'+em+'_'+phase
            names.append(name)
            if em == 'PM':
                units[name] = 'mg/kg'
            else:
                units[name] = 'g/kg'
            metric[name] = metric['CER_'+em+'_'+phase]*wood_Cfrac*1000

    #Emission factor, fuel energy based
    for em in emissions:
        for phase in phases:
            name = 'EFenergy_'+em+'_'+phase
            names.append(name)
            if em == 'PM':
                units[name] = 'mg/MJ'
            else:
                units[name] = 'g/MJ'
            metric[name] = metric['EFmass_'+em+'_'+phase]/emetric['fuel_heating_value']  #ISO 19869 Formula 70-73

    ###################################################
    #carbon in
    wood_Cfrac = 0.5 #carbon fraction of fuel
    if 'L1' in phases or 'L5' in phases: #if IDC test
        for phase in phases:
            name = 'carbon_in_' + phase
            units[name] = 'g'
            delta_char = emetric['final_pot1_mass_' + phase] - emetric['pot1_dry_mass']
            if eunits['final_pot1_mass_' + phase] == 'lb':
                delta_char = delta_char / 2.205 #lb to kg
            metric[name] = ((wood_Cfrac * emetric['fuel_dry_mass_' + phase]) - (0.81 * delta_char)) * 1000 #kg to g
    else:
        for phase in phases:
            name = 'carbon_in_' + phase
            units[name] = 'g'
            metric[name] = (wood_Cfrac * emetric['fuel_dry_mass_' + phase] - 0.81 * emetric['char_mass_' + phase]) * 1000

    #carbon out
    for phase in phases:
        name = 'carbon_out_' + phase
        units[name] = 'g'
        metric[name] = (emmetric['CO_total_mass_'+phase] * MW['C']/MW['CO'] + emmetric['CO2_total_mass_'+phase] *
                        MW['C']/MW['CO2'] + 0.91 * emmetric['PM_total_mass_' + phase])

    #carbon burn rate
    for phase in phases:
        name = 'ERC_' + phase
        units[name] = 'g/hr'
        metric[name] = (metric['carbon_out_' + phase] - metric['carbon_in_' + phase]) / (emetric['phase_time_' + phase] / 60)

    test = 1

#######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_CarbonBalanceCalcs(energypath,gravinputpath,aveinputpath,metricpath,logpath)