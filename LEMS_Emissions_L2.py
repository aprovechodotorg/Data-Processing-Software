import pandas as pd
import LEMS_DataProcessing_IO as io
import csv
import os
import math
import statistics
from scipy import stats
import json
import pandas as pd
import numpy as np

def PEMS_Emissions_L2(energyinputpath, emissionsinputpath, outputpath):

    # List of headers
    header = []
    # dictionary of data for each test run
    data_values = {}

    header = ['Energy Outputs', 'units']

    x = 0
    # Run through all tests entered
    for path in energyinputpath:
        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)

        # load in inputs from each energyoutput file
        [names, units, values, unc, uval] = io.load_constant_inputs(path)
        # Add dictionaries for additional columns of comparative data
        average = {}
        N = {}
        stadev = {}
        interval = {}
        high_tier = {}
        low_tier = {}
        COV = {}
        CI = {}

        # Loop through dictionary and add to data values dictionary wanted definitions
        # If this is the first row,add headers
        if (x == 0):
            data_values[name] = {"units": units[name], "values": [values[name]]}
        else:
                for name in names:
                    data_values[name]["values"].append(values[name])
        x += 1