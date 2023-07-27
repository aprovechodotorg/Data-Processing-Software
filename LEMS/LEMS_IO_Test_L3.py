
#inputpath = 'Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

import csv
import pandas as pd

#####################################################################
def LEMS_IO_test_L3(path):
    # function loads in variables from csv input file and stores variable names, units, and values in dictionaries
    # Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_EnergyInputs.csv

    names = []  # list of variable names
    units = {}  # dictionary keys are variable names, values are units
    val = {}  # dictionary keys are variable names, values are variable values
    average = {}


    # load input file
    stuff = []
    values = []
    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    i = 0
    while i < len(stuff[0]):
        if stuff[0][i] == 'average':
            averagerow = i
            #print(averagerow)

        i += 1
    names = []
    for row in stuff:
        names.append(row[0])

    #print(stuff[5][1])
    n = 0
    x = 0
    for name in names:
        #print(name)

        units[name] = stuff[n][1]
        #print(units[name])
        average[name] = stuff[n][averagerow]
        val[name] = stuff[n][2:averagerow]
        n+=1

        #print(val[name])
    #print(stuff[1][2:averagerow])
        #print(row[0][4])
    #print(average['time_to_boil_hp'])
    #col = list(zip(*stuff))
    #print(stuff[0])
    #print(names)


    '''
    cols = pd.read_csv(path)
    cols = len(cols.axes[1])
    print(cols)
    # put inputs in a dictionary
    for row in stuff:
        name = row[0]
        #print(name)
        units[name] = row[1]
        average[name] = row[cols-7]

        l = 0
        throw = 0

        while l <= (cols-6):
            try:
                num = float(row[l+2])
                values.append(num)
            except:
                print(row[l+2])
            l += 1
        val[name] = values
        names.append(name)
    print(average)
    '''


    return names, units, val, average

#####################################################################
#the following two lines allow this function to be run as an executable
#if __name__ == "__main__":
    #LEMS_IO_test_L3(inputpath)