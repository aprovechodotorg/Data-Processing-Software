# v0.5 Python3

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

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os
from uncertainties import ufloat
import subprocess
import sys

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_RawData_Recalibrated.csv'  # read
energyinputpath = 'foldername_EnergyOutputs.csv'  # read
ucpath = 'foldername_UCInputs.csv'  # read/write
outputpath = 'foldername_TimeSeries.csv'  # write
aveoutputpath = 'folderpath_Averages.csv'  # write
timespath = 'foldername_PhaseTimes.csv'  # write/read
bkgmethodspath = 'foldername_BkgMethods'  # write/read
logger = 'logging Python package'
savefig1 = 'foldername_subtractbkg1.png'  # save to
savefig2 = 'foldername_subtractbkg.png'  # save to
inputmethod = '0'  # (non-interactive) or 1 (interactive)


#################################################


def PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath, logger,
                     savefig1, savefig2, inputmethod):
    # Function purpose: Intake recalibrated data, ask user for inputs on background subtracting methods and background
    # time periods. Record inputs, subtract background from specified sensor data. Graph background subtracted data and
    # input data to show user difference. Save pictures of graphs.

    # Inputs:
    # Recalibrated timeseries data file
    # Energy calculations
    # Uncertainty inputs for each sensor (absolute and relative) (if exists)
    # File of phase and background times (if exists)
    # File of background subtraction methods for each specified sensor (if exists)
    # Python logging function
    # Inputmethod: 0 (non-interactive) or 1 (interactive)

    # Outputs:
    # Background subtracted timeseries for each phase and for the entire time series
    # Uncertainty inputs for each sensor (absolute and relative) (If it does not exist, uncertainties of 0 are default)
    # File of phase and background times
    # File of background subtraction methods for each specified sensor
    # 2 saved images of background subtracted data
    # logs: list of important events

    logs = []  # List of notable functions, errors, and calculations recorded for reviewing past processing of data

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

    #################################################
    potentialBkgNames = ['CO', 'CO2', 'CO2v', 'PM', 'COhi', 'CO2hi', 'VOC', 'CH4']  # define potential channel names
    # that will get background subtraction
    bkgnames = []  # initialize list of actual channel names that will get background subtraction

    #################################################
    # read in recalibrated raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    sample_rate = data['seconds'][1] - data['seconds'][0]  # check the sample rate (time between seconds)

    line = f'Loaded: {inputpath}'
    print(line)
    logger.info(line)
    logs.append(line)

    ##############################################
    # check for measurement uncertainty input file
    if os.path.isfile(ucpath):
        line = f'Measurement uncertainty input file already exists: {ucpath}\n' \
               f'Loaded uncertainty file and applied inputs.'
        print(line)
        logger.info(line)
        logs.append(line)
    else:  # if input file is not there then create it
        ucinputs = {}  # Dictionary of uncertainty values for each sensor, uncertainty values are absolute and relative
        for name in names:
            if name == 'time':
                ucinputs[name] = ['absolute uncertainty', 'relative uncertainty']
            else:
                ucinputs[name] = [0, 0]  # Default 0 uncertainty (absolute and relative)
        io.write_timeseries(ucpath, names, units, ucinputs)

        line = f'Created measurement uncertainty input file: {ucpath}\n' \
               f'Uncertainty values are defaulted at 0, to change, open file and modify values.'
        print(line)
        logger.info(line)
        logs.append(line)

    # define which channels will get background subtraction
    # could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:  # if there's a sensor in the data stream that would need bkg subtraction
            bkgnames.append(name)

    # get the date from the time series data
    date = data['time'][0][:8]
    print(len(data['time']))

    # time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name] = 'date'
    data[name] = []
    remove = []
    for n, val in enumerate(data['time']):
        try:
            dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
            data[name].append(dateobject)
        except ValueError:  # Incorrect time formatting, remove from data
            remove.append(n)

    if len(remove) != 0:  # If any time data wasn't correctly formatted
        for n in remove:
            for name in names:  # Remove line from all data
                data[name].pop(n)
            line = F'Removed line {n} from data due to invalid time format'
            print(line)
            logger.debug(line)
            logs.append(line)

    name = 'datenumbers'  # date objects to date numbers
    units[name] = 'date'
    names.append(name)
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)  # convert ndarray to a list in order to use index function
    data['datenumbers'] = datenums

    # add phase column to time series data
    name = 'phase'
    names.append(name)
    units[name] = 'text'
    data[name] = ['none'] * len(data['time'])

    ##############################################
    # check for phase times input file
    if os.path.isfile(timespath):
        line = f'PhaseTimes input file already exists: {timespath}\n' \
               f'Using previous inputs.'
        print(line)
        logger.info(line)
        logs.append(line)
    else:  # if input file is not there then create it
        # load EnergyInputs file
        [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)
        line = f'Loaded energy input file to get phase start and end times: {energyinputpath}'
        print(line)
        logger.info(line)
        logs.append(line)

        ####################################################
        #Create start and end times
        timenames = [enames[0]]  # start with header

        # Find format for phase start and end time entries
        for name in enames[1:]:
            if 'start_time' in name or 'end_time' in name:
                try:
                    # Attempt to parse time in 'yyyymmdd hh:mm:ss' format
                    dt.strptime(eval[name], '%Y%m%d %H:%M:%S')
                    timeformatstring = 'yyyymmdd hh:mm:ss'
                    break
                except (ValueError, NameError):
                    try:
                        # Attempt to parse time in 'hh:mm:ss' format
                        dt.strptime(eval[name], '%H:%M:%S')
                        timeformatstring = 'hh:mm:ss'
                        break
                    except Exception as e:
                        logger.error(
                            f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

        # add prebkg start time
        name = 'start_time_prebkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            # Attempt to create a date object with an offset of 4 minutes from time series start
            dateobject = data['dateobjects'][0] + timedelta(hours=0, minutes=4)
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except (KeyError, IndexError, TypeError):
            eval[name] = ''
        except Exception as e:
            logger.error(
                f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
        eunc[name] = ''

        # add prebkg end time
        name = 'end_time_prebkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            # Attempt to create a date object with an offset of 14 minutes from time series start
            dateobject = data['dateobjects'][0] + timedelta(hours=0, minutes=14)
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except (KeyError, IndexError, TypeError):
            eval[name] = ''
        except Exception as e:
            logger.error(
                f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
        eunc[name] = ''

        # add start and end times of test phases from the energy inputs file
        for name in enames[1:]:
            print(name)
            if 'start_time' in name or 'end_time' in name:
                timenames.append(name)
            else:
                try:
                    eval.pop(name)  # remove dictionary entry if variable is not a start or end time
                    eunc.pop(name)
                except KeyError:
                    pass
                except Exception as e:
                    logger.error(
                        f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

        # add post bkg start time
        name = 'start_time_postbkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            # Attempt to create a date object with an offset of 12 minutes from time series end
            dateobject = data['dateobjects'][-1] - timedelta(hours=0, minutes=12)
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except (KeyError, IndexError, TypeError):
            eval[name] = ''
        except Exception as e:
            logger.error(
                f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
        eunc[name] = ''

        # add post bkg end time
        name = 'end_time_postbkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            # Attempt to create a date object with an offset of 2 minutes from time series end
            dateobject = data['dateobjects'][-1] - timedelta(hours=0, minutes=2)
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except (KeyError, IndexError, TypeError):
            eval[name] = ''
        except Exception as e:
            logger.error(
                f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
        eunc[name] = ''

        # GUI box to edit input times (for adding bkg times)
        msg = f"Enter background start and end times. If start and end times are unknown, verify that the suggested " \
              f"inputs are valid times within the data series and press ok. You will be given a chance to modify" \
              f"them later. \n" \
              f"Time format = {eunits['start_time_prebkg']} \n\n" \
              f"Click OK to coninue\n" \
              f"Click Cancel to exit\n"
        title = "Start and End Times"
        fieldNames = timenames[1:]
        currentvals = []
        for name in timenames[1:]:
            currentvals.append(eval[name])  # Default/suggested values from energy inputs and data start and end
        newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)  # ask for new times
        if newvals:
            if newvals != currentvals:  # If user entered new values
                currentvals = newvals
                for n, name in enumerate(timenames[1:]):  # Save new values
                    eval[name] = currentvals[n]
        else:
            line = 'Undefined variables: start_time_prebkg, end_time_prebkg, start_time_postbkg, end_time_postbkg'
            print(line)
            logger.error(line)
            logs.append(line)

        io.write_constant_outputs(timespath, timenames, eunits, eval, eunc, euval)
        line = f'Created phase times input file: {timespath}'
        print(line)
        logger.info(line)
        logs.append(line)

    ##############################################
    # create background methods
    check = 0
    logs = bkgmethods(bkgmethodspath, logs, check, bkgnames)

    #########################################################

    # read in measurement uncertainty file
    [ucnames, ucunits, ucinputs] = io.load_timeseries(ucpath)

    # read in input file of phase start and end times
    [timenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(timespath)

    # read in input file of background subtraction methods
    [channels, methods, offsets, methodsunc, methodsuval] = io.load_constant_inputs(bkgmethodspath)

    # convert offsets from str to float
    for channel in channels:
        try:
            offsets[channel] = float(offsets[channel])
        except (KeyError, ValueError):
            pass

    ###############################################
    try:  # checking that all bkgseries exist in methods document(some were added later on)
        Data_bkgsubtracted = {}
        for name in names:  # for each channel
            Data_bkgsubtracted[name] = []
            if name in bkgnames:  # that will get background subtraction
                # make bkg series
                Data_bkgsubtracted[name] = 1
                if methods[name] == 'pre':
                    pass
    except KeyError:  # if a bkgseries doesn't exist, rerun methods document but make sure recreate it even if it exists
        check = 1
        logs = bkgmethods(bkgmethodspath, logs, check, bkgnames)
        # read in input file of background subtraction methods
        [channels, methods, offsets, methodsunc, methodsuval] = io.load_constant_inputs(bkgmethodspath)
        for channel in channels:
            try:
                offsets[channel] = float(offsets[channel])
            except (KeyError, ValueError):
                pass
    except Exception as e:
        logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

    ######################################################
    cycle = 0
    # Run functions to find time periods based on phase times and subtract data
    # Keep running functions until functions are successful, failure results in asking the user to enter valid inputs
    (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
     offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases, phaseindices,
     phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new,
     phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs,
                                    timeunits, channels,
                                    methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames,
                                    cycle, timespath, bkgmethodspath)

    if inputmethod == '1':  # If in interactive mode
        # plot data to check bkg and test periods
        plt.ion()  # turn on interactive plot mode

        lw = float(5)  # define the linewidth for the data series
        plw = float(2)  # define the linewidth for the bkg and sample period marker
        msize = 30  # marker size for start and end pints of each period

        colors = {}  # Define colors for plot
        for phase in phases:
            if phase == 'prebkg' or phase == 'postbkg':
                colors[phase] = 'r'
            elif phase == 'L1':
                colors[phase] = 'royalblue'
            elif phase == 'hp':
                colors[phase] = 'lawngreen'
            elif phase == 'mp':
                colors[phase] = 'orange'
            elif phase == 'lp':
                colors[phase] = 'y'
            elif phase == 'L5':
                colors[phase] = 'pink'
            else:
                colors[phase] = 'grey'

        f1, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)  # subplots sharing x axis
        plotnames = bkgnames
        for i, ax in enumerate(f1.axes):  # For each plot
            name = plotnames[i]
            # bkg data series
            ax.plot(data['datenumbers'], data_bkg[name], color='lavender', linewidth=lw, label='bkg_series')
            # original data series
            ax.plot(data['datenumbers'], data[name], color='silver', linewidth=lw, label='raw_data')
            # bkg subtracted data series
            ax.plot(data['datenumbers'], data_new[name], color='k', linewidth=lw, label='bkg_subtracted')
            for phase in phases:  # For each phase
                phasename = name + '_' + phase
                # original
                ax.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw, label=phase)
                # start and end markers
                ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                        [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase], linestyle='none',
                        marker='|', markersize=msize)
                ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                        [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase], linestyle='none',
                        marker='|', markersize=msize)
                # bkg subtracted
                ax.plot(phasedatenums[phase], phasedata_new[phasename], color=colors[phase], linewidth=plw)
                # start and end markers
                ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                        [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                        linestyle='none', marker='|', markersize=msize)
                ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                        [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                        linestyle='none', marker='|', markersize=msize)

            ax.set_ylabel(units[name])  # Add units to y-axis
            ax.set_title(name)  # Name plot with sensor name
            ax.grid(visible=True, which='major', axis='y')  # Create grid marks

        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # Format x-axis as a time
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)  # Rotate labels
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])  # squeeze it down to make room for the legend
        plt.subplots_adjust(top=.95, bottom=0.1)  # squeeze it verically to make room for the long x axis data labels
        ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5))  # Put a legend to the right of ax1

        #####################################################
        if len(plotnames) > 3:  # if more than 3 sensors that were bkg subtracted
            # second figure for 3 more subplots
            f2, (ax4, ax5, ax6) = plt.subplots(3, sharex=True)  # subplots sharing x axis
            try:
                for i, ax in enumerate(f2.axes):  # For each plot
                    name = plotnames[i + 3]
                    # bkg data series
                    ax.plot(data['datenumbers'], data_bkg[name], color='lavender', linewidth=lw, label='bkg_series')
                    # original data series
                    ax.plot(data['datenumbers'], data[name], color='silver', linewidth=lw, label='raw_data')
                    # bkg subtracted data series
                    ax.plot(data['datenumbers'], data_new[name], color='k', linewidth=lw, label='bkg_subtracted')
                    for phase in phases:  # For each phase
                        phasename = name + '_' + phase
                        # original
                        ax.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw, label=phase)
                        # start and end markers
                        ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase],
                                linestyle='none', marker='|', markersize=msize)
                        ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase],
                                linestyle='none', marker='|', markersize=msize)
                        # bkg shifted
                        ax.plot(phasedatenums[phase], phasedata_new[phasename], color=colors[phase], linewidth=plw)
                        # start and end markers
                        ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                                linestyle='none', marker='|', markersize=msize)
                        ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                                linestyle='none', marker='|', markersize=msize)
                    ax.set_ylabel(units[name])  # Add units to y-axis
                    ax.set_title(name)  # Name plot with sensor name
                    ax.grid(visible=True, which='major', axis='y')  # Create a grid
            except IndexError:
                pass
            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # Format x-axis as a time
            ax.xaxis.set_major_formatter(xfmt)
            for tick in ax.get_xticklabels():
                tick.set_rotation(30)  # rotate labels
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])  # squeeze it down to make room for legend
            plt.subplots_adjust(top=.95, bottom=0.1)  # squeeze it vertically to make room for long x axis data labels
            ax4.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1

        plt.show()  # show all figures
        ###############################################################################################
        # ask user to modify bkg methods and times
        running = 'fun'
        while running == 'fun':
            # GUI box to edit input times
            msg = f"Edit phase times\n" \
                  f"Time format = {timeunits['start_time_prebkg']} \n\n" \
                  f"Edit background subtraction methods\n" \
                  f"Format = method,offest\n" \
                  f"Methods:pre, post, prepoststave, prepostling, none\n\n" \
                  f"Pre finds the average value from the background period before the test and subtracts that " \
                  f"value from all values. Post does the same with the background period after the test. " \
                  f"Prepoststave finds the mean between the pre and post background periods and subtracts that " \
                  f"from all values. Prepostlin finds the linear equation between the pre and post background " \
                  f"periods and uses that to subtract from all value.\n" \
                  f"IF BOTH PRE AND POST BACKGROUND PERIODS ARE FLAT, THE PREFERED METHOD IS PREPOSTLIN.\n" \
                  f"Offsets: Offset by a specified value (add value to every number in data series)\n\n" \
                  f"Click OK to update plot\n" \
                  f"Click Cancel to exit\n"
            title = "Edit Times and Methods"
            fieldNames = timenames[1:]
            currentvals = []
            for name in timenames[1:]:
                currentvals.append(timestring[name])
            # append methods and offsets
            for name in channels[1:]:
                fieldNames.append(name)
                methodstring = methods[name] + ',' + str(offsets[name])
                currentvals.append(methodstring)
            newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)
            if newvals:
                if newvals != currentvals:  # If user entered new values
                    currentvals = newvals
                    for n, name in enumerate(fieldNames):
                        if 'time' in name:
                            timestring[name] = currentvals[n]
                        else:
                            try:
                                spot = currentvals[n].index(',')  # locate the comma
                                methods[name] = currentvals[n][:spot]  # grab the string before the comma
                                offsets[name] = currentvals[n][spot + 1:]  # grab the string after the comma
                            except ValueError:
                                message = f"Background method for {name} was not entered correctly. The Expected " \
                                          f"format is method,offset. Previous working methods will be shown again. " \
                                          f"When entering a new method please ensure the comma remains."
                                title = "ERROR"
                                easygui.msgbox(message, title, "OK")
                                # re-run functions
                                (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits,
                                 channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs,
                                 bkgnames, validnames, timeobject, phases, phaseindices, phasedatenums, phasedata,
                                 phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new,
                                 phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate,
                                                                names, data, ucinputs, timeunits, channels, methods,
                                                                offsets, methodsunc, methodsuval, timeunc, timeuval,
                                                                logs, bkgnames, cycle, timespath, bkgmethodspath)
                    # write new values
                    io.write_constant_outputs(bkgmethodspath, channels, methods, offsets, methodsunc, methodsuval)
                    line = 'Updated background subtraction methods input file:' + bkgmethodspath
                    print(line)
                    logger.info(line)
                    logs.append(line)

                    # convert offsets from str to float
                    for channel in channels:
                        try:
                            offsets[channel] = float(offsets[channel])
                        except (KeyError, ValueError):
                            pass

                    # write new values
                    io.write_constant_outputs(timespath, timenames, timeunits, timestring, timeunc, timeuval)
                    line = 'Updated phase times input file:' + timespath
                    print(line)
                    logs.append(line)
            else:  # cancel ends the interaction loop
                running = 'not fun'

            cycle = 1
            # run through functions with new vlaues
            (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
             offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases,
             phaseindices, phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums,
             phasedata_new, phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate, names,
                                                           data, ucinputs, timeunits, channels, methods, offsets,
                                                           methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames,
                                                           cycle, timespath, bkgmethodspath)

            reportlogs = printBkgReport(phases, bkgnames, bkgvalue, phasemean, phasemean_new, units, methods, offsets)

            ###################################################################
            # update plot
            ax1.get_legend().remove()

            for i, ax in enumerate(f1.axes):  # for each plot
                for n in range(len(ax.lines)):
                    plt.Artist.remove(ax.lines[0])  # remove old lines
                name = plotnames[i]
                # bkg data series
                ax.plot(data['datenumbers'], data_bkg[name], color='lavender', linewidth=lw, label='bkg_series')
                # original data series
                ax.plot(data['datenumbers'], data[name], color='silver', linewidth=lw, label='raw_data')
                # bkg subtracted data series
                ax.plot(data['datenumbers'], data_new[name], color='k', linewidth=lw, label='bkg_subtracted')
                for phase in phases:  # for each phase
                    phasename = name + '_' + phase
                    # original
                    ax.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw, label=phase)
                    # start and end markers
                    ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                            [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase], linestyle='none',
                            marker='|', markersize=msize)
                    ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                            [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase], linestyle='none',
                            marker='|', markersize=msize)
                    # bkg shifted
                    ax.plot(phasedatenums[phase], phasedata_new[phasename], color=colors[phase], linewidth=plw)
                    # start and end markers
                    ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                            [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                            linestyle='none', marker='|', markersize=msize)
                    ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                            [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                            linestyle='none', marker='|', markersize=msize)

            ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1

            f1.savefig(savefig1, bbox_inches='tight')  # save image
            f1.canvas.draw()

            #######################################################
            # second figure for 3 more subplots
            if len(plotnames) > 3:
                ax4.get_legend().remove()
                try:
                    for i, ax in enumerate(f2.axes):  # for each plot
                        for n in range(len(ax.lines)):
                            plt.Artist.remove(ax.lines[0])
                        name = plotnames[i + 3]
                        # bkg data series
                        ax.plot(data['datenumbers'], data_bkg[name], color='lavender', linewidth=lw, label='bkg_series')
                        # original data series
                        ax.plot(data['datenumbers'], data[name], color='silver', linewidth=lw, label='raw_data')
                        # bkg subtracted data series
                        ax.plot(data['datenumbers'], data_new[name], color='k', linewidth=lw, label='bkg_subtracted')
                        for phase in phases:  # for each phase
                            phasename = name + '_' + phase
                            ax.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw,
                                    label=phase)  # original
                            # start and end markers
                            ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                    [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase],
                                    linestyle='none', marker='|', markersize=msize)
                            ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                    [phasedata[phasename][0], phasedata[phasename][-1]], color=colors[phase],
                                    linestyle='none', marker='|', markersize=msize)
                            # bkg shifted
                            ax.plot(phasedatenums[phase], phasedata_new[phasename], color=colors[phase], linewidth=plw)
                            # start and end markers
                            ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                    [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                                    linestyle='none', marker='|', markersize=msize)
                            ax.plot([phasedatenums[phase][0], phasedatenums[phase][-1]],
                                    [phasedata_new[phasename][0], phasedata_new[phasename][-1]], color=colors[phase],
                                    linestyle='none', marker='|', markersize=msize)
                except IndexError:
                    pass
                ax4.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5))  # Put a legend to the right of ax1
                f2.savefig(savefig2, bbox_inches='tight')  # save image
                f2.canvas.draw()

    elif inputmethod == '2':
        reportlogs = []

    ######################################################
    # output new background subtracted time series data file
    # first add the background data series that were used for the subtraction
    newnames = []
    for name in names:
        newnames.append(name)
    for name in bkgnames:
        addname = name + '_bkg'
        newnames.append(addname)
        data_new[addname] = data_bkg[name]
        units[addname] = units[name]

    io.write_timeseries(outputpath, newnames, units, data_new)  # write background subtracted data

    line = 'Created background-corrected time series data file:\n' + outputpath
    print(line)
    logger.info(line)
    logs.append(line)

    # output time series data file for each phase
    for phase in phases:
        phaseoutputpath = outputpath[
                          :-4] + '_' + phase + '.csv'  # name the output file by inserting the phase name into
        # the outputpath
        phasedataoutput = {}  # initialize a dictionary of phase time series data for the output file
        for name in names:
            phasename = name + '_' + phase
            phasedataoutput[name] = phasedata_new[phasename]
        io.write_timeseries(phaseoutputpath, names, units, phasedataoutput)

        line = 'Created background-corrected time series data file:\n' + phaseoutputpath
        print(line)
        logger.info(line)
        logs.append(line)

    # output average values  #####################
    phasenames = []
    phaseunits = {}
    vals = {}
    unc = {}

    for phase in phases:
        for name in names:
            phasename = name + '_' + phase
            phasenames.append(phasename)
            if name == 'time':
                phaseunits[phasename] = 'yyyymmdd hh:mm:ss'
            else:
                phaseunits[phasename] = units[name]

    # Full period averages
    # Find first start time and last end time
    # Collect valid start and end times
    start_times = [timeuval[f'start_time_{phase}'] for phase in ['L1', 'hp', 'mp', 'lp', 'L5'] if
                   timeuval[f'start_time_{phase}']]
    end_times = [timeuval[f'end_time_{phase}'] for phase in ['L1', 'hp', 'mp', 'lp', 'L5'] if
                 timeuval[f'end_time_{phase}']]

    # Convert times to datetime objects
    try:
        start_times = [dt.strptime(t, '%Y%m%d %H:%M:%S') for t in start_times]
        end_times = [dt.strptime(t, '%Y%m%d %H:%M:%S') for t in end_times]
    except ValueError:
        # If times are in '%H:%M:%S' format, assume the date from the first fdata time
        time_data = [t.strip() for t in data_new['time']]
        earliest_fdata_date = time_data[0].split()[0]  # Extract the date from the first time entry

        # Recreate start and end times with the date prepended
        start_times = [f"{earliest_fdata_date} {timeuval[f'start_time_{phase}'].strip()}" for phase in
                       ['L1', 'hp', 'mp', 'lp', 'L5'] if timeuval[f'start_time_{phase}']]
        end_times = [f"{earliest_fdata_date} {timeuval[f'end_time_{phase}'].strip()}" for phase in
                     ['L1', 'hp', 'mp', 'lp', 'L5'] if timeuval[f'end_time_{phase}']]

        # Convert the adjusted times to datetime
        start_times = [dt.strptime(t, '%Y%m%d %H:%M:%S') for t in start_times]
        end_times = [dt.strptime(t, '%Y%m%d %H:%M:%S') for t in end_times]

    # Find the first valid start time and last valid end time
    start_time = min(start_times) if start_times else None
    end_time = max(end_times) if end_times else None

    # Convert fdata['time'] into datetime objects
    time_data = [dt.strptime(t, '%Y%m%d %H:%M:%S') for t in data_new['time']]

    # Find indices where the time is within the desired range
    cut_indices = [i for i, t in enumerate(time_data) if start_time <= t <= end_time]

    data_full = {}

    # Filter the data by these indices
    for name in data_new.keys():
        data_full[name] = [data_new[name][i] for i in cut_indices]

    for name in data_full.keys():
        phasename = name + '_full'
        phasenames.append(phasename)
        phaseunits[phasename] = units[name]
        try:
            phasemean_new[phasename] = sum(data_full[name]) / len(data_full[name])
        except ZeroDivisionError:
            phasemean_new[phasename] = ''
        except TypeError:
            phasemean_new[phasename] = ''

    # make header for averages file
    name = 'variable_name'
    phasenames = [name] + phasenames
    phaseunits[name] = 'units'
    phasemean_new[name] = 'average'
    unc[name] = 'uncertainty'

    io.write_constant_outputs(aveoutputpath, phasenames, phaseunits, vals, unc, phasemean_new)  # write all averages

    line = 'Created phase averages data file:\n' + aveoutputpath
    print(line)
    logger.info(line)
    logs.append(line)

    end_time = dt.now()
    log = f"Execution time: {end_time - start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    return logs, methods, timestring, phasemean_new


