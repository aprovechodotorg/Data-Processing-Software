#v0.0  Python3

#    Copyright (C) 2022 Aprovecho Research Center
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Contact: sam@aprovecho.org

import os
from turtle import shape
import pandas as pd
import numpy as np
import csv
import glob
import statistics as stat
from datetime import datetime
from csv import reader
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import PEMS_FuelCalcs
import itertools  

#Fuel_Path = input("Enter path of the fuel raw data directory.\n")
#place the path to your Fuel CSV. Put this in its own folder to read the file, for right now it only works for a single file
#csv_R_m = glob.glob(os.path.join(Fuel_Path, "*.csv"))

def PEMS_FuelScript(inputpath):
    with open(inputpath, 'r') as f:
        print('file opened')
        csv_reader = csv.reader(f)
        for idx, row in enumerate(csv_reader):
            if 'Timestamp' in row or 'time' in row:
                print('You have found the data')
                WHOLE_CSV = pd.read_csv(inputpath, skiprows=(idx+1))

                for Column, Metric in enumerate(row):
                    if Column == 0:
                        time = WHOLE_CSV.iloc[:,Column]
                    elif Metric[0:8] =='firewood' or Metric[0:2] =='kg':
                        Fuel = WHOLE_CSV.iloc[:,Column]
                break


    KG_removed, Array_mean_coutner = PEMS_FuelCalcs.FUEL_REMOVAL(Fuel, 0.1, 15, True, 30)
    #print(KG_removed)
    #print('Spaces from Array_mean_coutner', Array_mean_coutner)
    Removal_time_spaces = PEMS_FuelCalcs.FuelRemovalTime(KG_removed, True)
    #print(Removal_time_spaces)

    Total_removed_Fuel = list(set(KG_removed))
    print(' Total Fuel Removed ', sum(Total_removed_Fuel))