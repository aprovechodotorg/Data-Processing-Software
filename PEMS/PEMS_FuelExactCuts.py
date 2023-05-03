
import csv
import re
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta
import LEMS_DataProcessing_IO as io
import os

def PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath):
    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(fueloutputpath)
    matplotlib.rcParams['savefig.directory'] = directory

    names = [] #list of variable names
    units = {} #Dictionary keys are variable names, values are units
    data = {} #Dictionary #keys are variable names, values are times series as a list

    timezonehours = 0
    timezonedays = 0
    fuelstartidx = -20 #number of indexes to grab forward relative to the start time of the fuel sensor

    #Check if there's energy inputs. If not then script won't cut data to a time period
    if os.path.isfile(energypath):
        input = 1
    else:
        input = 0

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

    namestemp = []
    for name in stuff[namesrow]:
        if name == 'Timestamp':
            namestemp.append('time')
        else:
            namestemp.append(name)

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
        #special case for battery, split at spaces
        elif nameunit[0] == 'Battery':
            name = 'Battery level'
            names.append(name)
            units[name] = '%'
        #special case for firewood, unit not in parenthsis. Manually assign unit
        elif nameunit[0] == 'firewood':
            name = nameunit[0]
            names.append(name)
            units[name] = 'kg'
        #sometimes firewood isn't in the names
        elif nameunit[0] == 'kg':
            name = 'firewood'
            names.append(name)
            units[name] = nameunit[0]
        else:
            name = nameunit[0]
            names.append(name)
            units[name] = ''

        #Fill data dictionary with data from csv
        data[name] = [x[n] for x in stuff[datarow:]]

        #Create floats from data. If N/A then remove it
        invalid = []
        for m, val in enumerate(data[name]):
            if val == 'N/A':
                invalid.append(val)
            try:
                data[name][m]=float(data[name][m])
            except:
                pass
        for m in invalid:
            try:
                data[name].remove(m)
            except:
                pass

    # fuel time conversion
    datetimes = []
    for val in data['time']:
        # convert string to datetime object
        og = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        # Shift time to match PEMS timestamp
        datetimes.append(og + timedelta(hours=timezonehours) + timedelta(days=timezonedays))
    del data['time']
    data['time'] = datetimes
    units['time'] = 'yyyymmdd hhmmss'

    d = data['time'][1] - data['time'][0]
    fuelrate = d.seconds
    #Find seconds from times
    seconds = []
    for m, val in enumerate(data['time']):
        if m == 0:
            seconds.append(0)
        else:
            diff = val - data['time'][m - 1]
            diffsec = diff.seconds
            total = diffsec + seconds[m - 1]
            seconds.append(total)
    names.append('seconds')
    data['seconds'] = seconds  # add to dictionary
    units['seconds'] = 'seconds'

    # Plot fuel data
    fig, axs = plt.subplots(1, 2)

    for ax in axs.flat:
        ax.set(xlabel='Time(s)')

    #If there is not energy inputs, graph raw data
    if input == 0:
        axs[0].plot(seconds, data['firewood'])
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

    namestemp = []
    for name in stuff[namesrow]:
        if name == 'Timestamp':
            namestemp.append('time')
        else:
            namestemp.append(name)

    for n, name in enumerate(namestemp):
        #exnames.append(name)
        # Fuel names have names and units in parenthisis. Split each name at parenthsis. Returns list of strings
        extract_parenthesis = [x for x in re.split(r'[()]', name) if x.strip()]
        nested_result = [y.split() for y in extract_parenthesis]
        nameunit = [item for i in nested_result for item in i]
        # If name was split at parenthsis the first item is the name, the second is the unit
        if len(nameunit) > 3 and nameunit[2]  == 'Temperature':
            name = nameunit[2]
            exnames.append(name)
            exunits[name] = 'C'
        elif len(nameunit) > 3 and nameunit[3] == 'Usage':
            name = nameunit[2]
            exnames.append(name)
            exunits[name] = ''
        # Fill data dictionary with data from csv
        else:
            exnames.append(name)
            exunits[name] = ''
        exdata[name] = [x[n] for x in stuff[datarow:]]

        # Create floats from data. If N/A remove data
        invalid = []
        for m, val in enumerate(exdata[name]):
            if val == 'N/A':
                invalid.append(val)
                #for name in exnames:
                    #exdata[name].remove(exdata[name][m])
            try:
                exdata[name][m] = float(exdata[name][m])
            except:
                pass
        for m in invalid:
            try:
                exdata[name].remove(m)
            except:
                pass

    #convert time
    # fuel time conversion
    datetimes = []
    for val in exdata['time']:
        # convert string to datetime object
        og = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        # Shift time to match PEMS timestamp
        datetimes.append(og + timedelta(hours=timezonehours) + timedelta(days=timezonedays))
    del exdata['time']
    exdata['time'] = datetimes
    exunits['time'] = 'yyyymmdd hhmmss'

    d = exdata['time'][1] - exdata['time'][0]
    exactrate = d.seconds
    # create seconds list
    seconds = []
    for m, val in enumerate(exdata['time']):
        if m == 0:
            seconds.append(0)
        else:
            diff = val - exdata['time'][m - 1]
            diffsec = diff.seconds
            total = diffsec + seconds[m - 1]
            seconds.append(total)
    exnames.append('seconds')
    exdata['seconds'] = seconds  # add to dictionary
    exunits['seconds'] = 'seconds'

    #If no energy inputs plots raw data
    if input == 0:
        #### Plot exact sensor
        axs[1].plot(seconds, exdata['Temperature'])
        axs[1].set_title('Temperature')
        axs[1].set(ylabel='Temperatue(C)')

        plt.show()