def run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels,
                  methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, cycle, timespath,
                  bkgmethodspath):
    # Function calls other functions. Converts time strings. Define phases. Finds indicies of time periods. Grabs
    # data for each phase. Subtracts background. Asks user for new entries if anything fails.

    [validnames, timeobject] = makeTimeObjects(timenames, timestring, date)  # convert time strings to time objects

    phases = definePhases(validnames)  # read the names of the start and end times to get the name of each phase

    phaseindices = findIndices(validnames, timeobject, datenums,
                               sample_rate)  # find the indices in the time data series for the start and stop times
    # of each phase

    try:
        [phasedatenums, phasedata, phasemean] = definePhaseData(names, data, phases, phaseindices,
                                                                ucinputs)  # define phase data series for each channel
    except KeyError as e:
        e = str(e)
        message = f"Variable: {e} was entered incorrectly or is outside of the measured time period\n" \
                  f"* Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                  f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                  f"    * Check that the entered time exist within the data\n" \
                  f"    * Check that the time has not been left blank when there should be an entry.\n"
        title = "ERROR"
        easygui.msgbox(message, title, "OK")

        # Request new entries
        timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval, \
            logs = request_entry(timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval,
                                 timeunc, timeuval, logs, timespath, bkgmethodspath)

        # Run functions with new entries
        (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
         offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases,
         phaseindices, phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new,
         phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs,
                                        timeunits, channels, methods, offsets, methodsunc, methodsuval, timeunc,
                                        timeuval, logs, bkgnames, cycle, timespath, bkgmethodspath)

    if cycle == 1:
        # update the data series column named phase
        name = 'phase'
        data[name] = ['none'] * len(data['time'])  # clear all values to none
        for phase in phases:
            for n, val in enumerate(data['time']):
                if phaseindices['start_time_' + phase] <= n <= phaseindices['end_time_' + phase]:
                    if data[name][n] == 'none':
                        data[name][n] = phase
                    else:
                        data[name][n] = data[name][n] + ',' + phase

    [bkgvalue, data_bkg, data_new] = bkgSubtraction(names, data, bkgnames, phasemean, phaseindices, methods,
                                                    offsets)  # subtract the background

    # define phase data series after background subtraction
    [phasedatenums, phasedata_new, phasemean_new] = definePhaseData(names, data_new, phases, phaseindices, ucinputs)

    io.write_constant_outputs(bkgmethodspath, channels, methods, offsets, methodsunc, methodsuval)  # write times and
    # methods

    return (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
            offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases,
            phaseindices, phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums,
            phasedata_new, phasemean_new)


