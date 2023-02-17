

import LEMS_DataProcessing_IO as io
import field_plot_IO as plot
from matplotlib import pyplot as plt
import csv
import easygui


inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_RealtimeISO.csv'

def field_realtimeISO(inputpath, outputpath):
    # read in raw data file
    #[names, units, data, unc, uval] = io.load_constant_inputs(inputpath) #NOT SURE WHY THIS DOESN'T WORK
    units = {}  # dictionary keys are variable names, values are units
    data = {}  # dictionary keys are variable names, values are time series as a list

    # load input file
    stuff = []
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    names = stuff[0]

    for n,name in enumerate(names):
        units[name]=stuff[1][n] #second row is units
        data[name]=[x[n] for x in stuff[2:]]    #data series
        for m,val in enumerate(data[name]):
            try:
                data[name][m]=float(data[name][m])
            except:
                pass

    #potentialBkgNames = ['CO', 'CO2']  # define potential channel names that will get background subtraction
    #names, data = plot.subtract_background(names, data, potentialBkgNames)

    print(data['COhi'][0])
    print(data['CO2hi'][0])

    ##############################################
    #Concentration calculations

    ###### CO concentration
    Cco = [] #Co concentration g/m^3

    P = 101325 #standard pressure Pa
    MWco = 28.01 #molecular weight CO g/mol
    R = 8.314 #ideal gas constant m^3Pa/K/mal
    T = 293.15 #standard temperature K


    for item in data['COhi']: #Calculate concentration for each data point
        top = item * P * MWco
        bottom = 1000000 * R * T
        value = top/bottom
        Cco.append(value)

    ######## CO2 concentration
    Cco2 = [] #CO2 concentration g/m^3

    MWco2 = 44.01 #molecular weight CO2 g/mol

    for item in data['CO2hi']: #Calculate concentration for each data point
        top = item * P * MWco2
        bottom = 1000000 * R * T
        value = top/bottom
        Cco2.append(value)

    ######## SO2 conecntration
    Cso2 = [] #SO2 concentration g/m^3

    MWso2 = 64.07 #molecular weight SO2 g/mol

    for item in data['SO2']: #Calculate concentration for each data point
        top = item * P * MWso2
        bottom = 1000000 * R * T
        value = top/bottom
        Cso2.append(value)

    ########### NO Concentration
    Cno = [] #NO concentration g/m^3

    MWno = 30.01 #molecular weight NO g/mol

    for item in data['NO']: #Calculate concentration for each data point
        top = item * P * MWno
        bottom = 1000000 * R * T
        value = top/bottom
        Cno.append(value)

    ########### NO2 Concentration
    Cno2 = [] #NO2 concentration g/m^3

    MWno2 = 46.01 #molecular weight NO2 g/mol

    for item in data['NO2']: #Calculate concentration for each data point
        top = item * P * MWno2
        bottom = 1000000 * R * T
        value = top/bottom
        Cno2.append(value)

    ########### H2S Concentration
    Ch2s = [] #H2s concentration g/m^3

    MWh2s = 34.1 #molecular weight H2S g/mol

    for item in data['H2S']: #Calculate concentration for each data point
        top = item * P * MWh2s
        bottom = 1000000 * R * T
        value = top/bottom
        Ch2s.append(value)

    ########### VOC Concentration
    Cvoc = [] #H2s concentration g/m^3

    MWvoc = 96.95 #molecular weight VOC g/mol

    for item in data['VOC']: #Calculate concentration for each data point
        top = item * P * MWvoc
        bottom = 1000000 * R * T
        value = top/bottom
        Cvoc.append(value)

    ########### O2 Concentration
    Co2 = [] #O2 concentration g/m^3

    MWo2 = 31.999 #molecular weight O2 g/mol

    for item in data['O2']: #Calculate concentration for each data point
        top = item * P * MWo2
        bottom = 1000000 * R * T
        value = top/bottom
        Co2.append(value)

    #Add new values to dictionaries
    names.append('Cco')
    names.append('Cco2')
    names.append('Cso2')
    names.append('Cno')
    names.append('Cno2')
    names.append('Ch2s')
    names.append('Cvoc')
    names.append('Co2')
    data['Cco'] = Cco
    data['Cco2'] = Cco2
    data['Cso2'] = Cso2
    data['Cno'] = Cno
    data['Cno2'] = Cno2
    data['Ch2s'] = Ch2s
    data['Cvoc'] = Cvoc
    data['Co2'] = Co2
    units['Cco2'] = 'g/m^3'
    units['Cco'] = 'g/m^3'
    units['Cso2'] = 'g/m^3'
    units['Cno'] = 'g/m^3'
    units['Cno2'] = 'g/m^3'
    units['Ch2s'] = 'g/m^3'
    units['Cvoc'] = 'g/m^3'
    units['Co2'] = 'g/m^3'

    print(data['Cco'][0])
    print(data['Cco2'][0])

    #Total carbon concentration
    #ADD PM SUM HERE

    Cc = [] #Carbon concentration g/m^3
    COt = [] #Place holder for splitting up calcs
    CO2t = [] #Place holder for splitting up calcs

    MWc = 12.01 #molecular weight C g/mol
    Rco = MWc/MWco
    Rco2 = MWc / MWco2

    for item in data['Cco']:
        COt.append(item * Rco)
    for item in data['Cco2']:
        CO2t.append(item * Rco2)

    i = 0
    for item in COt: #Add Cco and Cco2 (and PM in the end) for total carbon
        Cc.append(item + CO2t[i])
        i += 1

    #Add values to dictionary
    names.append('Cc')
    data['Cc'] = Cc
    units['Cc'] = 'g/m^3'

    print(data['Cc'][0])

    ###############################
    #Plot concentrations
    plots = ['Cco', 'Cco2', 'Cc']
    y_label = 'Concentration'
    plot.field_plot_data(data, units, plots, y_label) #send to plot function

    #####################################
    #Emission ration calculations

    #ER for CO
    ERCco = [] #Emission ratio CO

    calc = [i / j for i, j in zip(data['Cco'], data['Cc'])] #Element wise divide values in data sets

    for item in calc:
        ERCco.append(item)

    #ER CO2
    ERCco2 = [] #Emission ratio CO2

    calc = [i / j for i, j in zip(data['Cco2'], data['Cc'])] #Element wise divide values in data sets

    for item in calc:
        ERCco2.append(item)

    #Emision ratio PM #NEEDS TO BE ADDED

    ################################################################
    #Emission factor, fuel mass based
    EFcomass = [] #CO
    Cfrac = 0.5 #Effective carbon fraction. Assumed 50%

    for item in ERCco:
        EFcomass.append(item * Cfrac * 1000.0)

    EFco2mass = [] #CO2
    for item in ERCco2:
        EFco2mass.append(item * Cfrac * 1000)

    #add all new values to dictonary
    names.append('ERCco')
    names.append('ERCco2')
    names.append('EFcomass')
    names.append('EFco2mass')
    data['ERCco'] = ERCco
    data['ERCco2'] = ERCco2
    data['EFcomass'] = EFcomass
    data['EFco2mass'] = EFco2mass
    units['EFcomass'] = 'g/kg'
    units['EFco2mass'] = 'g/kg'
    units['ERCco'] = 'g/g'
    units['ERCco2'] = 'g/g'

    print(data['ERCco'][0])
    print(data['ERCco2'][0])
    print(data['EFcomass'][0])
    print(data['EFco2mass'][0])


    ##################################################
    #Plot Emission factor, fuel mass based
    y_label = 'Emission factor, fuel mass based'
    plots = ['EFcomass', 'EFco2mass']
    plot.field_plot_data(data, units, plots, y_label)

    #################################################
    #Calculate emission factor, fuel energy based

    EHV = 15431 #effective heating value MJ/kg TEMPORARY VALUE

    EFcoenergy = []
    for item in data['ERCco']:
        EFcoenergy.append((item * Cfrac * 1000) / EHV)

    EFco2energy = []
    for item in data['ERCco2']:
        EFco2energy.append((item * Cfrac * 1000) / EHV)

    #Add values to dictionary
    names.append('EFcoenergy')
    names.append('EFco2energy')
    data['EFcoenergy'] = EFcoenergy
    data['EFco2energy'] = EFco2energy
    units['EFcoenergy'] = 'g/MJ'
    units['EFco2energy'] = 'g/MJ'

    print(data['EFcoenergy'][0])
    print(data['EFco2energy'][0])

    y_label = 'Emission factor, fuel energy based'
    plots = ['EFcoenergy', 'EFcoenergy']
    plot.field_plot_data(data, units, plots, y_label)


    ##############################################
    #print the time series output file
    io.write_timeseries(outputpath,names,units,data)
#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_realtimeISO(inputpath, outputpath)
