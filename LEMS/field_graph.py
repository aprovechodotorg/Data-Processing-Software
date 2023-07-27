

import pandas as pd
from matplotlib import pyplot as plt

######################
#input file of raw data:
inputpath='C:\\Users\\Jaden\\Documents\\GitHub\LEMS-Data-Processing\\Data\\2023_1_24_7_36_22.csv'
#output file of data to be created:
outputpath='C:\\Users\\Jaden\\Documents\\GitHub\\LEMS-Data-Processing\Data\graph_data.csv'
#########################


def field_graph(inputpath, outputpath):
    #cols = [1, 3, 5, 12, 14]
    raw = pd.read_csv(inputpath, skiprows=15) #usecols=cols)
    print(raw)
    #CO = []
    #CO.append((raw['CO']) *20)
    #O2 = []
    #O2.append((raw['O2']) *10000)
    vars = ['CO2', 'PM']
    leg = ['CO', 'CO2', 'PM', 'O2']
    CO2_cor = []
    Co2_cor.append((raw['CO'] - raw['CO']))
    plt.plot(raw['seconds'], ((((raw['CO']) * 20)) - (raw['CObkg'])))
    plt.plot(raw['seconds'], raw[vars])
    plt.plot(raw['seconds'], ((raw['O2']) * 1000))
    plt.ylim(0, 30000)
    plt.xlabel("Times (s)")
    plt.ylabel("PPM")
    plt.legend(leg)
    plt.ion()
    plt.show()
    plt.pause(300)


#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_graph(inputpath,outputpath)