def makeTimeObjects(Timenames, Timestring, Date):
    # Fuction converts entered times to time objects and validates entries

    Timeobject = {}  # initialize a dictionary of time objects
    Validnames = []  # initialize a list of time names that have a valid time entered
    for Name in Timenames:
        if len(Timestring[Name]) == 8:  # if time format
            Datestring = Date + ' ' + Timestring[Name]  # add the date to the time string
        else:  # if already date format
            Datestring = Timestring[Name]  # use it as is
        try:
            Timeobject[Name] = dt.strptime(Datestring, '%Y%m%d %H:%M:%S')  # convert the time string to date object
            Validnames.append(Name)
        except ValueError:
            try:
                Timeobject[Name] = dt.strptime(Datestring, '%Y-%m-%d %H:%M:%S')
                # convert the time string to date object
                Validnames.append(Name)
            except ValueError:
                pass

    return Validnames, Timeobject


def request_entry(timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc,
                  timeuval, logs, timespath, bkgmethodspath):
    # Function asks for new entries for time and methods if a failure occurs

    msg = f"ONE OR MORE INVALID PHASE TIMES.\n" \
          f"EDIT PHASE TIMES AND TRY AGAIN\n" \
          f"Time format = {timeunits['start_time_prebkg']} \n\n" \
          f"Edit background subtraction methods\n" \
          f"Format = method,offest\n" \
          f"Methods:pre, post, prepoststave, prepostling, none\n\n" \
          f"Pre finds the average value from the background period before the test and subtracts that " \
          f"value from all values. Post does the same with the background period after the test. " \
          f"Prepoststave finds the mean between the pre and post background periods and subtracts that " \
          f"from all values. Prepostlin finds the linear equation between the pre and post background " \
          f"periods and uses that to subtract from all value.\n" \
          f"IF BOTH PRE AND POST BACKGROUND PERIODS ARE FLAT, THE PREFERED METHOD IS PREPOSTLIN.\n" \
          f"Offsets: Offset by a specified value (add value to every number in data series)\n\n" \
          f"Click OK to update plot\n" \
          f"Click Cancel to exit\n"
    title = "Edit Times and Methods"
    fieldNames = timenames[1:]
    currentvals = []
    for name in timenames[1:]:
        currentvals.append(timestring[name])
    # append methods and offsets
    for name in channels[1:]:
        fieldNames.append(name)
        methodstring = methods[name] + ',' + str(offsets[name])
        currentvals.append(methodstring)
    newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)
    if newvals:
        if newvals != currentvals: # If new values were entered
            currentvals = newvals
            for n, name in enumerate(fieldNames):
                if 'time' in name:
                    timestring[name] = currentvals[n]
                else:
                    spot = currentvals[n].index(',')  # locate the comma
                    methods[name] = currentvals[n][:spot]  # grab the string before the comma
                    offsets[name] = currentvals[n][spot + 1:]  # grab the string after the comma

            # Update and write new values
            io.write_constant_outputs(bkgmethodspath, channels, methods, offsets, methodsunc, methodsuval)

            # convert offsets from str to float
            for channel in channels:
                try:
                    offsets[channel] = float(offsets[channel])
                except KeyError:
                    pass

            #Update and write new values
            io.write_constant_outputs(timespath, timenames, timeunits, timestring, timeunc, timeuval)

    return timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval, \
        logs


