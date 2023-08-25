#v1 Python3

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

#This script adjusts sensor calibrations and recalculates firmware calculations.
#It reads in raw data csv file
#It reads in header input file with updated calibration parameters
#It outputs recalculated data csv file

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
from LEMS_RedoFirmwareCalcs import RedoFirmwareCalcs
from PEMS_2041 import PEMS_2041
from LEMS_3002 import LEMS_3002

#########      inputs      ##############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#raw data input file:
inputpath='RawData.csv'
#output data file to be created:
outputpath='RawData_Recalibrated.csv'
#input header file to be used for the recalculation
headerpath='header.csv'
logpath='log.csv'
##########################################

def LEMS_Adjust_Calibrations(inputpath,outputpath,headerpath,logpath):
    # This function loads in raw data time series file, and creates header input file (if it does not already exist)
    # The user is prompted to edit the header input file (to update calibration parameters)
    # The firmware calculations are redone using the new calibration parameters and a new raw data file (with header) is output 
    # The old and new data series are plotted for any data series that changed
    
    ver = '0.1'

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Adjust_Calibrations v'+ver+'   '+timestampstring #add to log
    print(line)
    logs=[line]
    
    #################################################
    try:
        #read in raw data file

        [names,units,data_old,A_old,B_old,C_old,D_old,const_old] = io.load_timeseries_with_header(inputpath)

        ##############################################
        #read in header

        #check for header input file
        if os.path.isfile(headerpath):
            print('Header file already exists:')
        else:   #if header file is not there then create it by printing the existing header from raw data file
            io.write_header(headerpath,names,units,A_old,B_old,C_old,D_old)
            print('Header file created:')
        print('')
        print(headerpath)
        print('')

        #give instructions
        firstline='Open the Header input file and edit the desired calibration parameters:\n\n'
        secondline=headerpath
        thirdline='\n\nSave and close the Header input file then click OK to continue'
        boxstring=firstline+secondline+thirdline
        msgtitle='gitrdone'
        easygui.msgbox(msg=boxstring,title=msgtitle)

        #open header file and read in new cal params
        [names_new,units_new,A_new,B_new,C_new,D_new,const_new] = io.load_header(headerpath)
    except:
        pass
    
    ###########################################################
    #define firmware version for recalculations
    firmware_version='SB4003.16' #default
    msgstring='Enter sensorbox firmware version:'
    boxtitle='gitrdone'
    entered_firmware_version = easygui.enterbox(msg=msgstring, title=boxtitle, default=firmware_version, strip=True)
    if entered_firmware_version == firmware_version:
        firmware_version = entered_firmware_version #Only runs adjustments for SB4003.16 currently. Passes for any other SB
    
        line='firmware_version='+firmware_version #add to log
        print(line)
        logs.append(line)

        ############################################################
        #redo firmware calculations
        [data_new,updated_channels] = RedoFirmwareCalcs(firmware_version,names,A_old,B_old,const_old,data_old,A_new,B_new,const_new)

        ###############################################################
        #document which parameters were changed

        for name in names:
            if A_old[name] != A_new[name] and not np.isnan(A_old[name]) and not np.isnan(A_new[name]):
                line=name+' A_old = '+str(A_old[name])+ ' , A_new = '+str(A_new[name])
                print(line)
                logs.append(line)
            if B_old[name] != B_new[name] and not np.isnan(B_old[name]) and not np.isnan(B_new[name]):
                line=name+' B_old = '+str(B_old[name])+ ' , B_new = '+str(B_new[name])
                print(line)
                logs.append(line)
            if D_old[name] != D_new[name] and not np.isnan(D_old[name]) and not np.isnan(D_new[name]):
                line=str(C_old[name])+' old = '+str(D_old[name])+ ' , new = '+str(D_new[name])
                print(line)
                logs.append(line)

        if updated_channels == []:
            line = 'no channels were recalculated'
            print(line)
            logs.append(line)
        else:
            for name in updated_channels:
                line='recalculated '+name+' data series'
                print(line)
                logs.append(line)

        ###############################################################
        #print updated time series data file
        #io.write_timeseries_with_header(outputpath,names,units,data_new,A_new,B_new,C_new,D_new)
        io.write_timeseries(outputpath,names,units,data_new)

        line = 'created: '+outputpath #add to log
        print(line)
        logs.append(line)

        ##############################################
        #print to log file
        io.write_logfile(logpath,logs)

        ##################################################
        #plot the old and new data series to inspect the differences
        if len(updated_channels) >0: #if any data series were updated
            firstline='The following plots show the effect of the recalculation. Close the plots to continue.'
            msgtitle='gitrdun'
            easygui.msgbox(msg=firstline,title=msgtitle)

            for (fignum,name) in enumerate(updated_channels): #for each channel that was changed
                for n in range(len(data_old[name])):
                    data_old[name][n]=float(data_old[name][n])          # convert old and new data series to floats
                    data_new[name][n]=float(data_new[name][n])      # to remove strings so they will plot
                plt.figure(fignum+1)
                old=plt.plot(data_old[name], label=name + ' old')
                new=plt.plot(data_new[name], label=name + ' new')
                plt.xlabel('data points')
                plt.ylabel(units[name])
                plt.legend()
            plt.show()
        #end of figure
        #end of function

    elif entered_firmware_version == 'SB2041' or entered_firmware_version == '2041':
        PEMS_2041(inputpath, outputpath, logpath) #If 2041 SB, send to reconfigure script
    elif entered_firmware_version == 'SB3002' or entered_firmware_version == '3002':
        LEMS_3002(inputpath, outputpath, logpath)
    else:
        line = 'Firmware version: ' + entered_firmware_version + ' does not currently exist as a recalibration version, nothing was recalibrated'
        line_2 = 'Current supported firmware versions: SB4003.16, SB3002, SB2041'
        print(line)
        print(line_2)
        logs.append(line)
        logs.append(line_2)

        ###############################################################
        #Load in raw data and print it out as the same data
        try:
            [names, units, data_old, A_old, B_old, C_old, D_old, const_old] = io.load_timeseries_with_header(inputpath)
        except:
            [names, units, data_old] = io.load_timeseries(inputpath)

        #print time series data file
        io.write_timeseries(outputpath,names,units,data_old)

        line = 'created: '+outputpath #add to log
        print(line)
        logs.append(line)

        ##############################################
        #print to log file
        io.write_logfile(logpath,logs)


#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_Adjust_Calibrations(inputpath,outputpath,headerpath,logpath)
    