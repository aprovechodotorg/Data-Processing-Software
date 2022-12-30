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
from easygui import *
import os
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_EnergyCalcs_L2 import LEMS_EnergyCalcs_L2
from LEMS_BasicOp_L2 import LEMS_BasicOP_L2

#from LEMSDataCruncher_Energy import LEMSDataCruncher_Energy

logs=[]


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

#Setting up lists to record the files
testlen = [0] * testnum
list_input = []
list_filename = []
list_directory = []
list_testname = []
list_logname = []
button2 = 'No'
output = button2

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
funs = ['rsync verified data from the server',
       'load data entry form',
        'calculate energy metrics',
        'run comparison between all tests',
        'rsync unverified data to server',
        'rsync user data from user directory of server (remote work']

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
            print('pretend rsync from verified copy of data on the server')
            updatedonelist(donelist, var)

       elif var == '2':
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


       elif var == '3':
              list_energy = []
              for t in range(len(list_input)):
                     print('')
                     print(list_directory[t])
                     print(list_testname[t])
                     inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                     outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                     print(outputpath)
                     LEMS_EnergyCalcs(inputpath, outputpath, logpath)
                     list_energy.append(outputpath)
                     updatedonelist(donelist, var)
                     line = '\nstep ' + var + ' done, back to main menu'
                     print(line)
                     logs.append(line)
       elif var == '4':
              print('')
              print(testname)
              inputpath = list_energy #SAM use loop to define this variable so that menu option 3 in the level 2 analysis can be ran if you have already ran level 1
              outputpath = os.path.join(datadirectory, 'FormattedDataL2.csv')
              print(inputpath)
              print(outputpath)
              LEMS_EnergyCalcs_L2(inputpath, outputpath)
              LEMS_BasicOP_L2(inputpath, outputpath)
              updatedonelist(donelist, var)
              line = '\nstep ' + var + ' done, back to main menu'
              print(line)
              logs.append(line)
       elif var == '5':
              print('pretend rsync to user copy of data on the server (sending data for verification')
              updatedonelist(donelist, var)
       elif var == '6':
              print('pretend rsync from user copy of data on the server (remote work')
              updatedonelist(donelist, var)
       elif var == 'exit':
              pass

       else:
              print(var + ' is not a menu option')
#while t <= tests;
       #LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)

       #LEMS_FormatData_L2(inputpath2, outputpath2, logpath, testnum)