def definePhases(Timenames):
    # Function finds all the phases that exist in the data
    Phases = []  # initialize a list of test phases (prebkg, low power, med power, high power, post bkg)
    for Name in Timenames:
        spot = Name.rindex('_')  # locate the last underscore
        Phase = Name[spot + 1:]  # grab the string after the last underscore
        if Phase not in Phases:  # if it is a new phase
            Phases.append(Phase)  # add to the list of phases
    return Phases


def findIndices(InputTimeNames, InputTimeObject, Datenums, Sample_Rate):
    # Function finds the index number in the timeseries data for each entered time
    InputTimeDatenums = {}  # Dictionary of input times as date numbers, key is phase start and end
    Indices = {}  # Dictionary of indicies in the time series, key is phase start and end
    for Name in InputTimeNames:  # For each phase start and end
        m = 0
        ind = 0
        while m <= (Sample_Rate * 2) + 1 and ind == 0:  # Cycle through the sample rate to find a valid time
            try:
                InputTimeDatenums[Name] = matplotlib.dates.date2num(InputTimeObject[Name])
                Indices[Name] = Datenums.index(InputTimeDatenums[Name])  # Find index of entered time
                ind = 1  # Record the index was found
            except (ValueError, IndexError):  # If there is not a matching time in the time series
                InputTimeObject[Name] = InputTimeObject[Name] + timedelta(seconds=1)  # Add a second to the time and
                # try again
                m += 1
    return Indices


