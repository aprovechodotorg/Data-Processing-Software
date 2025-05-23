#v0 Python3
#Master program to calculate stove test energy metrics following ISO 19867

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
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_EnergyCalcs_L2 import LEMS_EnergyCalcs_L2
from LEMS_BasicOp_L2 import LEMS_BasicOP_L2
from LEMS_Emissions_L2 import LEMS_Emissions_L2
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_Combined_Scale import LEMS_Combined_Scale
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS_SubtractBkg import LEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_SubtractBkg import PEMS_SubtractBkg
from UploadData import UploadData
from PEMS_Plotter1 import PEMS_Plotter
from LEMS_Scale import LEMS_Scale
from LEMS_Int_Scale import LEMS_Int_Scale
from LEMS_FormattedL1 import LEMS_FormattedL1
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
from LEMS_CSVFormatted_L1 import LEMS_CSVFormatted_L1
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_TEOM import LEMS_TEOM
from LEMS_Sensirion import LEMS_Senserion
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from LEMS_Realtime import LEMS_Realtime
from LEMS_TEOM_SubtractBkg import LEMS_TEOM_SubtractBkg
from LEMS_OPS import LEMS_OPS
from LEMS_Pico import LEMS_Pico
from LEMS_CANThermalEfficiency import LEMS_CANThermalEfficiency
from LEMS_Adam_Scale import LEMS_Adam_Scale
import traceback
from PEMS_L2 import PEMS_L2

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

inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    # Prompt user for folder path
    folder_path = input("Enter folder path: ")

    # Initialize list to store file paths
    list_input = []

    # Check if DataEntrySheetFilePaths.csv already exists in main folder
    csv_file_path = os.path.join(folder_path, 'DataEntrySheetFilePaths.csv')
    if os.path.exists(csv_file_path):
        # If the CSV file exists, read in the file paths
        with open(csv_file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                list_input.append(row[0])

        # Print the existing file paths and prompt the user to edit if desired
        print("DataEntrySheetFilePaths.csv exists in main folder")
        print("Existing data entry sheets found in DataEntrySheetFilePaths.csv:")
        for path in list_input:
            print(path)
        edit_csv = input("Run all tests listed? (y/n): ")
        if edit_csv.lower() == 'n':
            input("Edit DataEntrySheetFilePaths.csv in main folder and save. Press enter when done.")
            # Clear the list of file paths
            list_input = []
            # Read in the updated file paths
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    list_input.append(row[0])
    else:
        print("DataEntrySheetFilePaths.csv file not found. A new CSV file will be created.")
        # Iterate over subfolders in folder_path
        for dirpath, dirnames, filenames in os.walk(folder_path):
            # Iterate over files in subfolder
            for filename in filenames:
                # Check if file name ends with '_DataEntrySheet'
                if filename.endswith('_DataEntrySheet.xlsx'):
                    # Get full file path
                    file_path = os.path.join(dirpath, filename)
                    # Add file path to list
                    list_input.append(file_path)

        if len(list_input) >= 1:
            # Print the existing file paths and prompt the user to edit if desired
            print(len(list_input))
            print("Data entry sheets found:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
        else:  # Look one subdirectory deeper
            for dirpath, dirnames, filenames in os.walk(folder_path):
                # Iterate over subfolders in each subfolder
                for subdirname in dirnames:
                    for sub_dirpath, sub_dirnames, sub_filenames in os.walk(os.path.join(dirpath, subdirname)):
                        # Iterate over files in sub-subfolder
                        for filename in sub_filenames:
                            # Check if file name ends with '_DataEntrySheet'
                            if filename.endswith('_DataEntrySheet.xlsx'):
                                # Get full file path
                                file_path = os.path.join(sub_dirpath, filename)
                                # Add file path to list if not already in list
                                if file_path not in list_input:
                                    list_input.append(file_path)
            # Print the existing file paths and prompt the user to edit if desired
            print("Data entry sheets found:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
        if len(list_input) == 0:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                # Iterate over subfolders in each subfolder
                for subdirname in dirnames:
                    sub_dirpath = os.path.join(dirpath, subdirname)
                    for sub_subdirname in os.listdir(sub_dirpath):
                        sub_subdirpath = os.path.join(sub_dirpath, sub_subdirname)
                        # Iterate over files in sub-sub-subfolder
                        for filename in os.listdir(sub_subdirpath):
                            # Check if file name ends with '_DataEntrySheet'
                            if filename.endswith('_DataEntrySheet.xlsx'):
                                # Get full file path
                                file_path = os.path.join(sub_subdirpath, filename)
                                # Add file path to list if not already in list
                                if file_path not in list_input:
                                    list_input.append(file_path)
            print("Data entry sheets found:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
        # Write file paths to csv in main folder
        csv_file_path = os.path.join(folder_path, 'DataEntrySheetFilePaths.csv')
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for file_path in list_input:
                writer.writerow([file_path])
        if edit_csv.lower() == 'n':
            input("Edit DataEntrySheetFilePaths.csv in main folder and save. Press enter when done.")
            # Clear the list of file paths
            list_input = []
            # Read in the updated file paths
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    list_input.append(row[0])

    # Setting up lists to record the files
    logs = []
    list_filename = []
    list_directory = []
    list_testname = []
    list_logname = []

    i = 0
    for x in list_input:
        inputpath = list_input[i]
        directory, filename = os.path.split(inputpath)
        datadirectory, testname = os.path.split(directory)
        logname = testname + '_log.txt'
        logpath = os.path.join(directory, logname)
        outputpath = os.path.join(directory, testname + '_FormattedData_L2.csv')
        testnum = x
        list_filename.append(filename)
        list_directory.append(directory)
        list_testname.append(testname)
        list_logname.append(logname)
        i = i + 1
    '''
    L3inputpaths = input("Input path to .csv file of test paths:\n")
    # load input file
    f = pd.read_csv(L3inputpaths, header=None)
    for L3inputpath in f[0]:
           list_input.append(L3inputpath)

    i = 0
    for x in list_input:

           inputpath = list_input[i]
           directory, filename = os.path.split(inputpath)
           datadirectory, testname = os.path.split(directory)
           logname = testname + '_log.txt'
           logpath = os.path.join(directory, logname)
           outputpath = os.path.join(directory, testname+'_FormattedData_L2.csv')
           testnum = x
           list_filename.append(filename)
           list_directory.append(directory)
           list_testname.append(testname)
           list_logname.append(logname)
           i = i+1
    '''
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
        outputpath = os.path.join(directory, testname+'_FormattedData_L2.csv')
        testnum = x
        list_input.append(inputpath)
        print(list_input[x])
        list_filename.append(filename)
        list_directory.append(directory)
        list_testname.append(testname)
        list_logname.append(logname)


        #Show user selected files and confirm that the files selected are correct. If not, rerun while loop and ask to enter files again
        #text = 'Are these the correct files? ' + str(list_filename)
        #title = 'gitrdone'
        #button_list = []
        #button1 = 'Yes'
        #button_list.append(button1)
        #button_list.append(button2)
        #output=buttonbox(text,title,button_list)

#Run option menu to make output files for each test (Currently just energy calcs)

# list of function descriptions in order:
funs = ['plot raw data',
        'load data entry form',
        'load additional raw data files (heating stoves only)',
        'calculate energy metrics',
        'adjust sensor calibrations',
        'correct for response times',
        'subtract background',
        'cut TEOM realtime data based on phases',
        'calculate gravimetric PM',
        'calculate emission metrics',
        'calculate efficiency metrics',
        'calculate averages from a specified cut period',
        'plot processed data',
        'create custom output table for each test',
        'compare processed data (unformatted)',
        'compare processed data (formatted)',
        'compare cut data (unformatted)',
        'create custom comparison table',
        'upload processed data (optional)']

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

#######################################################
inputmethod = input('Enter 1 for interactive mode (for first run and changing variables). \nEnter 2 for reprocessing '
                    'mode (for reprocessing data with variables already set - no outputs). \n')

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

line = '\nLEMSDataCruncher_ISO_v0.0\n'
print(line)
logs.append(line)

var = 'unicorn'
#print(list_testname)
while var != 'exit':
    print('')
    print('----------------------------------------------------')
    #print('testname = ' + testname)
    print('Data processing steps:')

    print('')
    for num, fun in enumerate(funs):  # print the list of data processing steps
        print(donelist[num] + str(num + 1) + ' : ' + fun)
    print('exit : exit program')
    print('')
    var = input("Enter menu option: ")


    if var == '1': #plot raw data
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
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
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e,
                                          e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
            print(line)


    elif var == '2': #load energy inputs
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            inputpath = list_input[t]
            print('Test:' + list_directory[t])
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            try:
                LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e,
                                          e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '3': #Load scale raw data file
        error = 3 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_ScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            try:
                LEMS_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed scale data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
                print(line)
                #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                #error = 1  # Indicate at least one error found
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_IntScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
            try:
                LEMS_Int_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed intelligent scale data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
                print(line)
                #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                #error = 1  # Indicate at least one error found
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_AdamScaleRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            try:
                LEMS_Adam_Scale(inputpath, outputpath, logpath)
                line = '\nloaded and processed intelligent scale data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
                print(line)
                #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                #error = 1  # Indicate at least one error found
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_NanoscanRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
            try:
                LEMS_Nanoscan(inputpath, outputpath, logpath)
                line = '\nloaded and processed Nanoscan data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                                   "If file exists, some other error may have occured."
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
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                                   "If file exists, some other error may have occured."
                print(line)
                logs.append(line)
            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
            senpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionInputs.csv')
            try:
                LEMS_Senserion(inputpath,  outputpath, senpath, logpath, inputmethod)
                line = '\nloaded and processed Senserion data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                                   "If file exists, some other error may have occured."
                print(line)
                logs.append(line)

            print('')
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_OPSRawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] +  '_FormattedOPSData.csv')
            try:
                LEMS_OPS(inputpath, outputpath, logpath)
                line = '\nloaded and processed OPS data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                                   "If file exists, some other error may have occured."
                print(line)
                logs.append(line)
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_PicoRawData.csv')
            lemspath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
            try:
                LEMS_Pico(inputpath,lemspath, outputpath, logpath)
                line = '\nloaded and processed Pico data'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                                   "If file exists, some other error may have occured."
                print(line)
                logs.append(line)

            scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
            adam_scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            if os.path.isfile(scale_path) and os.path.isfile(adam_scale_path):
                out_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                LEMS_Combined_Scale(scale_path, adam_scale_path, out_path, logpath)
        #if error == 1:  # If error show in menu
            #updatedonelisterror(donelist, var)
        #else:
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
        print(line)
        logs.append(line)

    elif var == '4': #calculate energy metrics
        error = 0 #reset error counter
        #list_energy = []
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            try:
                LEMS_EnergyCalcs(inputpath, outputpath, logpath)
                #list_energy.append(outputpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e,
                                          e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '5': #adjust sensor calibrations
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
            headerpath = os.path.join(list_directory[t], list_testname[t] + '_Header.csv')
            try:
                LEMS_Adjust_Calibrations(inputpath, sensorpath, outputpath, headerpath, logpath, inputmethod)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
    elif var == '6': #shift timeseries
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
            try:
                LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath, inputmethod)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '7': #subtract background
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
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
                                 bkgmethodspath, logpath,  savefig1, savefig2, inputmethod, bkgpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
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
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + 'TEOM_TimeSeries.csv')
            aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOM_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_TEOMPhaseTimes.csv')
            try:
                LEMS_TEOM_SubtractBkg(inputpath, outputpath, aveoutputpath, timespath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '9': #calculate gravametric data
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
            aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            try:
                LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '10': #calculate emissions metrics
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
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

            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')  # No fuel or exact taken in
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
            emissioninputpath = os.path.join(directory, testname + '_EmissionInputs.csv')
            bcpath = os.path.join(directory, testname + '_BCOutputs.csv')
            qualitypath = os.path.join(directory, testname + '_QualityControl.csv')
            bkgpath = os.path.join(list_directory[t], list_testname[t] + '_BkgOutputs.csv')
            try:
                LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                                   logpath,
                                   timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                                   intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                   emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath)
                LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, testname, logpath)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '11': #calculate canadian efficiency metrics
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            input_path = os.path.join(list_directory[t], list_testname[t] + "_TimeSeriesMetrics")
            pemsinputpath = os.path.join(list_directory[t], list_testname[t] + "_TimeSeries_test.csv")
            scaleinputpath = os.path.join(list_directory[t], list_testname[t] + "_FormattedScaleData.csv")
            intscalepath = os.path.join(list_directory[t], list_testname[t] + "_FormattedIntScaleData.csv")
            ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + "_EnergyOutputs.csv")
            cuttimepath = os.path.join(list_directory[t], list_testname[t] + "_ThermalEfficiencyCutTimes")
            fuelcutpic = os.path.join(list_directory[t], list_testname[t] + "_ThermalEfficiencyCut")
            outputtimepath = os.path.join(list_directory[t], list_testname[t] + "_TimeSeriesCanThermalEfficiency")
            outputpath = os.path.join(list_directory[t], list_testname[t] + "_CanThermalEfficiency.csv")

            try:
                LEMS_CANThermalEfficiency(input_path, pemsinputpath, scaleinputpath, intscalepath, ascalepath, energyinputpath,
                                          cuttimepath, fuelcutpic, outputtimepath, outputpath, logpath, inputmethod)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
                print(line)
                logs.append(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '12': #cut period
        print('')
        error = 0 #reset error counter
        for t in range(len(list_input)):
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            phasepath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod.png')

            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')  # No fuel or exact taken in
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
                # Find what phases people want graphed
                message = 'Select which phases will be graphed'  # message
                title = 'Gitrdun'
                phases = ['L1', 'hp', 'mp', 'lp', 'L5']  # phases to choose from
                choice = choicebox(message, title, phases)  # can select one or multiple

                inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + choice + '.csv')
                periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + choice + '.csv')
                outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + choice + '.csv')
                averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + choice + '.csv')

                if os.path.isfile(inputpath):
                    try:
                        LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath,
                                      savefig, choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                      scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
                    except Exception as e:  # If error in called fuctions, return error but don't quit
                        line = 'Error: ' + str(e)
                        print(line)
                        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                        logs.append(line)
                        error = 1
                else:
                    line = inputpath + ' does not exist'
                    print(line)
            else:
                phases = ['L1', 'hp', 'mp', 'lp', 'L5']  # phases to choose from
                for phase in phases:
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                    periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + phase + '.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                    averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv')

                    if os.path.isfile(inputpath):
                        try:
                            LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath,
                                          averageoutputpath, savefig, phase, logpath, inputmethod)
                        except Exception as e:  # If error in called fuctions, return error but don't quit
                            line = 'Error: ' + str(e)
                            print(line)
                            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
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

    elif var == '13': #plot processed data
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            # Find what phases people want graphed
            message = 'Select which phases will be graphed'  # message
            title = 'Gitrdun'
            phases = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']  # phases to choose from
            choices = multchoicebox(message, title, phases)  # can select one or multiple

            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')  # No fuel or exact taken in
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
            try:
                for phase in choices:  # for each phase selected, run through plot function
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                    if os.path.isfile(inputpath):  # check that the data exists
                        plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots_' + phase + '.csv')
                        savefig = os.path.join(list_directory[t], list_testname[t] + '_plot_' + phase + '.png')
                        names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                            PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath,
                                         nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig,
                                         logpath)
                        PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames,
                                            plotpath,
                                            savefig)
                        line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
                        print(line)
                    else:
                        line = inputpath + ' does not exist and will not be plotted.'
                        print(line)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)


    elif var == '14': #create custom output table for each test
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_AllOutputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.csv')
            outputexcel = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.xlsx')
            csvpath = os.path.join(list_directory[t], list_testname[t] + '_CutTableParameters.csv')
            try:
                LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, testname, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '15': #Compare data (unformatted)
        print('')
        t = 0
        energyinputpath = []
        emissionsinputpath = []
        allpath = []
        # Loop so menu option can be used out of order if energyOutput files already exist
        for dic in list_directory:
            allpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
            t += 1
        outputpath = os.path.join(folder_path, 'UnFormattedDataL2.csv')
        try:
            PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '16': #Compare data (formatted)
        error = 0 #reset error counter
        print('')
        t = 0
        energyinputpath=[]
        emissioninputpath = []
        #Loop so menu option can be used out of order if energyOutput files already exist
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissioninputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
            t += 1
        outputpath = os.path.join(folder_path, 'FormattedDataL2.csv')
        try:
            LEMS_EnergyCalcs_L2(energyinputpath, emissioninputpath, outputpath, list_testname)
            LEMS_BasicOP_L2(energyinputpath, outputpath)
            #for path in emissioninputpath:
            #if os.path.isfile(emissioninputpath):
            LEMS_Emissions_L2(emissioninputpath, outputpath)
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

    elif var == '17': #Compare cut data (unformatted)
        print('')
        t = 0
        error = 0
        phases = ['L1', 'hp', 'mp', 'lp', 'L5']
        energyinputpath = []
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            t+=1

        for phase in phases:
            emissionsinputpath = []
            for t, dic in enumerate(list_directory):
                emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv'))
            outputpath = os.path.join(folder_path, 'UnFormattedDataL2_' + phase + '.csv')
            try:
                PEMS_L2(energyinputpath, emissionsinputpath, outputpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)

        if error == 1:
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '18': #create custom comparison table
        print('')
        inputpath=[]
        #Loop so menu option can be used out of order if energyOutput files already exist
        for t, dic in enumerate(list_directory):
            inputpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
        outputpath = os.path.join(datadirectory, 'CustomCutTable_L2.csv')
        outputexcel = os.path.join(datadirectory, 'CustomCutTable_L2.xlsx')
        csvpath = os.path.join(datadirectory, 'CutTableParameters_L2.csv')
        write = 1
        try:
            LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logpath, write)
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

    elif var == '19': #upload data
        print('')
        compdirectory, folder = os.path.split(datadirectory)
        try:
            UploadData(datadirectory, folder)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + 'done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == 'exit':
        pass

    else:
        print(var + ' is not a menu option')
#while t <= tests;
       #LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)

       #LEMS_FormatData_L2(inputpath2, outputpath2, logpath, testnum)
