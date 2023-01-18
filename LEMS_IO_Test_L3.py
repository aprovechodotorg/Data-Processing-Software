
inputpath = 'Data/yatzo alcohol/yatzo_L2_FormattedData.csv'

import csv
import pandas as pd

#####################################################################
def LEMS_IO_test_L3(Inputpath):
    # function loads in variables from csv input file and stores variable names, units, and values in dictionaries
    # Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_EnergyInputs.csv

    names = []  # list of variable names
    units = {}  # dictionary keys are variable names, values are units
    val = {}  # dictionary keys are variable names, values are variable values
    average = {}


    # load input file
    stuff = []
    values = []
    testnum = len
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)
    cols = pd.read_csv(inputpath)
    cols = len(cols.axes[1])
    # put inputs in a dictionary
    for row in stuff:
        name = row[0]
        print(name)
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



    return names, units, val, average

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_IO_test_L3(inputpath)