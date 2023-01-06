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
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
#from openpyxl import load_workbook

logs=[]

#list of function descriptions in order:
funs = ['load data entry form',
        'calculate energy metrics',
        'rsync unverified data to remote server using sam\'s credentials',
        'rsync unverified data to local server using sam\'s credentials']

donelist=['']*len(funs)    #initialize a list that indicates which data processing steps have been done
##################################################################        

# Error handling function that prints the error and keeps the terminal open so the user can read the error
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit
####################################################

# this function updates the donelist when a data processing step is completed
def updatedonelist(donelist,var): 
    index=int(var)-1
    donelist[index]='(done)'    #mark the completed step as 'done'
    for num,item in enumerate(donelist):    #mark the remaining steps as 'not done'
        if num > index:
            donelist[num]=''
    return donelist    

line='\nLEMSDataCruncher_Energy_v0.0\n'
print(line)
logs.append(line)



#Can this be a menu item so that the program can be ran without choosing a specific test? or can this gui be used just to choose the level 3 directory?
inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
if inputmode == "cli":
    sheetinputpath = input("Input path of data entry form (spreadsheet):\n")
else:
    line = 'Select test data entry form (spreadsheet):'
    print(line)
    sheetinputpath = easygui.fileopenbox()
line=sheetinputpath
print(line)
#logs.append(line)

directory,filename=os.path.split(sheetinputpath)
datadirectory,testname=os.path.split(directory)
logname=testname+'_log.txt'
logpath=os.path.join(directory,logname)

#######################################################

var='unicorn'

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
###Update here when adding new menu options (also update [funs])
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
        # syncs data from workstation to remote server using sam's credentials. data must then be verified.
        os.system("rsync -a /home/sam/python_data/ sam@arcfileshare.ddns.net:/home/sam/python_data_new")
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)

    elif var == '4':
        # syncs data from workstation to local server using sam's credentials. data must then be verified.
        os.system("rsync -a /home/sam/python_data/ sam@stovesimulator:/home/sam/python_data_new")
        updatedonelist(donelist,var)
        line='\nstep '+var+' done, back to main menu'
        print(line)
        logs.append(line)
   
    elif var == 'exit':
        pass
        
    else:    
        print(var+' is not a menu option')
