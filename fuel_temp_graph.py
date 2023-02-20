




from matplotlib import pyplot as plt
import easygui
import numpy as np
import csv

inputpath = ['Data/EXACT 3944_2023-02-03_15-06-21.csv',
         'Data/FUELv2 4001_2023-02-03_15-06-21.csv']

def fuel_temp_graph(inputpath):



    for path in inputpath:
        stuff = []

        names = []
        data = {}
        with open(path) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        i = 0
        print(stuff)
        for row in stuff:
            try:
                if row[1] == 'EXACT':
                    type = 'exact'
                elif row[1] == 'FUELv2':
                    type = 'fuel'
            except:
                error = 1

            try:
                if row[0] == 'Timestamp':
                    namesrow = i
            except:
                error = 1
            i += 1

        names = stuff[namesrow]
        datarow = namesrow + 1

        for n, name in enumerate(names):
            data[name] = [x[n] for x in stuff[datarow:]]







#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    fuel_temp_graph(inputpath)