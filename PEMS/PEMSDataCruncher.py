# v0 Python3
# Master program to calculate stove test energy metrics following ISO 19867

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

# full data processing using carbon balance method and stack flow method

import sys
import easygui
import os
import LEMS_DataProcessing_IO as io
from PEMS_EnergyCalcs import PEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from PEMS_SubtractBkg import PEMS_SubtractBkg
from PEMS_GravCalcs import PEMS_GravCalcs
from PEMS_CarbonBalanceCalcs import PEMS_CarbonBalanceCalcs
from PEMS_Plotter1 import PEMS_Plotter
from PEMS_Realtime import PEMS_Realtime
from PEMS_FuelExactCuts import PEMS_FuelExactCuts
from PEMS_FuelCuts import PEMS_FuelCuts
from PEMS_FuelScript import PEMS_FuelScript
from PEMS_2041 import PEMS_2041
import traceback
from PEMS_SubtractBkgPitot import PEMS_SubtractBkgPitot
from PEMS_StackFlowCalcs import PEMS_StackFlowCalcs
from PEMS_StackFlowMetricCalcs import PEMS_StackFlowMetricCalcs
from PEMS_MultiCutPeriods import PEMS_MultiCutPeriods
from PEMS_AddCH4 import PEMS_AddCH4
from turtle import shape
import pandas as pd
import numpy as np
import glob
from csv import reader
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import PEMS_FuelCalcs
import itertools
from decimal import *
import itertools
from itertools import chain
from io import StringIO
import re
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PEMS_CSVFormatted_L1 import PEMS_CSVFormatted_L1


logs = []

# list of function descriptions in order:
funs = ['plot raw data',
        'calculate fuel metrics',
        'calculate energy metrics',
        'adjust sensor calibrations',
        'correct for response times',
        'subtract background',
        'calculate CH4',
        'calculate gravimetric PM',
        'calculate emission metrics',
        'zero pitot tube',
        'calculate stack flow',
        'calculate stack flow metrics',
        'perform realtime calculations (one cut period)',
        'perform realtime calculations (multiple cut periods)',
        'plot processed data',
        'plot processed data for averaging period only',
        'create custom output table']

donelist = [''] * len(funs)  # initialize a list that indicates which data processing steps have been done


##################################################################

# Error handling function that prints the error and keeps the terminal open so the user can read the error
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)
    # For launcher. If error, holds terminal open so user knows what to fix


sys.excepthook = show_exception_and_exit


####################################################

# this function updates the donelist when a data processing step is completed
# Allows for steps to be skipped if files from previous steps already exist
# To do: currently if files do no exist from skipped steps there is just error. Make user friendly to prompt for missing files
# Create optional steps and allow for optional steps to be skipped
def updatedonelist(donelist, var):
    index = int(var) - 1
    donelist[index] = '(done)'  # mark the completed step as 'done'

    for num, item in enumerate(donelist):  # mark the remaining steps as 'not done'
        if num < index:  # Mark steps as passed if they weren't run
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num] = ''
    return donelist


def updatedonelisterror(donelist, var):
    index = int(var) - 1
    donelist[index] = '(error)'  # mark the completed step as 'done'

    for num, item in enumerate(donelist):  # mark the remaining steps as 'not done'
        if num < index:  # Mark steps as passed if they weren't run
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num] = ''
    return donelist


line = '\nPEMSDataCruncher_v0.0\n'
print(line)
logs.append(line)

# Can this be a menu item so that the program can be ran without choosing a specific test? or can this gui be used just to choose the level 3 directory?
inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    sheetinputpath = input("Input path of _EnergyInputs.csv file:\n")
else:
    print('Select _EnergyInputs.csv file:')
    sheetinputpath = easygui.fileopenbox()
if sheetinputpath:
    line = sheetinputpath
    print(line)
    # logs.append(line)

    directory, filename = os.path.split(sheetinputpath)
    datadirectory, testname = os.path.split(directory)
    logname = testname + '_log.txt'
    logpath = os.path.join(directory, logname)

    var = 'unicorn'
else:
    print('Cancel')
    print('No test selected')
    print('Exit')
    var = 'exit'

#######################################################

