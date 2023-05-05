import itertools
import os
#from typing_extensions import clear_overloads
import pandas as pd
import numpy as np
import csv
import glob
from decimal import *
from itertools import chain
import statistics as stat
import datetime
from io import StringIO
import matplotlib.pyplot as plt

### Fuel Algorithm 

def FUEL_REMOVAL(Fuel_KG_nf, Thresold, min_average_spread,No_fuel, running_average):
# Fuel_KG_nf, is the non filtered raw array that you are looking at
# Thresold, is the threshold of removal (or change in fuel over the value you want to calculate)
# min_average_spread, is actually the log rate per minute. for 4 second log rate, this value would be a 15 times of logging per minute
# No_fuel, is a true or false, is the data corrupted or not
# running_average, is the spread length, for my study this was set to 30. So every two minutes, at a log rate of 4 seconds, i took the runnign median


        if No_fuel == True:

            count = 0
            n = 0
            Fuel_KG = []

            insert = []
            remove = []

            # this is for running average
            Mean_Count_min = []
            one_to_Aveg = np.arange(0,running_average+1,1)
            for one in one_to_Aveg:
                fiveee = abs(Fuel_KG_nf[one])
                Mean_Count_min.append(fiveee)

            count = 0
            not_first_value = 0
            inside_spread = [0]
            for kg in (Fuel_KG_nf):
                if count == min_average_spread:
                    median = stat.median(inside_spread)
                    Mean_Count_min.append(median)
                    inside_spread = []
                    count = -1
                elif not_first_value == 0:
                    # could take out this for loop...
                    Mean_Count_min.append(Mean_Count_min[-1])
                    inside_spread.append(abs(kg))
                    not_first_value = 1
                else:
                    Mean_Count_min.append(Mean_Count_min[-1])
                    inside_spread.append(abs(kg))

                count = count + 1
            
            Mean_Count_min.remove(Mean_Count_min[0])
            
            # two in one algorithm taking in the threshold and running average 
            KG_burned = [0]
            insert = []
            for vv, kg in enumerate(Fuel_KG_nf):
                if ((vv % 2) == 0) or (vv == 0):
                    KG_burned.append(KG_burned[-1])
                    if vv + 3 == len(Fuel_KG_nf):
                        KG_burned.append(KG_burned[-1])
                        KG_burned.append(KG_burned[-1])
                        KG_burned.remove(KG_burned[0])  
                        break
                    if (vv == 0):
                        previous = Fuel_KG_nf.iloc[(0)]
                        delta_up = 0
                        delta_down = 0
                    else:
                        previous = Fuel_KG_nf.iloc[vv -1]
                        delta_up =  abs(Fuel_KG_nf.iloc[vv +2] -kg)
                        delta_down = abs(kg - Fuel_KG_nf.iloc[vv +2])
                    pass
                elif vv + 3 == len(Fuel_KG_nf):
                        KG_burned.append(KG_burned[-1])
                        KG_burned.append(KG_burned[-1])
                        
                        break
                elif  delta_up > Thresold and Fuel_KG_nf[vv +3] > Mean_Count_min[vv]:
                    if previous < kg:
                        insert.append(vv)
                        KG_burned.append(KG_burned[-1])
                    else:
                        KG_burned.append(KG_burned[-1])
                elif delta_down > Thresold and Fuel_KG_nf.loc[vv +3] < Mean_Count_min[vv]:
                    if (kg  < previous) or (kg < Mean_Count_min[vv]) or (Fuel_KG_nf.loc[vv +1] < previous):
                        
                        KG_burned.append(delta_down)
                    else:
                        KG_burned.append(KG_burned[-1])
                else:
                    KG_burned.append(KG_burned[-1])
        else:
            KG_burned =-1
            Mean_Count_min = -1

        return KG_burned, Mean_Count_min
#removal algorithm

def FuelRemovalTime(KG_burned, No_fuel):
    # take the output from the removal to get the times between each removal
    # No_fuel is a false or a true if the file is corrupted or not
        if No_fuel != False:
            time = np.arange(0,len(KG_burned),1)
            remove = []
            count_rr = 1
            for rr in KG_burned:
                if count_rr +1 == len(time):
                    try:
                        remove.append(remove[-1])
                        break
                    except:
                        break
                elif rr != KG_burned[count_rr]:
                    remove.append(count_rr -1)
                    count_rr = count_rr +1
                else:
                    count_rr = count_rr +1
            Fuel_removal_countdown = []
            count = 0
            start = 0
            for t in time:
                try:
                    if t < remove[0]:
                        Fuel_removal_countdown.append(-1)
                    elif start + 1 == len(remove)+1:
                        g = np.arange (len(KG_burned)- len(Fuel_removal_countdown), len(KG_burned)-1, 1)
                        for h in g:
                            Fuel_removal_countdown.append(h)
                            break
                    elif t == remove[start]:
                        Fuel_removal_countdown.append(0)
                        start = start +1
                        count = 0
                    else:
                        Fuel_removal_countdown.append(count)
                    count = count + 1
                except:
                    pass
        else:
            Fuel_removal_countdown = -1
        return Fuel_removal_countdown