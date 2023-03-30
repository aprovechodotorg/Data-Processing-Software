
import csv
import re
import matplotlib.pyplot as plt

def PEMS_FuelCalcs(inputpath, energypath, exactpath, outputpath):

    names = [] #list of variable names
    units = {} #Dictionary keys are variable names, values are units
    data = {} #Dictionary #keys are variable names, values are times series as a list

    #load input file
    stuff=[]
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    #find the row indicies for data
    for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start of data
        if 'Timestamp' in row:
            namesrow = n #assign name row
    datarow = namesrow+1 # row after name row is start of data

    namestemp = stuff[namesrow] #temporary list of names

    for n, name in enumerate(namestemp):
        #Fuel names have names and units in parenthisis. Split each name at parenthsis. Returns list of strings
        extract_parenthesis = [x for x in re.split(r'[()]', name) if x.strip()]
        nested_result = [y.split() for y in extract_parenthesis]
        nameunit = [item for i in nested_result for item in i]
        #If name was split at parenthsis the first item is the name, the second is the unit
        if len(nameunit) == 2:
            name = nameunit[0]
            names.append(name)
            units[name] = nameunit[1]
        #special case for firewood, unit not in parenthsis. Manually assign unit
        elif nameunit[0] == 'firewood':
            name = nameunit[0]
            names.append(name)
            units[name] = 'kg'
        else:
            name = nameunit[0]
            names.append(name)
            units[name] = ''

        #Fill data dictionary with data from csv
        data[name] = [x[n] for x in stuff[datarow:]]

        #Create floats from data. If data is string, pass
        for m, val in enumerate(data[name]):
            try:
                data[name][m]=float(data[name][m])
            except:
                pass

    print(units)

    #Time stamp not in mm/dd/yyyy hh:mm:ss format which makes it hard convert consistently to time
    #Work around: sample rate is every 4 seconds, loop creates seconds data
    seconds = []
    x = 0
    n = 0
    while n < len(data['firewood']):
        seconds.append(x)
        x += 4
        n += 1
    data['time'] = seconds #add to dictionary
    units['time'] = seconds

    #Plot fuel data
    fig, axs = plt.subplots(1,2)

    for ax in axs:
        ax.set(xlabel='Time(s)')

    axs[0].plot(data['time'], data['firewood'])
    axs[0].set_title('Fuel Sensor')
    axs[0].set(ylabel='Fuel Weight(kg)')

    #####################################################################################
    #EXACT SENSOR

    exnames = []  # list of variable names
    exunits = {}  # Dictionary keys are variable names, values are units
    exdata = {}  # Dictionary #keys are variable names, values are times series as a list

    # load input file
    stuff = []
    with open(exactpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # find the row indicies for data
    for n, row in enumerate(stuff[:100]):  # iterate through first 101 rows to look for start of data
        if 'Timestamp' in row:
            namesrow = n  # assign name row
    datarow = namesrow + 1  # row after name row is start of data

    namestemp = stuff[namesrow]  # temporary list of names

    for n, name in enumerate(namestemp):
        exnames.append(name)
        if name == 'Coal Hea Temperature (EXACT 3944)':
            exunits[name] = 'C'
        # Fill data dictionary with data from csv
        exdata[name] = [x[n] for x in stuff[datarow:]]

        # Create floats from data. If data is string, pass
        for m, val in enumerate(exdata[name]):
            try:
                exdata[name][m] = float(exdata[name][m])
            except:
                pass

    #Time stamp not in mm/dd/yyyy hh:mm:ss format which makes it hard convert consistently to time
    #Work around: sample rate is every 4 seconds, loop creates seconds data
    seconds = []
    x = 0
    n = 0
    while n < len(exdata['Coal Hea Temperature (EXACT 3944)']):
        seconds.append(x)
        x += 4
        n += 1
    exdata['time'] = seconds #add to dictionary
    exunits['time'] = seconds

    #### Plot exact sensor
    axs[1].plot(exdata['time'], exdata['Coal Hea Temperature (EXACT 3944)'])
    axs[1].set_title('Temperature')
    axs[1].set(ylabel='Temperatue(C)')

    plt.show()


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
