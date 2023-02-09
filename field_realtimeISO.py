

import LEMS_DataProcessing_IO as io
import numpy as np
from matplotlib import pyplot as plt
import csv
import easygui


inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_TimeSeriesShifted.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_RealtimeISO.csv'

def field_realtimeISO(inputpath, outputpath):
    # read in raw data file
    #[names, units, data, unc, uval] = io.load_constant_inputs(inputpath)

    units = {}  # dictionary keys are variable names, values are units
    data = {}  # dictionary keys are variable names, values are time series as a list

    # load input file
    #stuff = []
    #with open(inputpath) as f:
        #reader = csv.reader(f)
        #for row in reader:
            #stuff.append(row)


    #names = stuff[0]

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
    #print(data['CO'])

    potentialBkgNames = ['CO', 'CO2']  # define potential channel names that will get background subtraction
    bkgnames = []  # initialize list of actual channel names that will get background subtraction

    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)

    for name in bkgnames:
        bkg = name + 'bkg'
        #for i in range(0, len(data[name])):
            #print(data[name][i])
            #data[name] = data[name][i] - data[bkg][i]
        data[name] = (np.subtract(data[name], data[bkg]))

    Cco = [] #Co concentration g/m^3

    P = 101325 #standard pressure Pa
    MWco = 28.01 #molecular weight CO g/mol
    R = 8.314 #ideal gas constant m^3Pa/K/mal
    T = 293.15 #standard temperature K


    for item in data['CO']:
        #print(type(item))
        top = item * P * MWco
        bottom = 1000000 * R * T
        value = top/bottom
        Cco.append(value)

    #print(Cco)


    Cco2 = [] #CO2 concentration g/m^3

    MWco2 = 44.01 #molecular weight CO2 g/mol

    #print(data['CO2'])

    for item in data['CO2']:
        top = item * P * MWco2
        bottom = 1000000 * R * T
        value = top/bottom
        Cco2.append(value)

    names.append('Cco')
    names.append('Cco2')
    data['Cco'] = Cco
    data['Cco2'] = Cco2
    units['Cco2'] = 'g/m^3'
    units['Cco'] = 'g/m^3'

    #print(data['Cco'])


    #Total carbon concentration
    #ADD PM SUM HERE

    Cc = [] #Carbon concentration g/m^3
    COt = []
    CO2t = []

    MWc = 12.01 #molecular weight C g/mol
    Rco = MWc/MWco
    Rco2 = MWc / MWco2

    n=0
    for item in data['Cco']:
        COt.append(item * Rco)
    for item in data['Cco2']:
        CO2t.append(item * Rco2)

    #Cc.append(np.add(CO, CO2))
    #Cc.append(a + b for a, b in zip(CO, CO2))
    i = 0
    for item in data['Cco']:
        Cc.append(item + data['Cco2'][i])
        i += 1

    #print(Cc[0])


    names.append('Cc')
    data['Cc'] = Cc
    units['Cc'] = 'g/m^3'


    plt.ion()
    plots = ['Cco', 'Cco2', 'Cc']
    scale = [1, 1, 1]



    n = 0
    for name in plots:
        scalar = scale[n]
        data[name] = [x * scalar for x in data[name]]
        plt.plot(data['seconds'], data[name])
        n += 1

    plt.ylim(0, 50)
    plt.xlabel("Times (s)")
    plt.ylabel("Concentration (g/m^3)")
    plt.title("Concentration of " + str(plots) + " over time")
    plt.legend(plots)
    plt.show()

    running = 'fun'

    while (running == 'fun'):

        zero = 'Edit scales\n'
        first = 'Click OK to update plot\n'
        second = 'Click Cancel to exit\n'
        msg = zero + first + second
        title = 'Gitrdone'

        newscale = easygui.multenterbox(msg, title, plots, scale)

        if newscale:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            scale = []
            for item in newscale:
                scale.append(int(item))

        else:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            running = 'not fun'

        plt.clf()
        n = 0
        for name in plots:
            scalar = scale[n]
            data[name] = [x * scalar for x in data[name]]
            plt.plot(data['seconds'], data[name])
            n += 1

        plt.ylim(0, 50)
        plt.xlabel("Times (s)")
        plt.ylabel("Concentration (g/m^3)")
        plt.title("Concentration of " + str(plots) + " over time")
        plt.legend(plots)
        plt.show()

    ERCco = [] #Emission ratio CO
    i = 0
    #for value in data['Cco']:
        #for num in data['Cc']:
    calc = [i / j for i, j in zip(data['Cco'], data['Cc'])]
    #print(calc[0])
    for item in calc:
        ERCco.append(item)
    #print(ERCco[0])
            #ERCco.append(value/num)
        #i += 1


    ERCco2 = [] #Emission ratio CO2
    i=0
    calc = [i / j for i, j in zip(data['Cco2'], data['Cc'])]
    #print(calc[0])
    for item in calc:
        ERCco2.append(item)

    #print(data['Cc'][0])

    #Emision ratio PM

    #Emission factor, fuel mass based
    EFcomass = [] #CO
    Cfrac = 0.5 #Effective carbon fraction. Assumed 50%
    #print(ERCco[0])
    for item in ERCco:
        EFcomass.append(item * Cfrac * 1000.0)

    EFco2mass = [] #CO2
    for item in ERCco2:
        EFco2mass.append(item * Cfrac * 1000)

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


    #print(data['EFcomass'][0])
    #print(data['EFco2mass'][0])


    plt.clf()
    plt.ion()
    plots = ['EFcomass', 'EFco2mass']
    scale = [1, 1]


    n = 0
    for name in plots:
        scalar = scale[n]
        data[name] = [x * scalar for x in data[name]]
        plt.plot(data['seconds'], data[name])
        n += 1

    plt.ylim(0, 1000)
    plt.xlabel("Times (s)")
    plt.ylabel("Emission Factor, Fuel mass based (g/kg)")
    plt.title("Emission Factor, Fuel mass based of CO and CO2 over time")
    plt.legend(plots)
    plt.show()

    running = 'fun'

    while (running == 'fun'):

        zero = 'Edit scales\n'
        first = 'Click OK to update plot\n'
        second = 'Click Cancel to exit\n'
        msg = zero + first + second
        title = 'Gitrdone'

        newscale = easygui.multenterbox(msg, title, plots, scale)

        if newscale:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            scale = []
            for item in newscale:
                scale.append(int(item))
        else:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            running = 'not fun'

        plt.clf()
        n = 0
        for name in plots:
            scalar = scale[n]
            data[name] = [x * scalar for x in data[name]]
            plt.plot(data['seconds'], data[name])
            n += 1

        plt.ylim(0, 1000)
        plt.xlabel("Times (s)")
        plt.ylabel("Emission Factor, Fuel mass based (g/kg)")
        plt.title("Emission Factor, Fuel mass based of CO and CO2 over time")
        plt.legend(plots)
        plt.show()

    EHV = 15431 #effective heating value MJ/kg TEMPORARY VALUE

    EFcoenergy = []
    for item in data['ERCco']:
        EFcoenergy.append((item * Cfrac * 1000) / EHV)

    EFco2energy = []
    for item in data['ERCco2']:
        EFco2energy.append((item * Cfrac * 1000) / EHV)

    names.append('EFcoenergy')
    names.append('EFco2energy')
    data['EFcoenergy'] = EFcoenergy
    data['EFco2energy'] = EFco2energy
    units['EFcoenergy'] = 'g/MJ'
    units['EFco2energy'] = 'g/MJ'

    plt.clf()
    plt.ion()
    plots = ['EFcoenergy', 'EFcoenergy']
    scale = [1, 1]


    n = 0
    for name in plots:
        scalar = scale[n]
        data[name] = [x * scalar for x in data[name]]
        plt.plot(data['seconds'], data[name])
        n += 1

    plt.ylim(0, 1)
    plt.xlabel("Times (s)")
    plt.ylabel("Emission Factor, Energy based (g/MJ)")
    plt.title("Emission Factor, Energy based (g/MJ) of CO and CO2 over time")
    plt.legend(plots)
    plt.show()

    running = 'fun'

    while (running == 'fun'):

        zero = 'Edit scales\n'
        first = 'Click OK to update plot\n'
        second = 'Click Cancel to exit\n'
        msg = zero + first + second
        title = 'Gitrdone'

        newscale = easygui.multenterbox(msg, title, plots, scale)

        if newscale:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            scale = []
            for item in newscale:
                scale.append(int(item))
        else:
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            running = 'not fun'

        plt.clf()
        n = 0
        for name in plots:
            scalar = scale[n]
            data[name] = [x * scalar for x in data[name]]
            plt.plot(data['seconds'], data[name])
            n += 1

        plt.ylim(0, 1)
        plt.xlabel("Times (s)")
        plt.ylabel("Emission Factor, Energy based (g/MJ)")
        plt.title("Emission Factor, Energy based (g/MJ)  of CO and CO2 over time")
        plt.legend(plots)
        plt.show()


    ##############################################
    #print the time series output file
    io.write_timeseries(outputpath,names,units,data)
#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_realtimeISO(inputpath, outputpath)
