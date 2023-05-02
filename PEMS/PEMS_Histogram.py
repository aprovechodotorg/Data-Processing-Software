import os
import csv
import math
import numpy as np
from scipy.signal import savgol_filter
import uncertainties as unumpy
import matplotlib
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg
#from PEMS_SubtractBkg import makeTimeObjects
#from PEMS_SubtractBkg import findIndices
#from PEMS_SubtractBkg import definePhaseData
#from PEMS_SubtractBkg import definePhases

def PEMS_Histogram(inputpath, energypath, gravinputpath, empath, periodpath, outputpath, averageoutputpath, averagecalcoutputpath):
    #################################################

    flow = 'F1Flow'

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
        if float(val) < 0.0:
            values.append(0.0)
        else:
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

#####################################################################
    #Volumetric flow rate/stack flow rate for PM
    #Currently not handling bkg
    try:
        name = 'Stak_PM'
        names.append(name)
        units[name] = 'g/m^3'
        values = []
        for n, val in enumerate(data['DilFlow']):
            stak = gravmetric['PMconc_tot'] / (1 - (val / (data['SampFlow'][n] + data[flow][n])))
            values.append(stak / 1000)
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
            values.append(flow)
        data[name] = values
        metric[name] = values

        name = 'ER_stak'
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

    avgPMflow = sum(metric['PM_flowrate']) / len(metric['PM_flowrate'])
    avgERPM = sum(metric['ER_PM_heat']) / len(metric['ER_PM_heat'])
    try:
        avgERstak = sum(metric['ER_stak']) / len(metric['ER_stak'])
    except:
        pass


    '''
    print('Average Carbon Balance ER PM ISO')
    print(emmetric['ER_PM_heat'].nominal_value)
    print('Average Carbon Balance ER PM Realtime')
    print(avgERPM)
    print('Average Flowrate ER PM')
    print(avgPMflow)
    try:
        print('Average Stak Flowrate')
        print(avgERstak.n)
    except:
        pass
    '''


    if 'ER_stak' in names:
        i = 3
    else:
        i = 2

    if i == 2:
        try:
            names.remove('Stak_PM')
            names.remove('StakFlow')
            names.remove('ER_stak')
        except:
            pass
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

    #################################################################
    # Defining averaging period for analysis
    # [enames, eunits, eval, eunc, emetric]
    # Check if average period times file exists
    if os.path.isfile(periodpath):
        line = '\nAverage Period time file already exists:'
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
        line = '\n Created averaging times input file:'
        print(line)
        print(periodpath)

    ################################################################
    # Read in averaging period start and end times
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

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
#################################################################
    #Create period averages
    #total_seconds = avgdata['seconds_test'][-1] - avgdata['seconds_test'][0]
    calcavg = {}
    unc={}
    uval={}
    for name in avgnames:
        #Try creating averages of values, nan value if can't
        try:
            calcavg[name] = sum(avgdata[name]) / len(avgdata[name])
        except:
            calcavg[name] = 'nan'
        ####Currently not handling uncertainties
        unc[name] = ''
        uval[name] = ''

    #add start and end time for reference
    for n, name in enumerate(titlenames):
        avgnames.insert(n, name)
        calcavg[name] = eval[name]
        avgunits[name] = 'yyyymmdd hh:mm:ss'

    #Print averages
    line = 'Average Carbon Balance ER PM ISO (Full dataset) ' + str(emmetric['ER_PM_heat'].nominal_value) + '\n'
    print(line)
    line = ('Average Carbon Balance ER PM Realtime (Averaging Period) ') + str(calcavg['ER_PM_heat_test']) + '\n'
    print(line)
    line = ('Average Flowrate ER PM (Averaging Period) ') + str(calcavg['PM_flowrate_test']) + '\n'
    print(line)
    try:
        line = 'Average Stak Flowrate ER PM (Averaging Period) ' + str(calcavg['ER_stak_test']) + '\n'
        print(line)
    except:
        pass

    #create file of averages for averaging period
    io.write_constant_outputs(averagecalcoutputpath, avgnames, avgunits, calcavg, unc, uval)

