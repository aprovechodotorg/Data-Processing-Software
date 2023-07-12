#v0.1 Python3

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

###inputs:
# firmware_version = SB4003.16 
# names: list of channel names
# A_old: dictionary keys are variable names, values are A (span) parameters from the raw data file header
# B_old = dictionary keys are variable names, values are B (offset) parameters from the raw data file header
# const_old: dictionary keys are constant variable names (C parameters), values are constant variable values (D parameters) from the raw data file header
# data_old: dictionary keys are variable names, values are lists of time series data from the raw data file
# A_new: dictionary keys are variable names, values are new A (span) parameters defined in the header input file
# B_new: dictionary keys are constant variable names, values are new B (offset) parameters defined in the header input file
# const_new: dictionary keys are constant variable names (C parameters), values are constant variable values (D parameters) from the header input file

###output: 
#data_new: dictionary keys are variable names, values are lists of recalculated time series data
#updated_channels: list of channel names that were updated

import math

def RedoFirmwareCalcs(firmware_version,names,A_old,B_old,const_old,data_old,A_new,B_new,const_new):
    #This function inputs time series data, and recalculates firmware calculations with updated calibration parameters
    # called by LEMS_Adjust_Calibrations()
    
    data_new = {} 
    updated_channels=[]
    ###  SB4003.16   ##############################
    if firmware_version == 'SB4003.16':
        calculated_channels=['O2_ave'] #define list of calculated channels that are not a function of A and B
        for name in names:
            data_new[name]=[]   #initialize a list to fill with the new data series
            if name not in calculated_channels:  
                if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(A_new[name]) and math.isnan(B_old[name]) and math.isnan(B_new[name]): #if A the B parameter did not change
                    data_new[name]=data_old[name]       #copy the old time series to the new time series
                else:   #if A or B did change     
                    updated_channels.append(name)
                    #recalculate data values using the following formula: CO=A*(CO_raw+B)
                    for n in range(len(data_old[name])):    #for each point in the old data series
                        oldval=data_old[name][n]    #grab the old value          
                        #back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters 
                        newval=A_new[name]*(oldval/A_old[name]-B_old[name]+B_new[name])
                        data_new[name].append(newval)   #append the new value to the new data list
                    print(name, ' updated')
            
        #calculated channels: 
        name = 'O2_ave'
        changed = 0 #initialize flag to see any values changed
        for n in range(len(data_old[name])):    #for each point in the old data series
            oldval = data_old[name][n]
            newval=float((data_new['O2_1'][n]+data_new['O2_2'][n]+data_new['O2_3'][n]+data_new['O2_4'][n]))/4
            data_new[name].append(newval)   #append the new value to the new data list
            if not math.isclose(oldval,newval,rel_tol=0.005): #if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  #set changed flag
        if changed == 1:
            updated_channels.append(name)
 
    #################################
    #add another firmware version here
    #################################
    
    else: #for all other firmware versions without any channels that have special calculations
        for name in names:
            data_new[name]=[]   #initialize a list to fill with the new data series
            if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(A_new[name]) and math.isnan(B_old[name]) and math.isnan(B_new[name]): #if A the B parameter did not change
                data_new[name]=data_old[name]       #copy the old time series to the new time series
            else:   #if A or B did change     
                updated_channels.append(name)
                #recalculate data values using the following formula: CO=A*(CO_raw+B)
                for n in range(len(data_old[name])):    #for each point in the old data series
                    oldval=data_old[name][n]    #grab the old value          
                    #back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters 
                    newval=A_new[name]*(oldval/A_old[name]-B_old[name]+B_new[name])
                    data_new[name].append(newval)   #append the new value to the new data list
                print(name, ' updated')
    
    return data_new, updated_channels
    
    