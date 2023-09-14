
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
from PEMS_L2 import PEMS_L2
from UploadData import UploadData
import csv
import traceback
from PEMS_StackFlowCalcs import PEMS_StackFlowCalcs
from PEMS_StackFlowMetricCalcs import PEMS_StackFlowMetricCalcs

logs=[]

#list of function descriptions in order:
funs = ['plot raw data',
        'calculate fuel metrics',
        'calculate energy metrics',
        'adjust sensor calibrations',
        'correct for response times',
        'subtract background',
        'calculate gravimetric PM',
        'calculate emission metrics',
        'zero pitot tube',
        'calculate stak flow',
        'calculate stak flow metrics',
        'perform realtime calculations',
        'plot processed data',
        'plot processed data for averaging period only',
        'run comparison between all selected tests',
        'run averages comparision between all selected tests',
        'upload processed data (optional)']

donelist=['']*len(funs)    #initialize a list that indicates which data processing steps have been done

##################################################################

# Error handling function that prints the error and keeps the terminal open so the user can read the error
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)
    #For launcher. If error, holds terminal open so user knows what to fix

sys.excepthook = show_exception_and_exit
####################################################

# this function updates the donelist when a data processing step is completed
#Allows for steps to be skipped if files from previous steps already exist
#To do: currently if files do no exist from skipped steps there is just error. Make user friendly to prompt for missing files
#Create optional steps and allow for optional steps to be skipped
def updatedonelist(donelist,var):
    index=int(var)-1
    donelist[index]='(done)'    #mark the completed step as 'done'
    for num,item in enumerate(donelist):    #mark the remaining steps as 'not done'
        if num < index:
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num]=''
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

line='\nPEMSDataCruncher_CarBal_v0.0\n'
print(line)
logs.append(line)

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
            if filename.endswith('_EnergyInputs.csv'):
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
    else: #Look one subdirectory deeper
        for dirpath, dirnames, filenames in os.walk(folder_path):
            # Iterate over subfolders in each subfolder
            for subdirname in dirnames:
                for sub_dirpath, sub_dirnames, sub_filenames in os.walk(os.path.join(dirpath, subdirname)):
                    # Iterate over files in sub-subfolder
                    for filename in sub_filenames:
                        # Check if file name ends with '_DataEntrySheet'
                        if filename.endswith('_EnergyInputs.csv'):
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
                        if filename.endswith('_EnergyInputs.csv'):
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
logs=[]
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
      outputpath = os.path.join(directory, testname+'_FormattedData_L2.csv')
      testnum = x
      list_filename.append(filename)
      list_directory.append(directory)
      list_testname.append(testname)
      list_logname.append(logname)
      i = i+1

line = '\nLEMSDataCruncher_ISO_v0.0\n'
print(line)
logs.append(line)

