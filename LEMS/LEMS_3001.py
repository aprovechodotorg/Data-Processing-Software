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
import os
import easygui
from LEMS_RedoFirmwareCalcs import RedoFirmwareCalcs

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_RawData.csv'  # read
outputpath = 'foldername_RawData_Recalibrated.csv'  # write
headerpath = 'folername_Header.csv'  # write
logger = 'logging Python package'
#################################################

def LEMS_3001(Inputpath, outputpath, headerpath, logger):

    # Function purpose: This function was made for 3001 sensor box. Raw data from 3001 is taken in and
    # reformatted into a readable format for the rest of the functions to take in and process

    # Inputs:
    # Raw data file of 3001 sensor box
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
    data = {}  # dictionary of data point. Key is names
    metric = {}  # Recalculated corrected data. Key is names

    ###########################################################################################
    # List of names to reformat that match 4000 series names
    names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'COtemp', 'TC aux',
                 'pd aux', 'O2_1', 'O2_2', 'O2_3', 'O2_4']

    # Constants for PM sensor
    scat_eff = 3
    flowslope = 1
    flowintercept = 0

    # load input file
    stuff = []  # List of lists, each list is a row in the csv file
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    line = f'Loaded: {Inputpath}'
    print(line)
    logger.info(line)
    logs.append(line)

    # put inputs in a dictionary
    for n, row in enumerate(stuff):
        if row[0] == '#headers: ':  # Find start time and data
            start_row = n - 1  # time is one row up
            date_row = n - 2  # date is two rows up
        if row[0] == '# 0':  # Find multiplier row (to change numbers from logunits)
            multi_row = n
        if row[0] == 'seconds':  # Find row of variable names
            names_row = n

    try:
        data_row = names_row + 1  # Data starts right after names
    except NameError:  # If names row can't be found, guess on data and names row based on typical output
        data_row = 5
        names_row = 4

    for name in stuff[names_row]:  # For each sensor name
        if name == '':  # skip if name is blank
            pass
        else:
            names.append(name)  # Assign valid names to list

    for n, name in enumerate(names):  # For each valid sensor name
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
    # recalibration
    # check for header input file
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

        # open header file and read in new cal params
        [names_new, units_new, A_new, B_new, C_new, D_new, const_new] = io.load_header(headerpath)

        # redo firmware calculations
        [data_new, add_logs] = RedoFirmwareCalcs(names, A_old, B_old, const_old, data,
                                                 A_new, B_new, const_new, units, logger)
        logs = logs + add_logs

        data = data_new
    else:  # create a header by asking user for input
        data, add_logs = io.create_header(headerpath, names, data, logger, logs)
        logs = logs + add_logs

    ###############################################
    for name in names_new:  # Different variables have different calculations for unit conversion
        values = []
        if name == 'CO':
            for val in data['co']:  # By multiplier
                try:
                    calc = val * multi['co']
                except TypeError:
                    calc = val
                values.append(calc)
        elif name == 'CO2':
            for val in data['co2']:  # By mulitplier
                try:
                    calc = val * multi['co2']
                except TypeError:
                    calc = val
                values.append(calc)
        elif name == 'PM':
            for val in data['pm']:  # By multiplier and light scattering coefficient
                try:
                    calc = val * multi['pm'] * scat_eff
                except TypeError:
                    calc = val
                values.append(calc)
        elif name == 'Flow':
            for val in data['duct pd']:
                try:
                    calc = val * 25.4  # convert inches of water column to mm of w.c.
                except TypeError:
                    calc = val
                values.append(calc)
        elif name == 'FLUEtemp':  # By multiplier
            for val in data['duct T']:
                try:
                    calc = val * multi['duct T']
                except TypeError:
                    calc = val
                values.append(calc)
        elif name == 'H2Otemp':  # No change
            for val in data['h2o T']:
                values.append(val)
        elif name == 'RH':  # No change
            for val in data['RH']:
                values.append(val)
        elif name == 'COtemp':  # No change
            for val in data['gas T']:
                values.append(val)
        elif name == 'TC aux':  # No change
            for val in data['TC aux']:
                values.append(val)
        elif name == 'pd aux':
            for val in data['pd aux']:
                try:
                    calc = val * 25.4  # convert inches of water column to mm of w.c.
                except:
                    calc = val
                values.append(calc)
        elif name == 'O2_1':  # No change
            for val in data['O2 1']:
                values.append(val)
        elif name == 'O2_2':  # No change
            for val in data['O2 2']:
                values.append(val)
        elif name == 'O2_3':  # No change
            for val in data['O2 3']:
                values.append(val)
        elif name == 'O2_4':  # No change
            for val in data['O2 4']:
                values.append(val)
        elif name == 'seconds':  # No change
            for val in data[name]:
                values.append(val)

        metric[name] = values  # Add values to output dictionary
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

    # Add units to names - not given in file
    units['seconds'] = 's'
    units['CO'] = 'ppm'
    units['CO2'] = 'ppm'
    units['PM'] = 'Mm^-1'
    units['Flow'] = 'mmH2O'
    units['FLUEtemp'] = 'C'
    units['H2Otemp'] = 'C'
    units['RH'] = '%'
    units['COtemp'] = 'C'
    units['TC aux'] = 'C'
    units['pd aux'] = 'mmH2O'
    units['O2_1'] = 'lambda'
    units['O2_2'] = 'lambda'
    units['O2_3'] = 'lambda'
    units['O2_4'] = 'lambda'

    ######################################################################
    # Write cut data to outputpath - Data isn't recalibrated just named that for next steps
    io.write_timeseries(outputpath, names_new, units, metric)

    line = f'created: {outputpath}'
    print(line)
    logger.info(line)
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
    LEMS_3001(inputpath, outputpath, headerpath, logger)

