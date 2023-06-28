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
    """Read in a .csv file containing FUEL data and creates a dictionary

    :param inputpath: Path to FUEL data .csv file
    :return: data - Dictionary containing data from .csv file,
             seconds - array with time data from each logged fuel weight"""

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

        return data

    # else:   # If there's no fuel data
        # fd = 0  # Track if fuel data exist

        # line = 'No fuel data found'  # Add to log
        # print(line)
        # logs.append(line)


if __name__ == "__main__":
    # Run tests for this script here
    # Ask user to input path to FUEL .csv file
    # sheetinputpath = input("Input path of _FuelData.csv file:\n")

    # Hardcoded input path for testing
    sheetinputpath = "D:\\School Stuff\\MS Research\\3.14.23\\3.14.23_FuelData.csv"
    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelDataCleaned.csv')

    # Load in fuel data and check if outputs exist
    fuel_data = load_fuel_data(inputpath)
    print(True if fuel_data else False)
    print(fuel_data['seconds'][:5])
    print(fuel_data.keys())
    print(type(fuel_data['firewood']))
