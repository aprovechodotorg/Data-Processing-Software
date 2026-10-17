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
from LEMS_FormatData_L3Pairs import LEMS_FormatData_L3Pairs
from LEMS_PairsPlotHelper import load_pairs_csv
from LEMS_L2FileSelector import select_l2_files_gui
import traceback

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
    csv_file_path = os.path.join(folder_path, 'UnformattedDataL2FilePaths.csv')
    if os.path.exists(csv_file_path):
        # If the CSV file exists, read in the file paths
        with open(csv_file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                list_input.append(row[0])

        # Print the existing file paths and prompt the user to edit if desired
        print("FormattedDataL2FilePaths.csv exists in main folder")
        print("Existing data entry sheets found in FormattedDataL2FilePaths.csv:")
        for path in list_input:
            print(path)
        edit_csv = input("Run all tests listed? (y/n): ")
        if edit_csv.lower() == 'n':
            input("Edit FormattedDataL2FilePathsL.csv in main folder and save. Press enter when done.")
            # Clear the list of file paths
            list_input = []
            # Read in the updated file paths
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    list_input.append(row[0])
    else:
        print("FormattedDataL2FilePaths.csv file not found. A new CSV file will be created.")
        # Iterate over subfolders in folder_path
        for dirpath, dirnames, filenames in os.walk(folder_path):
            # Iterate over files in subfolder
            for filename in filenames:
                # Check if file name ends with '_DataEntrySheet'
                if filename.endswith('UnFormattedDataL2.csv'):
                    # Get full file path
                    file_path = os.path.join(dirpath, filename)
                    # Add file path to list
                    list_input.append(file_path)

        if len(list_input) >= 1:
            # Print the existing file paths and prompt the user to edit if desired
            print(len(list_input))
            print("Formatted L2 data sheets found:")
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
                            if filename.endswith('UnFormattedDataL2.csv'):
                                # Get full file path
                                file_path = os.path.join(sub_dirpath, filename)
                                # Add file path to list if not already in list
                                if file_path not in list_input:
                                    list_input.append(file_path)
            # Print the existing file paths and prompt the user to edit if desired
            print("Formatted L2 data sheets found:")
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
                            if filename.endswith('UnFormattedDataL2.csv'):
                                # Get full file path
                                file_path = os.path.join(sub_subdirpath, filename)
                                # Add file path to list if not already in list
                                if file_path not in list_input:
                                    list_input.append(file_path)
            print("Formatted L2 data sheets found:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
        # Write file paths to csv in main folder
        csv_file_path = os.path.join(folder_path, 'UnformattedDataL2FilePaths.csv')
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for file_path in list_input:
                writer.writerow([file_path])
        if edit_csv.lower() == 'n':
            input("Edit FormattedDataL2FilePaths.csv in main folder and save. Press enter when done.")
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
        outputpath = os.path.join(directory, testname + '_FormattedData_L3.csv')
        testnum = x
        list_filename.append(filename)
        list_directory.append(directory)
        list_testname.append(testname)
        list_logname.append(logname)
        i = i + 1

else:
    folder_path, selected_paths = select_l2_files_gui()
    if not folder_path or not selected_paths:
        print("No folder or test files selected. Exiting.")
        exit()

    list_input = []
    list_filename = []
    list_directory = []
    list_testname = []
    list_logname = []

    for inputpath in selected_paths:
        directory, filename = os.path.split(inputpath)
        datadirectory, testname = os.path.split(directory)
        logname = testname + '_log.txt'
        list_input.append(inputpath)
        list_filename.append(filename)
        list_directory.append(directory)
        list_testname.append(testname)
        list_logname.append(logname)

if 'folder_path' not in locals() or not folder_path:
    folder_path = os.path.dirname(list_directory[0]) if list_directory else '.'
logpath = os.path.join(folder_path, 'L3_log.txt')

# Check for PairsUnformattedDataL2FilePaths.csv for paired plotting (steps 3-9)
list_input_pairs = []
list_labels_pairs = []
list_pair_groups = None
pairs_csv_path = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')
if os.path.exists(pairs_csv_path):
    try:
        list_input_pairs, list_labels_pairs, list_pair_groups = load_pairs_csv(pairs_csv_path)
        if list_pair_groups:
            print(f"Loaded pairs configuration from {pairs_csv_path}: {len(list_input_pairs)} test(s) across {len(list_pair_groups)} pair group(s).")
    except Exception as e:
        print(f"Warning: Failed to load pairs from {pairs_csv_path}: {e}")
#Run option menu to make output files for each test (Currently just energy calcs)

# list of function descriptions in order:
funs = ['compare all outputs',
        'compare all outputs, multi-pair',
        'create custom boxplot',
        'create multiple boxplots at once',
        'create custom bar chart',
        'create multiple barcharts at once',
        'create custom scatter plot',
        'create multiple scatter plots at once',
        'create subplots of scatter plots',
        'create custom comparison table']

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
    #print('testname = ' + testname)
    print('Data processing steps:')

    print('')
    for num, fun in enumerate(funs):  # print the list of data processing steps
        print(donelist[num] + str(num + 1) + ' : ' + fun)
    print('exit : exit program')
    print('')
    var = input("Enter menu option: ")


    if var == '1': #Compare all outputs
        print('')
        outputpath = os.path.join(folder_path, 'FormattedDataL3.csv')
        try:
            LEMS_FormatData_L3(list_input, outputpath, logpath)
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
    elif var == '2': #Compare all outputs, multi-pair
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

    elif var == '3': #create boxplots
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsBoxPlot')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3BoxPlot')
        try:
            LEMS_boxplots(plot_inputs, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '4': #create multiple box plots
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsBoxPlot')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3BoxPlot')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
        try:
            LEMS_multiboxplots(plot_inputs, parameterpath, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '5': #create barchart
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsBarChart')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3BarChart')
        try:
            LEMS_barcharts(plot_inputs, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '6': #create multiple bar charts
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsBarChart')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3BarChart')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
        try:
            LEMS_multibarcharts(plot_inputs, parameterpath, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '7': #create scatter plot
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsScatterPlot')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        try:
            LEMS_scatterplots(plot_inputs, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '8': #create subplots scatter plots
        print('')
        if list_pair_groups and list_input_pairs:
            plot_inputs = list_input_pairs
            plot_labels = list_labels_pairs
            plot_groups = list_pair_groups
            savefigpath = os.path.join(folder_path, 'L3PairsScatterPlot')
        else:
            plot_inputs = list_input
            plot_labels = None
            plot_groups = None
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
        parameterpath = os.path.join(folder_path, 'PlotSelection.csv')

        try:
            LEMS_multiscaterplots(plot_inputs, parameterpath, savefigpath, logpath, labels=plot_labels, pair_groups=plot_groups)
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

    elif var == '9': #create multiple scatter plots
        print('')
        savefigpath = os.path.join(folder_path, 'L3SubplotScatterPlot.png')
        parameterpath = os.path.join(folder_path, 'SubplotSelection.csv')

        try:
            LEMS_subplotscatterplot(list_input, parameterpath, savefigpath, logpath, labels=list_labels_pairs if list_pair_groups else None, pair_groups=list_pair_groups)
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

    elif var == '10': #create custom comparison table
        print('')
        inputpath = list_input
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