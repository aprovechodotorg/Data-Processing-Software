#v0.1  Python3

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

from UCET import LEMS_DataProcessing_IO as io

#import xlrd
#import pandas as pd

########### inputs (only used if this script is run as executable) #############
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TE_DataEntryForm.xlsx'
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_EnergyInputs.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_log.txt'

##################################

def LEMS_MakeInputFile_EnergyCalcs(inputpath,outputpath,logpath):
    ver = '0.1'
    
    logs=[]
    
    [names,units,nom,unc,val] = io.load_inputs_from_spreadsheet(inputpath)
    
    io.write_constant_outputs(outputpath,names,units,nom,unc,val)
    
    line = 'created: '+outputpath
    print(line)
    logs.append(line)
    
    #print to log file
    io.write_logfile(logpath,logs)


#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_MakeInputFile_EnergyCalcs(inputpath,outputpath,logpath)