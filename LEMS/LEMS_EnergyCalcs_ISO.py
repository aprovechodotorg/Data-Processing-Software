#v0.4  Python3

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

 #do: add case to timeperiod function handle date format for field testing (ddmmyyyy hh:mm:ss)
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

def LEMS_EnergyCalcs(inputpath,outputpath,logpath):
    ver = '0.41'
    #This function loads in variables from input file, calculates ISO 19867-1 thermal efficiency metrics, and outputs metrics to output file
    
    phases = ['hp','mp','lp']   #list of phases
    pots = ['pot1','pot2','pot3','pot4'] # list of pots

    logs=[]
    names=[]            #list of variable names
    outputnames=[]  #list of variable names for the output file
    units={}                #dictionary of units, keys are variable names
    val={}                 #dictionary of nominal values, keys are variable names
    unc={}                  #dictionary of uncertainty values, keys are variable names
    uval={}                   #dictionary of values as ufloat pairs, keys are variable names
    
    #For Jupyter
    trial={}
    
    Cp=4.18             #kJ/kg/K specific heat capacity of water from Clause 5.4.2 Formula 4
    
    #latent heat of vaporization of water lookup table from https://www.engineeringtoolbox.com/water-properties-d_1573.html
    hvap_kg={}
    hvap_mol={}
    hvap_kg[90]=2282.5 #kJ/kg
    hvap_kg[96]=2266.9 #kJ/kg
    hvap_kg[100]=2260 #kJ/kg    
    hvap_mol[90]=41120 #J/mol
    hvap_mol[96]=40839 #J/mol
    hvap_mol[100]=40650 #J/mol

    #Calorific Values of fuels
    CV = {}
    CV['wood'] = 1320 #kJ/kg
    CV['char'] =1200
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")
    
    line = 'LEMS_EnergyCalcs v'+ver+'   '+timestampstring #Add timestamp and version to log
    print(line)
    logs.append(line)

    ###############################################
    #load input file and store values in dictionaries
    [names,units,val,unc,uval] = io.load_constant_inputs(inputpath) 
    line = 'loaded: '+inputpath
    print(line)
    logs.append(line)
    #######################################################

    #start fuel calcs
    fuels = [] #blank list to track for multi fuels
    fuelvals = ['initial_fuel_mass', #list of fuel variables
                'final_fuel_mass',
                'fuel_type',
                'fuel_source',
                'fuel_dimensions',
                'fuel_higher_heating_value',
                'fuel_mc',
                'fuel_Cfrac_db']

    for name in names: #go through and check fuel types and if there's entered values
        if 'fuel_higher_heating_value_' in name: #only shows up in multi fuel version of data entry sheet
            if val[name] != '': #If there's an entered input for the fuel number, add it to the list of fuels
                fuels.append(name)

    if len(fuels) != 0: #If multifuel data sheet is being used
        for n, fuel in enumerate(fuels): #iterate through all fuels found
            fval={} #dictionary for values for each fuel
            metrics = [] #list of variable names that are calcualted
            identifier = '_' + str(n+1) #identifier is the fuel number

            for phase in phases:
                for name in fuelvals: #for each of the fuel variables
                    if 'initial' in name or 'final' in name:
                        name = name + identifier + '_' + phase
                        fval[name] = uval[name]
                    else:
                        name = name + identifier #add the fuel number
                        fval[name] = uval[name] #find enetered value and add to dictionary

            for phase in phases:
                name = 'fuel_mass_' + phase
                units[name] = 'kg'
                metrics.append(name)
                try:
                    fval[name] = fval['initial_fuel_mass' + identifier + '_' + phase] - fval['final_fuel_mass' + identifier + '_' + phase]
                except:
                    fval[name] = ''

            for phase in phases:
                name = 'fuel_dry_mass_' + phase #dry fuel mass
                units[name] = 'kg'
                metrics.append(name)
                try: #fuel dry mass is the fuel mass with moisture content removed
                    fval[name] = fval['fuel_mass_' + phase] * (1 - fval['fuel_mc' + identifier] / 100)
                except:
                    try:
                        fval['fuel_mass_' + phase] #test if fuel mass exists if function doesn't work
                        line = 'undefined variable: fuel_mass. Check initial and final fuel weight inputs'
                        print(line)
                        logs.append(line)
                        fval[name] = ''
                    except:
                        fval[name] = ''

            name = 'fuel_Cfrac' #carbon fraction
            units[name] = 'g/g'
            metrics.append(name)
            try:
                fval[name] = fval['fuel_Cfrac_db' + identifier] * (1-fval['fuel_mc' + identifier]/100)
            except:
                try:
                    fval['fuel_Cfrac_db' + identifier]
                    line = 'undefined variable: fuel_Cfrac_db'
                    print(line)
                    logs.append(line)
                    fval[name] = ''
                except:
                    fval[name] = ''

            for phase in phases:
                name = 'energy_consumed_' + phase #energy consumed from fuel during the test
                units[name] = 'kJ'
                metrics.append(name)
                try:
                    fval[name] = fval['fuel_mass_' + phase] * fval['fuel_higher_heating_value' + identifier]
                except:
                    try:
                        fval['fuel_mass_' + phase]
                        line = 'undefined variable: fuel_mass'
                        print(line)
                        logs.append(line)
                        fval[name] = ''
                    except:
                        fval[name] = ''

            cvwood = 1320 #kJ/kg
            cvchar = 1200 #kJ/kg

            name = 'fuel_net_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            if fval['fuel_Cfrac_db' + identifier] == 0.5: #if entered carbon fraction indicates wood use wood correction value
                fval[name] = fval['fuel_higher_heating_value' + identifier] - cvwood
            elif fval['fuel_Cfrac_db' + identifier] == 0.9: #if entered carbon fraction indicates charcoal use charcoal correction value
                fval[name] = fval['fuel_higher_heating_value' + identifier] - cvchar
            elif fval['fuel_Cfrac_db' + identifier] == '': #if entered value is blank, pass through
                pass
            else: #if entered value isn't standard, contact ARC to figure out specifal fuel correction value
                print('Please contact ARC for updated fuel data before continuing')
                quit()

            name = 'fuel_effective_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            try:
                fval[name] = fval['fuel_net_calorific_value'] * (1 - (fval['fuel_mc' + identifier]) / 100) - 2443 * (fval['fuel_mc' + identifier] / 100)
            except:
                try:
                    fval['fuel_mc' + identifier]  # check if fuel mass exists if equation doesn't work
                    line = 'undefined variable: fuel_mc'
                    print(line)
                    logs.append(line)
                    fval[name] = ''
                except:
                    fval[name] = ''

            for met in metrics:
                name = met + identifier  # add the fuel identifier to the variable name
                uval[name] = fval[met]  # add the value to the dictionary
                units[name] = units[met]
                names.append(name)  # add the new full variable name to the list of variables that will be output

    ###Start energy calcs 
    
    #latent heat of water vaporization at local boiling point (interpolate lookup table)
    name='Hvap'
    names.append(name)
    units[name]='kJ/kg' 
    if uval['boil_temp'] > 96:  
         uval[name]=hvap_kg[96]+(uval['boil_temp']-96)*(hvap_kg[100]-hvap_kg[96])/(100-96)
    else:
         uval[name]=hvap_kg[90]+(uval['boil_temp']-90)*(hvap_kg[96]-hvap_kg[90])/(96-90)

    name = 'char_lower_heating_value'
    names.append(name)
    units[name] = 'kJ/kg'
    if 'char_higher_heating_value' in names and uval['char_higher_heating_value'] != '':  # older data sheet takes LHV
        uval[name] = uval['char_higher_heating_value'] - CV['char']
    else:
        try: #for older data sheet
            uval[name] = uval['char_heating_value']
        except: #new data sheet with char as a multi fuel
            uval[name] = ''
    ###Energy calcs for each phase
    for phase in phases:
        pval={}                                                         #initialize dictionary of phase-specific metrics
        metrics = []                                                   #initialize list of phase-specific metrics (that will get renamed with phase identifier and put in 'names')
        phase_identifier='_'+phase
        for fullname in names:                              #go through the list of input variables
            if fullname[-3:] == phase_identifier:     # if the variable name has the phase identifier
                name = fullname[:-3]                           #strip off the phase identifier
                pval[name] = uval[fullname]                   #before passing the variable to the calculations


        trial[phase]={}

        if len(fuels) == 0:
            name = 'fuel_mass'  # mass of fuel fed
            units[name] = 'kg'
            metrics.append(name)
            try:
                pval[name] = pval['initial_fuel_mass'] - pval['final_fuel_mass']
            except:
                pval[name] = ''

            name = 'fuel_dry_mass'  # dry fuel mass
            units[name] = 'kg'
            metrics.append(name)
            try:
                pval[name] = pval['fuel_mass'] * (1 - uval['fuel_mc'] / 100)  # fuel_mc is phase independent
            except:
                try:
                    pval['fuel_mass']
                    line = 'undefined variable: fuel_mc'
                    print(line)
                    logs.append(line)
                    pval[name] = ''
                except:
                    pval[name] = ''

        name='phase_time' #total time of test phase
        units[name]='min'
        metrics.append(name)
        var1='start_time'
        var2='end_time'
        try:
            pval[name]=timeperiod(pval[var1],pval[var2])
        except:
            pval[name]=''
    
        name='time_to_boil'   
        units[name]='min'
        metrics.append(name)
        var1='start_time'
        var2='boil_time'
        try:
            pval[name]=timeperiod(pval[var1],pval[var2])
        except:
            pval[name]=''

        if len(fuels) != 0: #if multi fuels exist
            name = 'fuel_mass'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0) #start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels): #iterate through fuels
                    print(str(n+1))
                    pval[name] =pval[name] + uval['fuel_mass_' + phase + '_' + str(n+1)] #add fuel mass of each fuel
            except:
                pval[name] = ''

            name = 'fuel_mass_wo_char'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0)  # start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels):  # iterate through fuels
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n < 0.75:  # exclude fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_mass_' + phase + '_' + str(n + 1)]  # add fuel mass of each fuel
            except:
                pval[name] = ''

            name = 'fuel_dry_mass'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0) #start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels): #iterate through fuels
                    pval[name] = pval[name] + uval['fuel_dry_mass_' + phase + '_' + str(n + 1)] #add fuel mass of each to get summ
            except:
                pval[name] = ''

        name='char_mass'
        units[name]='kg'
        metrics.append(name)
        try:
            pval[name]= pval['final_char_mass'] - pval['initial_char_mass']
        except:
            pval[name]=''

        if len(fuels) != 0: #if multi fuels
            name = 'energy_consumed'
            units[name] = 'kJ'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval[name + '_' + phase + '_' + str(n+1)] #sum from all fuels used
            except:
                pval[name] = ''

            name = 'fuel_net_calorific_value' #weighted net heating value for all fuels
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_net_calorific_value_' + str(n+1)] * uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except:
                pval[name] = ''

            name = 'fuel_EHV' #effective heating value for all fuels
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n+1)] * uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except:
                pval[name] = ''

            name = 'fuel_EHV_wo_char' #effective heating value without carbon
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n < 0.75: #exclude fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n + 1)] * \
                                     uval['fuel_mass_' + phase + '_' + str(n + 1)] / pval['fuel_mass_wo_char']
            except:
                pval[name] = ''

            name = 'fuel_Cfrac'#effective carbon fraction for all fuels
            units[name] = 'g/g'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_Cfrac_' + str(n+1)] * uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except:
                pval[name] = ''

        for pot in pots:
            name='initial_water_mass_'+pot  #initial water mass in pot
            units[name]='kg'    
            metrics.append(name)
            initial_mass = 'initial_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                pval[name]= pval[initial_mass]-uval[empty_mass]
            except:
                pval[name]=''
            
            name='final_water_mass_'+pot    #final water mass in pot    
            units[name]='kg'    
            metrics.append(name)
            final_mass = 'final_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                pval[name]= pval[final_mass]-uval[empty_mass]
            except:
                pval[name]=''
    
            name='useful_energy_delivered_'+pot #useful energy delivered to pot
            units[name]='kJ'    
            metrics.append(name)
            #Clause 5.4.2 Formula 4: Q1=Cp*G1*(T2-T1)+(G1-G2)*gamma
            try:
                pval[name]= Cp*pval['initial_water_mass_'+pot]*(pval['max_water_temp_'+pot]-pval['initial_water_temp_'+pot])+(pval['initial_water_mass_'+pot]-pval['final_water_mass_'+pot])*uval['Hvap']    #hvap is phase independent
            except:
                pval[name]=''
 
        name='useful_energy_delivered'  #total useful energy delivered to all pots
        units[name]='kJ'    
        metrics.append(name)
        try:
            pval[name]= pval['useful_energy_delivered_pot1']
            try: 
                pval[name]=pval[name]+pval['useful_energy_delivered_pot2']
                try:
                    pval[name]=pval[name]+pval['useful_energy_delivered_pot3']
                    try:
                        pval[name]=pval[name]+pval['useful_energy_delivered_pot4']
                    except:
                        pass
                except:
                    pass
            except:
                pass
        except:
            pval[name]=''
            
        name='cooking_power'
        units[name]='kW'
        metrics.append(name)
        #Clause 5.4.3 Formula 5: Pc=Q1/(t3-t1)
        try:
            pval[name]= pval['useful_energy_delivered']/pval['phase_time']/60    
        except:
            pval[name]=''

        name='eff_wo_char'          #thermal efficiency with no energy credit for remaining char
        units[name]='%'
        metrics.append(name)
        #Clause 5.4.4 Formula 6: eff=Q1/B/Qnet,af*100
        try: #Current multi fuel sheet - use EHV without charcoal production factored in
            pval[name]= pval['useful_energy_delivered']/(pval['fuel_mass_wo_char']*pval['fuel_EHV_wo_char']) *100
            line = 'TE without char equation: useful energy delivered / (fuel mass * fuel effective heating value without char) * 100'
            print(line)
            logs.append(line)
        except: #if the values above do not exist
            try: #older spreadsheet where effective heating value is entered in spreadsheet
                pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] * uval['fuel_heating_value']) * 100 #old data sheet, uses effective heating value which is calculated in spreadsheet
                line = 'TE without char equation: useful energy delivered / (fuel mass * effective heating value * 100)'
                print(line)
                logs.append(line)
            except:
                pval[name]=''
            
        name='eff_w_char'           #thermal efficiency with energy credit for remaining char
        units[name]='%'
        metrics.append(name)
        #Clause 5.4.5 Formula 7: eff=Q1/(B*Qnet,af-C*Qnet,char)*100  
        try: #Typical equation. Current spreadsheet if charcoal is entered in char space and not as a multi fuel
            pval[name]= pval['useful_energy_delivered']/(pval['fuel_mass']*pval['fuel_EHV']-pval['char_mass']*uval['char_lower_heating_value'])*100
            line = 'TE with char equation: useful energy delivered / (fuel mass * fuel effective heating value - char mass * char lower heating value) * 100'
            print(line)
            logs.append(line)
        except: #if the values above do not exist
            try: #try multi fuel calculations where EHV includes char production
                pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] * pval['fuel_EHV']) * 100
                line = 'TE with char equation: useful energy delivered / (fuel mass * fuel effective heating value with char) * 100'
                print(line)
                logs.append(line)
            except: #if the values above do not exist
                try: #try the older spreadsheet where the effective heating value was entered for the fuel
                    pval[name]= pval['useful_energy_delivered']/(pval['fuel_mass']*uval['fuel_heating_value']-pval['char_mass']*uval['char_lower_heating_value'])*100    #old datasheet
                    line = 'TE with char equation: useful energy delivered / (fuel mass * fuel heating value (from entry sheet) - char mass * char lower heating value) *100'
                    print(line)
                    logs.append(line)
                except: #if the values above do not exist
                    try: #try calculating without the char values (they may not be entered or may be 0)
                        pval[name]= pval['useful_energy_delivered']/(pval['fuel_mass']*uval['fuel_heating_value'])*100 #old datasheet when no value for char
                        line = 'TE with char equation: useful energy delivered / fuel mass * fuel heating value (from entry sheet) * 100'
                        print(line)
                        logs.append(line)
                    except:
                        pval[name]=''

        if len(fuels) != 0: #if multi fuels
            name = 'char_mass'
            if pval[name] == '':
                pval[name] = ufloat(0, 0)
                try:
                    for n, fuel in enumerate(fuels):
                        if uval['fuel_Cfrac_db_' + str(n + 1)].n > 0.75:  # only include fuels where the cfrac indicates charcoal
                            pval[name] = pval[name] + abs(uval['fuel_mass_' + phase + '_' + str(n+1)].n)
                except:
                    pval[name] = ''

            name = 'EHV_char'
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n > 0.75:  # include fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n + 1)] * \
                                     uval['fuel_mass_' + phase + '_' + str(n + 1)] / pval['char_mass']
            except:
                pval[name] = ''

        name='char_energy_productivity'
        units[name]='%'
        metrics.append(name)
        # Clause 5.4.6 Formula 8: Echar=C*Qnet,char/B/Qnet,af*100
        try:
            pval[name] = pval['char_mass'] * uval['char_lower_heating_value'] / pval['fuel_mass'] / pval[
                'fuel_EHV'] * 100
        except:
            try:
                pval[name]= pval['char_mass']*uval['char_heating_value']/pval['fuel_mass']/uval['fuel_heating_value']*100
            except:
                try:
                    pval[name] = pval['char_mass'] * pval['EHV_char']/ pval['fuel_mass'] / pval['fuel_EHV'] * 100
                except:
                    pval[name]=''
    
        name='char_mass_productivity'
        units[name]='%'
        metrics.append(name)
        # Clause 5.4.7 Formula 9: mchar=C/B*100
        try:
            pval[name]= pval['char_mass']/pval['fuel_mass']*100
        except:
            pval[name]=''

        name='burn_rate' #fuel-burning rate, wet basis
        units[name]='g/min'
        metrics.append(name)
        try:
            pval[name]= pval['fuel_mass']/pval['phase_time']*1000
        except:
            pval[name]=''

        name='burn_rate_dry' #fuel-burning rate, dry basis
        units[name]='g/min'
        metrics.append(name)
        try:
            pval[name]= pval['fuel_dry_mass']/pval['phase_time']*1000
        except:
            pval[name]=''

        name = 'firepower_w_char'
        units[name] = 'kW'
        metrics.append(name)
        try:
            pval[name] = (pval['fuel_mass'] * pval['fuel_EHV'] - pval['char_mass'] * uval[
                'char_lower_heating_value']) / (pval['phase_time'] * 60)
        except:
            try:
                pval[name] = (pval['fuel_mass'] * pval['fuel_EHV']) / (pval['phase_time'] * 60)
            except:
                try:
                    pval[name] = pval['cooking_power'] / pval['eff_w_char'] * 100
                except:
                    pval[name] = ''

        for metric in metrics:                          #for each metric calculated for the phase
            name=metric+phase_identifier        #add the phase identifier to the variable name
            uval[name] = pval[metric]
            units[name]=units[metric]
            names.append(name)              #add the new full variable name to the list of variables that will be output

        trial[phase] = pval
        
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
    
    #CHANGES MADE AFTER THIS POINT 
    return trial, units, uval
    #CHANGES STOP HERE
    
def timeperiod(StartTime,EndTime):             
    #function calculates time difference in minutes
    #Inputs start and end times as strings and converts to time objects
    try:
        start_object=dt.strptime(StartTime, '%Y%m%d %H:%M:%S')       #convert the start time string to date object
        end_object=dt.strptime(EndTime, '%Y%m%d %H:%M:%S')          #convert the end time string to date object
    except:
        start_object=dt.strptime(StartTime, '%H:%M:%S')
        end_object=dt.strptime(EndTime, '%H:%M:%S')
    delta_object=end_object-start_object                           #time difference as date object
    Time=delta_object.total_seconds()/60                         #time difference as minutes
    return Time
    
#####################################################################
#the following two lines allow the main function to be run as an executable
if __name__ == "__main__":
    LEMS_EnergyCalcs(inputpath,outputpath,logpath)