###############################################################
    plt.ion() #Turn on interactive plot mode
    fig, axs = plt.subplots(1, i) #plot 2-3 plots depnding on number calculated ERs

    y = []
    #Remove 0s
    for val in metric['ER_PM_heat']:
        try:
            if float(val) < 0.0:
                y.append(0.0)
            else:
                y.append(val)
        except:
            y.append(val)

    #y_smooth = savgol_filter(y, 200, 3)
    #Smoothing needs to happen sooner for graphs to match
    y_smooth = y

    yavg = []
    for val in avgdata['ER_PM_heat_test']:
        try:
            if float(val) < 0.0:
                yavg.append(0.0)
            else:
                yavg.append(val)
        except:
            yavg.append(val)
    #yavg_smooth = savgol_filter(yavg, 200, 3)
    yavg_smooth = yavg

    #Plot full test and averaging period in same subplot
    axs[0].plot(data['datenumbers'], y_smooth, color = 'blue')
    axs[0].plot(avgdatenums['test'], yavg_smooth, color = 'red')
    axs[0].set_title('Realtime Carbon Balance ER PM')
    axs[0].set(ylabel='Emission Rate(g/hr)', xlabel='Time(s)')

    # numbins = int(len(y) / 200)
    # numbins = max(y)
    #numbins = int(max(y_smooth))*2

    '''
    axs[1, 0].hist(y_smooth, edgecolor='red', bins=numbins)
    # axs[1, 0].set_title('Histogram Carbon Balance ER PM')
    axs[1, 0].set(ylabel='Frequency', xlabel='Emission Rate(g/hr)')

    axs[2, 0].hist(y_smooth, edgecolor='red', bins=numbins, density=True)
    axs[2, 0].set(xlabel='Emission Rate(g/hr)')
    # axs[2, 0].set_title('Normalized Histogram CB ER PM')
    '''

    y = []
    for val in metric['PM_flowrate']:
        y.append(val)

    #y_smooth = savgol_filter(y, 1200, 3)
    y_smooth = y

    yavg = []
    for val in avgdata['PM_flowrate_test']:
        try:
            if float(val) < 0.0:
                yavg.append(0.0)
            else:
                yavg.append(val)
        except:
            yavg.append(val)
    #yavg_smooth = savgol_filter(yavg, 200, 3)
    yavg_smooth = yavg

    #numbins = int(max(y_smooth)) * 2

    #plot full data and averaging period in same subplot
    axs[1].plot(data['datenumbers'], y_smooth, color='blue')
    axs[1].plot(avgdatenums['test'], yavg_smooth, color = 'red')
    axs[1].set_title('Realtime Flowrate ER PM')
    axs[1].set(ylabel='Emission Rate(g/hr)')

    '''
    axs[1, 1].hist(y_smooth, edgecolor='red', bins=numbins)
    # axs[1, 1].set_title('Histogram Flowrate ER PM')
    axs[1, 1].set(xlabel='Emission Rate(g/hr)', ylabel='Frequency')

    axs[2, 1].hist(y_smooth, edgecolor='red', bins=numbins, density=True)
    axs[2, 1].set(xlabel='Emission Rate(g/hr)')
    # axs[2, 1].set_title('Normalized Histogram F ER PM')
    '''

    #if there's a third ER method, plot it too
    if i == 3:
        y = []
        for val in metric['ER_stak']:
            y.append(val.n)
        #y_smooth = savgol_filter(y, 100, 3) #least squarures to regress a small window onto polynomial, poly to estimate point in center of window. Window size 51, poly order 3
        y_smooth = y

        yavg = []
        for val in avgdata['ER_stak_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)
        #yavg_smooth = savgol_filter(yavg, 200, 3)
        yavg_smooth = yavg

        axs[2].plot(data['datenumbers'], y_smooth, color='blue')
        axs[2].plotplot(avgdatenums['test'], yavg_smooth, color='red')
        axs[2].set(ylabel='Emission Rate(g/hr)', title='Stak Velocity Emission Rate')
        '''
        numbins = int(max(y_smooth))*2

        

        axs[1, 2].hist(y_smooth, edgecolor='red', bins=numbins)
        axs[1, 2].set(xlabel='Emission Rate(g/hr)', ylabel='Frequency')

        axs[2, 2].hist(y_smooth, edgecolor='red', bins=numbins, density=True)
        axs[2, 2].set(xlabel='Emission Rate(g/hr)')
        '''
    #Format x axis to readable times
    xfmt = matplotlib.dates.DateFormatter('%H:%M:S') #pull and format time data
    for i, ax in enumerate(fig.axes):
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
    #plt.show()
##############################################################
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
        else:
            running = 'not fun'
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
        #################################################################
        # Create period averages
        #total_seconds = avgdata['seconds_test'][-1] - avgdata['seconds_test'][0]
        calcavg = {}
        unc = {}
        uval = {}
        for name in avgnames:
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
        line = 'Average Carbon Balance ER PM ISO (Full dataset) ' + str(emmetric['ER_PM_heat'].nominal_value) + '\n'
        print(line)
        line = 'Average Carbon Balance ER PM Realtime (Averaging period) ' + str(calcavg['ER_PM_heat_test']) + '\n'
        print(line)
        line = 'Average Flowrate ER PM (Averaging period) ' + str(calcavg['PM_flowrate_test']) + '\n'
        print(line)
        try:
            line = 'Average Stak Flowrate ER PM (Averaging period) ' + str(calcavg['ER_stak_test']) + '\n'
            print(line)
        except:
            pass

        #Record updated averaged
        io.write_constant_outputs(averagecalcoutputpath, avgnames, avgunits, calcavg, unc, uval)

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
        y = []
        for val in metric['ER_PM_heat']:
            try:
                if float(val) < 0.0:
                    y.append(0.0)
                else:
                    y.append(val)
            except:
                y.append(val)

        #y_smooth = savgol_filter(y, 200, 3)
        y_smooth = y

        yavg = []
        for val in avgdata['ER_PM_heat_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)
        #yavg_smooth = savgol_filter(yavg, 200, 3)
        yavg_smooth = yavg

        axs[0].plot(data['datenumbers'], y_smooth, color = 'blue')
        axs[0].plot(avgdatenums['test'], yavg_smooth, color = 'red')
        axs[0].set_title('Realtime Carbon Balance ER PM')
        axs[0].set(ylabel='Emission Rate(g/hr)', xlabel='Time(s)')

        # numbins = int(len(y) / 200)
        # numbins = max(y)
        numbins = int(max(y_smooth))*2

        '''
        axs[1, 0].hist(y_smooth, edgecolor='red', bins=numbins)
        # axs[1, 0].set_title('Histogram Carbon Balance ER PM')
        axs[1, 0].set(ylabel='Frequency', xlabel='Emission Rate(g/hr)')
    
        axs[2, 0].hist(y_smooth, edgecolor='red', bins=numbins, density=True)
        axs[2, 0].set(xlabel='Emission Rate(g/hr)')
        # axs[2, 0].set_title('Normalized Histogram CB ER PM')
        '''

        y = []
        for val in metric['PM_flowrate']:
            y.append(val)

        #y_smooth = savgol_filter(y, 1200, 3)
        y_smooth = y

        yavg = []
        for val in avgdata['PM_flowrate_test']:
            try:
                if float(val) < 0.0:
                    yavg.append(0.0)
                else:
                    yavg.append(val)
            except:
                yavg.append(val)
        #yavg_smooth = savgol_filter(yavg, 200, 3)
        yavg_smooth = yavg

        numbins = int(max(y_smooth)) * 2

        axs[1].plot(data['datenumbers'], y_smooth, color='blue')
        axs[1].plot(avgdatenums['test'], yavg_smooth, color = 'red')
        axs[1].set_title('Realtime Flowrate ER PM')
        axs[1].set(ylabel='Emission Rate(g/hr)')

        '''
        axs[1, 1].hist(y_smooth, edgecolor='red', bins=numbins)
        # axs[1, 1].set_title('Histogram Flowrate ER PM')
        axs[1, 1].set(xlabel='Emission Rate(g/hr)', ylabel='Frequency')
    
        axs[2, 1].hist(y_smooth, edgecolor='red', bins=numbins, density=True)
        axs[2, 1].set(xlabel='Emission Rate(g/hr)')
        # axs[2, 1].set_title('Normalized Histogram F ER PM')
        '''

        if i == 3:
            y = []
            for val in metric['ER_stak']:
                y.append(val.n)
            #y_smooth = savgol_filter(y, 100, 3) #least squarures to regress a small window onto polynomial, poly to estimate point in center of window. Window size 51, poly order 3
            y_smooth = y

            yavg = []
            for val in avgdata['ER_stak_test']:
                try:
                    if float(val) < 0.0:
                        yavg.append(0.0)
                    else:
                        yavg.append(val)
                except:
                    yavg.append(val)
            #yavg_smooth = savgol_filter(yavg, 200, 3)
            yavg_smooth = yavg

            axs[2].plot(data['datenumbers'], y_smooth, color='blue')
            axs[2].plotplot(avgdatenums['test'], yavg_smooth, color='red')
            axs[2].set(ylabel='Emission Rate(g/hr)', title='Stak Velocity Emission Rate')
        #fig.canvas.draw()
        plt.show()

    #Record full test outputs
    io.write_timeseries(outputpath, names, units, data)


    #for num, n in enumerate(data['PM']):
        #data['PM'][num] =float((n*0.1922))*60/1000000 #grams/ per hour.
    #fig = plt.figure()
    #ax = fig.add_subplot(111)
    #ax.plot(data['seconds'], data['PM'])
    #plt.show()


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