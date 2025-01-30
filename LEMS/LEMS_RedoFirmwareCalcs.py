# v0.1 Python3

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

import math
import subprocess
from datetime import datetime as dt
import matplotlib.pyplot as plt
import easygui


def RedoFirmwareCalcs(names, A_old,B_old, const_old, data_old, A_new, B_new, const_new, units, logger):
    # Function purpose: take calibration constants and recalibrate data if there are any new constants that were entered
    # in the header.

    # inputs:
    # names: list of channel names
    # A_old: dictionary keys are variable names, values are A (span) parameters from the raw data file header
    # B_old = dictionary keys are variable names, values are B (offset) parameters from the raw data file header
    # const_old: dictionary keys are constant variable names (C parameters), values are constant variable values
    # (D parameters) from the raw data file header
    # data_old: dictionary keys are variable names, values are lists of time series data from the raw data file
    # A_new: dictionary keys are variable names, values are new A (span) parameters defined in the header input file
    # B_new: dictionary keys are constant variable names, values are new B (offset) parameters defined in the header
    # input file
    # const_new: dictionary keys are constant variable names (C parameters), values are constant variable values
    # (D parameters) from the header input file
    # units: dictionary of sensor units

    # output:
    # data_new: dictionary keys are variable names, values are lists of recalculated time series data
    # updated_channels: list of channel names that were updated
    # logs: List of important events

    # Called by LEMS_Adjust_Calibrations() and io.create_header

    # C and D (const) are not currently handled in this function
    
    data_new = {}  # Dictionary for recalibrated data, keys are variable names
    updated_channels = []  # List of updated sensor data series
    logs = []  # record important events

    # Record start time of script
    start_time = dt.now()
    log = f"Started at: {start_time}"
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

    # SB4003.16  or any 4000 series ##############################
    calculated_channels = ['O2_ave']  # define list of calculated channels that are not a function of A and B
    for name in names:
        data_new[name] = []  # initialize a list to fill with the new data series
        if name not in calculated_channels:
            if (A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and
                    math.isnan(A_new[name]) and math.isnan(B_old[name]) and math.isnan(B_new[name])):
                # if A the B parameter did not change
                data_new[name] = data_old[name]  # copy the old time series to the new time series
            else:  # if A or B did change
                updated_channels.append(name)
                # recalculate data values using the following formula: CO=A*(CO_raw+B)
                for n in range(len(data_old[name])):  # for each point in the old data series
                    oldval = data_old[name][n]  # grab the old value
                    # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal
                    # parameters
                    newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                    data_new[name].append(newval)  # append the new value to the new data list
                line = f'Data series: {name} was recalibrated using: new value = {A_new[name]} * (old value / ' \
                       f'{A_old[name]} - {B_old[name]} + {B_new[name]})'
                print(line)
                logger.debug(line)
                logs.append(line)
            
    # calculated channels:
    name = 'O2_ave'
    changed = 0  # initialize flag to see any values changed
    try:
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            try:  # If there's 4 O2 channels
                newval = (data_new['O2_1'][n] + data_new['O2_2'][n] + data_new['O2_3'][n] + data_new['O2_4'][n]) / 4
                data_new[name].append(newval)  # append the new value to the new data list
            except KeyError:  # sometimes there's only 3 channels
                try:
                    newval = (data_new['O2_1'][n] + data_new['O2_2'][n] + data_new['O2_3'][n]) / 3
                    data_new[name].append(newval)  # append the new value to the new data list
                except KeyError:
                    try:  # sometimes there's only 2 channels
                        newval = (float(data_new['O2_1'][n]) + float(data_new['O2_2'][n])) / 2
                        data_new[name].append(newval)  # append the new value to the new data list
                    except (TypeError, KeyError, ValueError):
                        data_new[name].append('')
            try:
                if not math.isclose(oldval, newval, rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore
                    # roundoff error)
                    changed = 1  # set changed flag
            except TypeError:
                pass
        if changed == 1:  # If O2 average changed add to updated channels
            updated_channels.append(name)
            line = 'Updated O2 average channel by averaging all O2 sensors together'
            print(line)
            logger.debug(line)
            logs.append(line)
    except KeyError:  # if no O2 channels, skip calculation
        pass

    if not updated_channels:  # If no new parameters were entered
        line = 'No channels were recalculated'
        print(line)
        logger.info(line)
        logs.append(line)
    else:
        for name in updated_channels:
            line = f'Recalculated {name} data series'
            print(line)
            logger.info(line)
            logs.append(line)

    # plot the old and new data series to inspect the differences
    if len(updated_channels) > 0:  # if any data series were updated
        firstline = 'The following plots show the effect of the recalculation on each sensor. Close the plots to ' \
                    'continue.'
        msgtitle = 'Recalculation Plots'
        easygui.msgbox(msg=firstline, title=msgtitle)

        for (fignum, name) in enumerate(updated_channels):  # for each channel that was changed
            for n in range(len(data_old[name])):
                data_old[name][n] = float(data_old[name][n])  # convert old and new data series to floats
                data_new[name][n] = float(data_new[name][n])  # to remove strings so they will plot
            plt.figure(fignum + 1)
            plt.plot(data_old[name], label=name + ' old')  # plot old data
            plt.plot(data_new[name], label=name + ' new')  # plot new data
            plt.xlabel('Data Points')
            plt.ylabel(units[name])
            plt.legend()  # add legend
        plt.show()
    # end of figure
    # end of function

    end_time = dt.now()
    log = f"Execution time: {end_time - start_time}"
    print(log)
    logger.info(log)
    logs.append(log)
    
    return data_new, logs
    
    