from matplotlib import pyplot as plt
import LEMS_DataProcessing_IO as io
import easygui
import numpy as np
import csv

inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_TimeSeriesShifted.csv'

def field_Plot(inputpath):
    potentialBkgNames = ['CO', 'CO2']  # define potential channel names that will get background subtraction
    bkgnames = []  # initialize list of actual channel names that will get background subtraction
    # read in raw data file
    #[names, units, data] = io.load_timeseries(inputpath)
    #raw = pd.read_csv(inputpath, low_memory=False)
    #print(type(data))
    #names = []
    #for col in raw.columns:
        #names.append(col)
    #print(names)


    #for name in names:
        #units[name] = raw.loc[0]
        #data[name] = raw.loc[1:]
    #print(units['CO'])

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
    print(data['ID'])


    # define which channels will get background subtraction
    # could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)

    for name in bkgnames:
        bkg = name + 'bkg'
        #for i in range(0, len(data[name])):
            #print(data[name][i])
            #data[name] = data[name][i] - data[bkg][i]
        data[name] = (np.subtract(data[name], data[bkg]))
        #print(data[name])
        #print(data[name])

    plt.ion()
    plots = ['CO', 'CO2', 'O2', 'PM']
    scale = [1, 1, 1, 1]

    n = 0
    for name in plots:
        scalar = scale[n]
        data[name] = [x*scalar for x in data[name]]
        plt.plot(data['seconds'], data[name])
        n += 1

    plt.ylim(0, 30000)
    plt.xlabel("Times (s)")
    plt.ylabel("PPM")
    plt.title("Emission of " + str(plots) + " over time")
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
            print(scale)
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

        plt.ylim(0, 30000)
        plt.xlabel("Times (s)")
        plt.ylabel("PPM")
        plt.title("Emission of " + str(plots) + " over time")
        plt.legend(plots)
        plt.show()

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_Plot(inputpath)