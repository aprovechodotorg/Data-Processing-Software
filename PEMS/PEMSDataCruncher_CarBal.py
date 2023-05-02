
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
        'plot processed data for averaging period only']

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

#Can this be a menu item so that the program can be ran without choosing a specific test? or can this gui be used just to choose the level 3 directory?
inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    sheetinputpath = input("Input path of _EnergyInputs.csv file:\n")
else:
    print('Select _EnergyInputs.csv file:')
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
        inputpath = os.path.join(directory, testname + '_RawData.csv')
        fuelpath = os.path.join(directory, testname + '_null.csv')
        exactpath = os.path.join(directory, testname + '_null.csv')
        plotpath = os.path.join(directory, testname + '_rawplots.csv')
        PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ' done, back to main menu'
        print(line)
        line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
        print(line)
        print('')
    elif var == '2':
        inputpath=os.path.join(directory, testname+'_FuelData.csv')
        energypath=os.path.join(directory, testname+'_EnergyInputs.csv')
        exactpath=os.path.join(directory, testname+'_ExactData.csv')
        fueloutputpath=os.path.join(directory, testname+'_FuelDataCut.csv')
        exactoutputpath=os.path.join(directory, testname+'_ExactDataCut.csv')
        if os.path.isfile(exactpath):
            PEMS_FuelExactCuts(inputpath, energypath, exactpath, fueloutputpath, exactoutputpath)
        else:
            PEMS_FuelCuts(inputpath, energypath, fueloutputpath)
        if os.path.isfile(fueloutputpath):
            PEMS_FuelScript(fueloutputpath)
        else:
            PEMS_FuelScript(inputpath)
        updatedonelist(donelist, var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)
    elif var == '3':
        print('')
        inputpath=os.path.join(directory,testname+'_EnergyInputs.csv')
        outputpath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        PEMS_EnergyCalcs(inputpath,outputpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)
        
    elif var == '4':
        print('')
        energyinputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)
        inputpath=os.path.join(directory,testname+'_RawData.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        if eval['SB'] == '2041':
            PEMS_2041(inputpath, outputpath)
        else:
            headerpath = os.path.join(directory,testname+'_Header.csv')
            LEMS_Adjust_Calibrations(inputpath,outputpath,headerpath,logpath)
            updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)        
        
    elif var == '5':
        print('')
        inputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Shifted.csv')
        timespath = os.path.join(directory,testname+'_TimeShifts.csv')
        LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)      
        
    elif var == '6':
        print('')
        inputpath=os.path.join(directory,testname+'_RawData_Shifted.csv')
        energyinputpath = os.path.join(directory,testname+'_EnergyInputs.csv')
        ucpath = os.path.join(directory,testname+'_UCInputs.csv')
        outputpath=os.path.join(directory,testname+'_TimeSeries.csv')
        aveoutputpath=os.path.join(directory,testname+'_Averages.csv')
        timespath = os.path.join(directory,testname+'_PhaseTimes.csv')
        bkgmethodspath = os.path.join(directory,testname+'_BkgMethods.csv')
        PEMS_SubtractBkg(inputpath,energyinputpath,ucpath,outputpath,aveoutputpath,timespath,bkgmethodspath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)       
        
    elif var == '7':
        print('')
        gravinputpath=os.path.join(directory,testname+'_GravInputs.csv')
        timeseriespath = os.path.join(directory,testname+'_TimeSeries.csv')
        ucpath=os.path.join(directory,testname+'_UCInputs.csv')
        gravoutputpath=os.path.join(directory,testname+'_GravOutputs.csv')        
        PEMS_GravCalcs(gravinputpath,timeseriespath,ucpath,gravoutputpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)    
        
    elif var == '8':
        print('')
        energypath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        gravinputpath=os.path.join(directory,testname+'_GravOutputs.csv')
        aveinputpath = os.path.join(directory,testname+'_Averages.csv')
        metricpath=os.path.join(directory,testname+'_EmissionOutputs.csv')
        PEMS_CarbonBalanceCalcs(energypath,gravinputpath,aveinputpath,metricpath,logpath)
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)


    elif var == '9':
        print('')
        inputpath = os.path.join(directory, testname + '_TimeSeries_test.csv')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        gravinputpath = os.path.join(directory, testname + '_GravOutputs.csv')
        empath = os.path.join(directory, testname + '_EmissionOutputs.csv')
        periodpath = os.path.join(directory, testname + '_AveragingPeriod.csv')
        outputpath = os.path.join(directory, testname + '_RealtimeOutputs.csv')
        fullaverageoutputpath = os.path.join(directory, testname + '_RealtimeAveragesOutputs.csv')
        averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodOutputs.csv')
        averagecalcoutputpath = os.path.join(directory, testname + '_AveragingPeriodCalcs.csv')
        PEMS_Histogram(inputpath, energypath, gravinputpath, empath, periodpath, outputpath, averageoutputpath, averagecalcoutputpath, fullaverageoutputpath)
        updatedonelist(donelist,var)
        line='\nstep ' +var+ ' done, back to main menu'

    elif var == '10':
        print('')
        inputpath = os.path.join(directory, testname + '_RealtimeOutputs.csv')
        fuelpath=os.path.join(directory, testname + '_FuelDataCut.csv')
        exactpath=os.path.join(directory, testname + '_ExactDataCut.csv')
        plotpath = os.path.join(directory, testname + '_plots.csv')
        PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath)
        updatedonelist(donelist,var)
        line='\nstep ' +var+ ' done, back to main menu'
        print(line)
        line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
        print(line)

    elif var == '11':
        print('')
        #Plot over averaging period only, not full data set
        inputpath = os.path.join(directory, testname + '_AveragingPeriodOutputs.csv')
        fuelpath=os.path.join(directory, testname + '_FuelDataCut.csv')
        exactpath=os.path.join(directory, testname + '_ExactDataCut.csv')
        plotpath = os.path.join(directory, testname + '_averageplots.csv')
        PEMS_Plotter(inputpath, fuelpath, exactpath, plotpath)
        updatedonelist(donelist,var)
        line='\nstep ' +var+ ' done, back to main menu'
        print(line)
        line = '\nopen' +plotpath+ ', update and rerun step' +var+ ' to create a new graph'
        print(line)
   
    elif var == 'exit':
        pass
        
    else:    
        print(var+' is not a menu option')