def definePhaseData(Names, Data, Phases, Indices, Ucinputs):
    # Function grabs time series data for each phase and averages data over the phase time period

    Phasedatenums = {}  # Dictionary of date numbers within the phase, key is phase
    Phasedata = {}  # Dictionary of data within the phase start and end times, key is sensor names
    Phasemean = {}  # Dictionary of time series averages, key is sensor names
    for Phase in Phases:  # for each test phase
        # make data series of date numbers
        key = 'start_time_' + Phase
        startindex = Indices[key]
        key = 'end_time_' + Phase
        endindex = Indices[key]
        Phasedatenums[Phase] = Data['datenumbers'][startindex:endindex + 1]  # Collect date numbers from start to end
        # of phase

        # make phase data series for each data channel
        for Name in Names:  # For each sensor
            Phasename = Name + '_' + Phase
            Phasedata[Phasename] = Data[Name][startindex:endindex + 1]  # Collect data from start to end of phase
            remove = []
            for n, val in enumerate(Phasedata[Phasename]):
                if val == '':  # Remove invalid blank values to avoid calculation errors
                    remove.append(n)
            if len(remove) != 0:
                for n in remove:
                    for name in Names:  # remove data for every sensor in the invalid index
                        Phasedata[name + '_' + Phase].pop(n)

            # calculate average value
            if Name != 'time' and Name != 'phase':  # don't calculate for phase or time columns
                non_nan_values = [value for value in Phasedata[Phasename] if not np.isnan(value)]  # Check if there's
                # nan values
                if len(non_nan_values) == 0:  # if there's only nan vlaues (unplugger sensors), don't average
                    Phasemean[Phasename] = np.nan
                else:
                    ave = np.mean(non_nan_values)  # Average valid data streams
                    if Name == 'datenumbers':
                        Phasemean[Phasename] = ave
                    else:
                        uc = abs(float(Ucinputs[Name][0]) + ave * float(Ucinputs[Name][1]))  # Uncertainty of average
                        Phasemean[Phasename] = ufloat(ave, uc)

        # time channel: use the mid-point time string
        Phasename = 'datenumbers_' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean


