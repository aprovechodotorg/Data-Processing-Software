# v0 Python3
# Master program to calculate stove test energy metrics following ISO 19867

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
import math
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io


def UCET_EnergyCalcs(inputpath,outputpath,logpath):
    ver = '0.4'

    #Create holders for values
    logs = []
    names=[]            #list of variable names
    outputnames=[]  #list of variable names for the output file
    units={}                #dictionary of units, keys are variable names
    data={}                 #dictionary of nominal values, keys are variable names
    unc={}                  #dictionary of uncertainty values, keys are variable names
    uval={}                   #dictionary of values as ufloat pairs, keys are variable names

    #CHANGE START HERE
    const={}
    metric={}
    #CHANGE END HERE

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
    CV['Wood'] = 1320 #kJ/kg
    CV['Char'] = 1200



    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'UCET_EnergyCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs.append(line)

    ###############################################
    #load input file and store values in dictionaries
    [names,units,data,unc,uval] = io.load_constant_inputs(inputpath)
    line = 'loaded: '+inputpath
    print(line)
    logs.append(line)
    #######################################################

    ########CHANGE HERE
    for name in names:
        const[name] = uval[name]
    #############CHANGE END

    ###Start fuel calcs
    fuels = [] #blank list to track for multi fuels
    fuelvals = ['initial_fuel_mass', #list of fuel variables
                'final_fuel_mass',
                'fuel_species',
                'fuel_source',
                'gross_calorific_value',
                'fuel_mc',
                'fuel_type']

    for name in names:  # go through and check fuel types and if there's entered values
        if 'gross_calorific_value_' in name: #Fuel_species_ only shows up in multi fuel version of data sheet
            if data[name] != '':
                fuels.append(name)

    if len(fuels) != 0: #if multifuel data sheet is being used
        for n, fuel in enumerate(fuels): #iterate through all fuels found
            fval={} #dictionary for values for each fuel
            metrics = [] #list of variable names that are calculated
            identifier = '_' + str(n + 1) #identifier is the fuel number

            for name in fuelvals: #for each of the fuel variables
                name = name + identifier #add the fuel number
                fval[name] = uval[name] #find the entered value and add to dictionary

            name = 'fuel_mass'
            units[name] = 'kg'
            metrics.append(name)
            try: #fuel mass is the inital mass - the final mass
                fval[name] = fval['initial_fuel_mass' + identifier] - fval['final_fuel_mass' + identifier]
            except:
                fval[name] = ''

            name = 'fuel_dry_mass'  # dry fuel mass
            units[name] = 'kg'
            metrics.append(name)
            try: #fuel dry mass is the fuel mass with moisture content removed
                fval[name] = fval['fuel_mass'] * (1 - fval['fuel_mc' + identifier] / 100)
            except:
                try:
                    fval['fuel_mass'] #test is fuel mass exists if function doesn't work
                    line = 'undefined variable: fuel_mass'
                    print(line)
                    logs.append(line)
                    fval[name] = ''
                except:
                    fval[name] = ''

            # name = 'fuel_Cfrac'
            # units[name] = 'g/g'
            # metrics.append(name)
            # try:
            # fval[name] = fval['fuel_Cfrac_db'] * (1 - fval['fuel_mc'] / 100)
            # except:
            # try:
            # fval['fuel_Cfrac_db']
            # line = 'undefined variable: fuel_Cfrac_db'
            # print(line)
            # logs.append(line)
            # fval[name] = ''
            # except:
            # fval[name] = ''

            name = 'fuel_energy'  # fuel energy
            units[name] = 'MJ'
            metrics.append(name)
            try: #energy from fuel is mass of fuel consumed by the HHV of the fuel species
                fval[name] = fval['fuel_mass'] * fval['gross_calorific_value' + identifier]
            except:
                try:
                    fval['fuel_mass'] #check if fuel mass exists if equation doesn't work
                    line = 'undefined variable: fuel_mass'
                    print(line)
                    logs.append(line)
                    fval[name] = ''
                except:
                    fval[name] = ''

            name = 'net_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            if fval['fuel_type' + identifier] == 'Wood':
                fval[name] = fval['gross_calorific_value' + identifier] - CV['Wood']
            elif fval['fuel_type' + identifier] == 'Char':
                fval[name] = fval['gross_calorific_value' + identifier] - CV['Char']
            elif fval['fuel_type' + identifier] == '':
                fval[name] = ''
            else:
                print('Please contact ARC for updated fuel data before continuing')
                quit()

            name = 'effective_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            try:
                fval[name] = fval['net_calorific_value'] * (1 - (fval['fuel_mc' + identifier]) / 100) - 2443 * (fval['fuel_mc' + identifier] / 100)
            except:
                try:
                    fval['fuel_mc' + identifier]  # check if fuel mass exists if equation doesn't work
                    line = 'undefined variable: fuel_mc'
                    print(line)
                    logs.append(line)
                    fval[name] = ''
                except:
                    fval[name] = ''

            for met in metrics:  # for each metric calculated for the fuel type
                name = met + identifier  # add the fuel identifier to the variable name
                uval[name] = fval[met] #add the value to the dictionary
                units[name] = units[met]
                names.append(name)  # add the new full variable name to the list of variables that will be output

    else: #if multi fuels don't exist
        name = 'net_calorific_value'
        names.append(name)
        units[name] = 'kJ/kg'

        #print(data['fuel_type'])

        if data['fuel_type'] == 'Wood':
            uval[name] = uval['gross_calorific_value'] - CV['Wood']
            metric[name] = uval[name]
        elif data['fuel_type'] == 'Char':
            uval[name] = uval['gross_calorific_value'] - CV['Char']
            metric[name] = uval[name]
        else:
            print('Please contact ARC for updated fuel data before continuing')
            quit()

        name = 'effective_calorific_value'
        names.append(name)
        units[name] = 'kJ/kg'
        uval[name] = uval['net_calorific_value'] * (1 - (uval['fuel_mc']) / 100) - 2443 * (uval['fuel_mc'] / 100)
        metric[name] = uval[name]

    name = 'LHV_char'
    names.append(name)
    units[name] = 'kJ/kg'
    #if data['fuel_type'] == 'Wood' or data['fuel_type'] == 'Char':
    uval[name] = uval['HHV_char'] - CV['Char']
    metric[name] = uval[name]

    #######################################
    #Start environmental calcs

    name = 'p_ambient'
    names.append(name)
    units[name] = 'Pa'
    uval[name] = uval['pressure'] * 3386 #conversion
    metric[name] = uval[name]

    name = 'local_boil_temp'
    names.append(name)
    units[name] = 'C'
    try:
        amb = uval['p_ambient'].n
        X = math.log(amb/101325)
        uval[name] = 1 / (1 / 373.14 - 8.14 * X / 40650) - 273.15
    except:
        uval[name] = 100 #If missing environmental sesnors, use default local boiling point
    metric[name] = uval[name]

    #latent heat of water vaporization at local boiling point (interpolate lookup table)
    name='Hvap'
    names.append(name)
    units[name]='kJ/kg'
    if uval['local_boil_temp'] > 96:
        uval[name]=hvap_kg[96]+(uval['local_boil_temp']-96)*(hvap_kg[100]-hvap_kg[96])/(100-96)
        metric[name] = uval[name]
    else:
        uval[name]=hvap_kg[90]+(uval['local_boil_temp']-90)*(hvap_kg[96]-hvap_kg[90])/(96-90)
        metric[name] = uval[name]

    #############################################
    #test calcs
    name = 'test_time'
    names.append(name)
    units[name] = 'min'
    try:
        uval[name] = timeperiod(data['start_time'], data['end_time'])
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'time_to_boil'
    names.append(name)
    units[name] = 'min'
    try:
        uval[name] = timeperiod(uval['start_time'], uval['boil_time'])
        metric[name] = uval[name]
    except:
        data[name] = 'no boil'
        metric[name] = data[name]


    name = 'fuel_mass'
    names.append(name)
    units[name] = 'kg'
    if len(fuels) != 0:  # if multi fuels exist
        uval[name] = ufloat(0, 0) #values starts at 0 and is added to to sum fuel mass of all fuels
        try:
            for n, fuel in enumerate(fuels): #itreate through fuels list
                uval[name] = uval[name] + uval['fuel_mass_' + str(n + 1)] #add fuel mass of each fuel to sum
        except:
            uval[name] = ''
    else: #if no multi fuel
        try:
            initial = uval['initial_fuel_mass'] + uval['kindle_mass']
        except:
            initial = uval['initial_fuel_mass']
        uval[name] = initial - uval['final_fuel_mass']
        metric[name] = uval[name]

    name = 'fuel_dry_mass'  # dry fuel mass
    units[name] = 'kg'
    names.append(name)
    if len(fuels) != 0: #if multi fuels exist
        uval[name] = ufloat(0, 0) #values starts at 0 and is added to to sum fuel mass of all fuels
        try:
            for n, fuel in enumerate(fuels):
                uval[name] = uval[name] + uval['fuel_dry_mass_' + str(n + 1)] #add fuel mass of each fuel to sum
        except:
            uval[name] = ''
    else: #if no multi fuels
        try:
            uval[name] = uval['fuel_mass'] * (1 - uval['fuel_mc'] / 100)
            metric[name] = uval[name]
        except:
            try:
                uval['fuel_mass']
                line = 'undefined variable: fuel_mc'
                print(line)
                logs.append(line)
                uval[name] = ''
                metric[name] = uval[name]
            except:
                uval[name] = ''
                metric[name] = uval[name]

    name = 'char_mass'
    units[name] = 'kg'
    names.append(name)
    try:
        uval[name] = uval['final_mass_char'] - uval['initial_mass_char']
        metric[name] = uval[name]
    except:
        try:
            uval[name] = uval['final_mass_char'] - uval['weight_tray']
            metric[name] = uval[name]
        except:
            uval[name] = ''
            metric[name] = uval[name]

    if len(fuels)!= 0: #if multi fuels being used
        name = 'effective_calorific_value'
        units[name] = 'kJ/kg'
        names.append(name)
        uval[name] = ufloat(0, 0)
        try:
            for n, fuel in enumerate(fuels): #fuel is the sum of each fuel HHV by each fuel mass over fuel mass sum
                uval[name] = uval[name] + uval['effective_calorific_value_' + str(n +1)] * uval['fuel_mass_' + str(n +1)] / uval['fuel_mass']
        except:
            uval[name] = ''

    name = 'energy_consumed'
    units[name] = 'kJ'
    names.append(name)
    try: #energy consumed is the HV of all fuel by the mass of all fuel burned
        uval[name] = uval['effective_calorific_value'] * uval['fuel_mass']
    except:
        uval[name] = ''

