# v0.3 Python3

#    Copyright (C) 2022 Mountain Air Engineering
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
from uncertainties import ufloat, unumpy
import math as math
from datetime import datetime as dt

#########      inputs      ##############
#
logpath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'


##########################################

def PEMS_StackFlowMetricCalcs(inputpath, energypath, carbalpath, avgpath, gravpath, metricpath, alloutputpath, logpath):
    ver = '0.3'  # for Apro
    # vo.2: handles inputs with and without unc
    # v0.3: added energy output metrics from CAN B415.1
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_StackFlowMetricCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    metricnames = []
    val = {}
    unc = {}
    metric = {}

    possible_emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'NO', 'NO2', 'HC', 'VOC', 'CH4', 'PM','C']  # possible emission species that will get metric calculations
    emissions = []  # emission species that will get metric calculations, defined after channel names are read from time series data file

    Tstd = float(293)  # define standard temperature in Kelvin
    Pstd = float(101325)  # define standard pressure in Pascals
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

    timestep = 1  # time step for emission rate integration, add code to read dt from time series

    # load stack flow time series data file (test period)
    [names, units, data] = io.load_timeseries_with_uncertainty(inputpath)
    # [names,units,data]=io.load_timeseries(inputpath)   #use this if time series input file does not have uncertainty

    line = 'Loaded time series data:' + inputpath
    print(line)
    logs.append(line)

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'Loaded energy metrics:' + energypath
    print(line)
    logs.append(line)

    # load carbon balance emission metrics
    [cbnames, cbunits, cbval, cbunc, cbmetric] = io.load_constant_inputs(carbalpath)

    line = 'Loaded carbon balance emission metrics:' + carbalpath
    print(line)
    logs.append(line)

    ################################################
    # define emission species that will get metric calculations
    for name in possible_emissions:
        ername = 'ER' + name + 'stak'
        if ername in names:
            emissions.append(name)

    #################################################
    # calculate metrics

    # total emissions
    for em in emissions:
        name = 'Mass_' + em
        metricnames.append(name)
        ername = 'ER' + em + 'stak'
        units[name] = 'g'

        nans = 0
        # integrate the emission rate series
        # unc assuming perfect correlation between time series values
        valsum = float(0)  # initialize cumulative sum of nominal values
        uncsum = float(0)  # initializer cumulative sum of uncertainty values
        for n, er in enumerate(data[ername]):
            valsum = valsum + er.n / 3600 * timestep
            if math.isnan(er.std_dev):  # if the unc = nan
                nans = nans + 1
            else:
                uncsum = uncsum + er.std_dev / 3600 * timestep
        line = name + ' ' + str(nans) + ' uncnans'
        print(line)
        logs.append(line)

        if em == 'PM' or em == 'OC' or em == 'EC' or em == 'TC':
            metric[name] = ufloat(valsum, uncsum) / 1000  # convert mg to g
        else:
            metric[name] = ufloat(valsum, uncsum)

    try:
        metric['Mass_OC'] = metric['Mass_PM'] * cbmetric['OC/PM']
        metric['Mass_EC'] = metric['Mass_PM'] * cbmetric['EC/PM']
        metric['Mass_TC'] = metric['Mass_PM'] * cbmetric['TC/PM']
    except:
        pass

    # average emission rates
    for em in emissions:
        name = 'ER_' + em + '_stak'
        units[name] = 'g/hr'
        metricnames.append(name)
        massname = 'Mass_' + em
        try:
            metric[name] = metric[massname] * 3600 / len(data['time'])
        except:
            metric[name] = ''

    # Emission factor, fuel mass based
    for em in emissions:
        name = 'EFmass_' + em + '_stak'
        metricnames.append(name)
        units[name] = 'g/kg'
        massname = 'Mass_' + em
        try:
            metric[name] = metric[massname] / emetric['fuel_mass']
        except:
            metric[name] = ''

    # Emission factor, dry fuel mass based
    for em in emissions:
        name = 'EFmass_dry_' + em + '_stak'
        metricnames.append(name)
        units[name] = 'g/kg'
        massname = 'Mass_' + em
        try:
            metric[name] = metric[massname] / emetric['fuel_dry_mass']
        except:
            metric[name] = ''

    # Emission factor, fuel energy based
    for em in emissions:
        name = 'EFenergy_' + em + '_stak'
        metricnames.append(name)
        units[name] = 'g/MJ'
        massname = 'Mass_' + em
        try:
            metric[name] = metric[massname] / emetric['fuel_energy']
        except:
            metric[name] = ''

    name = 'Firepower'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)

    name = 'UsefulPower'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)

    name = 'ThermalEfficiency'
    metricnames.append(name)
    units[name] = '%'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
    
    # CAN B415.1 output metrics
    
    #Fuel energy input
    name = 'I_CAN'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)    
    
    #sensible energy loss out the chimney
    name = 'L_sen_CAN'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
    
    #latent energy loss out the chimney
    name = 'L_lat_CAN'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
   
    #chemical energy loss out the chimney
    name = 'L_chem_CAN'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
    
    # overall heat output (claue 13.7.9.1)
    name = 'E_out_CAN'
    metricnames.append(name)
    units[name] = 'W'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
    
    #combustion efficiency (clause 13.7.9.2)
    name = 'CE_CAN'
    metricnames.append(name)
    units[name] = '%'
    average = sum(data[name]) / len(data[name])
    uncertainty_list = unumpy.std_devs(data[name])
    avg_unc = sum(uncertainty_list)/len(uncertainty_list)
    metric[name] = ufloat(average.n, avg_unc)
    
    #combustion efficiency (clause 13.7.9.2)
    name = 'CE_CAN'
    units[name] = '%'
    metricnames.append(name)
    metric[name] = (metric['I_CAN']-metric['L_chem_CAN'])/metric['I_CAN']*100
    
    #overall efficiency  (clause 13.7.9.3)
    name = 'OE_CAN'
    units[name] = '%'
    metricnames.append(name)
    metric[name] = metric['E_out_CAN']/metric['I_CAN']*100  
    
    #heat transfer efficiency (clause 13.7.9.4)
    name = 'HTE_CAN'
    units[name] = '%'
    metricnames.append(name)
    metric[name] = metric['OE_CAN']/metric['CE_CAN']*100

    # make header for output file:
    name = 'variable_name'
    metricnames = [name] + metricnames
    units[name] = 'units'
    val[name] = 'value'
    unc[name] = 'unc'

    # print metrics output file
    io.write_constant_outputs(metricpath, metricnames, units, val, unc, metric)

    line = '\ncreated emission metrics output file:\n' + metricpath
    print(line)
    logs.append(line)

    ############################################################
    #create all outputs file
    allnames = []
    allunits = {}
    allvals = {}
    allunc = {}
    alluvals = {}

    #Add energy outputs
    for name in enames[1:]:
        allnames.append(name)
        allunits[name] = eunits[name]
        allvals[name] = eval[name]
        allunc[name] = eunc[name]
        alluvals[name] = emetric[name]

    #Add average sensor data
    [avgnames, avgunits, avgvals, avgunc, avguvals] = io.load_constant_inputs(avgpath)
    for name in avgnames[1:]:
        allnames.append(name)
        allunits[name] = avgunits[name]
        allvals[name] = avgvals[name]
        allunc[name] = avgunc[name]
        alluvals[name] = avguvals[name]

    #Add gravametric data
    [gravnames, gravunits, gravvals, gravunc, gravuvals] = io.load_constant_inputs(gravpath)
    for name in gravnames[1:]:
        allnames.append(name)
        allunits[name] = gravunits[name]
        allvals[name] = gravvals[name]
        allunc[name] = gravunc[name]
        alluvals[name] = gravuvals[name]

    #Add carbon balance emission data
    for name in cbnames[1:]:
        allnames.append(name)
        allunits[name] = cbunits[name]
        allvals[name] = cbval[name]
        allunc[name] = cbunc[name]
        alluvals[name] = cbmetric[name]

    #Add stack emission data
    for name in metricnames[1:]:
        allnames.append(name)
        allunits[name] = units[name]
        allvals[name] = val[name]
        allunc[name] = unc[name]
        alluvals[name] = metric[name]

    # print all output file
    io.write_constant_outputs(alloutputpath, allnames, allunits, allvals, allunc, alluvals)

    line = '\ncreated all output file:\n' + alloutputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_StackFlowMetricCalcs(inputpath, energypath, carbalpath, metricpath, logpath)
    