while var != 'exit':
    print('')
    print('----------------------------------------------------')
    print('testname = ' + testname)
    print('Data processing steps:')

    print('')
    for num, fun in enumerate(funs):  # print the list of data processing steps
        print(donelist[num] + str(num + 1) + ' : ' + fun)
    print('exit : exit program')
    print('')
    var = input("Enter menu option: ")

    if var == '1':  # Plot raw data
        print('')
        inputpath = os.path.join(directory,
                                 testname + '_RawData.csv')  # Not currently working for SB2041 - rawdata formatted wrong
        fuelpath = os.path.join(directory, testname + '_null.csv')  # No fuel or exact taken in
        exactpath = os.path.join(directory, testname + '_null.csv')
        scalepath = os.path.join(directory, testname + '_RawScaleData.csv')
        nanopath = os.path.join(directory, testname + '_RawNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_RawTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
        fuelmetricpath = os.path.join(directory, testname + '_null.csv')
        plotpath = os.path.join(directory, testname + '_rawplots.csv')
        savefig = os.path.join(directory, testname + '_rawplot.png')
        try:
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, plotpath, savefig = \
                PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, plotpath, savefig, logpath)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, plotpath,
                                savefig)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
            print(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
    elif var == '2':  # Plot and cut exact and fuel data
        inputpath = os.path.join(directory, testname + '_FuelData.csv')
        energypath = os.path.join(directory, testname + '_EnergyInputs.csv')
        exactpath = os.path.join(directory, testname + '_ExactData.csv')
        fueloutputpath = os.path.join(directory, testname + '_FuelDataCut.csv')
        exactoutputpath = os.path.join(directory, testname + '_ExactDataCut.csv')
        fulloutputpath = os.path.join(directory, testname + '_FuelMetrics.csv')
        savefig = os.path.join(directory, testname + '_fuelexactcuts.png')
        # if os.path.isfile(exactpath):
        try:
            PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, fulloutputpath,
                               savefig, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '3':  # Calculate energy metrics
        print('')
        inputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
        outputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        try:
            PEMS_EnergyCalcs(inputpath, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '4':  # Recalibrate data
        print('')
        energyinputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)  # Load energy metrics
        inputpath = os.path.join(directory, testname + '_RawData.csv')
        outputpath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
        try:
            try:
                if eval['SB'] == '2041':  # If SB2041 (PC) send to function to reformat data
                    PEMS_2041(inputpath, outputpath, logpath)
                else:  # All other data goes to recalibration
                    headerpath = os.path.join(directory, testname + '_Header.csv')
                    LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
                    updatedonelist(donelist, var)
            except:  # If no SB is entered, go to standard recalibration
                headerpath = os.path.join(directory, testname + '_Header.csv')
                LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
                updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '5':  # Adjust for response time
        print('')
        inputpath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
        outputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
        timespath = os.path.join(directory, testname + '_TimeShifts.csv')
        try:
            LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '6':  # Subtract background
        print('')
        inputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
        energyinputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        outputpath = os.path.join(directory, testname + '_TimeSeries.csv')
        aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
        timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
        bkgmethodspath = os.path.join(directory, testname + '_BkgMethods.csv')
        savefig1 = os.path.join(directory, testname + '_subtractbkg1.png')
        savefig2 = os.path.join(directory, testname + '_subtractbkg2.png')
        savefig3 = os.path.join(directory, testname + '_subtractbkg3.png')
        try:
            PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath,
                             logpath, savefig1, savefig2, savefig3)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '7': #add CH4
        print('')
        inputpath = os.path.join(directory, testname + '_TimeSeries.csv')
        outputpath = os.path.join(directory, testname + '_TimeSeries.csv')
        # outputpath=os.path.join(directory,testname+'_TimeSeries_wCH4.csv')
        aveinputpath = os.path.join(directory, testname + '_Averages.csv')
        aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
        # aveoutputpath=os.path.join(directory,testname+'_Averages_wCH4.csv')
        matrixpath = os.path.join(directory, testname + '_CrossSensitivityMatrix.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        try:
            PEMS_AddCH4(inputpath, outputpath, aveinputpath, aveoutputpath, matrixpath, ucpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '8':  # Calculate gravimetric data
        print('')
        gravinputpath = os.path.join(directory, testname + '_GravInputs.csv')
        timeseriespath = os.path.join(directory, testname + '_TimeSeries.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        gravoutputpath = os.path.join(directory, testname + '_GravOutputs.csv')
        try:
            PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '9':  # Calculate emissions metrics
        print('')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        gravinputpath = os.path.join(directory, testname + '_GravOutputs.csv')
        aveinputpath = os.path.join(directory, testname + '_Averages.csv')
        metricpath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        try:
            PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '10':  # zero pitot
        print('')
        inputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
        energyinputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        outputpath = os.path.join(directory, testname + '_TimeSeriesPitot.csv')
        aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
        timespath = os.path.join(directory, testname + '_PhaseTimesPitot.csv')
        bkgmethodspath = os.path.join(directory, testname + '_BkgMethodsPitot.csv')
        try:
            PEMS_SubtractBkgPitot(inputpath, energyinputpath, ucpath, outputpath, timespath, bkgmethodspath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '11':  # calculate stak velocity
        print('')
        inputpath = os.path.join(directory, testname + '_TimeSeriesPitot.csv')
        stackinputpath = os.path.join(directory, testname + '_StackFlowInputs.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        gravpath = os.path.join(directory, testname + '_GravOutputs.csv')
        metricpath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        dilratinputpath = os.path.join(directory, testname + '_DilRatInputs.csv')
        outputpath = os.path.join(directory, testname + '_TimeSeriesStackFlow.csv')
        savefig3 = os.path.join(directory, testname + '_dilrat.png')
        try:
            PEMS_StackFlowCalcs(inputpath, stackinputpath, ucpath, gravpath, metricpath, energypath, dilratinputpath,
                                outputpath, logpath, savefig3)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '12':  # calculate stak velocity metrics
        print('')
        inputpath = os.path.join(directory, testname + '_TimeSeriesStackFlow.csv')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        carbalpath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        avgpath = os.path.join(directory, testname + '_Averages.csv')
        gravpath = os.path.join(directory, testname + '_GravOutputs.csv')
        metricpath = os.path.join(directory, testname + '_StackFlowEmissionOutputs.csv')
        alloutputpath = os.path.join(directory, testname + '_AllOutputs.csv')
        try:
            PEMS_StackFlowMetricCalcs(inputpath, energypath, carbalpath, avgpath, gravpath, metricpath, alloutputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '13':  # Calculate realtime and cut for one period
        print('')
        inputpath = os.path.join(directory, testname + '_TimeSeries_test.csv')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        gravinputpath = os.path.join(directory, testname + '_GravOutputs.csv')
        empath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        stakpath = os.path.join(directory, testname + '_TimeSeriesStackFlow.csv')
        stakempath = os.path.join(directory, testname + '_StackFlowEmissionOutputs.csv')
        periodpath = os.path.join(directory, testname + '_AveragingPeriod.csv')
        outputpath = os.path.join(directory, testname + '_RealtimeOutputs.csv')
        fullaverageoutputpath = os.path.join(directory, testname + '_RealtimeAveragesOutputs.csv')
        averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodOutputs.csv')
        averagecalcoutputpath = os.path.join(directory, testname + '_AveragingPeriodCalcs.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        savefig = os.path.join(directory, testname)
        try:
            PEMS_Realtime(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, periodpath, outputpath,
                          averageoutputpath,
                          averagecalcoutputpath, fullaverageoutputpath, savefig, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        print('')

    elif var == '14':  # Calculate realtime and cut for multiple periods
        inputpath = os.path.join(directory, testname + '_TimeSeries_test.csv')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        gravinputpath = os.path.join(directory, testname + '_GravOutputs.csv')
        empath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        stakpath = os.path.join(directory, testname + '_TimeSeriesStackFlow.csv')
        stakempath = os.path.join(directory, testname + '_StackFlowEmissionOutputs.csv')
        fuelmetricpath = os.path.join(directory, testname + '_FuelMetrics.csv')
        fuelpath = os.path.join(directory, testname + '_FuelDataCut.csv')
        cutpath = os.path.join(directory, testname + '_CutTimes.csv')
        periodpath = os.path.join(directory, testname + '_AveragingPeriod.csv')
        outputpath = os.path.join(directory, testname + '_RealtimeOutputs.csv')
        fullaverageoutputpath = os.path.join(directory, testname + '_RealtimeAveragesOutputs.csv')
        averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodOutputs.csv')
        averagecalcoutputpath = os.path.join(directory, testname + '_AveragingPeriodCalcs.csv')
        savefig = os.path.join(directory, testname + '_Multicut.png')
        try:
            PEMS_MultiCutPeriods(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, fuelmetricpath,
                                 fuelpath, cutpath, outputpath, averageoutputpath, averagecalcoutputpath,
                                 fullaverageoutputpath, savefig, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)


    elif var == '15':  # Plot full data series
        print('')
        inputpath = os.path.join(directory, testname + '_FuelData.csv')
        energypath = os.path.join(directory, testname + '_N/A')
        exactpath = os.path.join(directory, testname + '_ExactData.csv')
        fueloutputpath = os.path.join(directory, testname + '_FuelDataProcessed.csv')
        exactoutputpath = os.path.join(directory, testname + '_ExactDataProcessed.csv')
        fulloutputpath = os.path.join(directory, testname + '_FuelMetricsFull.csv')
        savefigfuel = os.path.join(directory, testname + '_fullperiodfuel.png')
        ''''
        try:
            PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, fulloutputpath,
                               savefigfuel, logpath)  # Output full period fuel and exact
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        '''
        inputpath = os.path.join(directory, testname + '_RealtimeOutputs.csv')
        fuelpath=os.path.join(directory, testname + '_FuelDataCut.csv')
        fuelmetricpath = os.path.join(directory, testname + '_FuelMetrics.csv')
        exactpath=os.path.join(directory, testname + '_ExactDataCut.csv')
        scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
        plotpath = os.path.join(directory, testname + '_plots.csv')
        savefig = os.path.join(directory, testname + '_fullperiodplot.png')
        try:
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, plotpath, savefig =\
                PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, plotpath, savefig, logpath)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, plotpath,
                                savefig)
            updatedonelist(donelist,var)
            line='\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)


    elif var == '16':  # Plot period data series
        print('')
        # Plot over averaging period only, not full data set
        inputpath = os.path.join(directory, testname + '_FuelData.csv')
        energypath = os.path.join(directory, testname + '_AveragingPeriod.csv')
        exactpath = os.path.join(directory, testname + '_ExactData.csv')
        fueloutputpath = os.path.join(directory, testname + '_FuelDataAverageCut.csv')
        exactoutputpath = os.path.join(directory, testname + '_ExactDataAverageCut.csv')
        fulloutputpath = os.path.join(directory, testname + '_FuelMetrics.csv')
        savefig = os.path.join(directory, testname + '_averagingperiodplot.png')
        savefigfuel = os.path.join(directory, testname + '_averagingperiodfuel.png')
        try:
            PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, fulloutputpath, savefigfuel,
                               logpath)  # Recut fuel and exact
            inputpath = os.path.join(directory, testname + '_AveragingPeriodOutputs.csv')
            fuelpath = os.path.join(directory, testname + '_FuelDataCut.csv')
            fuelmetricpath = os.path.join(directory, testname + '_FuelMetrics.csv')
            exactpath = os.path.join(directory, testname + '_ExactDataCut.csv')
            scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
            nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
            TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
            senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
            OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
            plotpath = os.path.join(directory, testname + '_averageplots.csv')
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, plotpath, savefig = \
                PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath,
                             senserionpath, OPSpath, plotpath, savefig, logpath)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames,
                                plotpath, savefig)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
            print(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '17': #create custom output table
        print('')
        energyinputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        emissioninputpath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        stackinputpath = os.path.join(directory, testname + '_AllOutputs.csv')
        outputpath = os.path.join(directory, testname + '_CustomCutTable.csv')
        outputexcel = os.path.join(directory, testname + '_CustomCutTable.xlsx')
        csvpath = os.path.join(directory, testname + '_CutTableParameters.csv')
        try:
            PEMS_CSVFormatted_L1(energyinputpath, emissioninputpath, stackinputpath, outputpath, outputexcel, csvpath, testname, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e: #If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == 'exit':
        pass

    else:
        print(var + ' is not a menu option')