def bkgSubtraction(Names, Data, Bkgnames, Phasemean, Indices, Methods, Offsets):
    # Function takes in data, times, offsets, and background methods. Subtracts background from data according to
    # the method. Offsets data according to offset. Returns background subtracted data
    Bkgvalue = {}  # dictionary of constant bkg values
    Data_bkgseries = {}  # data series that will get subtracted
    Data_bkgsubtracted = {}  # new data series after bkg subtraction

    for Name in Names:  # For each sensor
        remove = []
        for n, val in enumerate(Data[Name]):
            if val == '':  # If there's a blank in the data stream, remove the row to avoid calculation errors
                remove.append(n)
        if len(remove) != 0:
            for Name in Names:
                for n in remove:
                    Data[Name].pop(n)
    for Name in Names:  # for each channel
        Data_bkgsubtracted[Name] = []
        if Name in Bkgnames:  # that will get background subtraction
            # make bkg series
            Data_bkgseries[Name] = []
            if Methods[Name] == 'pre':  # Pre value is average of pre background period - offset
                Bkgvalue[Name] = Phasemean[Name + '_prebkg'].n - Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'post':  # Post value is average of pre background period - offset
                Bkgvalue[Name] = Phasemean[Name + '_postbkg'].n - Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostave':  # Prepost stave value is the average of the average of pre and post
                # grabround perios - offset
                Bkgvalue[Name] = np.mean([Phasemean[Name + '_prebkg'].n, Phasemean[Name + '_postbkg'].n]) - Offsets[
                    Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostlin':  # Prepostlin value is the slope of a line made by the average pre and
                # post value - offset
                Bkgvalue[Name] = -Offsets[Name]
                x1 = int((Indices['start_time_prebkg'] + Indices['end_time_prebkg'] + 1) / 2)  # middle index of prebkg
                y1 = Phasemean[Name + '_prebkg'].n  # prebkg average value
                x2 = int(
                    (Indices['start_time_postbkg'] + Indices['end_time_postbkg'] + 1) / 2)  # middle index of postbkg
                y2 = Phasemean[Name + '_postbkg'].n  # post bkg average value
                # equation of line from 2 points, y=mx+b
                m = (y2 - y1) / (x2 - x1)
                b = y1 - x1 * (y2 - y1) / (x2 - x1)
                for x, val in enumerate(Data[Name]):
                    y = m * x + b
                    Data_bkgseries[Name].append(y + Bkgvalue[Name])
            elif Methods[Name] == 'realtime':  # Realtime depends on the sensor having a secondary sensor sampling
                # ambient air for the duration of the test - currently non existent in any sensor box
                Bkgvalue[Name] = -Offsets[Name]
                if 'hi' in Name:
                    bkgseriesname = Name[:-2]
                else:
                    bkgseriesname = Name

                for x, val in enumerate(Data[bkgseriesname + 'bkg']):  # realtime bkg series
                    Data_bkgseries[Name].append(val + Bkgvalue[Name])
            else:  # None or non valid methods will just apply offset
                Bkgvalue[Name] = -Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])

            # subtract bkg data series
            for n, val in enumerate(Data[Name]):
                try:
                    newval = val - Data_bkgseries[Name][n]
                    Data_bkgsubtracted[Name].append(newval)
                except TypeError:
                    Data[Name].pop(n)  # Remove invalid values
        else:  # if no bkg subtraction, data is the same as input data
            Data_bkgsubtracted[Name] = Data[Name]

    return Bkgvalue, Data_bkgseries, Data_bkgsubtracted


