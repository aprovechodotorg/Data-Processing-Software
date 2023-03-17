
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
from PEMS_L2 import PEMS_L2

logs=[]

#list of function descriptions in order:
funs = ['calculate energy metrics',
        'adjust sensor calibrations',
        'correct for response times',
        'subtract background',
        'calculate gravimetric PM',
        'calculate emission metrics',
        'run comparison between all tests']

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

inputnum = input("Enter number of tests.\n")

list_input = []
list_filename = []
list_directory = []
list_testname = []
list_logname = []
x = 0
while x < int(inputnum):
    inputpath = input("Input path of _EnergyInputs.csv file:\n")
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

    x+=1

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
               inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
               outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
               PEMS_EnergyCalcs(inputpath, outputpath, logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '2':
           for t in range(len(list_input)):
               print('')
               inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
               outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
               headerpath = os.path.join(list_directory[t], list_testname[t] + '_Header.csv')
               LEMS_Adjust_Calibrations(inputpath, outputpath, headerpath, logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '3':
           for t in range(len(list_input)):
               print('')
               inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
               outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
               timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
               LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '4':
           for t in range(len(list_input)):
               print('')
               inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
               energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
               ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
               outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
               aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
               timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
               bkgmethodspath = os.path.join(list_directory[t], list_testname[t] + '_BkgMethods.csv')
               PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath,
                                logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '5':
           for t in range(len(list_input)):
               print('')
               gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
               timeseriespath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
               ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
               gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
               PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '6':
           for t in range(len(list_input)):
               print('')
               energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
               gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
               aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
               metricpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
               PEMS_CarbonBalanceCalcs(energypath, gravinputpath, aveinputpath, metricpath, logpath)
               updatedonelist(donelist, var)
               line = '\nstep ' + var + ' done, back to main menu'
               print(line)
               logs.append(line)

       elif var == '7':
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

       elif var == 'exit':
           pass

       else:
           print(var + ' is not a menu option')

