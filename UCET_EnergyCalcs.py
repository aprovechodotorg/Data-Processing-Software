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
    CV['Char'] =1200



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
        const[name] = data[name]
    #############CHANGE END

    ###Start fuel calcs

    name = 'net_calorific_value'
    names.append(name)
    units[name] = 'kJ/kg'

    if data['fuel_type'] == 'Wood':
        data[name] = float(data['gross_calorific_value']) - CV['Wood']
        metric[name] = data[name]
    elif data['fuel_type'] == 'Char':
        data[name] = float(data['gross_calorific_value']) - CV['Char']
        metric[name] = data[name]
    else:
        print('Please contact ARC for updated fuel data before continuing')
        quit()

    name = 'effective_calorific_value'
    names.append(name)
    units[name] = 'kJ/kg'
    data[name] = float(data['net_calorific_value']) * (1 - (float(data['fuel_mc'])) / 100) - 2443 * (float(data['fuel_mc']) / 100)
    metric[name] = data[name]

    name = 'LHV_char'
    names.append(name)
    units[name] = 'kJ/kg'
    if data['fuel_type'] == 'Wood' or data['fuel_type'] == 'Char':
        data[name] = float(data['HHV_char']) - CV['Char']
        metric[name] = data[name]

    #######################################
    #Start environmental calcs

    name = 'p_ambient'
    names.append(name)
    units[name] = 'Pa'
    data[name] = float(data['pressure']) * 3386 #conversion
    metric[name] = data[name]

    name = 'local_boil_temp'
    names.append(name)
    units[name] = 'C'
    data[name] = 1 / (1 / 373.14 - 8.14 * math.log(data['p_ambient']/101325) / 40650) - 273.15
    metric[name] = data[name]

    #latent heat of water vaporization at local boiling point (interpolate lookup table)
    name='Hvap'
    names.append(name)
    units[name]='kJ/kg'
    if data['local_boil_temp'] > 96:
        data[name]=hvap_kg[96]+(data['local_boil_temp']-96)*(hvap_kg[100]-hvap_kg[96])/(100-96)
        metric[name] = data[name]
    else:
        data[name]=hvap_kg[90]+(data['local_boil_temp']-90)*(hvap_kg[96]-hvap_kg[90])/(96-90)
        metric[name] = data[name]

    #############################################
    #test calcs
    name = 'test_time'
    names.append(name)
    units[name] = 'min'
    try:
        data[name] = timeperiod(data['start_time'], data['end_time'])
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'time_to_boil'
    names.append(name)
    units[name] = 'min'
    try:
        data[name] = timeperiod(data['start_time'], data['boil_time'])
        metric[name] = data[name]
    except:
        data[name] = 'no boil'
        metric[name] = data[name]

    name = 'fuel_mass'
    names.append(name)
    units[name] = 'kg'
    try:
        initial = float(data['initial_fuel_mass']) + float(data['kindle_mass'])
    except:
        initial = float(data['initial_fuel_mass'])
    data[name] = initial - float(data['final_fuel_mass'])
    metric[name] = data[name]

    name = 'fuel_dry_mass'  # dry fuel mass
    units[name] = 'kg'
    names.append(name)
    try:
        data[name] = data['fuel_mass'] * (1 - float(data['fuel_mc']) / 100)
        metric[name] = data[name]
    except:
        try:
            data['fuel_mass']
            line = 'undefined variable: fuel_mc'
            print(line)
            logs.append(line)
            data[name] = ''
            metric[name] = data[name]
        except:
            data[name] = ''
            metric[name] = data[name]

    name = 'char_mass'
    units[name] = 'kg'
    names.append(name)
    try:
        data[name] = float(data['final_mass_char']) - float(data['initial_mass_char'])
        metric[name] = data[name]
    except:
        try:
            data[name] = float(data['final_mass_char']) - float(data['weight_tray'])
            metric[name] = data[name]
        except:
            data[name] = ''
            metric[name] = data[name]

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
        data[temp_name] = float(data[final_name]) - float(data[int_name])
        metric[temp_name] = data[temp_name]

        mass_name = 'mass_ingredient' + str(x)
        names.append(mass_name)
        units[mass_name] = 'kg'
        cont_name = 'container_ingredient' + str(x)
        ing_name = 'initial_mass_ingredient' + str(x)
        try:
            data[mass_name] = float(data[ing_name]) - float(data[cont_name])
            metric[mass_name] = data[mass_name]
        except:
            data[mass_name] = float(data[ing_name])
            metric[mass_name] = data[mass_name]
        mass.append(data[mass_name])

        name = 'sensible_energy_ingredient' + str(x)
        names.append(name)
        units[name] = 'kJ'
        SH_name = 'SH_ingredient' + str(x)
        data[name] = data[mass_name] * data[temp_name] * float(data[SH_name])
        metric[name] = data[name]
        sensible_energy.append(data[name])

        x += 1

    name = 'total_sensible_energy'
    names.append(name)
    units[name] = 'kj'
    data[name] = sum(sensible_energy)
    metric[name] = data[name]

    name = 'initial_content_mass'
    names.append(name)
    units[name] = 'kg'
    data[name] = sum(mass)
    metric[name] = data[name]

    name = 'final_content_mass'
    names.append(name)
    units[name] = 'kg'
    x = 1
    final_mass = []
    pot_mass = []
    while x <= number_dishes:
        mass_name = 'final_food_mass' + str(1)
        final_mass.append(float(data[mass_name]))
        pot_name = 'weight_pot' + str(x)
        pot_mass.append(float(data[pot_name]))
        x += 1
    try:
        data[name] = sum(final_mass) + float(data['add_mass_loss']) - sum(pot_mass)
        metric[name] = data[name]
    except:
        data[name] = sum(final_mass) - sum(pot_mass)
        metric[name] = data[name]

    name = 'water_loss'
    names.append(name)
    units[name] = 'kg'
    data[name] = data['initial_content_mass'] - data['final_content_mass']
    metric[name] = data[name]

    name = 'latent_energy'
    names.append(name)
    units[name] = 'kJ'
    data[name] = data['water_loss'] * data['Hvap']
    metric[name] = data[name]

    name = 'useful_energy'
    names.append(name)
    units[name] = 'kJ'
    data[name] = data['total_sensible_energy'] + data['latent_energy']
    metric[name] = data[name]

    name = 'cooking_power'
    units[name] = 'kW'
    names.append(name)
    # Clause 5.4.3 Formula 5: Pc=Q1/(t3-t1)
    try:
        data[name] = data['useful_energy'] / data['test_time'] / 60
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'eff_w_char'  # thermal efficiency with energy credit for remaining char
    units[name] = '%'
    names.append(name)
    # Clause 5.4.5 Formula 7: eff=Q1/(B*Qnet,af-C*Qnet,char)*100
    try:
        data[name] = data['useful_energy'] / (
                    data['fuel_mass'] * data['effective_calorific_value'] - data['char_mass'] * data[
                'LHV_char']) * 100
        metric[name] = data[name]
    except:
        try:
            data[name] = data['useful_energy'] / (
                    data['fuel_mass'] * data['effective_calorific_value']) * 100 # try without char in case char has blank entry
            metric[name] = data[name]
        except:
            data[name] = ''
            metric[name] = data[name]

    name = 'eff_wo_char'
    names.append(name)
    units[name] = '%'
    try:
        data[name] = data['useful_energy'] / (data['fuel_mass'] * data[
            'effective_calorific_value']) * 100  # try without char in case char has blank entry
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'char_energy_productivity'
    units[name] = '%'
    names.append(name)
    # Clause 5.4.6 Formula 8: Echar=C*Qnet,char/B/Qnet,af*100
    try:
        data[name] = data['char_mass'] * data['LHV_char'] / data['fuel_mass'] / data[
            'effective_calorific_value'] * 100
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'char_mass_productivity'
    units[name] = '%'
    names.append(name)
    # Clause 5.4.7 Formula 9: mchar=C/B*100
    try:
        data[name] = data['char_mass'] / data['fuel_mass'] * 100
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'burn_rate'  # fuel-burning rate
    units[name] = 'g/min'
    names.append(name)
    try:
        data[name] = data['fuel_mass'] / data['test_time'] * 1000
        metric[name] = data[name]
    except:
        data[name] = ''
        metric[name] = data[name]

    name = 'firepower'
    units[name] = 'kW'
    names.append(name)
    try:
        data[name] = (data['fuel_mass'] * uval['effective_calorific_value'] - data['char_mass'] * data['LHV_char']) /\
                     data['test_time'] / 60
        metric[name] = data[name]
    except:
        try:
            data[name] = (data['fuel_mass'] * data['effective_calorific_value']) / data[
                'test_time'] / 60  # try without char in case char is blank
            metric[name] = data[name]
        except:
            data[name] = ''
            metric[name] = data[name]

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