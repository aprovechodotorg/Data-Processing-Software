# v0.2 Python3

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
from datetime import datetime, timedelta
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import subprocess
import easygui
import os
from LEMS_RedoFirmwareCalcs import RedoFirmwareCalcs

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_RawData.csv'  # read
outputpath = 'foldername_RawData_Recalibrated.csv'  # write
headerpath = 'folername_Header.csv'  # write
logger = 'logging Python package'
#################################################


def PEMS_2041(Inputpath, outputpath, headerpath, logger):

    # Function purpose: This function was made for PC sensor box(not possum). Raw data from PC is taken in and
    # reformatted into a readable format for the rest of the functions to take in and process

    # Inputs:
    # Raw data file of PC sensor box
    # logger: python logging function
    # header of calibration values if it exists

    # Outputs:
    # Formatted timeseries data of PC sensor box
    # logs: list of noteable events
    # header of calibration values if created

    # Called by LEMS_Adjust_Calibrations

    logs = []  # list of important events

    # Record start time of script
    func_start_time = dt.now()
    log = f"Started at: {func_start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    # Log script version if available
    try:
        version = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%h", "--", __file__], text=True
        ).strip()
    except subprocess.CalledProcessError:
        version = "unknown_version"
    log = f"Version: {version}"
    print(log)
    logger.info(log)
    logs.append(log)

    names = []  # list of variable names
    units = {}  # dictionary of units. Key is names
    multi = {}  # Dictionary of multipliers. Key is name
    data = {}  # Dictionary of data point. Key is names
    metric = {}  # Recalcualted corrected data. Key is names
    names_new = ['time', 'seconds', 'CO', 'ChipTemp', 'PM', 'Flow', 'FlueTemp', 'TC', 'F1Flow', 'DilFlow', 'CO2',
                 'PM_RH']  # List of names that will be asigned to current sensor channels

    # load input file
    stuff = []  # List of lists, each list is a row in the csv file
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    line = f'Loaded: {inputpath}'
    print(line)
    logger.info(line)
    logs.append(line)

    # Put inputs in a dictionary
    for n, row in enumerate(stuff):
        if row[0] == '##':  # Find start time and data
            start_row = n - 1
            date_row = n - 2
        if row[0] == '#0':  # Find multiplier row
            multi_row = n
        if row[0] == 'seconds':  # Find the variable name row
            names_row = n

    try:
        data_row = names_row + 1  # Data starts right after names
    except NameError:  # If names row can't be found, guess on data and names row based on typical output
        data_row = 5
        names_row = 4

    for name in stuff[names_row]:  # for each sensor name
        if name == '':  # skip any blank names
            pass
        else:
            names.append(name)  # Add valid names to names list

    for n, name in enumerate(names):
        try:
            multi[name] = float(stuff[multi_row][n])  # Grab the multiplier for each named row
        except ValueError:
            multi[name] = stuff[multi_row][n]
        data[name] = [x[n] for x in stuff[data_row:]]  # Grab all the data for each named row
        for m, val in enumerate(data[name]):  # Convert data to floats
            try:
                data[name][m] = float(data[name][m])
            except ValueError:
                pass
    ##############################################
    # Recalibration
    # Check for header input file
    if os.path.isfile(headerpath):
        line = f'Header file already exists: {headerpath}'
        print(line)
        logger.info(line)
        logs.append(line)

        # open header file and read in old cal params
        [names_old, units_new, A_old, B_old, C_old, D_old, const_old] = io.load_header(headerpath)

        # give instructions
        line = f'Open the Header input file and edit the desired calibration parameters if needed:\n\n' \
               f'{headerpath}\n\n' \
               f'Save and close the Header input file then click OK to continue'
        msgtitle = 'Edit Header'
        easygui.msgbox(msg=line, title=msgtitle)

        # Open header file and read in new cal params
        [names_new, units_new, A_new, B_new, C_new, D_new, const_new] = io.load_header(headerpath)

        # Redo firmware calculations
        [data_new, add_logs] = RedoFirmwareCalcs(names, A_old, B_old, const_old, data,
                                                 A_new, B_new, const_new, units, logger)
        logs = logs + add_logs

        data = data_new
    else:  # Create a header by asking user for input
        data, add_logs = io.create_header(headerpath, names, data, logger, logs)
        logs = logs + add_logs

    ###############################################
    # Log unit conversion and formatting

    for name in names_new:  # Different variables have different calculations with their multipliers
        values = []
        if name == 'CO' or name == 'ChipTemp' or name == 'FlueTemp' or name == 'TC':  # By mulitplier
            for val in data[name]:
                calc = val * multi[name]
                values.append(calc)
            line = f'{name} recalculated using: new value = old value * {multi[name]}. To change this, open the raw' \
                   f'data file and change the heading numbers.'
            print(line)
            logger.debug(line)
            logs.append(line)
        elif name == 'seconds' or name == 'Flow' or name == 'CO2' or name == 'PM_RH':  # No change
            for val in data[name]:
                values.append(val)
        elif name == 'PM':  # By mulitplier divided by 3
            for val in data[name]:
                calc = val * multi[name] / 3
                values.append(calc)
            line = f'{name} recalculated using: new value = old value * {multi[name]} / 3. To change this, open ' \
                   f'the raw data file and change the heading numbers.'
            print(line)
            logger.debug(line)
            logs.append(line)
        elif name == 'F1Flow':  # By mulitplier by 1000
            for val in data['grav']:
                calc = val * multi['grav'] * 1000
                values.append(calc)
            line = f"{name} recalculated using: new value = old value * {multi['grav']} * 1000. To change this," \
                   f"open the raw data file and change the heading numbers."
            print(line)
            logger.debug(line)
            logs.append(line)
        elif name == 'DilFlow':  # By mulitplier by 1000
            for val in data['dilution']:
                calc = val * multi['dilution'] * 1000
                values.append(calc)
            line = f"{name} recalculated using: new value = old value * {multi['dilution']} * 1000. To change this," \
                   f"open the raw data file and change the heading numbers."
            print(line)
            logger.debug(line)
            logs.append(line)
        metric[name] = values  # Add recalculated values to output dictionary

    # Calculate time row
    try:
        start_time = stuff[start_row][1]  # Find start time for time data
    except (IndexError, NameError):
        pass

    try:
        date = stuff[date_row][1]  # Find date for time data
    except (IndexError, NameError):
        pass

    try:
        # Format data
        x = date.split("-")  # split at "-", when the file is opened it excel it displays as split with "/", but in
        # notebook it has - with the zeroes
        if len(x[0]) == 1:  # if one number of month
            x[0] = '0' + x[0]  # add 0 at start
        if len(x[1]) == 1:  # if one numer of day
            x[1] = '0' + x[1]
    except (ValueError, IndexError):
        # Format data
        x = date.split("/")  # split at "/", when the file is opened it excel it displays as split with "/", but in
        # notebook it has - with the zeroes
        if len(x[0]) == 1:  # if one number of month
            x[0] = '0' + x[0]  # add 0 at start
        if len(x[1]) == 1:  # if one numer of day
            x[1] = '0' + x[1]

    try:
        date = x[0] + x[1] + x[2]  # yyyymmdd notepad has the correct order from the beginning
        date_time = date + ' ' + start_time  # Combine into one datetime

        con_date_time = datetime.strptime(date_time, '%Y%m%d %H:%M:%S')  # convert str to readable datetime
    except (ValueError, IndexError):
        date = x[2] + x[0] + x[1]  # yyyymmdd notepad has the correct order from the beginning
        date_time = date + ' ' + start_time  # Combine into one datetime

        con_date_time = datetime.strptime(date_time, '%Y%m%d %H:%M:%S')  # convert str to readable datetime

    timetemp = []
    for sec in data['seconds']:  # Add seconds to time for each second point
        timetemp.append(con_date_time + timedelta(seconds=sec))

    time = []
    for val in timetemp:
        temp = str(val).replace("-", "")  # convert format from yyyy-mm-dd to yyyymmdd
        time.append(temp)

    names.append('time')  # Add to dictionaries
    data['time'] = time
    metric['time'] = time
    units['time'] = 'yyyymmdd hhmmss'

    # Add units to names - not given in file - units reflect recalibration constants
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

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    ##############################################
    end_time = dt.now()  # record function execution time
    log = f"Execution time: {end_time - func_start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    return logs

    #######################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    PEMS_2041(inputpath, outputpath, headerpath, logger)

