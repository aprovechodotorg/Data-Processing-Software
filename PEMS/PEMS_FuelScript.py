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
#Fuel_Path = "C:\\Users\\Sam\\Documents\\research projects\\DOE heating stove\\choosing baseline stoves\\snow ball sampling\\GP003\\fuel processed data\\day 2"
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
                    elif Metric[0:8] =='firewood' or Metric[0:8] =='firewood kg (FUEL 4003)':
                        Fuel = WHOLE_CSV.iloc[:,Column]
                break


    KG_removed, Array_mean_coutner = PEMS_FuelCalcs.FUEL_REMOVAL(Fuel, 0.1, 15, True, 30)
    #print(KG_removed)
    #print('Spaces from Array_mean_coutner', Array_mean_coutner)
    Removal_time_spaces = PEMS_FuelCalcs.FuelRemovalTime(KG_removed, True)
    #print(Removal_time_spaces)

    Total_removed_Fuel = list(set(KG_removed))
    print(' Total Fuel Removed ', sum(Total_removed_Fuel))