var = 'unicorn'
print(list_testname)

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

    if var == '1': #Plot raw data
        error = 0 #Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
            plotpath = os.path.join(list_directory[t], list_testname[t] + '_rawplots.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_rawplot.png')
            try:
                PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1 #Indicate at least one error found
        if error == 1: #If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
            print(line)

    elif var == '2': #Read in fuel and exact data, cut at input time
        error = 0 #Reset error counter
        for t in range(len(list_input)):
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_FuelData.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_ExactData.csv')
            fueloutputpath = os.path.join(list_directory[t], list_testname[t] + '_FuelDataCut.csv')
            exactoutputpath = os.path.join(list_directory[t], list_testname[t] + '_ExactDataCut.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_fuelexactcuts.png')
            try:
                PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefig, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1 #Indicate at least one error found
        if error == 1: #If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '3': #Run energy calculations
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            try:
                PEMS_EnergyCalcs(inputpath, outputpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '4': #Recalibrate data or reformat for SB2041(PC)
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            try:
                try:
                   if eval['SB'] == '2041':
                       PEMS_2041(inputpath, outputpath)
                   else:
                       headerpath = os.path.join(directory, testname + '_Header.csv')
                       LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
                except:
                   headerpath = os.path.join(directory, testname + '_Header.csv')
                   LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '5': #Shift for response time
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
            try:
                LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '6': #Subtract background
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
            aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
            bkgmethodspath = os.path.join(list_directory[t], list_testname[t] + '_BkgMethods.csv')
            savefig1 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg1.png')
            savefig2 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg2.png')
            try:
                PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath, logpath, savefig1, savefig2)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '7': #calculate grav metrics
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
            timeseriespath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
            ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
            gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            try:
                PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '8': #calculate emission metrics
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            metricpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            try:
                PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '9': #zero pitot
        error = 0 #reset error counter
        for t in ranger(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesPitot.csv')
            aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
            timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimesPitot.csv')
            bkgmethodspath = os.path.join(list_directory[t], list_testname[t] + '_BkgMethodsPitot.csv')
            try:
                PEMS_SubtractBkgPitot(inputpath, energyinputpath, ucpath, outputpath, timespath, bkgmethodspath,
                                      logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '10': #calcualte stak velocity
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesPitot.csv')
            stackinputpath = os.path.join(list_directory[t], list_testname[t] + '_StackFlowInputs.csv')
            ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
            gravpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            metricpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            dilratinputpath = os.path.join(list_directory[t], list_testname[t] + '_DilRatInputs.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesStackFlow.csv')
            try:
                PEMS_StackFlowCalcs(inputpath, stackinputpath, ucpath, gravpath, metricpath, dilratinputpath,
                                    outputpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
    elif var == '11': #calculate stak velocity metrics
        error = 0 #reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesStackFlow.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            carbalpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            metricpath = os.path.join(list_directory[t], list_testname[t] + '_StackFlowEmissionOutputs.csv')
            try:
                PEMS_StackFlowMetricCalcs(inputpath, energypath, carbalpath, metricpath, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '12': #calculate realtime outputs. Cut for periods
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test: ' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries_test.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            empath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            stakpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesStackFlow.csv')
            stakempath = os.path.join(list_directory[t], list_testname[t] + '_StackFlowEmissionOutputs.csv')
            periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeOutputs.csv')
            fullaverageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeAveragesOutputs.csv')
            averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodOutputs.csv')
            averagecalcoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodCalcs.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_averagingperiod.png')
            try:
                PEMS_Realtime(inputpath, energypath, gravinputpath, empath, stakpath, stakempath, periodpath,
                              outputpath, averageoutputpath,
                              averagecalcoutputpath, fullaverageoutputpath, savefig, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '13': #plot full data series
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeOutputs.csv')
            fuelpath=os.path.join(list_directory[t], list_testname[t] + '_FuelDataCut.csv')
            exactpath=os.path.join(list_directory[t], list_testname[t] + '_ExactDataCut.csv')
            plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_fullperiodplot.png')
            try:
                PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist,var)
            line='\nstep ' +var+ ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
            print(line)
    elif var == '14': #plot cut period
        error = 0  # Reset error counter
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            #Plot over averaging period only, not full data set
            inputpath=os.path.join(list_directory[t], list_testname[t] +'_FuelData.csv')
            energypath=os.path.join(list_directory[t], list_testname[t] +'_AveragingPeriod.csv')
            exactpath=os.path.join(list_directory[t], list_testname[t] +'_ExactData.csv')
            fueloutputpath=os.path.join(list_directory[t], list_testname[t] +'_FuelDataAverageCut.csv')
            exactoutputpath=os.path.join(list_directory[t], list_testname[t] +'_ExactDataAverageCut.csv')
            savefig = os.path.join(directory, testname + '_averagingperiodplot.png')
            savefigfuel = os.path.join(directory, testname + '_averagingperiodfuel.png')
            try:
                PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefigfuel, logpath)
                inputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodOutputs.csv')
                fuelpath=os.path.join(list_directory[t], list_testname[t] + '_FuelDataAverageCut.csv')
                exactpath=os.path.join(list_directory[t], list_testname[t] + '_ExactDataAverageCut.csv')
                plotpath = os.path.join(list_directory[t], list_testname[t] + '_averageplots.csv')
                PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig, logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
                logs.append(line)
                error = 1  # Indicate at least one error found
        if error == 1:  # If error show in menu
            updatedonelisterror(donelist, var)
        else:
            updatedonelist(donelist,var)
            line='\nstep ' +var+ ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
            print(line)

    elif var == '15': #Compare data
        print('')
        t = 0
        energyinputpath = []
        emissionsinputpath = []
        # Loop so menu option can be used out of order if energyOutput files already exist
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
            t += 1
        outputpath = os.path.join(datadirectory, 'FormattedDataL2.csv')
        print(energyinputpath)
        print(emissionsinputpath)
        print(outputpath)
        try:
            PEMS_L2(energyinputpath, emissionsinputpath, outputpath, logpath)
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

    elif var == '16': #Compare cut data
        print('')
        t = 0
        energyinputpath = []
        emissionsinputpath = []
        # Loop so menu option can be used out of order if energyOutput files already exist
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_AveragingPeriodCalcs.csv'))
            t += 1
        outputpath = os.path.join(datadirectory, 'FormattedDataL2_averages.csv')
        print(energyinputpath)
        print(emissionsinputpath)
        print(outputpath)
        try:
            PEMS_L2(energyinputpath, emissionsinputpath, outputpath, logpath)
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

    elif var == '17': #Upload data
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