def printBkgReport(Phases, Bkgnames, Bkgvalue, Phasemean, Phasemean_new, Units, Methods, Offsets):
    # Function prints a report on what was background subtracted and other calculated values.

    # add arg to print to log file
    Reportlogs = []  # List of repost lines
    line = '\nbackground subtraction report:'
    print(line)
    Reportlogs.append(line)
    line = '\nphase averages before background subtraction:'
    print(line)
    Reportlogs.append(line)
    line1 = 'channel'.ljust(10) + 'units'.ljust(10)
    line2 = '-------'.ljust(10) + '-----'.ljust(10)
    for Phase in Phases:
        line1 = line1 + Phase.ljust(10)
        line2 = line2 + '------'.ljust(10)
    line1 = line1 + 'bkgValue'.ljust(10) + 'offset'.ljust(10) + 'method'.ljust(10)
    line2 = line2 + '------'.ljust(10) + '------'.ljust(10) + '------'.ljust(10)
    print(line1)
    Reportlogs.append(line1)
    print(line2)
    Reportlogs.append(line2)
    for Name in Bkgnames:
        line = Name.ljust(10) + str(Units[Name]).ljust(10)
        for Phase in Phases:
            Phasename = Name + '_' + Phase
            line = line + str(round(Phasemean[Phasename].n, 1)).ljust(10)
        line = line + str(round(Bkgvalue[Name], 1)).ljust(10) + str(round(Offsets[Name], 1)).ljust(10) + \
               Methods[Name].ljust(10)
        print(line)
        Reportlogs.append(line)

    line = '\nphase averages after background subtraction:'
    print(line)
    Reportlogs.append(line)
    print(line1)
    Reportlogs.append(line1)
    print(line2)
    Reportlogs.append(line2)
    for Name in Bkgnames:
        line = Name.ljust(10) + str(Units[Name]).ljust(10)
        for Phase in Phases:
            Phasename = Name + '_' + Phase
            line = line + str(round(Phasemean_new[Phasename].n, 1)).ljust(10)
        print(line)
        Reportlogs.append(line)

    return Reportlogs


