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
from easygui import *
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
from UploadData import UploadData
from PEMS_Plotter1 import PEMS_Plotter
from LEMS_3002 import LEMS_3002
from LEMS_Scale import LEMS_Scale
from LEMS_FormattedL1 import LEMS_FormattedL1
from LEMS_CSVFormatted_L1 import LEMS_CSVFormatted_L1
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_Sensirion import LEMS_Senserion
from LEMS_TEOM import LEMS_TEOM
from LEMS_TEOM_SubtractBkg import LEMS_TEOM_SubtractBkg
from LEMS_OPS import LEMS_OPS
from LEMS_customscatterplot import LEMS_customscatterplot
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from LEMS_Realtime import LEMS_Realtime
from LEMS_Pico import LEMS_Pico
import traceback
#from openpyxl import load_workbook

logs=[]

#list of function descriptions in order:
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
        'calculate averages from a specified cut period',
        'create a custom output table',
        'plot processed data',
        'create scatter plot of 2 variables',
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

def updatedonelisterror(donelist,var):
    index=int(var)-1
    donelist[index]='(error)'    #mark the completed step as 'done'

    for num,item in enumerate(donelist):    #mark the remaining steps as 'not done'
        if num < index: #Mark steps as passed if they weren't run
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
    
    if var == '1': #Plot raw data
        print('')
        inputpath = os.path.join(directory, testname + '_RawData.csv')
        fuelpath = os.path.join(directory, testname + '_null.csv')
        exactpath = os.path.join(directory, testname + '_null.csv')
        fuelmetricpath  = os.path.join(directory, testname + '_null.csv')
        scalepath = os.path.join(directory, testname + '_null.csv')
        nanopath = os.path.join(directory, testname + '_null.csv')
        TEOMpath = os.path.join(directory, testname + '_null.csv')
        senserionpath = os.path.join(directory, testname + '_null.csv')
        OPSpath = os.path.join(directory, testname + '_null.csv')
        Picopath = os.path.join(directory, testname + '_null.csv')
        plotpath = os.path.join(directory, testname + '_rawplots.csv')
        savefig = os.path.join(directory, testname + '_rawplot.png')
        try:
            names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
            PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath,
                                savefig)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
            line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
            print(line)
        except Exception as e:#If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '2': #load energy inputs
        print('')
        inputpath=sheetinputpath
        outputpath=os.path.join(directory,testname+'_EnergyInputs.csv')
        try:
            LEMS_MakeInputFile_EnergyCalcs(inputpath,outputpath,logpath)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:#If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '3': #load in additonal raw data files
        print('')
        inputpath = os.path.join(directory, testname + '_ScaleRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        try:
            LEMS_Scale(inputpath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and processed scale data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
            print(line)
            #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)
        print('')
        inputpath = os.path.join(directory, testname + '_NanoscanRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        try:
            LEMS_Nanoscan(inputpath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and processed nanoscan data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                               "If file exists, some other error may have occured."
            print(line)
            #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)
        print('')
        inputpath = os.path.join(directory, testname + '_TEOMRawData.txt')
        rawoutputpath = os.path.join(directory, testname + '_TEOMRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        try:
            LEMS_TEOM(inputpath, rawoutputpath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and processed TEOM data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                               "If file exists, some other error may have occured."
            print(line)
           #traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)
        print('')
        topatch = input("Enter patch for Senserion Raw Data controller board patch and fill or press enter for normal Senserion data processing.\n")
        if topatch == "patch":
            inputpath_topatch = os.path.join(directory, testname + '_SenserionRawData_topatch.csv')
            outputpath_patched = os.path.join(directory, testname + '_SenserionRawData.csv')
            io.fill_controller_reboot_data(inputpath_topatch, outputpath_patched)
            inputpath = os.path.join(directory, testname + '_SenserionRawData.csv')
            outputpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        else:
            inputpath = os.path.join(directory, testname + '_SenserionRawData.csv')
            outputpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        try:
            LEMS_Senserion(inputpath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and patched Senserion data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. " \
                                               "If file exists, some other error may have occured."
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)

        print('')
        inputpath = os.path.join(directory, testname + '_OPSRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
        try:
            LEMS_OPS(inputpath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and processed OPS data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)
        inputpath = os.path.join(directory, testname + '_PicoRawData.csv')
        lemspath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
        outputpath = os.path.join(directory, testname + '_FormattedPicoData.csv')
        try:
            LEMS_Pico(inputpath, lemspath, outputpath, logpath)
            #updatedonelist(donelist, var)
            line = '\nloaded and processed Pico data'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = "Data file: " + inputpath + " doesn't exist and will not be processed. If file exists, some other " \
                                               "error may have occured."
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            #updatedonelisterror(donelist, var)
        updatedonelist(donelist, var)
        line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
        print(line)
        logs.append(line)

    elif var == '4': #calculate energy metrics
        print('')
        inputpath=os.path.join(directory,testname+'_EnergyInputs.csv')
        outputpath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        try:
            LEMS_EnergyCalcs(inputpath,outputpath,logpath)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:#If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        
    elif var == '5': #recalbrate data
        print('')
        sensorpath = os.path.join(directory, testname + '_SensorboxVersion.csv')
        #[enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energyinputpath)  # Load energy metrics
        inputpath=os.path.join(directory,testname+'_RawData.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        headerpath = os.path.join(directory,testname+'_Header.csv')
        try:
            LEMS_Adjust_Calibrations(inputpath, sensorpath, outputpath,headerpath,logpath, inputmethod)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        
    elif var == '6': #shift timeseries data
        print('')
        inputpath=os.path.join(directory,testname+'_RawData_Recalibrated.csv')
        outputpath=os.path.join(directory,testname+'_RawData_Shifted.csv')
        timespath = os.path.join(directory,testname+'_TimeShifts.csv')
        try:
            LEMS_ShiftTimeSeries(inputpath,outputpath,timespath,logpath, inputmethod)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        
    elif var == '7': #subtract background
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
        try:
            PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath, bkgmethodspath,
                             logpath, savefig1, savefig2, inputmethod)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '8':  # cut TEOM realtime data based on phases
        print('')
        inputpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        outputpath = os.path.join(directory, testname + 'TEOM_TimeSeries.csv')
        aveoutputpath = os.path.join(directory, testname + '_TEOM_Averages.csv')
        timespath = os.path.join(directory, testname + '_TEOMPhaseTimes.csv')
        try:
            LEMS_TEOM_SubtractBkg(inputpath, outputpath, aveoutputpath, timespath, logpath)
            updatedonelist(donelist, var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            print('did you create _TEOMPhaseTimes.csv ?')
            updatedonelisterror(donelist, var)

    elif var == '9': #calculate gravimetric data
        print('')
        gravinputpath=os.path.join(directory,testname+'_GravInputs.csv')
        aveinputpath = os.path.join(directory,testname+'_Averages.csv')
        timespath = os.path.join(directory,testname+'_PhaseTimes.csv')
        energypath = os.path.join(directory, testname+'_EnergyOutputs.csv')
        gravoutputpath=os.path.join(directory,testname+'_GravOutputs.csv')
        try:
            LEMS_GravCalcs(gravinputpath,aveinputpath,timespath,energypath,gravoutputpath,logpath, inputmethod)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called functions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)
        
    elif var == '10': #calculate emission metrics
        print('')
        inputpath=os.path.join(directory,testname+'_TimeSeries.csv')
        energypath=os.path.join(directory,testname+'_EnergyOutputs.csv')
        gravinputpath=os.path.join(directory,testname+'_GravOutputs.csv')
        aveinputpath = os.path.join(directory,testname+'_Averages.csv')
        timespath = os.path.join(directory,testname+'_PhaseTimes.csv')
        sensorpath = os.path.join(directory, testname + '_SensorboxVersion.csv')
        emisoutputpath=os.path.join(directory,testname+'_EmissionOutputs.csv')
        alloutputpath=os.path.join(directory,testname+'_AllOutputs.csv')
        cutoutputpath=os.path.join(directory,testname+'_CutTable.csv')
        outputexcel=os.path.join(directory,testname+'_CutTable.xlsx')

        fuelpath = os.path.join(directory, testname + '_null.csv') #No fuel or exact taken in
        exactpath = os.path.join(directory, testname + '_null.csv')
        fuelmetricpath = os.path.join(directory, testname + '_null.csv')
        scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname+ '_FormattedOPSData.csv')
        Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
        emissioninputpath = os.path.join(directory, testname + '_EmissionInputs.csv')
        try:
            LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath,
                               timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,nanopath, TEOMpath,
                               senserionpath, OPSpath, Picopath, emissioninputpath, inputmethod)
            LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, testname, logpath)
            updatedonelist(donelist,var)
            line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
            print(line)
            logs.append(line)
        except Exception as e:  # If error in called fuctions, return error but don't quit
            line = 'Error: ' + str(e)
            print(line)
            traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
            logs.append(line)
            updatedonelisterror(donelist, var)

    elif var == '11': #cut period
        print('')
        energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
        gravpath = os.path.join(directory, testname + '_GravOutputs.csv')
        phasepath = os.path.join(directory, testname + '_PhaseTimes.csv')
        periodpath = os.path.join(directory, testname + '_AveragingPeriod.csv')
        outputpath = os.path.join(directory, testname + '_AveragingPeriodTimeSeries.csv')
        averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodAverages.csv')
        savefig = os.path.join(directory, testname + '_AveragingPeriod.png')

        fuelpath = os.path.join(directory, testname + '_null.csv') #No fuel or exact taken in
        exactpath = os.path.join(directory, testname + '_null.csv')
        fuelmetricpath = os.path.join(directory, testname + '_null.csv')
        scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname+ '_FormattedOPSData.csv')
        Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')

        if inputmethod == '1':
            # Find what phases people want graphed
            message = 'Select which phases will be graphed'  # message
            title = 'Gitrdun'
            phases = ['L1', 'hp', 'mp', 'lp', 'L5']  # phases to choose from
            choice = choicebox(message, title, phases)  # can select one or multiple

            inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + choice + '.csv')
            periodpath = os.path.join(directory, testname + '_AveragingPeriod_' + choice + '.csv')
            outputpath = os.path.join(directory, testname + '_AveragingPeriodTimeSeries_' + choice + '.csv')
            averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodAverages_' + choice + '.csv')

            if os.path.isfile(inputpath):
                try:
                    LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath,
                                  savefig, choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath, scalepath,
                                  nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
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
            else:
                line = inputpath + ' does not exist'
                print(line)
        else:
            phases = ['L1', 'hp', 'mp', 'lp', 'L5']  # phases to choose from
            error = 0
            for phase in phases:

                inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
                periodpath = os.path.join(directory, testname + '_AveragingPeriod_' + phase + '.csv')
                outputpath = os.path.join(directory, testname + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodAverages_' + phase + '.csv')

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

    elif var == '12': #Custom cut table
        print('')
        inputpath = os.path.join(directory, testname + '_AllOutputs.csv')
        outputpath = os.path.join(directory, testname + '_CustomCutTable.csv')
        outputexcel = os.path.join(directory, testname + '_CustomCutTable.xlsx')
        csvpath = os.path.join(directory, testname + '_CutTableParameters.csv')
        try:
            LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, testname, logpath)
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

    elif var == '13': #plot processed data
        print('')
        #Find what phases people want graphed
        message = 'Select which phases will be graphed' #message
        title = 'Gitrdun'
        phases = ['L1', 'hp', 'mp', 'lp', 'L5', 'full'] #phases to choose from
        choices = multchoicebox(message, title, phases) #can select one or multiple

        fuelpath = os.path.join(directory, testname + '_null.csv') #No fuel or exact taken in
        exactpath = os.path.join(directory, testname + '_null.csv')
        fuelmetricpath = os.path.join(directory, testname + '_null.csv')
        scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname+ '_FormattedOPSData.csv')
        Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')

        try:
            for phase in choices: #for each phase selected, run through plot function
                inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
                if os.path.isfile(inputpath): #check that the data exists
                    plotpath = os.path.join(directory, testname + '_plots_' + phase + '.csv')
                    savefig = os.path.join(directory, testname + '_plot_' + phase + '.png')
                    names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                        PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, nnames, tnames, sennames, opsnames, pnames, plotpath,
                                        savefig)
                    line = '\nopen' + plotpath + ', update and rerun step' + var + ' to create a new graph'
                    print(line)
                else:
                    line = inputpath + ' does not exist and will not be plotted.'
                    print(line)
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

    elif var == '14': #plot scatter plot of 2 variables
        print('')
        #Find what phases people want graphed
        message = 'Select which phases will be graphed. To look at the cut period of the phase also select cut period' #message
        title = 'Gitrdun'
        phases = ['L1', 'hp', 'mp', 'lp', 'L5', 'full', 'cut period'] #phases to choose from
        choices = multchoicebox(message, title, phases) #can select one or multiple

        fuelpath = os.path.join(directory, testname + '_FormattedFuelData.csv')
        exactpath = os.path.join(directory, testname + '_FormattedExactData.csv')
        scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        OPSpath = os.path.join(directory, testname+ '_FormattedOPSData.csv')
        Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
        regressionpath = os.path.join(directory, testname + '_Regressions.csv')

        try:
            if 'cut period' in choices:
                choices = choices[:-1] #remove last from list
                for phase in choices:
                    savefigpath = os.path.join(directory, testname + '_cut')
                    inputpath = os.path.join(directory, testname + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                    if os.path.isfile(inputpath):  # check that the data exists
                        LEMS_customscatterplot(inputpath, fuelpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                               regressionpath, phase, savefigpath, logpath)
                    else:
                        line = phase + ' data does not exist and will not be plotted.'
                        print(line)
            else:
                for phase in choices:
                    savefigpath = os.path.join(directory, testname)
                    inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
                    if os.path.isfile(inputpath):  # check that the data exists
                        LEMS_customscatterplot(inputpath, fuelpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                               regressionpath, phase, savefigpath, logpath)
                    else:
                        line = phase + ' data does not exist and will not be plotted.'
                        print(line)
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

    elif var == '15': #Upload data
        print('')
        try:
            UploadData(directory, testname)
            updatedonelist(donelist, var)
            line='\nstep ' + var + 'done, back to main menu'
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
        print(var+' is not a menu option')
