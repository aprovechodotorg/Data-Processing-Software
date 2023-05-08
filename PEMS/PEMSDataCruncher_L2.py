
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
from PEMS_Histogram import PEMS_Histogram
from PEMS_FuelExactCuts import PEMS_FuelExactCuts
from PEMS_FuelCuts import PEMS_FuelCuts
from PEMS_FuelScript import PEMS_FuelScript
from PEMS_2041 import PEMS_2041
from PEMS_L2 import PEMS_L2
import csv

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
        'perform realtime calculations',
        'plot processed data',
        'plot processed data for averaging period only',
        'run comparison between all selected tests',
        'run averages comparision between all selected tests'
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
'''
inputnum = input("Enter number of tests.\n")

inputnum = len(list_input)
list_filename = []
list_directory = []
list_testname = []
list_logname = []
x = 0
while x < int(inputnum):
    #inputpath = input("Input path of _EnergyInputs.csv file:\n")
    directory, filename = os.path.split(inputpath)
    datadirectory, testname = os.path.split(directory)
    logname = testname + '_log.txt'
    logpath = os.path.join(directory, logname)
    outputpath = os.path.join(directory, testname + '_FormattedData_L2.csv')
    testnum = x
    list_input.append(inputpath)
    list_filename.append(filename)
    list_directory.append(directory)
    list_testname.append(testname)
    list_logname.append(logname)

    x += 1
'''
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

    if var == '1':
        for t in range(len(list_input)):
           print('')
           print('Test:' + list_directory[t])
           inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
           fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
           exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
           plotpath = os.path.join(list_directory[t], list_testname[t] + '_rawplots.csv')
           savefig = os.path.join(list_directory[t], list_testname[t] + '_rawplot.png')
           PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
           print(line)
           print('')
    elif var == '2':
        for t in range(len(list_input)):
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_FuelData.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
            exactpath = os.path.join(list_directory[t], list_testname[t] + '_ExactData.csv')
            fueloutputpath = os.path.join(list_directory[t], list_testname[t] + '_FuelDataCut.csv')
            exactoutputpath = os.path.join(list_directory[t], list_testname[t] + '_ExactDataCut.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_fuelexactcuts.png')
            if os.path.isfile(exactpath):
                PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefig)
            else:
                PEMS_FuelCuts(inputpath, energypath, fueloutputpath, savefig)
            if os.path.isfile(fueloutputpath):
                PEMS_FuelScript(fueloutputpath)
            else:
                PEMS_FuelScript(inputpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)
    elif var == '3':
       for t in range(len(list_input)):
           print('')
           print('Test:' + list_directory[t])
           inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
           outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
           PEMS_EnergyCalcs(inputpath, outputpath, logpath)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           logs.append(line)

    elif var == '4':
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
            try:
               if eval['SB'] == '2041':
                   PEMS_2041(inputpath, outputpath)
               else:
                   headerpath = os.path.join(directory, testname + '_Header.csv')
                   LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
                   updatedonelist(donelist, var)
            except:
               headerpath = os.path.join(directory, testname + '_Header.csv')
               LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
               updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
            print(line)
            logs.append(line)

    elif var == '5':
       for t in range(len(list_input)):
           print('')
           print('Test:' + list_directory[t])
           inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
           outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
           timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
           LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           logs.append(line)

    elif var == '6':
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
           PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath,
                            bkgmethodspath, logpath, savefig1, savefig2)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           logs.append(line)

    elif var == '7':
        for t in range(len(list_input)):
           print('')
           print('Test:' + list_directory[t])
           gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
           timeseriespath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
           ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
           gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
           PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           logs.append(line)

    elif var == '8':
        for t in range(len(list_input)):
           print('')
           print('Test:' + list_directory[t])
           energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
           gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
           aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
           metricpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
           PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath)
           updatedonelist(donelist, var)
           line = '\nstep ' + var + ' done, back to main menu'
           print(line)
           logs.append(line)
    elif var == '9':
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries_test.csv')
            energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
            gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
            empath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
            periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod.csv')
            outputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeOutputs.csv')
            fullaverageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeAveragesOutputs.csv')
            averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodOutputs.csv')
            averagecalcoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodCalcs.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_averagingperiod.png')
            PEMS_Histogram(inputpath, energypath, gravinputpath, empath, periodpath, outputpath, averageoutputpath,
                           averagecalcoutputpath, fullaverageoutputpath, savefig)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ' done, back to main menu'
    elif var == '10':
        for t in range(len(list_input)):
            print('')
            print('Test:' + list_directory[t])
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_RealtimeOutputs.csv')
            fuelpath=os.path.join(list_directory[t], list_testname[t] + '_FuelDataCut.csv')
            exactpath=os.path.join(list_directory[t], list_testname[t] + '_ExactDataCut.csv')
            plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots.csv')
            savefig = os.path.join(list_directory[t], list_testname[t] + '_fullperiodplot.png')
            PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig)
            updatedonelist(donelist,var)
            line='\nstep ' +var+ ' done, back to main menu'
            print(line)
            line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
            print(line)
    elif var == '11':
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
            if os.path.isfile(exactpath):
                PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath, savefigfuel)
            else:
                try:
                    PEMS_FuelCuts(inputpath, energypath, fueloutputpath, savefigfuel)
                except:
                    pass
            if os.path.isfile(fueloutputpath):
                PEMS_FuelScript(fueloutputpath)
            else:
                #PEMS_FuelScript(inputpath)
                pass
            inputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodOutputs.csv')
            fuelpath=os.path.join(list_directory[t], list_testname[t] + '_FuelDataAverageCut.csv')
            exactpath=os.path.join(list_directory[t], list_testname[t] + '_ExactDataAverageCut.csv')
            plotpath = os.path.join(list_directory[t], list_testname[t] + '_averageplots.csv')
            PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath, savefig)
            updatedonelist(donelist,var)
            line='\nstep ' +var+ ' done, back to main menu'
            print(line)
            line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
            print(line)

    elif var == '12':
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
        PEMS_L2(energyinputpath, emissionsinputpath, outputpath)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ' done, back to main menu'
        print(line)

    elif var == '13':
        print('')
        t = 0
        energyinputpath = []
        emissionsinputpath = []
        # Loop so menu option can be used out of order if energyOutput files already exist
        for dic in list_directory:
            energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
            emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_AveragingPeriodCalcs.csv'))
            t += 1
        outputpath = os.path.join(datadirectory, 'FormattedDataL2.csv')
        print(energyinputpath)
        print(emissionsinputpath)
        print(outputpath)
        PEMS_L2(energyinputpath, emissionsinputpath, outputpath)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ' done, back to main menu'
        print(line)

    elif var == '14':
        print('')
        compdirectory, folder = os.path.split(datadirectory)
        UploadData(datadirectory, folder)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + 'done, back to main menu'
        print(line)
        logs.append(line)
    elif var == 'exit':
        pass

    else:
        print(var + ' is not a menu option')

