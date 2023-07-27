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


import csv
import re
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import datetime, timedelta
import LEMS_DataProcessing_IO as io
import os

########### inputs (only used if this script is run as executable) #############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
inputpath='FuelData.csv'
energypath='EnergyInputs.csv'
exactpath='ExactData.csv'
fueloutputpath='FuelDataCut.csv'
exactoutputpath="ExactDataCut.csv"
savefig='fuelexactperiod.png'
logpath='log.txt'
##################################

def PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefig, logpath):
    #Function takes in fuel and exact data and cuts data for start and end of test period. Graphs data and saves graph

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_FuelExactCuts v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(fueloutputpath)
    matplotlib.rcParams['savefig.directory'] = directory

    timezonehours = 0 #CHANGE FOR DATA IN DIFFERENT TIMEZONES THAN PEMS TIMEZONE
    timezonedays = 0
    fuelstartidx = -20 #number of indexes to grab forward relative to the start time of the fuel sensor

    #Check if there's energy inputs. If not then script won't cut data to a time period
    if os.path.isfile(energypath):
        input = 1
    else:
        input = 0

    if os.path.isfile(inputpath): #check if there's fuel data

        names = []  # list of variable names
        units = {}  # Dictionary keys are variable names, values are units
        data = {}  # Dictionary #keys are variable names, values are times series as a list

        #load input file
        stuff=[]
        with open(inputpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)
        line = 'loaded: ' + inputpath #add to log
        print(line)
        logs.append(line)

        #find the row indicies for data
        for n, row in enumerate(stuff[:100]): #iterate through first 101 rows to look for start of data
            if 'Timestamp' in row:
                namesrow = n #assign name row
        datarow = namesrow+1 # row after name row is start of data

        namestemp = [] #Create temporary list of names
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
        del data['time'] #delte previous dictionary entry
        data['time'] = datetimes #add to dict
        units['time'] = 'yyyymmdd hhmmss'

        d = data['time'][1] - data['time'][0] #find sample rate for fuel
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

        fd = 1  # track if fuel data exist

    else: #If there's no fuel data
        fd = 0 #track if fuel data exist

        line = 'No fuel data found' #add to log
        print(line)
        logs.append(line)

    if os.path.isfile(exactpath): #setting up number of subplots
        fig, axs = plt.subplots(1, 2)
    else:
        fig, axs = plt.subplots(1)
    # Plot fuel data
    #fig, axs = plt.subplots(1, ex)

    try:
        for ax in axs.flat:
            ax.set(xlabel='Time(s)')
    except:
        axs.set(xlabel='Time(s)')

    if fd == 1:
        # If there is not energy inputs, graph raw data
        if input == 0:
            try:
                axs[0].plot(seconds, data['firewood'])
                axs[0].set_title('Fuel Sensor')
                axs[0].set(ylabel='Fuel Weight(kg)')
            except:
                axs.plot(seconds, data['firewood'])
                axs.set_title('Fuel Sensor')
                axs.set(ylabel='Fuel Weight(kg)')

    #####################################################################################
    #EXACT SENSOR

    if os.path.isfile(exactpath): #check if exact data exists
        exnames = []  # list of variable names
        exunits = {}  # Dictionary keys are variable names, values are units
        exdata = {}  # Dictionary #keys are variable names, values are times series as a list

        # load input file
        stuff = []
        with open(exactpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        line = 'loaded: ' + exactpath #add to log
        print(line)
        logs.append(line)

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
            #axs depends on if fuel data exists
            axs[fd].plot(seconds, exdata['Temperature'])
            axs[fd].set_title('Temperature')
            axs[fd].set(ylabel='Temperatue(C)')

            plt.savefig(savefig, bbox_inches='tight')
            plt.show()

    else:
        line = 'no exact data found' #add to log
        print(line)
        logs.append(line)

#########################################################################
    #if energy path exists, take start and end time values and output excel with only data points during test period
    if input == 1:

        ###############################################
        #load energy input file and store values in dictionaries
        [enames,eunits,eval,eunc,euval] = io.load_constant_inputs(energypath)

        line = 'loaded: ' + energypath #add to log
        print(line)
        logs.append(line)

        #Pull entered start and end times from energy inputs. Convert to datetime
        start = datetime.strptime(euval['start_time_test'], '%Y%m%d %H:%M:%S')
        end = datetime.strptime(euval['end_time_test'], '%Y%m%d %H:%M:%S')

        line = 'From energy inputs start time: ' + start.strftime('%Y%m%d %H:%M:%S') + ' end time: ' + end.strftime('%Y%m%d %H:%M:%S') + ' Data will be cut at time values' #add to log
        print(line)
        logs.append(line)

        if os.path.isfile(inputpath): #If there is fuel data
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

        if os.path.isfile(exactpath):
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

        pf = 0
        if os.path.isfile(inputpath):
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

            try:
                axs[0].plot(metric['seconds'], metric['firewood'])
                axs[0].set_title('Fuel Sensor Test Time Only')
                axs[0].set(ylabel='Fuel Weight(kg)')
            except:
                axs.plot(metric['seconds'], metric['firewood'])
                axs.set_title('Fuel Sensor Test Time Only')
                axs.set(ylabel='Fuel Weight(kg)')

            #Indicate that fuel is plotted
            pf = 1

        if os.path.isfile(exactpath):
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
            #axs depends on if fuel data exists or not
            axs[pf].plot(exmetric['seconds'], exmetric['Temperature'])
            axs[pf].set_title('Temperature Test Time Only')
            axs[pf].set(ylabel='Temperatue(C)')

        plt.savefig(savefig, bbox_inches='tight')
        plt.show()




        ######################################################################
        #Write cut data to outputpaths
        try:
            io.write_timeseries(fueloutputpath, names, units, metric)

            line = 'Created: ' + fueloutputpath #add to log
            print(line)
            logs.append(line)
        except:
            line = 'No fuel data output created' #add to log
            print(line)
            logs.append(line)

        try:
            io.write_timeseries(exactoutputpath, exnames, exunits, exmetric)
            line = 'Created: ' + exactoutputpath  # add to log
            print(line)
            logs.append(line)
        except:
            line = 'No exact data output created'  # add to log
            print(line)
            logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)

#####################################################################
#the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefig, logpath)

