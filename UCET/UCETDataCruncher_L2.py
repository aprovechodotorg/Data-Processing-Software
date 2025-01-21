# v0 Python3
# Master program to calculate stove Unit Tests energy metrics following ISO 19867

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


import os
import csv
from UCET.LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from UCET_EnergyCalcs import UCET_EnergyCalcs
from PEMS_L2 import PEMS_L2
from UploadData import UploadData


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

    # Write file paths to csv in main folder
    csv_file_path = os.path.join(folder_path, 'DataEntrySheetFilePaths.csv')
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for file_path in list_input:
            writer.writerow([file_path])

    # Print the existing file paths and prompt the user to edit if desired
    print("Data entry sheets found:")
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

# list of function descriptions in order:
funs = ['load data entry form',
        'calculate energy metrics',
        'run comparison between all selected tests',
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
                     inputpath = list_input[t]
                     print(inputpath)
                     outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                     LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)
                     updatedonelist(donelist, var)
                     line = '\nstep ' + var + ' done, back to main menu'
                     print(line)
                     logs.append(line)


       elif var == '2':
              list_energy = []
              for t in range(len(list_input)):
                     print('')
                     print(list_directory[t])
                     print(list_testname[t])
                     inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                     outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                     print(outputpath)
                     const, units, metric = UCET_EnergyCalcs(inputpath, outputpath, logpath)
                     print(metric)
                     list_energy.append(outputpath)
                     updatedonelist(donelist, var)
                     line = '\nstep ' + var + ' done, back to main menu'
                     print(line)
                     logs.append(line)
       elif var == '3':
              print('')
              print(testname)
              t = 0
              energyinputpath=[]
              emissioninputpath = []
              #Loop so menu option can be used out of order if energyOutput files already exist
              for dic in list_directory:
                     energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
                     emissioninputpath.append(os.path.join(dic, list_testname[t] + '_NA.csv'))
                     t += 1
              outputpath = os.path.join(folder_path, 'FormattedDataL2.csv')
              print(energyinputpath)
              print(outputpath)
              trial, units, average, data_values, uncertainty, N, stadev, interval, high_tier, low_tier, COV =PEMS_L2(energyinputpath, emissioninputpath, outputpath, list_testname)
              print(uncertainty)
              updatedonelist(donelist, var)
              line = '\nstep ' + var + ' done, back to main menu'
              print(line)
              logs.append(line)
       elif var == '4':
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
#while t <= tests;
       #LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)

       #LEMS_FormatData_L2(inputpath2, outputpath2, logpath, testnum)
