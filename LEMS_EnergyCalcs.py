#v0.3  Python3

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

from uncertainties import ufloat
import csv
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io

########### inputs (only used if this script is run as executable) #############
inputpath='C:\Mountain Air\equipment\Aprovecho\LEMSData\CrappieCooker\CrappieCooker_EnergyInputs_test.csv'
outputpath='C:\Mountain Air\equipment\Aprovecho\LEMSData\CrappieCooker\CrappieCooker_EnergyOutputs.csv'
logpath='C:\Mountain Air\equipment\Aprovecho\LEMSData\CrappieCooker\CrappieCooker_log.txt'

##################################

def LEMS_EnergyCalcs(inputpath,outputpath,logpath):
    ver = '0.3'
    
    phases = ['hp','mp','lp']   #list of phases
    pots = ['pot1','pot2','pot3','pot4'] # list of pots

    logs=[]
    global names
    names=[]   #list of variable names
    global metrics
    metrics = []
    outputnames=[] #list of variable names for the output file
    global units
    units={}  #dictionary of units, keys are variable names
    val={}   #dictionary of values as ufloat pairs, keys are variable names
    nom={}   #dictionary of nominal values, keys are variable names
    unc={}  #dictionary of uncertainty values, keys are variable names
    
    Cp=4.18 #kJ/kg/K specific heat capacity of water from Clause 5.4.2 Formula 4
    
    #latent heat of vaporization of water lookup table from https://www.engineeringtoolbox.com/water-properties-d_1573.html
    hvap_kg={}
    hvap_mol={}
    hvap_kg[90]=2282.5 #kJ/kg
    hvap_kg[96]=2266.9 #kJ/kg
    hvap_kg[100]=2260 #kJ/kg    
    hvap_mol[90]=41120 #J/mol
    hvap_mol[96]=40839 #J/mol
    hvap_mol[100]=40650 #J/mol    
    
    timestampobject=dt.now()
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")
    
    line = 'LEMS_EnergyCalcs v'+ver+'   '+timestampstring
    print(line)
    logs.append(line)

    ###############################################
    [names,units,nom,unc,val] = io.load_constant_inputs(inputpath)
    line = 'loaded '+inputpath
    print(line)
    logs.append(line)
    #######################################################
    ###Start Energy calcs 
    
    #latent heat of water vaporization at local boiling point (interpolate lookup table)
    name='Hvap'
    names.append(name)
    units[name]='kJ/kg' 
    if val['boil_temp'] > 96:  
         val[name]=hvap_kg[96]+(val['boil_temp']-96)*(hvap_kg[100]-hvap_kg[96])/(100-96)
    else:
         val[name]=hvap_kg[90]+(val['boil_temp']-90)*(hvap_kg[96]-hvap_kg[90])/(96-90)
    
    ###Energy calcs for each phase
    for phase in phases:
        phase_identifier='_'+phase
        for fullname in names:
            if fullname[-3:] == phase_identifier:
                name = fullname[:-3]
                val[name] = val[fullname]

        name='phase_time' #total time of test phase
        units[name]='min'
        metrics.append(name)
        var1='start_time'
        var2='end_time'
        val[name]=timeperiod(val[var1],val[var2])
    
        name='time_to_boil' 
        units[name]='min'
        metrics.append(name)
        var1='start_time'
        var2='boil_time'
        try:
            val[name]=timeperiod(val[var1],val[var2])
        except:
            val[name]='NaN'
            
        name='fuel_mass'   #mass of fuel fed
        units[name]='kg'
        metrics.append(name)
        val[name]= val['initial_fuel_mass'] - val['final_fuel_mass']
    
        name='fuel_dry_mass'
        units[name]='kg'       
        metrics.append(name)
        val[name]= val['fuel_mass']*(1-val['fuel_mc']/100)
    
        name='char_mass'
        units[name]='kg'
        metrics.append(name)
        val[name]= val['final_char_mass'] - val['initial_char_mass']

        for pot in pots:
            name='initial_water_mass_'+pot
            units[name]='kg'    
            metrics.append(name)
            initial_mass = 'initial_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                val[name]= val[initial_mass]-val[empty_mass]
            except:
                val[name]=0

            name='final_water_mass_'+pot
            units[name]='kg'    
            metrics.append(name)
            final_mass = 'final_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                val[name]= val[final_mass]-val[empty_mass]
            except:
                val[name]=0
    
            name='useful_energy_delivered_'+pot
            units[name]='kJ'    
            metrics.append(name)
            #Clause 5.4.2 Formula 4: Q1=Cp*G1*(T2-T1)+(G1-G2)*gamma
            try:
                val[name]= Cp*val['initial_water_mass_'+pot]*(val['max_water_temp_'+pot]-val['initial_water_temp_'+pot])+(val['initial_water_mass_'+pot]-val['final_water_mass_'+pot])*val['Hvap']
            except:
                val[name]=0
 
        name='useful_energy_delivered'
        units[name]='kJ'    
        metrics.append(name)
        val[name]= val['useful_energy_delivered_pot1']+val['useful_energy_delivered_pot2']+val['useful_energy_delivered_pot3']+val['useful_energy_delivered_pot4']
    
        name='cooking_power'
        units[name]='kW'
        metrics.append(name)
        #Clause 5.4.3 Formula 5: Pc=Q1/(t3-t1)
        val[name]= val['useful_energy_delivered']/val['phase_time']/60    
    
        #thermal efficiency with no energy credit for remaining char
        name='eff_wo_char'
        units[name]='%'
        metrics.append(name)
        #Clause 5.4.4 Formula 6: eff=Q1/B/Qnet,af*100
        val[name]= val['useful_energy_delivered']/val['fuel_mass']/val['fuel_heating_value']*100
    
        #thermal efficiency with energy credit for remaining char
        name='eff_w_char'
        units[name]='%'
        metrics.append(name)
        #Clause 5.4.5 Formula 7: eff=Q1/(B*Qnet,af-C*Qnet,char)*100  
        val[name]= val['useful_energy_delivered']/(val['fuel_mass']*val['fuel_heating_value']-val['char_mass']*val['char_heating_value'])*100
    
        name='char_energy_productivity'
        units[name]='%'
        metrics.append(name)
        # Clause 5.4.6 Formula 8: Echar=C*Qnet,char/B/Qnet,af*100
        val[name]= val['char_mass']*val['char_heating_value']/val['fuel_mass']/val['fuel_heating_value']*100
    
        name='char_mass_productivity'
        units[name]='%'
        metrics.append(name)
        # Clause 5.4.7 Formula 9: mchar=C/B*100
        val[name]= val['char_mass']/val['fuel_mass']*100
    
        name='burn_rate' #fuel-burning rate
        units[name]='g/min'
        metrics.append(name)
        val[name]= val['fuel_mass']/val['phase_time']
    
        name='firepower'
        units[name]='kW'
        metrics.append(name)
        val[name]= (val['fuel_mass']*val['fuel_heating_value']-val['char_mass']*val['char_heating_value'])/val['phase_time']/60
    
        for metric in metrics:
            name=metric+phase_identifier
            val[name] = val[metric]
            units[name]=units[metric]
            names.append(name)
    
    #end calculations
    ######################################################

    #make output file    
    io.write_constant_outputs(outputpath,names,units,nom,unc,val)
    
    line = 'created: '+outputpath
    print(line)
    logs.append(line)
    
    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)
    
def timeperiod(StartTime,EndTime): #add case to handle date format for field testing
    start_object=dt.strptime(StartTime, '%H:%M:%S') #convert the start time string to date object
    end_object=dt.strptime(EndTime, '%H:%M:%S') #convert the end time string to date object
    delta_object=end_object-start_object #time difference as date object
    Time=delta_object.total_seconds()/60 #time difference as minutes
    return Time
    
#####################################################################
#the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    LEMS_EnergyCalcs(inputpath,outputpath,logpath)
