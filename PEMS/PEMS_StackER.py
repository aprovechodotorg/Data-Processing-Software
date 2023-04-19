

import EF
import PM
import csv
import math
import numpy as np
from uncertainties import ufloat
import easygui
import LEMS_DataProcessing_IO as io


#########################################
#Use background subtracted
inputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_Timeseries.csv'
ucpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_UCInputs.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\HH_24\\GP003_24\\3.7.23\\3.7.23_StackER.csv'