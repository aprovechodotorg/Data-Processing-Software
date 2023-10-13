# v0.0  Python3

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
import csv
import re
from datetime import datetime as dt
from datetime import datetime, timedelta


def load_fuel_data(inputpath):
    """Reads in a .csv file containing FUEL data and creates a dictionary

    :param inputpath: Path to FUEL data .csv file
    :return: data - Dictionary containing data from .csv file;"""

    timezonehours = 0 #CHANGE FOR DATA IN DIFFERENT TIMEZONES THAN PEMS TIMEZONE
    timezonedays = 0
    # fuelstartidx = -20 #number of indexes to grab forward relative to the start time of the fuel sensor

    if os.path.isfile(inputpath):   # Check if there's fuel data

        names = []  # List of variable names
        units = {}  # Dictionary keys are variable names, values are units
        data = {}  # Dictionary keys are variable names, values are times series as a list

        # Load input file
        stuff = []
        with open(inputpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        # Find the row indices for data
        for n, row in enumerate(stuff[:100]):   # Iterate through first 101 rows to look for start of data
            if 'Timestamp' in row:
                namesrow = n    # Assign name row
        datarow = namesrow + 1  # Row after name row is start of data

        namestemp = []  # Create temporary list of names
        for name in stuff[namesrow]:
            if name == 'Timestamp':
                namestemp.append('time')
            else:
                namestemp.append(name)

        for n, name in enumerate(namestemp):
            # Fuel names have names and units in parentheses. Split each name at parentheses. Returns list of strings
            extract_parenthesis = [x for x in re.split(r'[()]', name) if x.strip()]
            nested_result = [y.split() for y in extract_parenthesis]
            nameunit = [item for i in nested_result for item in i]
            # If name was split at parentheses the first item is the name, the second is the unit
            if len(nameunit) == 2:
                name = nameunit[0]
                names.append(name)
                units[name] = nameunit[1]
            # Special case for battery, split at spaces
            elif nameunit[0] == 'Battery':
                name = 'Battery level'
                names.append(name)
                units[name] = '%'
            # Special case for firewood, unit not in parentheses. Manually assign unit
            elif nameunit[0] == 'firewood':
                name = nameunit[0]
                names.append(name)
                units[name] = 'kg'
            # Sometimes firewood isn't in the names
            elif nameunit[0] == 'kg':
                name = 'firewood'
                names.append(name)
                units[name] = nameunit[0]
            else:
                name = nameunit[0]
                names.append(name)
                units[name] = ''

            # Fill data dictionary with data from .csv
            data[name] = [x[n] for x in stuff[datarow:]]

            # Create floats from data. If N/A then remove it
            invalid = []
            for m, val in enumerate(data[name]):
                if val == 'N/A':
                    invalid.append(val)
                try:
                    data[name][m] = float(data[name][m])
                except:
                    pass
            for m in invalid:
                try:
                    data[name].remove(m)
                except:
                    pass

        # Fuel time conversion
        datetimes = []
        for val in data['time']:
            # Convert string to datetime object
            og = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
            # Shift time to match PEMS timestamp
            datetimes.append(og + timedelta(hours=timezonehours) + timedelta(days=timezonedays))
        del data['time']    # Delete previous dictionary entry
        data['time'] = datetimes    # Add to dict
        units['time'] = 'yyyymmdd hhmmss'

        d = data['time'][1] - data['time'][0]   # Find sample rate for fuel
        # fuelrate = d.seconds
        # Find seconds from times
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
        data['seconds'] = seconds  # Add to dictionary
        units['seconds'] = 'seconds'

        # fd = 1  # Track if fuel data exist

    # else:   # If there's no fuel data
        # fd = 0  # Track if fuel data exist

        # line = 'No fuel data found'  # Add to log
        # print(line)
        # logs.append(line)

        return data

# Note: US Daylight Savings started on March 12 and ends on November 5 in 2023. French Daylight Savings started on
# March 26 and ends on October 29 in 2023. Between March 12-26 and October 29-November 5 France is 8 hours ahead of the
# West Coast (timezonehours = -8). Otherwise, France is 9 hours ahead of the West Coast (timezonehours = -9). Only use
# these adjustments if the FUEL and EXACT times were not adjusted to US time before the sensing session was started.
# From Jaden: Tests before March 12 -> -9 hours. Tests between March 12-17 -> -8 hours. Tests after March 17 -> 0 hours.
def load_exact_data(exactpath):
    """Reads in a .csv file containing EXACT data and creates a dictionary

    :param exactpath: Path to EXACT data .csv file
    :return: exdata - Dictionary containing data from .csv file;"""

    timezonehours = 0 #CHANGE FOR DATA IN DIFFERENT TIMEZONES THAN PEMS TIMEZONE
    timezonedays = 0
    # fuelstartidx = -20 #number of indexes to grab forward relative to the start time of the fuel sensor

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

        # line = 'loaded: ' + exactpath #add to log
        # print(line)
        # logs.append(line)

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

    # else:
    #     line = 'no exact data found' #add to log
    #     print(line)
    #     logs.append(line)

        return exdata


if __name__ == "__main__":
    # Run tests for this script here
    # Ask user to input path to FUEL .csv file
    # sheetinputpath = input("Input path of _FuelData.csv file:\n")

    # Hardcoded input path for testing
    # sheetinputpath = "D:\\School Stuff\\MS Research\\3.14.23\\3.14.23_FuelData.csv"
    sheetinputpath = "C:\\Users\\kiern\\Downloads\\GP003\\3.8.23\\3.8.23_FuelData.csv"
    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    exactpath = os.path.join(directory, testname+'_ExactData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelDataCleaned.csv')
    exactoutputpath = os.path.join(directory, testname+'_ExactDataCut.csv')

    # Load in fuel data and check if outputs exist
    fuel_data = load_fuel_data(inputpath)
    print(True if fuel_data else False)
    print(fuel_data['seconds'][:5])
    print(fuel_data.keys())
    print(type(fuel_data['firewood']))

    # Load in exact data and check if outputs exist
    exact_data = load_exact_data(exactpath)
    print(True if exact_data else False)
    print(exact_data['seconds'][:5])
    print(exact_data.keys())
    print(type(exact_data['Temperature']))