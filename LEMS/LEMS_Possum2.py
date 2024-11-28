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
from datetime import  datetime as dt
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


def LEMS_Possum2(inputpath, outputpath, headerpath, logger):

    # Function purpose: This function was made for 3002 sensor box. Raw data from 3002 is taken in and
    # reformatted into a readable format for the rest of the functions to take in and process

    # Inputs:
    # Raw data file of 3002 sensor box
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
    data = {}  # dictionary of data point. Key is names
    metric = {}  # Recalcualted corrected data. Key is names

    names_new = []  # New list for names

    # load input file
    stuff = []  # List of lists, each list is a row in the csv file
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    line = f'loaded: {inputpath}'
    print(line)
    logger.info(line)
    logs.append(line)

    # put inputs in a dictionary
    for n, row in enumerate(stuff):
        if 'time' in row[0]:  # Find row of variable names
            names_row = n
        if row[0] == '#units:':  # Find row of units
            units_row = n

    data_row = names_row + 1  # Data starts right after names

    for name in stuff[names_row]:
        if name == '':
            pass
        else:
            names.append(name)  # Assign names

    for n, name in enumerate(names):
        data[name] = [x[n] for x in stuff[data_row:]]  # Grab all the data for each named row
        for m, val in enumerate(data[name]):  # Convert data to floats
            try:
                units[name] = stuff[units_row][n]  # second row is units
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

    for name in names:  # Different variables have different calculations for unit conversion
        values = []
        if name == 'Pitot':
            for val in data[name]:
                try:
                    calc = val / 9.80665  # Pa to mmH20
                except TypeError:
                    calc = val
                values.append(calc)
            names_new.append('Flow')
            units['Flow'] = 'mmH2O'
            metric['Flow'] = values
        elif name == 'Pamb':
            for val in data[name]:
                try:
                    calc = val * 0.01  # Pa to hPa
                except TypeError:
                    calc = val
                values.append(calc)
            names_new.append('AmbPres')
            units['AmbPres'] = 'hPa'
            metric['AmbPres'] = values
        elif name == 'FlueTemp':
            for val in data[name]:  # No change
                values.append(val)
            names_new.append('FLUEtemp')
            units['FLUEtemp'] = 'C'
            metric['FLUEtemp'] = values
        else:
            for val in data[name]:  # No change
                values.append(val)
            names_new.append(name)
            metric[name] = values

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
    LEMS_Possum2(inputpath, outputpath, headerpath, logger)
