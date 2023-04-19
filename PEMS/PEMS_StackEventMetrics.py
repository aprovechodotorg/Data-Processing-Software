

import EF
import PM
import csv
import math
import easygui
from uncertainties import ufloat
import numpy as np
import LEMS_DataProcessing_IO as io


#########################################
inputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_Averages.csv'
ucpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_UCInputs.csv'
fuelpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_EnergyOutputs.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_Metrics.csv'


#################################################################
def PEMS_StackEventMetrics(in)