#########################################################################
    #if energy path exists, take start and end time values and output excel with only data points during test period
    if input == 1:

        ###############################################
        #load energy input file and store values in dictionaries
        [enames,eunits,eval,eunc,euval] = io.load_constant_inputs(energypath)

        #Pull entered start and end times from energy inputs. Convert to datetime
        start = datetime.strptime(euval['start_time_test'], '%Y%m%d %H:%M:%S')
        end = datetime.strptime(euval['end_time_test'], '%Y%m%d %H:%M:%S')

        #fuel
        search = []
        x = -fuelrate
        while x <= fuelrate:
            search.append(x)
            x+=1
        #Go through and find the index of the start and end times. Since data is 4 second sample rate, check four seconds around data
        for n, val in enumerate(data['time']):
            for m in search:
                if (val + timedelta(seconds=m)) == start:
                    startidx = n + fuelstartidx #when the fuel sensor is started before the sensor box
                elif (val + timedelta(seconds=m)) == end:
                    endidx = n

        del data['seconds']
        names.remove('seconds')

        metric = {}
        for name in names:
            numbers = []
            for n, val in enumerate(data[name]):
                if n  > startidx and n < endidx:
                    numbers.append(val)
            metric[name] = numbers


        #exact
        search = []
        x = -exactrate
        while x <= exactrate:
            search.append(x)
            x+=1
        #Go through and find the index of the start and end times. Since data is 4 second sample rate, check four seconds around data
        for n, val in enumerate(exdata['time']):
            for m in search:
                if (val + timedelta(seconds=m)) == start:
                    exstartidx = n
                elif (val + timedelta(seconds=m)) == end:
                    exendidx = n

        del exdata['seconds']
        exnames.remove('seconds')

        exmetric = {}
        for name in exnames:
            numbers = []
            for n, val in enumerate(exdata[name]):
                if n > exstartidx and n < exendidx:
                    numbers.append(val)
            exmetric[name] = numbers


        #create seconds list
        seconds = []
        m = 0
        for val in metric['time']:
            if m == 0:
                seconds.append(0)
            else:
                diff = val - metric['time'][m-1]
                diffsec = diff.seconds
                total = diffsec + seconds[m-1]
                seconds.append(total)
            m+=1

        names.append('seconds')
        metric['seconds'] = seconds  # add to dictionary
        units['seconds'] = 's'

        axs[0].plot(metric['seconds'], metric['firewood'])
        axs[0].set_title('Fuel Sensor Test Time Only')
        axs[0].set(ylabel='Fuel Weight(kg)')

        # create seconds list
        seconds = []
        m = 0
        for val in exmetric['time']:
            if m == 0:
                seconds.append(0)
            else:
                diff = val - exmetric['time'][m - 1]
                diffsec = diff.seconds
                total = diffsec + seconds[m - 1]
                seconds.append(total)
            m+=1

        exnames.append('seconds')
        exmetric['seconds'] = seconds #add to dictionary
        exunits['seconds'] = 's'

        #### Plot exact sensor
        axs[1].plot(exmetric['seconds'], exmetric['Temperature'])
        axs[1].set_title('Temperature Test Time Only')
        axs[1].set(ylabel='Temperatue(C)')

        plt.show()




        ######################################################################
        #Write cut data to outputpaths
        io.write_timeseries(fueloutputpath, names, units, metric)
        io.write_timeseries(exactoutputpath, exnames, exunits, exmetric)


    #read in input file of phase start and end times
    #[timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)

    #[validnames,timeobject]=makeTimeObjects(timenames,timestring,date)  #convert time strings to time objects

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
