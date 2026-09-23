#v0.2 Python3

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

import easygui
import pandas as pd
from easygui import *
import os
import csv
from LEMS_FormatData_L3 import LEMS_FormatData_L3
from LEMS_boxplots import LEMS_boxplots
from LEMS_barcharts import LEMS_barcharts
from LEMS_scatterplots import LEMS_scatterplots
from LEMS_multiscatterslopt import LEMS_multiscaterplots
from LEMS_multiboxplots import LEMS_multiboxplots
from LEMS_multibarcharts import LEMS_multibarcharts
from LEMS_subplotscatterplot import LEMS_subplotscatterplot
from LEMS_CSVFormatted_L3 import LEMS_CSVFormatted_L3
from LEMS_CustomFormatted_L3 import LEMS_CustomFormatted_L3
from LEMS_CustomFormatted_L3Pairs import LEMS_CustomFormatted_L3Pairs
from LEMS_FormatData_L3Pairs import LEMS_FormatData_L3Pairs
import traceback
# --- Imports for L2 reprocessing steps 1-15 ---
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_Combined_Scale import LEMS_Combined_Scale
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS_SubtractBkg import LEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_SubtractBkg import PEMS_SubtractBkg
from PEMS_Plotter1 import PEMS_Plotter
from LEMS_Scale import LEMS_Scale
from LEMS_Int_Scale import LEMS_Int_Scale
from LEMS_FormattedL1 import LEMS_FormattedL1
from LEMS_CSVFormatted_L1 import LEMS_CSVFormatted_L1
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_TEOM import LEMS_TEOM
from LEMS_Sensirion import LEMS_Senserion
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries_Grid
from LEMS_Realtime import LEMS_Realtime
from LEMS_TEOM_SubtractBkg import LEMS_TEOM_SubtractBkg
from LEMS_OPS import LEMS_OPS
from LEMS_Pico import LEMS_Pico
from LEMS_CANThermalEfficiency import LEMS_CANThermalEfficiency
from LEMS_Adam_Scale import LEMS_Adam_Scale
# --- Imports for L2 comparison steps 16-19 and upload step ---
from PEMS_L2 import PEMS_L2
from LEMS_EnergyCalcs_L2 import LEMS_EnergyCalcs_L2
from LEMS_BasicOp_L2 import LEMS_BasicOP_L2
from LEMS_Emissions_L2 import LEMS_Emissions_L2
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
from UploadData import UploadData

#from LEMSDataCruncher_Energy import LEMSDataCruncher_Energy

logs=[]

# Setting up lists to record the files
list_input = []
list_filename = []
list_directory = []
list_testname = []
list_logname = []
button2 = 'No'
output = button2

list_input_LP = []
list_filename_LP = []
list_directory_LP = []
list_testname_LP = []
list_logname_LP = []

inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    # Prompt user for folder path
    folder_path = input("Enter folder path: ")

    # --- Two-level input loading ---
    # list_input_L3 : UnFormattedDataL2.csv paths (one per group) -> comparison steps 16-28
    # list_input    : per-test paths (all groups flattened)        -> reprocessing steps 1-15
    list_input_L3  = []
    list_input     = []
    list_filename  = []
    list_directory = []
    list_testname  = []
    list_logname   = []
    logs           = []

    meta_csv_path = os.path.join(folder_path, 'UnformattedDataL2FilePaths_DataEntrySheetFilePaths.csv')
    if os.path.exists(meta_csv_path):
        with open(meta_csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                group_csv_path = row[0].strip().strip('"')
                group_dir = os.path.dirname(group_csv_path)

                # Build L3 comparison list: UnFormattedDataL2.csv in same dir as group CSV
                unformatted_path = os.path.join(group_dir, 'UnFormattedDataL2.csv')
                list_input_L3.append(unformatted_path)

                # Read each group's DataEntrySheetFilePaths.csv -> per-test paths
                if os.path.exists(group_csv_path):
                    with open(group_csv_path, 'r', newline='') as gf:
                        greader = csv.reader(gf)
                        for grow in greader:
                            if not grow or not grow[0].strip():
                                continue
                            test_path = grow[0].strip().strip('"')
                            list_input.append(test_path)
                            directory, filename = os.path.split(test_path)
                            datadirectory, testname = os.path.split(directory)
                            logname = testname + '_log.txt'
                            list_filename.append(filename)
                            list_directory.append(directory)
                            list_testname.append(testname)
                            list_logname.append(logname)
                else:
                    print('Warning: group CSV not found: ' + group_csv_path)
        print('Loaded ' + str(len(list_input)) + ' individual test(s) across '
              + str(len(list_input_L3)) + ' group(s).')
    else:
        print('Warning: ' + meta_csv_path + ' not found.')
        print('Steps 1-15 (reprocessing) and 16-28 (comparison) will have no input.')

    # Check if UnformattedDataL2FilePaths_lp.csv already exists in main folder
    csv_file_path_LP = os.path.join(folder_path, 'UnformattedDataL2FilePaths_lp.csv')
    if os.path.exists(csv_file_path_LP):
        with open(csv_file_path_LP, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                list_input_LP.append(row[0])
        print('UnformattedDataL2FilePaths_lp.csv exists in main folder')
        print('Existing LP paths found:')
        for path in list_input_LP:
            print(path)
        edit_csv_LP = input('Run all LP tests listed? (y/n): ')
        if edit_csv_LP.lower() == 'n':
            input('Edit UnformattedDataL2FilePaths_lp.csv in main folder and save. Press enter when done.')
            list_input_LP = []
            with open(csv_file_path_LP, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    list_input_LP.append(row[0])

else:
    # Prompt user to enter number of test runs done
    # message to be displayed
    text = "Enter number of test runs"
    # window title
    title = "gitrdone"
    # default text
    d_int = 1
    #lower bound
    lower = 0
    #upperbound
    upper = 999
    # creating an enter box
    testnum = integerbox(text, title, d_int, lower, upper)
    # title for the message box
    title = "gitrdone"
    # creating a message
    message = "Enterted Number : " + str(testnum)
    # creating a message box
    msg = msgbox(message, title)


    #Request data entry form for each test (ideally in the future this would just request the general folder and then find the entry form
    testlen = [0] * testnum
    #Need to fix this error handling later

    #Ask for each data entry file for each test and record the file in lists
    for x in testlen:
        line = 'Select Data Entry Form for Test ' + str(x) + ':'
        print(line)

        inputpath = easygui.fileopenbox()
        directory, filename = os.path.split(inputpath)
        datadirectory, testname = os.path.split(directory)
        logname = testname + '_log.txt'
        logpath = os.path.join(directory, logname)
        outputpath = os.path.join(directory, testname+'_FormattedData_L3.csv')
        testnum = x
        list_input.append(inputpath)
        print(list_input[x])
        list_filename.append(filename)
        list_directory.append(directory)
        list_testname.append(testname)
        list_logname.append(logname)

logpath = os.path.join(folder_path, 'L3_log.txt')

#######################################################
inputmethod = input(
    'Enter 1 for interactive mode (default - for first run and changing variables). \n'
    'Enter 2 for reprocessing mode (for reprocessing data with variables already set). \n'
    'Press Enter to accept default [1]: '
).strip() or '1'

if inputmethod == '1':
    line = 'Interactive mode selected - enter variables when prompted'
    print(line)
    logs.append(line)
elif inputmethod == '2':
    line = 'Reprocessing mode selected - previously entered variables will be used'
    print(line)
    logs.append(line)
else:
    inputmethod = '1'
    line = "Entered variable doesn't exist, defaulting to interactive mode"
    print(line)
    logs.append(line)
#######################################################
#Run option menu to make output files for each test

# list of function descriptions in order:
funs = [
    # --- L2 per-test reprocessing steps (1-15) ---
    'plot raw data',                                         # 1
    'load data entry form',                                  # 2
    'load additional raw data files (heating stoves only)',  # 3
    'calculate energy metrics',                              # 4
    'adjust sensor calibrations',                            # 5
    'correct for response times',                            # 6
    'subtract background',                                   # 7
    'cut TEOM realtime data based on phases',                # 8
    'calculate gravimetric PM',                              # 9
    'calculate emission metrics',                            # 10
    'calculate efficiency metrics',                          # 11
    'calculate averages from a specified cut period',        # 12
    'plot processed data',                                   # 13
    'plot processed data subplots',                          # 14
    'create custom output table for each test',              # 15
    # --- L2 cross-test comparison steps (16-19) ---
    'compare all outputs - unformatted (L2)',                # 16
    'compare all outputs - formatted (L2)',                  # 17
    'compare cut data - unformatted (L2)',                   # 18
    'create custom comparison table (L2)',                   # 19
    # --- L3 cross-test comparison steps (20-32) ---
    'compare all outputs',                                   # 20
    'LP - compare all outputs (UnformattedDataL2FilePaths_lp.csv must be defined)',  # 21
    'compare all outputs, multi-pair',                       # 22
    'create custom boxplot',                                 # 23
    'create multiple boxplots at once',                      # 24
    'create custom bar chart',                               # 25
    'create multiple barcharts at once',                     # 26
    'create custom scatter plot',                            # 27
    'create multiple scatter plots at once',                 # 28
    'create subplots of scatter plots',                      # 29
    'create custom comparison table',                        # 30
    'create formatted custom comparison table',              # 31
    'create formatted custom comparison table of pairs',     # 32
    # --- L2 upload step ---
    'upload processed data (L2)',                            # 33
]

donelist = [''] * len(funs)  # initialize a list that indicates which data processing steps have been done


# this function updates the donelist when a data processing step is completed
# Allows for steps to be skipped if files from previous steps already exist
# To do: currently if files do no exist from skipped steps there is just error. Make user friendly to prompt for missing files
# Create optional steps and allow for optional steps to be skipped (Optional: adjust calibrations and response time: 3,4)
def updatedonelist(donelist, var):
    index = int(var) - 1
    donelist[index] = '(done)'  # mark the completed step as 'done'
    for num, item in enumerate(donelist):  # mark the remaining steps as 'not done'
        if num < index:
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num] = ''
    return donelist

def updatedonelisterror(donelist,var):
    index=int(var)-1
    donelist[index]='(error)'    #mark the completed step as 'done'
    for num,item in enumerate(donelist):    #mark the remaining steps as 'not done'
        if num < index:
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num]=''
    return donelist

line = '\nLEMSDataCruncher_ISO_v0.0\n'
print(line)
logs.append(line)

var = 'unicorn'
#print(list_testname)
while var != 'exit':
    print('')
    print('----------------------------------------------------')
    print('Data processing steps:')

    print('')
    for num, fun in enumerate(funs):  # print the list of data processing steps
        print(donelist[num] + str(num + 1) + ' : ' + fun)
    print('exit : exit program')
    print('')
    var = input("Enter menu option: ")


    if var == '1':  # plot raw data
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            scalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
            nanopath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            senserionpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            OPSpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            Picopath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            plotpath = os.path.join(list_directory[t], list_testname[t] + '_rawplots.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_rawplot.png')
            try:
                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath, nanopath,
                                 TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cscalepath, nnames, tnames, sennames, opsnames, pnames, plotpath,
                                    savefig)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '2':  # load energy inputs
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            inputpath = list_input[t]
            print('Test:' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            try:
                LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '3':  # Load scale raw data file
        error = 3  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_ScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            try:
                LEMS_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed scale data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_IntScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            try:
                LEMS_Int_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed intelligent scale data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_AdamScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            try:
                LEMS_Adam_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed Adam scale data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_NanoscanRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            try:
                LEMS_Nanoscan(inputpath, outputpath, logpath)
                line = '\nloaded and processed Nanoscan data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOMRawData.txt')
            rawoutputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOMRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            try:
                LEMS_TEOM(inputpath, rawoutputpath, outputpath, logpath)
                line = '\nloaded and processed TEOM data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            senpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionInputs.csv')
            try:
                LEMS_Senserion(inputpath, outputpath, senpath, logpath, inputmethod)
                line = '\nloaded and processed Senserion data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_OPSRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            try:
                LEMS_OPS(inputpath, outputpath, logpath)
                line = '\nloaded and processed OPS data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_PicoRawData.csv')
            lemspath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            try:
                LEMS_Pico(inputpath, lemspath, outputpath, logpath)
                line = '\nloaded and processed Pico data'
                print(line)
                logs.append(line)
            except Exception as e:
                line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                print(line)
                logs.append(line)
            scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            adam_scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            if os.path.isfile(scale_path) and os.path.isfile(adam_scale_path):
                out_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                LEMS_Combined_Scale(scale_path, adam_scale_path, out_path, logpath)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
        print(line)
        logs.append(line)

    elif var == '4':  # calculate energy metrics
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            try:
                LEMS_EnergyCalcs(inputpath, outputpath, logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '5':  # adjust sensor calibrations
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
            headerpath = os.path.join(list_directory[t], list_testname[t] + '_Header.csv')
            try:
                LEMS_Adjust_Calibrations(inputpath, sensorpath, outputpath, headerpath, logpath, inputmethod)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '6':  # shift timeseries
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
            try:
                LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath, inputmethod)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '7':  # subtract background
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
            aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            bkgmethodspath = os.path.join(list_directory[t], list_testname[t] + '_BkgMethods.csv')
            savefig1 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg1.png')
            savefig2 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg2.png')
            bkgpath = os.path.join(list_directory[t], list_testname[t] + '_BkgOutputs.csv')
            try:
                PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath,
                                 bkgmethodspath, logpath, savefig1, savefig2, inputmethod, bkgpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '8':  # cut TEOM realtime data based on phases
        print('')
        error = 0
        for t in range(len(list_input)):
            print('')
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + 'TEOM_TimeSeries.csv')
            aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOM_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_TEOMPhaseTimes.csv')
            try:
                LEMS_TEOM_SubtractBkg(inputpath, outputpath, aveoutputpath, timespath, logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '9':  # calculate gravimetric data
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
            aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            try:
                LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '10':  # calculate emissions metrics
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            emisoutputpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            alloutputpath = os.path.join(list_directory[t], list_testname[t] + '_AllOutputs.csv')
            cutoutputpath = os.path.join(list_directory[t], list_testname[t] + '_CutTable.csv')
            outputexcel = os.path.join(list_directory[t], list_testname[t] + '_CutTable.xlsx')
            senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
            nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
            OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
            emissioninputpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionInputs.csv')
            bcpath = os.path.join(list_directory[t], list_testname[t] + '_BCOutputs.csv')
            qualitypath = os.path.join(list_directory[t], list_testname[t] + '_QualityControl.csv')
            bkgpath = os.path.join(list_directory[t], list_testname[t] + '_BkgOutputs.csv')
            try:
                LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                                   logpath, timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                                   intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                   emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath)
                LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, list_testname[t], logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '11':  # calculate canadian efficiency metrics
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            input_path = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics')
            pemsinputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries_test.csv')
            scaleinputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            cuttimepath = os.path.join(list_directory[t], list_testname[t] + '_ThermalEfficiencyCutTimes')
            fuelcutpic = os.path.join(list_directory[t], list_testname[t] + '_ThermalEfficiencyCut')
            outputtimepath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesCanThermalEfficiency')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_CanThermalEfficiency.csv')
            try:
                LEMS_CANThermalEfficiency(input_path, pemsinputpath, scaleinputpath, intscalepath, ascalepath,
                                          energyinputpath, cuttimepath, fuelcutpic, outputtimepath, outputpath,
                                          logpath, inputmethod)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '12':  # cut period
        print('')
        error = 0  # reset error counter
        for t in range(len(list_input)):
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            phasepath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod.png')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
            nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')

            if inputmethod == '1':
                message = 'Select which phases will be graphed'
                title = 'Gitrdun'
                phases = ['L1', 'hp', 'mp', 'lp', 'L5']
                choice = choicebox(message, title, phases)
                inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + choice + '.csv')
                periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + choice + '.csv')
                outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + choice + '.csv')
                averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + choice + '.csv')
                if os.path.isfile(inputpath):
                    try:
                        LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath,
                                      savefig, choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                      scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
                    except Exception as e:
                        line = 'Error: ' + str(e)
                        print(line)
                        traceback.print_exception(type(e), e, e.__traceback__)
                        logs.append(line)
                        error = 1
                else:
                    line = inputpath + ' does not exist'
                    print(line)
            else:
                phases = ['L1', 'hp', 'mp', 'lp', 'L5']
                for phase in phases:
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                    periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + phase + '.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                    averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv')
                    if os.path.isfile(inputpath):
                        try:
                            LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath,
                                          averageoutputpath, savefig, phase, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                          scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
                        except Exception as e:
                            line = 'Error: ' + str(e)
                            print(line)
                            traceback.print_exception(type(e), e, e.__traceback__)
                            logs.append(line)
                            error = 1
                    else:
                        line = inputpath + ' does not exist'
                        print(line)
        if error == 0:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        elif error == 1:
            updatedonelisterror(donelist, var)

    elif var == '13':  # plot processed data
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
            nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
            if inputmethod == '1':
                message = 'Select which phases will be graphed'
                title = 'Gitrdun'
                phases_list = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                choices = multchoicebox(message, title, phases_list)
            else:
                choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
            try:
                for phase in choices:
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                    if os.path.isfile(inputpath):
                        plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots_' + phase + '.csv')
                        savefig = os.path.join(list_directory[t], list_testname[t] + '_plot_' + phase + '.png')
                        names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                            PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath,
                                         nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                        PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames,
                                            plotpath, savefig)
                        line = '\nopen ' + plotpath + ', update and rerun step ' + var + ' to create a new graph'
                        print(line)
                    else:
                        line = inputpath + ' does not exist and will not be plotted.'
                        print(line)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '14':  # plot processed data subplots
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
            nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
            all_phase_data = []
            valid_phases = []
            if inputmethod == '1':
                message = 'Select which phases will be graphed'
                title = 'Gitrdun'
                phases_list = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                choices = multchoicebox(message, title, phases_list)
            else:
                choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
            try:
                for phase in choices:
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                    if os.path.isfile(inputpath):
                        plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots.csv')
                        savefig = os.path.join(list_directory[t], list_testname[t] + '_GridPlot.png')
                        names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                            PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                                         ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                        all_phase_data.append(data)
                        valid_phases.append(phase)
                        line = '\nLoaded data for phase: ' + phase
                        print(line)
                    else:
                        line = inputpath + ' does not exist and will not be plotted.'
                        print(line)
                if len(all_phase_data) > 0:
                    PEMS_PlotTimeSeries_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                             snames, isnames, anames, cnames, [], nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
                    print('\nGrid plot generated: ' + savefig)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '15':  # create custom output table for each test
        error = 0  # reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_AllOutputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.csv')
            outputexcel = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.xlsx')
            csvpath = os.path.join(list_directory[t], list_testname[t] + '_CutTableParameters.csv')
            try:
                LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, list_testname[t], logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '16':  # compare all outputs - unformatted (L2 step 16)
        print('')
        t = 0
        energyinputpath = []
        emissionsinputpath = []
        allpath = []
        for dic in list_directory:
            allpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
            t += 1
        outputpath = os.path.join(folder_path, 'UnFormattedDataL2.csv')
        try:
            PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '17':  # compare all outputs - formatted (L2 step 17)
        error = 0
        print('')
        t = 0
        energyinputpath = []
        emissioninputpath = []
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissioninputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
            t += 1
        outputpath = os.path.join(folder_path, 'FormattedDataL2.csv')
        try:
            LEMS_EnergyCalcs_L2(energyinputpath, emissioninputpath, outputpath, list_testname)
            LEMS_BasicOP_L2(energyinputpath, outputpath)
            LEMS_Emissions_L2(emissioninputpath, outputpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '18':  # compare cut data - unformatted (L2 step 18)
        print('')
        error = 0
        phases = ['L1', 'hp', 'mp', 'lp', 'L5']
        energyinputpath = []
        allpath = []
        for phase in phases:
            emissionsinputpath = []
            for t, dic in enumerate(list_directory):
                p = os.path.join(dic, list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv')
                if os.path.isfile(p):
                    emissionsinputpath.append(p)
            if not emissionsinputpath:
                line = 'No AveragingPeriodAverages files found for phase ' + phase + ', skipping.'
                print(line)
                logs.append(line)
                continue
            outputpath = os.path.join(folder_path, 'UnFormattedDataL2_' + phase + '.csv')
            try:
                PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                error = 1
        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '19':  # create custom comparison table (L2 step 19)
        print('')
        inputpath = []
        for t, dic in enumerate(list_directory):
            inputpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
        outputpath = os.path.join(folder_path, 'CustomCutTable_L2.csv')
        outputexcel = os.path.join(folder_path, 'CustomCutTable_L2.xlsx')
        csvpath = os.path.join(folder_path, 'CutTableParameters_L2.csv')
        write = 1
        try:
            LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logpath, write)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '20':  # compare all outputs (L3)
        print('')
        outputpath = os.path.join(folder_path, 'FormattedDataL3.csv')
        try:
            LEMS_FormatData_L3(list_input_L3, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '21':  # LP - compare all outputs (L3)
        print('')
        outputpath = os.path.join(folder_path, 'FormattedDataL3_lp.csv')
        try:
            LEMS_FormatData_L3(list_input_LP, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '22':  # compare all outputs, multi-pair (L3)
        print('')
        outputpath = os.path.join(folder_path, 'PairsFormattedDataL3.csv')
        pair_inputs = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')
        try:
            LEMS_FormatData_L3Pairs(pair_inputs, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '23':  # create custom boxplot (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3BoxPlot')
        try:
            LEMS_boxplots(list_input_L3, savefigpath, logpath)
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

    elif var == '24':  # create multiple boxplots at once (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
        try:
            LEMS_multiboxplots(list_input_L3, parameterpath, savefigpath, logpath)
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

    elif var == '25':  # create custom bar chart (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3BarChart')
        try:
            LEMS_barcharts(list_input_L3, savefigpath, logpath)
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

    elif var == '26':  # create multiple barcharts at once (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
        try:
            LEMS_multibarcharts(list_input_L3, parameterpath, savefigpath, logpath)
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

    elif var == '27':  # create custom scatter plot (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        try:
            LEMS_scatterplots(list_input_L3, savefigpath, logpath)
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

    elif var == '28':  # create multiple scatter plots at once (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')

        try:
            LEMS_multiscaterplots(list_input_L3, parameterpath, savefigpath, logpath)
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

    elif var == '29':  # create subplots of scatter plots (L3)
        print('')
        savefigpath = os.path.join(folder_path, 'L3SubplotScatterPlot.png')
        parameterpath = os.path.join(folder_path, 'SubplotSelection.csv')

        try:
            LEMS_subplotscatterplot(list_input_L3, parameterpath, savefigpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '30':  # create custom comparison table (L3)
        print('')
        inputpath = list_input_L3
        outputpath = os.path.join(folder_path, 'CustomCutTable_L3.csv')
        outputexcel = os.path.join(folder_path, 'CustomCutTable_L3.xlsx')
        csvpath = os.path.join(folder_path, 'CutTableParameters_L3.csv')
        write = 1
        try:
            LEMS_CSVFormatted_L3(inputpath, outputpath, outputexcel, csvpath, logpath, write)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '31':  # create custom comparison table, formatted (L3)
        print('')
        inputpath = os.path.join(folder_path, 'FormattedDataL3.csv')
        inputpath_lp = os.path.join(folder_path, 'FormattedDataL3_lp.csv')
        outputpath = os.path.join(folder_path, 'FormattedCustomCutTable_L3.csv')
        outputexcel = os.path.join(folder_path, 'FormattedCustomCutTable_L3.xlsx')
        csvpath = os.path.join(folder_path, 'FormattedCutTableL3_template_md.xlsx')
        try:
            LEMS_CustomFormatted_L3(inputpath, inputpath_lp, outputpath, outputexcel, csvpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '32':  # create custom comparison table of pairs, formatted (L3)
        print('')
        inputpath = os.path.join(folder_path, 'PairsFormattedDataL3.csv')
        outputpath = os.path.join(folder_path, 'FormattedCustomCutTable_L3Pairs.csv')
        outputexcel = os.path.join(folder_path, 'FormattedCustomCutTable_L3Pairs.xlsx')
        template = os.path.join(folder_path, 'FormattedCutTableL3Pairs_template.xlsx')
        try:
            LEMS_CustomFormatted_L3Pairs(inputpath, outputpath, outputexcel, template, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '33':  # upload processed data (L2 step 20)
        print('')
        compdirectory, folder = os.path.split(folder_path)
        try:
            UploadData(folder_path, folder)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == 'exit':
        pass

    else:
        print(var + ' is not a menu option')