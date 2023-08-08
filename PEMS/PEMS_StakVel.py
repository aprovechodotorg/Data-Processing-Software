


import csv
import os

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import easygui
import LEMS_DataProcessing_IO as io
from datetime import datetime as dt
import math


def PEMS_StakVel(data, names, units, outputpath):

    #Define constants
    Tstd = float(293) #Standared temperature in Kelvin
    Pstd = float(101325) #Standard pressure in Pascals
    R = float(8.314) #Universal gas standard in m^3Pa/mol/K

    #Create dictionary of molecular weight. Variable names are dictionary keys. Weights in g/mol
    MW = {}
    MW['CO'] = float(28.01)
    MW['CO2'] = float(44.01)
    MW['H2O'] = float(18.02)
    MW['O2'] = float(32)
    MW['N2'] = float(28.01)

    #Diluted sample species used for stack MW calcs
    diluted_species = ['CO', 'CO2', 'H2O']  #O2 is undiluted and N2 is calculated by difference
    other_species = ['O2', 'N2'] #other species used for MW calcs
    stack_species = diluted_species + other_species

    metric = {}

    #############Define paths
    directory, filename = os.path.split(outputpath)
    datadirectory, testname = os.path.split(directory)

    ##############Load header
    headerpath = os.path.join(directory, testname + '_Header.csv')
    hnames,hunits,A,B,C,D,hconst = io.load_header(headerpath)

    ################################################################
    #H2O in diluted sample
    name = 'Psat' #satuation pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name] = []

    name = 'PH2O' #partial pressure of H2O
    names.append(name)
    units[name] = 'Pa'
    data[name] = []

    name = 'H2O' #H2O concentraction
    names.append(name)
    units[name] = 'ppm'
    data[name] = []

    #Vapor pressure of water from http://endmemo.com/chem/vaporpressurewater.php
    A = 8.07131
    B = 1730.63
    C = 233.426

    for n in range(len(data['RH'])):
        Tval = float(data['TC2'][n]) #Was Tsamp in R code

        RHval = data['RH'][n]

        Pambval = data['Pamb'][n]

        Psatval = pow(10, (A - B / (C + Tval))) / 0.0075 #1 Pa = 0.0075 mmHg
        PH2Oval = Psatval * RHval / 100 #Pa
        H2Oval = PH2Oval / Pambval * 1000000 #ppm

        data['Psat'].append(Psatval)
        data['PH2O'].append(PH2Oval)
        data['H2O'].append(H2Oval)

    ########################################################
    #Undiluted stack concentrations

    #conservation of mass
    #1: Cnoz * Qnoz * Qdil = Csampp * Qsamp
    #2: Qnoz + Qdil = Qsamp

    # Cnoz = concentration into the sampling nozzle (ppm)
    # Qnoz = sample nozzle flow rate (sccm)
    # Cdil = dilution air concentration (ppm)
    # Qdil = dilution air flow (sccm)
    # Csamp = diluted sample concentration (ppm)
    # Qsamp = diluted sample flow (sccm)

    for name in diluted_species: #for each diluted species
        dilname = name + 'bkg'
        stakname = name + 'stak'

        names.append(stakname)
        units[stakname] = '%vol'
        data[stakname] = []

        for n in range(len(data[name])):
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

            #Cnoz = (Csamp + Qsamp - Qdil) / Qnoz #not correct - units make no sense - recalculated below
            Cnoz = ((Csamp * Qsamp) - (Cdil * Qdil)) / Qnoz #ppm
            Cnoz = Cnoz / 1000000 * 100 #convert from ppm to %

            data[stakname].append(Cnoz)

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

        newoffset = easygui.enterbox(msg, title, offset) #save new vals from user input
        if newoffset:
            if newoffset != offset:
                #plt.clf()
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
        #ax1.set_ylabel('Pa')
        #ax1.set_xlabel('Time')
        #xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        #ax1.xaxis.set_major_formatter(xfmt)
        #ax1.legend()

        plt.show()

    data[name] = metric[name]
    
    ###############################################################
    #Recalcualte Stack Velocity

    name = 'StakVel'
    metric[name] = []
    units[name] = 'm/s'

    Kp = float(129)
    for n in range(len(data[name])):
        data[name][n] = float(data[name][n]) #convert data to float

        Pres1val = metric['Pitot'][n]

        Pambval = data['Pamb'][n]

        MWval = data['MW'][n]

        TCnozval = data['TCnoz'][n]

        if TCnozval == 'nan':
            newval = 'nan'
        else:
            TCnozval = data['TCnoz'][n]

            if Pres1val < 0:
                Pres1val = -Pres1val
                inside = Pres1val * (TCnozval + 273.15) / Pambval / MWval
                newval = -hconst['Cpitot(-)'] * Kp * math.sqrt(inside)
            else:
                print('TCnoz')
                print(TCnozval)
                print('Pamb')
                print(Pambval)
                print('MW')
                print(MWval)
                print(n)
                inside = Pres1val * (TCnozval + 273.15) / Pambval / MWval
                newval = hconst['Cpitot(-)'] * Kp * math.sqrt(inside)

            if abs(newval) < 0.0001: #Really small numbers give big uc vals
                newvale = 0

        metric[name].append(newval)
    data[name] = metric[name]


    ############################################################
    
    #Plot old and new stak vel
    fig, ax1 = plt.subplots()
    ax1.plot(datenums, data[name], marker='.', color='b', label='old Stakvel')
    ax1.plot(datenums, metric[name], marker='.', color='r', label='new Stakvel')
    ax1.set_ylabel('m/s')
    ax1.set_xlabel('Time')
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    ax1.xaxis.set_major_formatter(xfmt)
    ax1.legend()
    plt.show()


    velpath = os.path.join(directory, testname + '_RawDataStakCorrected.csv')

    io.write_timeseries(velpath, names, units, data)

    line = ('created: ' + velpath)
    print(line)

    #Write values into a file
    io.write_timeseries(outputpath, names, units, data)
    
    return(data, names, units)



