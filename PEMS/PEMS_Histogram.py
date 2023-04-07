import os
import csv
import numpy as np
import uncertainties as unumpy
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io

def PEMS_Histogram(inputpath, energypath, gravinputpath, empath, outputpath):
    #################################################

    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)
    '''fig = plt.figure()
    ax = fig.add_subplot(111)
    for num, n in enumerate(data['PM']):
        data['PM'][num] = float((n)/0.951170131) #MSC
    numbins = int(max(data['PM'])/100)
    ax.hist(data['PM'], edgecolor='red', bins = numbins, density = True)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(data['seconds'], data['PM'])
    '''
    emissions = ['CO', 'COhi', 'CO2', 'CO2hi', 'PM']  # emission species that will get metric calculations

    for em in emissions:
        try:
            data[em]
        except:
            emissions.remove(em)
    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    # load grav metrics data file
    [gravnames, gravunits, gravval, gravunc, gravmetric] = io.load_constant_inputs(gravinputpath)

    # load emissions data file
    [emnames, emunits, emval, emunc, emmetric] = io.load_constant_inputs(empath)

    #load test averages data file
    #[avenames,aveunits,aveval,aveunc,ave]=io.load_constant_inputs(aveinputpath)
    metric = {}

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

    name = 'ER_PM_heat'
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['ER_PM']:
        values.append(val*60/1000)
    metric[name] = values
    data[name] = values

    volflowPM = emmetric['ER_PM_heat'].nominal_value / gravmetric['PMconc_tot'].nominal_value  # m^3/hr

    name = 'Realtime_conc_PM'
    names.append(name)
    units[name] = 'mg/m^3'
    values = []
    for val in data['PM']:
        values.append(val / gravmetric['MSC'].nominal_value)  # mg/m^3 realtime concentration
    metric[name] = values
    data[name] = values

    name = 'PM_flowrate'
    names.append(name)
    units[name] = 'g/hr'
    values = []
    for val in metric['Realtime_conc_PM']:
        values.append((val * volflowPM) / 1000)
    metric[name] = values
    data[name] = values

    avgPMflow = sum(metric['PM_flowrate']) / len(metric['PM_flowrate'])
    avgERPM = sum(metric['ER_PM_heat']) / len(metric['ER_PM_heat'])

    print('Average Carbon Balance ER PM ISO')
    print(emmetric['ER_PM_heat'].nominal_value)
    print('Average Carbon Balance ER PM Realtime')
    print(avgERPM)
    print('Average Flowrate ER PM')
    print(avgPMflow)


    fig, axs = plt.subplots(3, 2)

    y = []
    for val in metric['ER_PM_heat']:
            y.append(val)
    axs[0, 0].plot(data['seconds'], y)
    axs[0, 0].set_title('Realtime Carbon Balance ER PM')
    axs[0, 0].set(ylabel='Emission Rate(g/hr)', xlabel='Time(s)')

    # numbins = int(len(y) / 200)
    # numbins = max(y)
    numbins = 12

    axs[1, 0].hist(y, edgecolor='red', bins=numbins)
    # axs[1, 0].set_title('Histogram Carbon Balance ER PM')
    axs[1, 0].set(ylabel='Frequency', xlabel='Emission Rate(g/hr)')

    axs[2, 0].hist(y, edgecolor='red', bins=numbins, density=True)
    axs[2, 0].set(xlabel='Emission Rate(g/hr)')
    # axs[2, 0].set_title('Normalized Histogram CB ER PM')

    y = []
    for val in metric['PM_flowrate']:
        y.append(val)

    axs[0, 1].plot(data['seconds'], y)
    axs[0, 1].set_title('Realtime Flowrate ER PM')
    axs[0, 1].set(ylabel='Emission Rate(g/hr)')

    axs[1, 1].hist(y, edgecolor='red', bins=numbins)
    # axs[1, 1].set_title('Histogram Flowrate ER PM')
    axs[1, 1].set(xlabel='Emission Rate(g/hr)', ylabel='Frequency')

    axs[2, 1].hist(y, edgecolor='red', bins=numbins, density=True)
    axs[2, 1].set(xlabel='Emission Rate(g/hr)')
    # axs[2, 1].set_title('Normalized Histogram F ER PM')
    plt.show()

    io.write_timeseries(outputpath, names, units, data)


    #for num, n in enumerate(data['PM']):
        #data['PM'][num] =float((n*0.1922))*60/1000000 #grams/ per hour.
    #fig = plt.figure()
    #ax = fig.add_subplot(111)
    #ax.plot(data['seconds'], data['PM'])
    #plt.show()
