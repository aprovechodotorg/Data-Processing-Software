#v0.0  Python3

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

 #added case to timeperiod function handle date format for field testing (ddmmyyyy hh:mm:ss)
 #do: add error handling for input variables with weird or incorrect formats
 
from uncertainties import ufloat
import csv
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io

########### inputs (only used if this script is run as executable) #############
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test1\CrappieCooker_test1_EnergyInputs.csv'
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test1\CrappieCooker_test1_EnergyOutputs.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test1\CrappieCooker_test1_log.txt'
##################################

def PEMS_EnergyCalcs(inputpath,outputpath,logpath):
    ver = '0.0'
    #This function loads in variables from input file, calculates ISO 19869 fuel and energy metrics, and outputs metrics to output file

    logs=[]
    names=[]            #list of variable names
    outputnames=[]  #list of variable names for the output file
    units={}                #dictionary of units, keys are variable names
    val={}                 #dictionary of nominal values, keys are variable names
    unc={}                  #dictionary of uncertainty values, keys are variable names
    uval={}                   #dictionary of values as ufloat pairs, keys are variable names
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")
    
    line = 'LEMS_EnergyCalcs v'+ver+'   '+timestampstring
    print(line)
    logs.append(line)

    ###############################################
    #load input file and store values in dictionaries
    [names,units,val,unc,uval] = io.load_constant_inputs(inputpath) 
    line = 'loaded: '+inputpath
    print(line)
    logs.append(line)
    #######################################################
    
    #define fuel types by reading the variable names in the input file
    
    fuels=[]   #initialize list of fuel types
    for name in names:
        if 'fuel_type_' in name:
            fuel = name[10:]
            fuels.append(fuel)
    line = 'fuel types =' + str(fuels)
    print(line)
    logs.append(line)
    
    ###Start energy calcs 
    
    name='phase_time_test' #total time of test phase
    units[name]='min'
    names.append(name)
    var1='start_time_test'
    var2='end_time_test'
    try:
        uval[name]=timeperiod(uval[var1],uval[var2])
    except:
        uval[name]=''
    
    ###Energy calcs for each fuel type
    for fuel in fuels:
        fval={}                                                         #initialize dictionary of fuel-specific metrics
        metrics = []                                                   #initialize list of fuel-specific metrics (that will get renamed with fuel identifier and put in 'names')
        fuel_identifier='_'+fuel
        for fullname in names:                              #go through the list of input variables
            if fullname[-len(fuel_identifier):] == fuel_identifier:     # if the variable name ends with the fuel identifier
                name = fullname[:-len(fuel_identifier)]                           #strip off the fuel identifier
                fval[name] = uval[fullname]                   #before passing the variable to the calculations

        name='fuel_mass'   #mass of fuel fed
        units[name]='kg'
        metrics.append(name)
        try:
            fval[name]= fval['initial_fuel_mass'] - fval['final_fuel_mass']
        except:
            fval[name]=''
    
        name='fuel_dry_mass'    #dry fuel mass
        units[name]='kg'       
        metrics.append(name)
        try:
            fval[name]= fval['fuel_mass']*(1-fval['fuel_mc']/100)   
        except:
            try:
                fval['fuel_mass']
                line='undefined variable: fuel_mass'
                print(line)
                logs.append(line)
                fval[name]=''
            except:
                fval[name]=''
                
        name='fuel_Cfrac'
        units[name]='g/g'
        metrics.append(name)
        try:
            fval[name]=fval['fuel_Cfrac_db']*(1-fval['fuel_mc']/100)   
        except:
            try:
                fval['fuel_Cfrac_db']
                line='undefined variable: fuel_Cfrac_db'
                print(line)
                logs.append(line)
                fval[name]=''
            except:
                fval[name]=''
 
        name='fuel_energy'    #fuel energy
        units[name]='MJ'       
        metrics.append(name)
        try:
            fval[name]= fval['fuel_mass']*fval['fuel_heating_value']
        except:
            try:
                fval['fuel_mass']
                line='undefined variable: fuel_mass'
                print(line)
                logs.append(line)
                fval[name]=''
            except:
                fval[name]=''
                
        for metric in metrics:                          #for each metric calculated for the fuel type
            name=metric+fuel_identifier        #add the fuel identifier to the variable name
            uval[name] = fval[metric]
            units[name]=units[metric]
            names.append(name)              #add the new full variable name to the list of variables that will be output
    
    #########Energy calcs for all fuels combined
    
    name='fuel_mass'   #total net mass of fuel consumed including all fuels
    units[name]='kg'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval['fuel_mass_'+fuel]
    except:
        uval[name]=''
    
    name='fuel_dry_mass'    #total net mass dry fuel consumed
    units[name]='kg'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval['fuel_dry_mass_'+fuel]
    except:
        uval[name]=''
    
    name='burn_rate' #fuel-burning rate
    units[name]='g/min'
    names.append(name)
    try:
        uval[name]= uval['fuel_mass']/uval['phase_time_test']*1000
    except:
        uval[name]=''
    
    name='fuel_energy'   #total net energy of fuel consumed including all fuels. ISO 19869 clause 7.6.6.1 Formula 3
    units[name]='MJ'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval[name+'_'+fuel]
    except:
        uval[name]=''
    
    name='firepower'    #average firepower. ISO 19869 clause 9.3.5.2 Formula 80
    units[name]='W'
    names.append(name)
    try:
        uval[name]= uval['fuel_energy']/uval['phase_time_test']/60*1000000 #60 sec/min, 10^6 J/MJ
    except:
        uval[name]=''
        
    name='fuel_EHV'      #: effective heating value of total fuel consumed (MJ/kg). ISO 19869 clause 7.8.8.2 Formula 17
    units[name] = 'MJ/kg'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval['fuel_heating_value_'+fuel]*uval['fuel_mass_'+fuel]/uval['fuel_mass']
    except:
        uval[name]=''
    
    name = 'fuel_Cfrac'   #  effective fuel carbon fraction of total fuel consumed (g/g).  ISO 19869 clause 7.8.8.3 Formula 18
    units[name] = 'g/g'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval['fuel_Cfrac_'+fuel]*uval['fuel_mass_'+fuel]/uval['fuel_mass']
    except:
        uval[name]=''
        
    name = 'fuel_Cfrac_db'   #  effective fuel carbon fraction of total fuel consumed, dry basis (g/g)
    units[name] = 'g/g'
    names.append(name)
    uval[name]=ufloat(0,0)
    try:
        for fuel in fuels:
            uval[name]=uval[name]+uval['fuel_Cfrac_db_'+fuel]*uval['fuel_dry_mass_'+fuel]/uval['fuel_dry_mass']
    except:
        uval[name]=''
        
    #end calculations
    ######################################################
    #make output file
    io.write_constant_outputs(outputpath,names,units,val,unc,uval)       
    
    line = 'created: '+outputpath
    print(line)
    logs.append(line)
    
    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
    
def timeperiod(StartTime,EndTime):             
    #function calculates time difference in minutes
    #Inputs start and end times as strings and converts to time objects
    if len(StartTime) == 8 and len(EndTime) == 8: #if time is entered
        start_object=dt.strptime(StartTime, '%H:%M:%S')       #convert the start time string to date object
        end_object=dt.strptime(EndTime, '%H:%M:%S')          #convert the end time string to date object
    elif len(StartTime) == 17 and len(EndTime) == 17:   #if date is entered
        start_object=dt.strptime(StartTime, '%Y%m%d  %H:%M:%S')       #convert the start time string to date object
        end_object=dt.strptime(EndTime, '%Y%m%d  %H:%M:%S')          #convert the end time string to date object
    else:
        print('Error: Invalid time format')
    delta_object=end_object-start_object                           #time difference as date object
    Time=delta_object.total_seconds()/60                         #time difference as minutes
    return Time
    
#####################################################################
#the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    PEMS_EnergyCalcs(inputpath,outputpath,logpath)
