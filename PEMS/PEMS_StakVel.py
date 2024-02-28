
import csv
import os
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import easygui
import LEMS_DataProcessing_IO as io
from datetime import datetime as dt
import math
from easygui import *


def PEMS_StakVel(data, names, units, outputpath, savefig):

    # Define constants
    Tstd = float(293)  # Standared temperature in Kelvin
    Pstd = float(101325)  # Standard pressure in Pascals
    R = float(8.314)  # Universal gas standard in m^3Pa/mol/K

    # Create dictionary of molecular weight. Variable names are dictionary keys. Weights in g/mol
    MW = {}
    MW['CO'] = float(28.01)
    MW['CO2'] = float(44.01)
    MW['H2O'] = float(18.02)
    MW['O2'] = float(32)
    MW['N2'] = float(28.01)

    # Diluted sample species used for stack MW calcs
    diluted_species = ['CO', 'CO2', 'H2O']  # O2 is undiluted and N2 is calculated by difference
    other_species = ['O2', 'N2']  # other species used for MW calcs
    stack_species = diluted_species + other_species

    metric = {}

    #############Define paths
    directory, filename = os.path.split(outputpath)
    datadirectory, testname = os.path.split(directory)

    ##############Load header
    headerpath = os.path.join(directory, testname + '_Header.csv')
    hnames ,hunits ,A ,B ,C ,D ,hconst = io.load_header(headerpath)

    ################################################################
    # H2O in diluted sample
    name = 'Psat'  # satuation pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name] = []

    name = 'PH2O'  # partial pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name] = []

    name = 'H2O'  # H2O concentraction
    names.append(name)
    units[name] = 'ppm'
    data[name] = []

    # Vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    A = 8.07131
    B = 1730.63
    C = 233.426

    for n in range(len(data['RH'])):
        Tval = float(data['COtemp'][n])  # Was Tsamp in R code

        RHval = data['RH'][n]

        Pambval = data['Pamb'][n]

        Psatval = pow(10, (A - B / (C + Tval))) / 0.0075  # 1 Pa = 0.0075 mmHg
        PH2Oval = Psatval * RHval / 100  # Pa
        H2Oval = PH2Oval / Pambval * 1000000  # ppm

        data['Psat'].append(Psatval)
        data['PH2O'].append(PH2Oval)
        data['H2O'].append(H2Oval)

    ########################################################
    # Undiluted stack concentrations

    ### Calculate dilution ratios ###

    # calculate dilution ratio from flows ###
    # this is different than the firmware calculation (no F2Flow or TAPflow)
    # unless F2Flow and TAPflow are always = 0
    name = 'DilRat_Flow'
    names.append(name)
    units[name] = units['DilRat']
    data[name ] =[] x=[]
    for n,val in enumerate(data['time']):
        try:
            dilrat = 1
        except:
            dilrat = 1
        data[name].append(dilrat)
        x.append(n)

    print('calculated dilution ratio from flows')

    #########calculate dilution ratio from CO2 ######################
    name = 'DilRat_CO2'
    names.append(name)
    units[name] = units['DilRat']
    data[name]=[]
    x=[]
    for n,val i n enumerate(data['time']):
        try:
            dilrat = (data['CO2hi'][n]+data [ 'CO2hi_bkg'][n]-data [ 'CO2'][n]-data [ 'CO2_bkg'][n])/(dat a ['CO2'][n])
        except:
            dilrat = 1
        data[name].append(dilrat)
        x.append(n)

    n = 100  # boxcar length
    name = 'DilRat_CO2_smooth'
    names.append(name)
    units[name]=unit s ['DilRat']
    data[name] = []
    for m,val i n enumerate(data['DilRat_CO2']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['DilRat_CO2'][m-n:m]
            else:
                boxcar = data['DilRat_CO2'][:m]
            newval=sum( b oxcar)/len( b oxcar)
        data[name].append(newval)

    print('calculated dilution ratio from CO2')
    #########calculate dilution ratio from CO ######################
    name = 'DilRat_CO'
    names.append(name)
    units[name] = units['DilRat']
    data[name]=[]
    for n,val i n enumerate(data['time']):
        try:
            dilrat = (data['COhi'][n]+data [ 'COhi_bkg'][n]-data [ 'CO'][n]-data [ 'CO_bkg'][n])/(dat a ['CO'][n])
        except:
            dilrat = 1
        data[name].append(dilrat)

    n = 100  # boxcar length
    name = 'DilRat_CO_smooth'
    names.append(name)
    units[name]=unit s ['DilRat']
    data[name] = []
    for m,val i n enumerate(data['DilRat_CO']):
        if m==0:
            newval=val
        else:
            if m >= n:
                boxcar = data['DilRat_CO'][m-n:m]
            else:
                boxcar = data['DilRat_CO'][:m]
            newval=sum( b oxcar)/len( b oxcar)
        data[name].append(newval)

    print('calculated dilution ratio from CO')
    #################################################
    '''
    #calculate dilution ratio from constant

    name = 'DilRat_Firmware_Const'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = []
    const = metric['DilRat'] 
    for m,val in enumerate(data['DilRat']):
        data[name].append(const)  

    name = 'DilRat_Flow_Const'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = []
    const = sum(metric['DilRat_Flow'] 
    for m,val in enumerate(data['DilRat']):
        data[name].append(const)  

    name = 'DilRat_CO2_Const'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = []
    const = metric['DilRatCO2']
    for m,val in enumerate(data['DilRat']):
        data[name].append(const)  

    name = 'DilRat_CO_Const'
    names.append(name)
    units[name]=units['DilRat']  
    data[name] = []
    const = metric['DilRatCO'] 
    for m,val in enumerate(data['DilRat']):
        data[name].append(const)  

    print('calculated dilution ratio from constant')
    '''
    ##########################################################

    # Plot and choose a dilution ratio
    name = 'dateobjects'
    units[name] = 'date'
    # names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    try:
        for n, val in enumerate(data['time']):
            dateobject = dt.strptime(val, '%Y%m%d  %H:%M:%S')  # Convert time to readble datetime object
            data[name].append(dateobject)
    except:  # some files have different name convention
        for n, val in enumerate(data['time_test']):
            dateobject = dt.strptime(val, '%Y%m%d  %H:%M:%S')
            data[name].append(dateobject)

    name='dat e numbers'
    units[name]='dat e '
    # names.append(name)
    datenums=matp l otlib.dates.date2num(data['dateobjects'])
    datenums=list ( datenums)  # convert ndarray to a list in order to use index function
    data['datenumbers']=date n ums

    plt.ion()
    f1, (ax1) = plt.subplots()
    ax1.plot(data['datenumbers'], data['DilRat'], color='red', label='From Firmware')
    # ax1.plot(data['datenumbers'], dilratCO, color='blue', label='From CO')
    # ax1.plot(data['datenumbers'], dilratCO2, color='green', label='From CO2')

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    # plt.savefig(savefig, bbox_inches='tight')
    # plt.show()

    running = 'fun'
    # default dilrat is firmware dilrat
    dilrat = data['DilRat']

    while running == 'fun':
        # Select which dilution ratio to use
        text = "Select a dilution ratio method"
        title = 'Gitrdone'
        choices = ['From firmware', 'From CO', 'From CO2']
        output = choicebox(text, title, choices)

        if output == 'From firmware':
            dilrat = data['DilRat']  # ge   dilution ratio from output of sensor box
            running = 'not fun'
            plt.ioff()
            plt.close()
        # SUDO CODE FOR OTHER DILRAT
        # elif output == 'From CO':
        # dilrat = dilratCO
        # running = 'not fun'
        # elif output == 'From CO2':
        # dilrat = dilratCO2
        # running == 'not fun'

    plt.ioff()
    plt.close

    # conservation of mass
    # 1: Cnoz * Qnoz * Qdil = Csampp * Qsamp
    # 2: Qnoz + Qdil = Qsamp

    # Cnoz = concentration into the sampling nozzle (ppm)
    # Qnoz = sample nozzle flow rate (sccm)
    # Cdil = dilution air concentration (ppm)
    # Qdil = dilution air flow (sccm)
    # Csamp = diluted sample concentration (ppm)
    # Qsamp = diluted sample flow (sccm)

    for name in diluted_species:  # fo   each diluted species
        dilname = name + 'bkg'
        stakname = name + 'stak'

        names.append(stakname)
        units[stakname] = '%vol'
        data[stakname] = []

        for n in range(len(data[name])):
            '''
            Csamp = data[name][n]

            Qf1 = data['F1Flow'][n]

            Qf2 = data['F2Flow'][n]

            Qgas = data['SampFlow'][n] #GasFlow in R code

            try:
                Qtap = data['TAPflow'][n]
            except:
                Qtap = 'nan'

            if Qtap == 'nan':
                Qtap = 0
            else:
                Qtap = float(Qtap)

            Qsamp = Qf1 + Qgas #F2 and TAPflow are not connected to the sample train
            #Qsamp = 1500

            try:
                Cdil = data[dilname][n]
            except:
                Cdil = 0 #if the dilution air concentration was not measured, assume 0

            Qdil = data['DilFlow'][n]
            #Qdil = 1300

            Qnoz = Qsamp - Qdil

            Cnoz = (Csamp * Qsamp - Cdil * Qdil) / Qnoz #ppm

            Cnoz = Cnoz / 1000000 * 100 #convert from ppm to %

            data[stakname].append(Cnoz)

            stak_con = (dilrat[n] + 1) * data[name][n] / 1000000 * 100
            data[stakname].append(stak_con)

    #O2 is measured as undiluter stack conc dry basis (%)
    #convert to wet basia
    name = 'O2stak'
    names.append(name)
    units[name] = '%vol'
    data[name] = []

    for n in range(len(data['O2'])):
        O2db = data['O2'][n]

        mc = data['H2Ostak'][n] / 100

        O2wb = O2db * (1 - mc)

        data[name].append(O2wb)

    #balanca stack composition is nitrogen
    name = 'N2stak'
    names.append(name)
    units[name] = '%vol'
    data[name] = []

    for n in range(len(data['O2'])):
        val = 100
        for name in diluted_species:
            stakname = name + 'stak'
            val = val - data[stakname][n]

        val = val - data['O2stak'][n]

        data['N2stak'].append(val)

    #########################################################
    #flu gas molecular weight
    name = 'MW'
    names.append(name)
    units[name] = 'g/mol'
    data[name] = []

    for n in range(len(data['O2'])):
        mw = 0

        for name in stack_species:
            stakname = name + 'stak'
            mw = mw + MW[name] * data[stakname][n] / 100

        data['MW'].append(mw)

    ###############################################################
    #Zero the pitot pressure

    #Convert datetime to date numbers for reading/plotting
    dateobjects = []
    for n, val in enumerate(data['time']):
        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        dateobjects.append(dateobject)

    datenums = matplotlib.dates.date2num(dateobjects)
    datenums = list(datenums) #convert ndarray to a list in order to use index function

    name = 'Pitot' #Pres1 in R code
    for n in range(len(data[name])):
        data[name][n] = float(data[name][n]) #convert data series to floats

    #smooth with moving average
    metric[name] = []
    window_size = int(500)

    for n in range(len(data[name])):
        start = int(max(0, n - (window_size/2)))
        end = int(min(len(data[name]), n + (window_size/2) + 1))
        val = sum(data[name][start:end]) / (end - start)
        metric[name].append(val)

    plt.ion()

    fig, ax1 = plt.subplots()
    ax1.plot(datenums, data[name], marker='.', color='b', label='Original Pitot')
    ax1.plot(datenums, metric[name], marker='.', color='r', label='Smoothed Pitot (window size: ' + str(window_size) + ')')
    ax1.set_ylabel('Pa')
    ax1.set_xlabel('Time')
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    ax1.legend()

    running = 'fun'
    while running == 'fun':
        # GUI box to edit input times
        zeroline = 'Enter window size for smoothing\n'
        firstline = 'A larger window size will result in a smoother line\n'
        secondline = 'Click OK to confirm entered values\n'
        thirdline = 'Click Cancel to exit\n'
        msg = zeroline + firstline + secondline + thirdline
        title = "Gitrdone"

        newwindow = easygui.enterbox(msg, title, window_size) #save new vals from user input
        if newwindow:
            if newwindow != window_size:
                for n in range(len(ax1.lines)):
                    plt.Artist.remove(ax1.lines[0])
                #plt.clf()
                newwindow = int(newwindow)
                window_size = newwindow
        else:
            running = 'not fun'
            savefig = os.path.join(savefig + '_smoothedpitot.png')
            plt.savefig(savefig, bbox_inches='tight')
            plt.ioff()
            plt.close()

        metric[name] = []
        for n in range(len(data[name])):
            start = int(max(0, n - (window_size / 2)))
            end = int(min(len(data[name]), n + (window_size / 2) + 1))
            val = sum(data[name][start:end]) / (end - start)
            metric[name].append(val)

        ax1.plot(datenums, data[name], marker='.', color='b', label='Original Pitot')
        ax1.plot(datenums, metric[name], marker='.', color='r', label='Smoothed Pitot (window size: ' + str(window_size) + ')')
        plt.show()
    '''
    offset = float(0)

    plt.ion()

    metric[name] = []

    for n in range(len(data[name])):
        val = float(data[name][n]) + offset
        metric[name].append(val)

    fig, ax1 = plt.subplots()
    ax1.plot(datenums, data[name], marker='.', color='b', label='old Pres1')
    ax1.plot(datenums, metric[name], marker='.', color='r', label='new Pres1')
    ax1.set_ylabel('Pa')
    ax1.set_xlabel('Time')
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    ax1.legend()

    running = 'fun'
    while running == 'fun':

        # GUI box to edit input times
        zeroline = 'Enter offset for Pitot\n'
        firstline = 'Click OK to confirm entered values\n'
        secondline = 'Click Cancel to exit\n'
        msg = zeroline + firstline + secondline
        title = "Gitrdone"

        newoffset = easygui.enterbox(msg, title, offset)  # sa  e new vals from user input
        if newoffset:
            if newoffset != offset:
                # plt.clf()
                newoffset = float(newoffset)
                offset = newoffset
        else:
            running = 'not fun'
            plt.ioff()
            plt.close()

        metric[name] = []
        for n in range(len(data[name])):
            val = float(data[name][n]) + offset
            metric[name].append(val)

        ax1.plot(datenums, data[name], marker='.', color='b', label='old Pres1')
        ax1.plot(datenums, metric[name], marker='.', color='r', label='new Pres1')
        # ax1.set_ylabel('Pa')
        # ax1.set_xlabel('Time')
        # xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        # ax1.xaxis.set_major_formatter(xfmt)
        # ax1.legend()

        plt.show()

    data[name] = metric[name]

    ###############################################################
    # Choose TC2 or TCnoz
    name = 'dateobjects'
    units[name] = 'date'
    # names.append(name) #don't add to print list because time object cant print to csv
    data[name] = []
    try:
        for n,val i n enumerate(data['time']):
            dateobject=dt.s t rptime(val, '%Y%m%d  %H:%M:%S')  # Co  vert time to readble datetime object
            data[name].append(dateobject)
    except:  # so  e files have different name convention
        for n,val i n enumerate(data['time_test']):
            dateobject=dt.s t rptime(val, '%Y%m%d  %H:%M:%S')
            data[name].append(dateobject)

    name='dat e numbers'
    units[name]='dat e '
    # names.append(name)
    datenums=matp l otlib.dates.date2num(data['dateobjects'])
    datenums=list ( datenums)  # convert ndarray to a list in order to use index function
    data['datenumbers']=date n ums

    # check which TC channels exist
    channel = 1
    TCchan = []
    while channel <= 8:  # up  to 8 TC channels
        try:
            name = 'TC' + str(channel)
            test = data[name]
            TCchan.append(name)
            channel += 1
        except:
            channel += 1

    plt.ion()
    f1, (ax1) = plt.subplots()
    ax1.plot(data['datenumbers'], data['TCnoz'], color='red', label='TCnoz')
    for chan in TCchan:
        ax1.plot(data['datenumbers'], data[chan], label=chan)
    ax1.set_ylabel('Temperature (C)')

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    # plt.savefig(savefig, bbox_inches='tight')
    # plt.show()

    running = 'fun'
    # default TC to TCnoz
    TC = data['TCnoz']

    while running == 'fun':
        # Ask user which one they want
        text = 'Select best temperature channel'
        title = 'Gitrdone'
        TCchan.insert(0, 'TCnoz')
        choices = TCchan
        output = choicebox(text, title, choices)

        if output:
            TC = data[output]
            running = 'not fun'

    savefig, end = savefig.rsplit('_', 1)
    savefig = os.path.join(savefig + '_TCchannels.png')
    plt.savefig(savefig, bbox_inches='tight')
    plt.ioff()
    plt.close()

    # Recalcualte Stack Velocity

    name = 'StakVel'
    metric[name] = []
    units[name] = 'm/s'

    Kp = float(129)
    for n in range(len(data[name])):
        data[name][n] = float(data[name][n])  # co  vert data to float

        Pres1val = metric['Pitot'][n]

        Pambval = data['Pamb'][n]

        MWval = data['MW'][n]

        TCnozval = TC[n]

        if TCnozval == 'nan':
            newval = 'nan'
        else:
            TCnozval = TC[n]

            if Pres1val < 0:
                Pres1val = -Pres1val
                inside = Pres1val * (TCnozval + 273.15) / Pambval / MWval
                newval = -hconst['Cpitot(-)'] * Kp * math.sqrt(inside)
            else:
                inside = Pres1val * (TCnozval + 273.15) / Pambval / MWval
                newval = hconst['Cpitot(-)'] * Kp * math.sqrt(inside)

            if abs(newval) < 0.0001:  # Re  lly small numbers give big uc vals
                newvale = 0

        metric[name].append(newval)

    ############################################################

    # Plot old and new stak vel
    fig, ax1 = plt.subplots()
    ax1.plot(datenums, data[name], marker='.', color='b', label='old Stakvel')
    ax1.plot(datenums, metric[name], marker='.', color='r', label='new Stakvel')
    ax1.set_ylabel('m/s')
    ax1.set_xlabel('Time')
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    ax1.legend()
    plt.show()
    savefig, end = savefig.rsplit('_', 1)
    savefig = os.path.join(savefig + '_stakvelocity.png')
    plt.savefig(savefig, bbox_inches='tight')

    data[name] = metric[name]

    velpath = os.path.join(directory, testname + '_RawDataStakCorrected.csv')

    io.write_timeseries(velpath, names, units, data)

    line = ('created: ' + velpath)
    print(line)

    # Write values into a file
    io.write_timeseries(outputpath, names, units, data)

    return(data , names, units, TC, dilrat)