#######################################################
    #Ingredient calcs
    number_ingredients = 0
    number_dishes = 0

    check = 20 #check through 20 values
    x = 1
    while x <= check:
        name = 'name_ingredient' + str(x)
        try:
            if data[name] == '':
                pass
            else:
                number_ingredients += 1
        except:
            pass
        name = 'final_food_mass' + str(x)
        try:
            if data[name] == '':
                pass
            else:
                number_dishes += 1
        except:
            pass
        x += 1

    x = 1
    sensible_energy = [] #list of sensible energy
    mass = [] #list of masses

    while x <= number_ingredients: #loop through ingredient list
        temp_name = 'temp_change_' + str(x)
        names.append(temp_name)
        units[temp_name] = 'C'
        int_name = 'initial_temp_ingredient' + str(x)
        final_name = 'final_temp_ingredient' + str(x)
        uval[temp_name] = uval[final_name] - uval[int_name]
        metric[temp_name] = uval[temp_name]

        mass_name = 'mass_ingredient' + str(x)
        names.append(mass_name)
        units[mass_name] = 'kg'
        cont_name = 'container_ingredient' + str(x)
        ing_name = 'initial_mass_ingredient' + str(x)
        try:
            uval[mass_name] = uval[ing_name] - uval[cont_name]
            metric[mass_name] = uval[mass_name]
        except:
            uval[mass_name] = uval[ing_name]
            metric[mass_name] = uval[mass_name]
        mass.append(uval[mass_name])

        name = 'sensible_energy_ingredient' + str(x)
        names.append(name)
        units[name] = 'kJ'
        SH_name = 'SH_ingredient' + str(x)
        uval[name] = uval[mass_name] * uval[temp_name] * uval[SH_name]
        metric[name] = uval[name]
        sensible_energy.append(uval[name])

        x += 1

    name = 'total_sensible_energy'
    names.append(name)
    units[name] = 'kJ'
    uval[name] = sum(sensible_energy)
    metric[name] = uval[name]

    name = 'initial_content_mass'
    names.append(name)
    units[name] = 'kg'
    uval[name] = sum(mass)
    metric[name] = uval[name]

    name = 'final_content_mass'
    names.append(name)
    units[name] = 'kg'
    x = 1
    final_mass = []
    pot_mass = []
    while x <= number_dishes:
        mass_name = 'final_food_mass' + str(x)
        final_mass.append(uval[mass_name])
        pot_name = 'weight_pot' + str(x)
        pot_mass.append(uval[pot_name])
        x += 1
    try:
        uval[name] = sum(final_mass) + uval['add_mass_loss'] - sum(pot_mass)
        metric[name] = uval[name]
    except:
        uval[name] = sum(final_mass) - sum(pot_mass)
        metric[name] = uval[name]

    name = 'water_loss'
    names.append(name)
    units[name] = 'kg'
    uval[name] = uval['initial_content_mass'] - uval['final_content_mass']
    metric[name] = uval[name]

    name = 'latent_energy'
    names.append(name)
    units[name] = 'kJ'
    uval[name] = uval['water_loss'] * uval['Hvap']
    metric[name] = uval[name]

    name = 'useful_energy'
    names.append(name)
    units[name] = 'kJ'
    uval[name] = uval['total_sensible_energy'] + uval['latent_energy']
    metric[name] = uval[name]

    name = 'cooking_power'
    units[name] = 'kW'
    names.append(name)
    # Clause 5.4.3 Formula 5: Pc=Q1/(t3-t1)
    try:
        uval[name] = uval['useful_energy'] / uval['test_time'] / 60
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'eff_w_char'  # thermal efficiency with energy credit for remaining char
    units[name] = '%'
    names.append(name)
    # Clause 5.4.5 Formula 7: eff=Q1/(B*Qnet,af-C*Qnet,char)*100
    try:
        uval[name] = uval['useful_energy'] / (
                    uval['fuel_mass'] * uval['effective_calorific_value'] - uval['char_mass'] * uval[
                'LHV_char']) * 100
        metric[name] = uval[name]
    except:
        try:
            uval[name] = uval['useful_energy'] / (
                    uval['fuel_mass'] * uval['effective_calorific_value']) * 100 # try without char in case char has blank entry
            metric[name] = uval[name]
        except:
            uval[name] = ''
            metric[name] = uval[name]

    name = 'eff_wo_char'
    names.append(name)
    units[name] = '%'
    try:
        uval[name] = uval['useful_energy'] / (uval['fuel_mass'] * uval[
            'effective_calorific_value']) * 100  # try without char in case char has blank entry
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'char_energy_productivity'
    units[name] = '%'
    names.append(name)
    # Clause 5.4.6 Formula 8: Echar=C*Qnet,char/B/Qnet,af*100
    try:
        uval[name] = uval['char_mass'] * uval['LHV_char'] / uval['fuel_mass'] / uval[
            'effective_calorific_value'] * 100
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'char_mass_productivity'
    units[name] = '%'
    names.append(name)
    # Clause 5.4.7 Formula 9: mchar=C/B*100
    try:
        uval[name] = uval['char_mass'] / uval['fuel_mass'] * 100
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'burn_rate'  # fuel-burning rate
    units[name] = 'g/min'
    names.append(name)
    try:
        uval[name] = uval['fuel_mass'] / uval['test_time'] * 1000
        metric[name] = uval[name]
    except:
        uval[name] = ''
        metric[name] = uval[name]

    name = 'firepower'
    units[name] = 'kW'
    names.append(name)
    try:
        uval[name] = (uval['fuel_mass'] * uval['effective_calorific_value'] - uval['char_mass'] * uval['LHV_char']) /\
                     uval['test_time'] / 60
        metric[name] = uval[name]
    except:
        try:
            uval[name] = (uval['fuel_mass'] * uval['effective_calorific_value']) / uval[
                'test_time'] / 60  # try without char in case char is blank
            metric[name] = uval[name]
        except:
            uval[name] = ''
            metric[name] = uval[name]

    ######################################################
    # make output file
    io.write_constant_outputs(outputpath, names, units, data, unc, uval)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    ##############################################
    # print to log file
    io.write_logfile(logpath, logs)

    # CHANGES MADE AFTER THIS POINT
    return const, units, metric
    # CHANGES STOP HERE

def timeperiod(StartTime,EndTime):
    #function calculates time difference in minutes
    #Inputs start and end times as strings and converts to time objects
    start_object=dt.strptime(StartTime, '%H:%M:%S')       #convert the start time string to date object
    end_object=dt.strptime(EndTime, '%H:%M:%S')          #convert the end time string to date object
    delta_object=end_object-start_object                           #time difference as date object
    Time=delta_object.total_seconds()/60                         #time difference as minutes
    return Time