def bkgmethods(bkgmethodspath, logs, check, bkgnames):
    # Function asks user to enter methods and offsets, saves entered values to specified file path

    # check for background subtraction methods input file
    if os.path.isfile(bkgmethodspath) and check != 1:
        line = '\nBackground subtraction methods input file already exists:'
        print(line)
        logs.append(line)

    else:  # if input file is not there then create it
        working = False
        while not working:
            # GUI box to edit background subtraction methods
            zeroline = 'Enter background subtraction: method,offset\n\n'
            firstline = 'methods: pre, post, prepostave, prepostlin, realtime, none\n\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit\n'
            msg = zeroline + firstline + secondline + thirdline
            title = "Gitrdone"
            fieldNames = bkgnames
            currentvals = []
            for name in fieldNames:
                currentvals.append('pre,0')
            newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)
            if newvals:
                if newvals != currentvals:
                    currentvals = newvals
            else:
                line = 'Error: Undefined background subtraction methods'
                print(line)
                logs.append(line)
            methods = {}  # initialize dictionary of background subtraction methods
            offsets = {}  # initialize dictionary of background subtraction offsets
            blank = {}  # initialize dictionary of blank values
            fieldNames = ['channel'] + fieldNames  # add header
            methods['channel'] = 'method'  # add header
            offsets['channel'] = 'offset'  # add header
            error = 0
            for n, name in enumerate(fieldNames[1:]):  # for each channel
                try:
                    spot = currentvals[n].index(',')  # locate the comma
                    methods[name] = currentvals[n][:spot]  # grab the string before the comma
                    offsets[name] = currentvals[n][spot + 1:]  # grab the string after the comma
                    blank[name] = ''
                except ValueError:
                    message = f"Background method for {name} was entered incorrectly. Correct format is " \
                              f"method,offset. Default will be shown again, when entering a new method please ensure " \
                              f"comma remains."
                    title = "ERROR"
                    easygui.msgbox(message, title, "OK")
                    error = 1
            if error != 1:
                working = True
        io.write_constant_outputs(bkgmethodspath, fieldNames, methods, offsets, blank, blank)
        line = '\nCreated background subtraction methods input file:'
        print(line)
        logs.append(line)

    line = bkgmethodspath
    print(line)
    logs.append(line)

    return logs
    #######################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath, logger,
                     savefig1, savefig2, inputmethod)
