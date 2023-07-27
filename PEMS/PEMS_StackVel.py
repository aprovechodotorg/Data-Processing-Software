


import csv
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import easygui
import LEMS_DataProcessing_IO as io

#########################################
#Use RawData_Shifted
inputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_RawData_Shifted.csv'
ucpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_UCInputs.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_RawData_Stackvelcorrected.csv'
def PEMS_StackVel(inputpath, ucpath, outputpath): #NOT NEEDED???

    #Define constants
    Tstd = float(293) #Standared temperature in Kelvin
    Pstd = float(101325) #Standard pressure in Pascals
    R = float(8.314) #Universal gas standard in m^3Pa/mol/K

    #Create dictionary of molecular weight. Variable names are dictionary keys. Weights in g/mol
    MW = {}
    MW['CO'] = float(28.01)
    MW['CO2'] = float(44.01)
    MW['H20'] = float(18.02)
    MW['O2'] = float(32)
    MW['N2'] = float(28.01)

    #Diluted sample species used for stack MW calcs
    diluted_species = ['CO', 'CO2', 'H2O']  #O2 is undiluted and N2 is calculated by difference
    other_species = ['O2', 'N2'] #other species used for MW calcs
    stack_species = diluted_species + other_species

    #Create empty dictionary for calculations
    rel_uc = {}
    abs_uc = {}
    metric = {}

    #Uncertainty inputs that are not in the uncertainty file
    rel_uc['Pres1'] = float(0.005) #pitot differential pressure of 0.5% relative uncertainty
    abs_uc['Pres1'] = float(0.1)  # pitot differential pressure 0.1 Pa absolute uncertainty

    rel_uc['TAPflow'] = float(.01)  # TAP flow sensor 1% relative uncertainty
    abs_uc['TAPflow'] = float(1)  # TAP flow sensor 1 sccm absolute uncertainty



    #################################################
    # read in raw data file

    [names, units, data] = io.load_timeseries(inputpath)

    ##################################################
    #read in measurement uncertainty file
    ucstuff = []

    with open(ucpath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            ucstuff.append(row)

    ucnames = ucstuff[0]
    for n, name in enumerate(ucnames):
        try:
            rel_uc[name] = float(ucstuff[2][n])
            abs_uc[name] = float(ucstuff[3][n])
        except:
            rel_uc[name] = ucstuff[2][n]
            abs_uc[name] = ucstuff[3][n]


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
        Tval = float(data['Tsamp'][n])

        RHval_uc = float(data['RH'][n]) * rel_uc['RH'] + abs_uc['RH'] #uncertainty is combo of rel and abs from ucinput
        RHval = ufloat(data['RH'][n], RHval_uc)

        Pambval_uc = float(data['Pamb'][n]) * rel_uc['Pamb'] + abs['Pamb'] #uncertainty is combo of rel and abs from ucinput
        Pambval = ufloat(data['Pamb'][n], Pambval_uc)

        Psatval = pow(10, (A - B / (C + Tval))) / 0.0075 #1 Pa = 0.0075 mmHg
        PH2Oval = Psatval * RHval / 100 #ufloat
        H2Oval = PH2Oval / Pambval * 1000000 #ufloat ppm

        data['Psat'].append(Psatval)
        data['PH2O'].append(PH2Oval.n)
        data['H2O'].append(H2Oval.n)
        data['H2O_unc'].append(H2Oval.s)

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

        names. append(stakname)
        units[stakname] = '%vol'
        data[stakname] = []

        uc_stackname = stakname + '_unc'
        names.append(uc_stackname) #uncertainty
        units[uc_stackname] = '%vol'
        data[uc_stackname] = []

        for n in range(len(data[name])):
            if name == 'H2O':
                Csamp = ufloat(data[name][n], data[uc_stackname][n]) #uncertainty already defined
            else:
                Csamp_uc = float(data[name][n]) * rel_uc[name] + abs_uc[name] #uncertainty is combo of rel and abs from ucinput
                Csamp = ufloat(data[name][n], Csamp_uc)

            Qf1_uc = float(data['F1Flow'][n]) * rel_uc['F1Flow'] + abs_uc['F1Flow'] #uncertainty is combo of rel and abs from ucinput
            Qf1 = ufloat(data['F1Flow'][n], Qf1_uc)

            Qf2_uc = float(data['F2flow'][n]) * rel_uc['F2Flow'] + abs_uc['F2Flow'] #uncertainty is combo of rel and abs from ucinput
            Qf2 = ufloat(data['F2Flow'][n], Qf2_uc)

            Qgas_uc = float(data['GasFlow'][n]) * rel_uc['GasFlow'] + abs_uc['GasFlow'] #uncertainty is combo of rel and abs from ucinput
            Qgas = ufloat(data['GasFlow'][n], Qgas_uc)

            Qtap = data['TAPflow'][n]

            if Qtap == 'nan':
                Qtap = ufloat(0, 0)
            else:
                Qtap_uc = float(data['TAPflow'][n]) * rel_uc['TAPflow'] + abs_uc['TAPflow'] #uncertainty is combo of rel and abs from ucinput
                Qtap = ufloat(float(Qtap), Qtap_uc)

            Qsamp = Qf1 + Qf2 + Qgas + Qtap

            try:
                Cdil_uc = float(data[dilname][n]) * rel_uc[name] + abs_uc[name] #uncertainty is combo of rel and abs from ucinput
                Cdil = ufloat(data[dilname][n], Cdil_uc)
            except:
                Cdil = ufloat(0, 0) #if the dilution air concentration was not measured, assume 0

            Qfil_uc = float(data['DilFlow'][n]) * rel_uc['DilFlow'] + abs_uc['DilFlow'] #uncertainty is combo of rel and abs from ucinput
            Qdil = ufloat(data['DilFlow'][n], Qfil_uc)

            Qnoz = Qsamp - Qdil

            Cnoz = (Csamp + Qsamp - Qdil) / Qnoz
            Cnoz = Cnoz / 1000000 * 100 #convert from ppm to %

            data[stakname].append(Cnoz.n)
            data[uc_stackname].append(Cnoz.s)

    #O2 is measured as undiluter stack conc dry basis (%)
    #convert to wet basia
    name = 'O2stak'
    names.append(name)
    units[name] = '%vol'
    data[name] = []

    uc_name = name + '_uc'
    names.append(uc_name)
    units[uc_name] = '%vol'
    data[uc_name] = []

    for n in range(len(data['O2'])):
        O2db_uc = float(data['O2'][n]) * rel_uc['O2'] + abs_uc['O2'] #uncertainty is combo of rel and abs from ucinput
        O2db = ufloat(data['O2'][n], O2db_uc)

        mc = ufloat(data['H2Ostak'][n] / 100, data['H2Ostak_uc'][n] / 100)

        O2wb = O2db * (1 - mc)

        data[name].append(O2wb.n)
        data[uc_name].append(O2wb.s)

    #balanca stack composition is nitrogen
    name = 'N2stak'
    names.append(name)
    units[name] = '%vol'
    data[name] = []

    uc_name = name + '_uc'
    names.append(uc_name)
    units[uc_name] = '%vol'
    data[uc_name] = []

    for n in range(len(data['O2'])):
        val = ufloat(100, 0)
        for name in diluted_species:
            stakname = name + 'stak'
            uc_stackname = stakname + '_uc'
            val = val - ufloat(data[stakname][n], data[uc_name][n])

        val = val - ufloat(data['O2stak'][n], data['O2stack_uc'][n])

        data['N2stak'].append(val.n)
        data['N2stak_uc'].append(val.s)


    #########################################################
    #flu gas molecular weight
    name = 'MW'
    names.append(name)
    units[name] = 'g/mol'
    data[name] = []

    uc_name = name + '_uc'
    names.append(name)
    units[name] = 'g/mol'
    data[name] = []

    for n in range(len(data['O2'])):
        mw = ufloat(0, 0)

        for name in stack_species:
            stakname = name + 'stak'
            uc_stackname = stakname + '_uc'
            mw = mw + MW[name] + ufloat(data[stakname][n], data[uc_stackname][n]) / 100
            if n < 100:
                print(stakname + ' ' + str(mw) + ' ' + str(MW[name]) + ' ' + str(data[uc_stackname][n]))

        data['MW'].append(mw.n)
        data['MW_uc'].append(mw.s)

    ###############################################################
    #Zero the pitot pressure

    #Convert datetime to date numbers for reading/plotting
    dateobjects = []
    for n, val in enumerate(data['time']):
        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        dateobjests.append(dateobject)

    datenums = matplotlib.dates.date2num(dateobjects)
    datenums = list(datenums) #convert ndarray to a list in order to use index function

    name = 'Pres1'
    for n in range(len(data[name])):
        data[name][n] = float(data[name][n]) #convert data series to floats

    offset = float(0)
    while 1:
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
        ax1.xaxis.set_major_formatter('%H:%M:%S')
        ax1.legend()
        plt.show()

        shifted = str(offset)
        offset = raw_input("Enter Pres1 offset:")
        if offset == 'done':
            break
        else:
            offset = float(offset)

    ###############################################################
    #Recalcualte Stack Velocity

    name = 'StakVel'
    metric[name] = []
    ucname = name + '_uc'
    metric[ucname] = []
    units[ucname] = units[name]

    spot = names.index('StakVel') + 1 #Add uc col next to Stakvel col
    names.insert(spot, ucname)

    Kp = float(129)
    for n in range(len(data[name])):
        data[name][n] = float(data[name][n]) #convert data to float

        Pres1val_uc = float(metric['Pres1'][n]) * rel_uc['Pres1'] + abs_uc['Pres1'] #uncertainty is combo of rel and abs from ucinput
        Pres1val = ufloat(metric['Pres1'][n], Pres1val_uc)

        Pambval_uc = float(data['Pamb'][n]) * rel_uc['Pamb'] + abs_uc['Pams'] #uncertainty is combo of rel and abs from ucinput
        Pambval = ufloat(data['Pamb'][n], Pambval_uc)

        MWval = ufloat(data['MW'][n], data['MW_uc'][n])
        TCnozval = data['TCnoz'][n]
        if TCnozval == 'nan':
            newval = 'nan'
        else:
            TCnozval_uc = float(data['TCnoz'][n]) * rel_uc['TCnoz'] + abs_uc['TCnoz'] #uncertainty is combo of rel and abs from ucinput
            TCnozval = ufloat(data['TCnoz'][n], TCnozval_uc)

            if Pres1val < 0:
                Pres1val = -Pres1val
                inside = Pres1val * (TCnozval + 273.15) / Pambval / MWval
                newval = -Cpitot * Kp * umath.sqrt(inside)
            else:
                inside = Pres1val * (TCnoz + 273.15) / Pambval / MWval
                newval = Cpitot * Kp * umath.sqrt(inside)

            if abs(newval.n) < 0.0001: #Really small numbers give big uc vals
                newvale = ufloat(0, 0)

        metric[name].append(newval.n)
        metric[ucname].append(newval.s)

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

    ##################################################################
    # store data as a list of lists to print by row

    newstuff = []
    row = []
    for name in names:
        row.append(units[name])
    newstuff.append(row)
    row = []
    for name in names:
        row.append(name)
    newstuff.append(row)
    for n, val in enumerate(data['time']):
        row = []
        for name in names:
            if name == 'Pres1' or name == 'StakVel' or name == 'StakVel_uc':
                row.append(metric[name][n])
            else:
                row.append(data[name][n])
        newstuff.append(row)

    io.write_timeseries(outputpath, names, units, data)

