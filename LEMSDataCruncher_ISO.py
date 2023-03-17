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

#do: currently all steps are required. make steps optional: 3,4,

import sys
import easygui
import os
import LEMS_DataProcessing_IO as io
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS_SubtractBkg import LEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_SubtractBkg import PEMS_SubtractBkg
#from openpyxl import load_workbook

logs=[]

#list of function descriptions in order:
funs = ['load data entry form',
        'calculate energy metrics',
        'adjust sensor calibrations',
        'correct for response times',
        'subtract background',
        'calculate gravimetric PM',
        'calculate emission metrics']

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
#Create optional steps and allow for optional steps to be skipped (Optional: adjust calibrations and response time: 3,4)
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

line='\nLEMSDataCruncher_ISO_v0.0\n'
print(line)
logs.append(line)

#Can this be a menu item so that the program can be ran without choosing a specific test? or can this gui be used just to choose the level 3 directory?
inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    sheetinputpath = input("Input path of data entry form (spreadsheet):\n")
    directory, filename = os.path.split(sheetinputpath)
    datadirectory, testname = os.path.split(directory)
    logname = testname + '_log.txt'
    logpath = os.path.join(directory, logname)

    var = 'unicorn'
else:
    line = 'Select test data entry form (spreadsheet):'
    print(line)
    sheetinputpath = easygui.fileopenbox()
    if sheetinputpath:
        line=sheetinputpath
        print(line)
        #logs.append(line)

        directory,filename=os.path.split(sheetinputpath)
        datadirectory,testname=os.path.split(directory)
        logname=testname+'_log.txt'
        logpath=os.path.join(directory,logname)

        var='unicorn'
    else:
        print('Cancel')
        print('No test selected')
        print('Exit')
        var = 'exit'

#######################################################

while var != 'exit':
    print('')
    print('----------------------------------------------------')
    print('testname = '+testname)
    print('Data processing steps:')

    print('')
    for num,fun in enumerate(funs): #print the list of data processing steps
        print(donelist[num]+str(num+1)+' : '+fun) 
    print('exit : exit program')
    print('')
    var = input("Enter menu option: ")
    
    if var == '1':
        print('')
        inputpath=sheetinputpath
        outputpath=os.path.join(directory,testname+'_EnergyInputs.csv')
        LEMS_MakeInputFile_EnergyCalcs(inputpath,outputpath,logpath) 
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)
        
    elif var == '2':
        print('')
        inputpath=os.path.join(directory,testname+'_EnergyInputs.csv')
        outputpath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        LEMS_EnergyCalcs(inputpath,outputpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)
        
    elif var == '3':
        print('')
        inputpath=os.path.join(directory,testname+'_RawData.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        headerpath = os.path.join(directory,testname+'_Header.csv')
        LEMS_Adjust_Calibrations(inputpath,outputpath,headerpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)        
        
    elif var == '4':
        print('')
        inputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Shifted.csv')
        timespath = os.path.join(directory,testname+'_TimeShifts.csv')
        LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)        
        
    elif var == '5':
        print('')
        inputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
        energyinputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
        ucpath = os.path.join(directory, testname + '_UCInputs.csv')
        outputpath = os.path.join(directory, testname + '_TimeSeries.csv')
        aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
        timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
        bkgmethodspath = os.path.join(directory, testname + '_BkgMethods.csv')
        PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)       
        
    elif var == '6':
        print('')
        gravinputpath=os.path.join(directory,testname+'_GravInputs.csv')
        aveinputpath = os.path.join(directory,testname+'_Averages.csv')
        timespath = os.path.join(directory,testname+'_PhaseTimes.csv')
        gravoutputpath=os.path.join(directory,testname+'_GravOutputs.csv')
        LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,gravoutputpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)    
        
    elif var == '7':
        print('')
        inputpath=os.path.join(directory,testname+'_TimeSeries.csv')
        energypath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        gravinputpath=os.path.join(directory,testname+'_GravOutputs.csv')
        aveinputpath = os.path.join(directory,testname+'_Averages.csv')
        timespath = os.path.join(directory,testname+'_PhaseTimes.csv')
        emisoutputpath=os.path.join(directory,testname+'_EmissionOutputs.csv')
        alloutputpath=os.path.join(directory,testname+'_AllOutputs.csv')
        LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)    
   
    elif var == 'exit':
        pass
        
    else:    
        print(var+' is not a menu option')
