
from csv import reader
import re


def PEMS_FuelCalcs(inputpath, energypath, exactpath, outputpath):

    names = [] #list of variable names
    units = {} #Dictionary keys are variable names, values are units
    data = {} +Dictionary #keys are variable names, values are times series as a list

    #load input file
    stuff=[]
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.appened(row)

    #find the row indicies for data
    for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start of data
        if row[0] == 'Timestamp':
            namesrow = n
    datarow = namesrow+1

    names = stuff[namesrow]
    for n, name in enumerate(names):
        extract_parenthesis = [x for x in re.split(r'[()]', name) if x.strip()]
        nested_result = [y.split() for y in extract_parenthesis]
        nameunit = [item for i in nested_result for item in i]
        if len(nameunit) == 2:
            name = nameunit[0]
            names.append(name)
            unit[name] = nameunit
        else:
            name = nameunit[0]
            names.append(name)
            unit[name] = ''
        data[name] = [x[n] for x in stuff[datarow:]]
        for m, val in enumerate(data[name]):
            try:
                data[name][m]=float(data[name][m])
            except:
                pass
    print(data)
    seconds = []


    '''with open(inputpath, 'r') as f:
        print('file opened')
        csv_reader = csv.reader(f)
        for idx, row in enumerate(csv_reader):
            if 'Timestamp' in row:
                print('You have found the data')
                WHOLE_CSV = pd.read_csv(file, skiprows=(idx))

                for Column, Metric in enumerate(row):
                    if Column == 0:
                        time = WHOLE_CSV.iloc[:, Column]
                    elif Metric[0:8] == 'firewood':
                        Fuel = WHOLE_CSV.iloc[:, Column]
                break'''
