

import csv
from datetime import datetime, timedelta
import LEMS_DataProcessing_IO as io

def PEMS_2041(Inputpath, outputpath):

    #Read in partial capture data, output correctly formatted data

    names = [] #list of variable names
    units = {} #dictionary of units. Key is names
    multi = {} #Dictionary of multipliers. Key is name
    data = {} #dictionary of data point. Key is names
    metric = {} #Recalcualted corrected data. Key is names
    names_new = ['time', 'seconds', 'CO', 'ChipTemp', 'PM', 'Flow', 'FlueTemp', 'TC', 'F1Flow', 'DilFlow', 'CO2', 'PM_RH'] #New list for names

    # load input file
    stuff = []
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # put inputs in a dictionary
    for n, row in enumerate(stuff):
        if row[0] == '##': #Find start time and data
            start_row = n - 1
            date_row = n - 2
        if row[0] == '#0': #Find multiplier row
            multi_row = n
        if row[0] == 'seconds':
            names_row = n

    data_row = names_row + 1 #Data starts right after names

    for name in stuff[names_row]:
        if name == '':
            pass
        else:
            names.append(name) #Assign names

    for n,name in enumerate(names):
        try:
            multi[name]=float(stuff[multi_row][n]) #Grab the multiplier for each named row
        except:
            multi[name] = stuff[multi_row][n]
        data[name]=[x[n] for x in stuff[data_row:]] #Grab all the data for each named row
        for m,val in enumerate(data[name]): #Convert data to floats
            try:
                data[name][m]=float(data[name][m])
            except:
                pass

    '''
    for name in names: #Calculate the data by the multipliers to get useable data in metric dictionary
        values = []
        #names_new.append(name)
        if name == 'seconds' or name == 'Flow' or name == 'CO2' or name == 'PM_RH': #Just append the raw data
            for val in data[name]:
                values.append(val)
        elif name == 'PM': #Multiply by multiplier, divde by 3
            for val in data[name]:
                calc = val * multi[name] / 3
                values.append(calc)
        elif name == 'F1Flow' or name == 'DilFlow': #Multiply by multiplier and 100
            for val in data[name]:
                calc = val * multi[name] * 100
                values.append(calc)
        else:
            for val in data[name]: #Multiply by multiplier
                calc = val * multi[name]
                values.append(calc)
        metric[name] = values #Add calculated values to metric dictionary
    '''
    for name in names_new:
        values = []
        if name == 'CO' or name == 'ChipTemp' or name == 'FlueTemp' or name == 'TC':
            for val in data[name]:
                calc = val * multi[name]
                values.append(calc)
        elif name == 'seconds' or name == 'Flow' or name == 'CO2' or name == 'PM_RH':
            for val in data[name]:
                values.append(val)
        elif name == 'PM':
            for val in data[name]:
                calc = val * multi[name] / 3
                values.append(calc)
        elif name == 'F1Flow':
            for val in data['grav']:
                calc = val * multi['grav'] * 1000
                values.append(calc)
        elif name == 'DilFlow':
            for val in data['dilution']:
                calc = val * multi['dilution'] * 1000
                values.append(calc)
        metric[name] = values

    #Calculate time row
    try:
        start_time = stuff[start_row][1] #Find start time for time data
    except:
        pass


    try:
        date = stuff[date_row][1] #Find date for time data
    except:
        pass

    #Format data
    x = date.split("-") #split at "-", when the file is opened it excel it displays as split with "/", but in notebook it has - with the zeroes
    print(x)
    if len(x[0]) == 1: #if one number of month
        x[0] = '0' + x[0] #add 0 at start
    if len(x[1]) == 1: #if one numer of day
        x[1] = '0' + x[1]

    date = x[0] + x[1] + x[2] #yyyymmdd notepad has the correct order from the beginning
    date_time = date + ' ' + start_time #Combine into one datetime

    con_date_time = datetime.strptime(date_time, '%Y%m%d %H:%M:%S') #convert str to readable datetime

    timetemp = []
    for sec in data['seconds']: #Add seconds to time for each second point
        timetemp.append(con_date_time + timedelta(seconds=sec))

    time = []
    for val in timetemp:
        temp = str(val).replace("-","")
        time.append(temp)

    names.append('time')
    data['time'] = time
    metric['time'] = time
    units['time'] = 'yyyymmdd hhmmss'

    #Add units to names - not given in file
    units['seconds'] = 's'
    units['CO'] = 'ppm'
    units['ChipTemp'] = 'degC'
    units['PM'] = 'Mm^-1'
    units['Flow'] = ''
    units['FlueTemp'] = 'degC'
    units['TC'] = 'degC'
    units['F1Flow'] = 'ccm'
    units['DilFlow'] = 'ccm'
    units['CO2'] = 'ppm'
    units['PM_RH'] = '%'

    ######################################################################
    # Write cut data to outputpath - Data isn't recalibrated just named that for next steps
    io.write_timeseries(outputpath, names_new, units, metric)


