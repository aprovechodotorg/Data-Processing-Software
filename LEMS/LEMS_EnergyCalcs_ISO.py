# v0.4  Python3

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
from uncertainties import ufloat
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import math
import subprocess
import sys

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_EnergyInputs.csv'  # read
outputpath = 'foldername_EnergyOutputs.csv'  # written
logger = 'logging Python package'
###################################################################


def LEMS_EnergyCalcs(inputpath, outputpath, logger):
    # Function purpose: Using inputs from user, calculate ISO 19867-1 energy metrics
    # Inputs: Entered inputs of fuel, evironment, and test results
    # Outputs: All metrics that do not require emission data (thermal efficiency, cooking power, burn rate, etc.)
    
    phases = ['hp', 'mp', 'lp']  # list of phases
    pots = ['pot1', 'pot2', 'pot3', 'pot4']  # list of pots

    logs = []  # List of notable functions, errors, and calculations recorded for reviewing past processing of data

    Cp = 4.18  # kJ/kg/K specific heat capacity of water from Clause 5.4.2 Formula 4
    
    # latent heat of vaporization of water lookup table from
    # https://www.engineeringtoolbox.com/water-properties-d_1573.html
    hvap_kg = {90: 2282.5, 96: 2266.9, 100: 2260}  # kJ/kg

    # Calorific Values of fuels
    CV = {'wood': 1320, 'char': 1200}  # Dictionary of calorific values

    # Record start time of script
    start_time = dt.now()
    log = f"Started at: {start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    # Log script version if available
    try:
        version = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%h", "--", __file__], text=True
        ).strip()
    except subprocess.CalledProcessError:
        version = "unknown_version"

    log = f"Version: {version}"
    print(log)
    logger.info(log)
    logs.append(log)

    ###############################################
    # load input file and store values in dictionaries
    [names, units, val, unc, uval] = io.load_constant_inputs(inputpath)
    log = f'loaded: {inputpath}'
    print(log)
    logger.debug(log)
    logs.append(log)
    #######################################################

    # start fuel calcs
    fuels = []  # blank list to track for multi fuels
    fuelvals = ['initial_fuel_mass',  # list of user entered fuel variables
                'final_fuel_mass',
                'fuel_type',
                'fuel_source',
                'fuel_dimensions',
                'fuel_higher_heating_value',
                'fuel_mc',
                'fuel_Cfrac_db']

    for name in names:  # go through and check fuel types and if there's entered values
        if 'fuel_higher_heating_value_' in name:  # only shows up in multi fuel version of data entry sheet
            if val[name] != '':  # If there's an entered input for the fuel number, add it to the list of fuels
                fuels.append(name)

    if len(fuels) != 0:  # If multifuel data sheet is being used
        for n, fuel in enumerate(fuels):  # iterate through all fuels found
            fval = {}  # dictionary for values for each fuel
            metrics = []  # list of variable names that are calcualted
            identifier = '_' + str(n+1)  # identifier is the fuel number

            for phase in phases:
                for name in fuelvals:  # for each of the fuel variables
                    if 'initial' in name or 'final' in name:
                        name = name + identifier + '_' + phase
                        fval[name] = uval[name]
                    else:
                        name = name + identifier  # add the fuel number
                        fval[name] = uval[name]  # find enetered value and add to dictionary

            for phase in phases:
                name = 'fuel_mass_' + phase
                units[name] = 'kg'
                metrics.append(name)
                try:
                    fval[name] = fval['initial_fuel_mass' + identifier + '_' + phase] - \
                                 fval['final_fuel_mass' + identifier + '_' + phase]
                except (KeyError, TypeError):
                    fval[name] = ''
                    line = f'{name} left blank due to incorrect initial or final fuel mass {identifier} at ' \
                           f'phase {phase}'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

            for phase in phases:
                name = 'fuel_dry_mass_' + phase  # dry fuel mass
                units[name] = 'kg'
                metrics.append(name)
                try:  # fuel dry mass is the fuel mass with moisture content removed
                    fval[name] = fval['fuel_mass_' + phase] * (1 - fval['fuel_mc' + identifier] / 100)
                except (KeyError, TypeError):
                    log = f'Undefined variable: fuel_mass_{phase} or fuel_mc{identifier}. ' \
                          f'Check initial and final fuel weight inputs and moisture content inputs. {name} left ' \
                          f'blank. Check if entries were entered properly.'
                    print(log)
                    logger.error(log)
                    logs.append(log)
                    fval[name] = ''
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

            name = 'fuel_Cfrac'  # carbon fraction
            units[name] = 'g/g'
            metrics.append(name)
            try:
                fval[name] = fval['fuel_Cfrac_db' + identifier] * (1-fval['fuel_mc' + identifier]/100)
            except (KeyError, TypeError):
                log = f'Undefined variable: fuel_Cfrac_db{identifier} or fuel_mc{identifier}. {name} left blank' \
                      f'Check if entries were entered properly.'
                print(log)
                logger.error(log)
                logs.append(log)
                fval[name] = ''
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

            for phase in phases:
                name = 'energy_consumed_' + phase  # energy consumed from fuel during the test
                units[name] = 'kJ'
                metrics.append(name)
                try:
                    fval[name] = fval['fuel_mass_' + phase] * fval['fuel_higher_heating_value' + identifier]
                except (KeyError, TypeError):
                    log = f'Undefined variable: fuel_mass_{phase} or fuel_higher_heating_value{identifier}. {name}' \
                          f'left blank. Check inital and final fuel mass and if entries were entered properly.'
                    print(log)
                    logger.error(log)
                    logs.append(log)
                    fval[name] = ''
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

            cvwood = 1320  # kJ/kg
            cvchar = 1200  # kJ/kg

            name = 'fuel_net_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            if 0.4 < fval['fuel_Cfrac_db' + identifier] < 0.6:  # if entered carbon fraction indicates wood use wood
                # correction value
                fval[name] = fval['fuel_higher_heating_value' + identifier] - cvwood
            elif fval['fuel_Cfrac_db' + identifier] >= 0.75:  # if entered carbon fraction indicates charcoal use
                # charcoal correction value
                fval[name] = fval['fuel_higher_heating_value' + identifier] - cvchar
            elif fval['fuel_Cfrac_db' + identifier] == '':  # if entered value is blank, pass through
                pass
            else:  # if entered value isn't standard, contact ARC to figure out specifal fuel correction value
                print('Please contact ARC for updated fuel data before continuing')
                quit()

            name = 'fuel_effective_calorific_value'
            metrics.append(name)
            units[name] = 'kJ/kg'
            try:
                fval[name] = fval['fuel_net_calorific_value'] * (1 - (fval['fuel_mc' + identifier]) / 100) - 2443 * \
                             (fval['fuel_mc' + identifier] / 100)
            except (KeyError, TypeError):
                log = f'Undefined variable: fuel_mc{identifier} or fuel_higher_heating_value{identifier}. {name} left' \
                      f'blank. Check if entries were entered properly.'
                print(log)
                logger.error(log)
                logs.append(log)
                fval[name] = ''
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

            for met in metrics:
                name = met + identifier  # add the fuel identifier to the variable name
                uval[name] = fval[met]  # add the value to the dictionary
                units[name] = units[met]
                names.append(name)  # add the new full variable name to the list of variables that will be output

    ncv_names = []
    defaults = []
    for name in names:
        if 'fuel_net_calorific_value' in name:
            defaults.append(uval[name].n)
            ncv_names.append(name)
    message = f"The calculated net(lower) calorific values are as follows. Please enter a new value if needed.\n" \
              f"Net calorific values are calculated as (higher heating value - correction value).\n" \
              f"Correction values are: \n" \
              f"    * 2600 for kerosene\n" \
              f"    * 3300 for LPG\n" \
              f"    * 1200 for charcoal\n" \
              f"    * 1320 for wood"
    title = 'Check fuel inputs'
    ncv = easygui.multenterbox(message, title, ncv_names, defaults)
    for n, num in enumerate(ncv):
        try:
            ncv[n] = float(num)
        except ValueError:
            ncv[n] = num
    if ncv != defaults:
        for n, name in enumerate(ncv_names):
            uval[name] = ncv[n]

            name = f'fuel_effective_calorific_value_{n + 1}'
            try:
                uval[name] = ncv[n] * (1 - (uval[f'fuel_mc_{n + 1}']) / 100) - 2443 * (uval[f'fuel_mc_{n + 1}'] / 100)
            except (KeyError, TypeError):
                log = f'Undefined variable: fuel_mc_{n + 1}. {name} left blank. Check if entry was entered properly.'
                print(log)
                logger.error(log)
                logs.append(log)
                uval[name] = ''
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

    # Start energy calcs #####################################
    # environment calcs
    name = 'p_ambient'  # ambient pressure
    names.append(name)
    units[name] = 'Pa'
    if units['initial_pressure'] == 'hPa':
        uval[name] = (uval['initial_pressure'] * 0.029529983) * 3386  # conversion
    else:
        uval[name] = uval['initial_pressure'] * 3386  # conversion

    name = 'boil_temp'  # local boil temperature based on ambient pressure
    names.append(name)
    units[name] = 'C'
    try:
        amb = uval['p_ambient'].n
        X = math.log(amb/101325)
        uval[name] = 1 / (1 / 373.14 - 8.14 * X / 40650) - 273.15
    except (KeyError, TypeError):
        uval[name] = 100
        line = f'Unable to calculate local boiling point either due to blank or incorrectly entered ambient pressure.' \
               f'Assumed local boiling point: {uval[name]}'
        print(line)
        logger.error(line)
        logs.append(line)
    except Exception as e:
        logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
    
    # latent heat of water vaporization at local boiling point (interpolate lookup table)
    name = 'Hvap'
    names.append(name)
    units[name] = 'kJ/kg'
    if uval['boil_temp'] > 96:  
        uval[name] = hvap_kg[96] + (uval['boil_temp'] - 96) * (hvap_kg[100] - hvap_kg[96]) / (100 - 96)
    else:
        uval[name] = hvap_kg[90] + (uval['boil_temp'] - 90) * (hvap_kg[96] - hvap_kg[90]) / (96 - 90)

    # net calorific value for charocal (old data sheet only)
    name = 'char_lower_heating_value'
    names.append(name)
    units[name] = 'kJ/kg'
    if 'char_higher_heating_value' in names and uval['char_higher_heating_value'] != '':  # older data sheet takes LHV
        uval[name] = uval['char_higher_heating_value'] - CV['char']
    else:
        try:  # for older data sheet
            uval[name] = uval['char_heating_value']
        except KeyError:  # new data sheet with char as a multi fuel
            uval[name] = ''
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')

    # Energy calcs for each phase#####################################
    for phase in phases:
        pval = {}  # initialize dictionary of phase-specific metrics
        metrics = []  # initialize list of phase-specific metrics (that will get renamed with phase identifier and
        # put in 'names')
        phase_identifier = '_'+phase
        for fullname in names:  # go through the list of input variables
            if fullname[-3:] == phase_identifier:  # if the variable name has the phase identifier
                name = fullname[:-3]  # strip off the phase identifier
                pval[name] = uval[fullname]  # before passing the variable to the calculations

        if len(fuels) == 0:
            name = 'fuel_mass'  # mass of fuel fed
            units[name] = 'kg'
            metrics.append(name)
            try:
                pval[name] = pval['initial_fuel_mass'] - pval['final_fuel_mass']
            except TypeError:
                pval[name] = ''
                line = f'Initial or final fuel mass for phase was not calculated correctly. {name}_{phase} was ' \
                       f'left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_dry_mass'  # dry fuel mass
            units[name] = 'kg'
            metrics.append(name)
            try:
                pval[name] = pval['fuel_mass'] * (1 - uval['fuel_mc'] / 100)  # fuel_mc is phase independent
            except (KeyError, TypeError):
                log = f'Undefined variable: fuel_mc_{phase} or fuel_mass_{phase}. One was not calculated correctly.' \
                      f'{name}_{phase} was left blank'
                print(log)
                logger.error(log)
                logs.append(log)
                pval[name] = ''
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

        name = 'phase_time'  # total time of test phase
        units[name] = 'min'
        metrics.append(name)
        var1 = 'start_time'
        var2 = 'end_time'
        try:
            pval[name] = timeperiod(pval[var1], pval[var2])
        except TypeError:
            pval[name] = ''
            line = f'{var1} or {var2} for phase: {phase} is entered incorrectly or left blank. Check values and that' \
                   f'both start and end times were entered in the same format. {name}_{phase} left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line {sys.exc_info()[2].tb_lineno}')
    
        name = 'time_to_boil'
        units[name] = 'min'
        metrics.append(name)
        var1 = 'start_time'
        var2 = 'boil_time'
        try:
            pval[name] = timeperiod(pval[var1], pval[var2])
        except TypeError:
            pval[name] = ''
            line = f'{var1} or {var2} for phase: {phase} is entered incorrectly or left blank. Check values and that' \
                   f'both times were entered in the same format. {name}_{phase} left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        if len(fuels) != 0:  # if multi fuels exist
            name = 'fuel_mass'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0)  # start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels):  # iterate through fuels
                    pval[name] = pval[name] + uval['fuel_mass_' + phase + '_' + str(n+1)]  # add fuel mass of each fuel
            except TypeError:
                pval[name] = ''
                line = f'fuel_mass_{phase}_{n+1} was calculated incorrectly. Check initial and final fuel mass' \
                       f'values. {name} left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_mass_wo_char'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0)  # start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels):  # iterate through fuels
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n < 0.75:  # exclude fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_mass_' + phase + '_' + str(n + 1)]  # add fuel mass of fuel
            except TypeError:
                pval[name] = ''
                line = f'fuel_Cfrac_db_{n+1} or fuel_mass_{phase}_{n+1} was not entered correctly. {name}_{phase} ' \
                       f'left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_dry_mass'
            metrics.append(name)
            units[name] = 'kg'
            pval[name] = ufloat(0, 0)  # start and 0 and add for each fuel
            try:
                for n, fuel in enumerate(fuels):  # iterate through fuels
                    pval[name] = pval[name] + uval['fuel_dry_mass_' + phase + '_' + str(n + 1)]  # add fuel mass of
                    # each to get summ
            except TypeError:
                pval[name] = ''
                line = f'fuel_dry_mass_{phase}_{n+1} was not calculated correctly. {name}_{phase} left blank'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

        name = 'char_mass'
        units[name] = 'kg'
        metrics.append(name)
        try:
            pval[name] = pval['final_char_mass'] - pval['initial_char_mass']
        except TypeError:
            pval[name] = ''
            line = f'initial_char_mass_{phase} or final_char_mass_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        if len(fuels) != 0:  # if multi fuels
            name = 'energy_consumed'
            units[name] = 'kJ'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval[name + '_' + phase + '_' + str(n+1)]  # sum from all fuels used
            except TypeError:
                pval[name] = ''
                line = f'{name}_{phase}_{n+1} was not calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_net_calorific_value'  # weighted net heating value for all fuels
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_net_calorific_value_' + str(n+1)] * \
                                 uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except TypeError:
                pval[name] = ''
                line = f'fuel_net_calorific_value_{n+1}, fuel_mass_{phase}_{n+1}, or fuel_mass_{phase} was not' \
                       f'entered/calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_EHV'  # effective heating value for all fuels
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n+1)] * \
                                 uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except TypeError:
                pval[name] = ''
                line = f'fuel_effective_calorific_value_{n+1}, fuel_mass_{phase}_{n+1}, or fuel_mass_{phase}' \
                       f'was not entered/calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_EHV_wo_char'  # effective heating value without carbon
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n < 0.75:  # exclude fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n + 1)] * \
                                     uval['fuel_mass_' + phase + '_' + str(n + 1)] / pval['fuel_mass_wo_char']
            except TypeError:
                pval[name] = ''
                line = f'fuel_effective_calorific_value_{n+1}, fuel_mass_{phase}_{n+1}, or fuel_mass_wo_char_{phase}' \
                       f'was not entered/calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            name = 'fuel_Cfrac'  # effective carbon fraction for all fuels
            units[name] = 'g/g'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    pval[name] = pval[name] + uval['fuel_Cfrac_' + str(n+1)] * \
                                 uval['fuel_mass_' + phase + '_' + str(n+1)] / pval['fuel_mass']
            except TypeError:
                pval[name] = ''
                line = f'fuel_Cfrac_{n+1}, fuel_mass_{phase}_{n+1}, fuel_mass_{phase} was not entered/calculated' \
                       f'correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

        for pot in pots:
            name = 'initial_water_mass_'+pot  # initial water mass in pot
            units[name] = 'kg'
            metrics.append(name)
            initial_mass = 'initial_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                pval[name] = pval[initial_mass]-uval[empty_mass]
            except TypeError:
                pval[name] = ''
                line = f'{initial_mass} or {empty_mass} was left blank or not entered correctly. {name}_{phase} was' \
                       f'left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
            
            name = 'final_water_mass_'+pot  # final water mass in pot
            units[name] = 'kg'
            metrics.append(name)
            final_mass = 'final_'+pot+'_mass'
            empty_mass = pot+'_dry_mass'
            try:
                pval[name] = pval[final_mass] - uval[empty_mass]
            except TypeError:
                pval[name] = ''
                line = f'{final_mass} or {empty_mass} was left blank or not entered correctly. {name}_{phase} was' \
                       f'left blank'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
    
            name = 'useful_energy_delivered_'+pot  # useful energy delivered to pot
            units[name] = 'kJ'
            metrics.append(name)
            # Clause 5.4.2 Formula 4: Q1=Cp*G1*(T2-T1)+(G1-G2)*gamma
            try:
                pval[name] = Cp * pval['initial_water_mass_'+pot] * \
                            (pval['max_water_temp_' + pot] - pval['initial_water_temp_' + pot]) + \
                            (pval['initial_water_mass_' + pot] - pval['final_water_mass_' + pot]) * \
                            uval['Hvap']    # hvap is phase independent
            except TypeError:
                pval[name] = ''
                line = f'initial_water_mass_{pot}, max_water_temp_{pot}, initial_water_temp_{pot}, ' \
                       f'initial_water_mass_{pot}, or final_water_mass_{pot} was left blank or not entered ' \
                       f'correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
 
        name = 'useful_energy_delivered'  # total useful energy delivered to all pots
        units[name] = 'kJ'
        metrics.append(name)
        try:
            pval[name] = pval['useful_energy_delivered_pot1']
            try: 
                pval[name] = pval[name] + pval['useful_energy_delivered_pot2']
                try:
                    pval[name] = pval[name] + pval['useful_energy_delivered_pot3']
                    try:
                        pval[name] = pval[name] + pval['useful_energy_delivered_pot4']
                    except TypeError:
                        pass
                except TypeError:
                    pass
            except TypeError:
                pass
        except (KeyError, TypeError):
            pval[name] = ''
            line = f'useful_energy_delivered_pot1_{phase} was not calculated correctly. {name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')
            
        name = 'cooking_power'
        units[name] = 'kW'
        metrics.append(name)
        # Clause 5.4.3 Formula 5: Pc=Q1/(t3-t1)
        try:
            pval[name] = pval['useful_energy_delivered'] / pval['phase_time'] / 60
        except TypeError:
            pval[name] = ''
            line = f'useful_energy_delivered_{phase} or phase_time_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        name = 'eff_wo_char'  # thermal efficiency with no energy credit for remaining char
        units[name] = '%'
        metrics.append(name)
        # Clause 5.4.4 Formula 6: eff=Q1/B/Qnet,af*100
        try:  # Current multi fuel sheet - use EHV without charcoal production factored in
            pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass_wo_char'] * pval['fuel_EHV_wo_char']) * 100
            line = 'TE without char equation: useful energy delivered / (fuel mass * fuel effective heating value ' \
                   'without char) * 100'
            print(line)
            logger.info(line)
            logs.append(line)
        except KeyError:  # if the values above do not exist
            try:  # older spreadsheet where effective heating value is entered in spreadsheet
                pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] * uval['fuel_heating_value']) \
                             * 100  # old data sheet, uses effective heating value which is calculated in spreadsheet
                line = 'TE without char equation: useful energy delivered / (fuel mass * effective heating value * 100)'
                print(line)
                logger.info(line)
                logs.append(line)
            except TypeError:
                pval[name] = ''
                line = f'useful_energy_delivered_{phase}, fuel_mass_{phase}, or fuel_heating_value_{phase} was' \
                       f'not calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
        except TypeError:
            pval[name] = ''
            line = f'useful_energy_delivered_{phase}, fuel_mass_wo_char_{phase}, or fuel_EHV_wo_char_{phase} was' \
                   f'not calcualted correctly. {name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')
            
        name = 'eff_w_char'  # thermal efficiency with energy credit for remaining char
        units[name] = '%'
        metrics.append(name)
        # Clause 5.4.5 Formula 7: eff=Q1/(B*Qnet,af-C*Qnet,char)*100
        try:  # Typical equation. Current spreadsheet if charcoal is entered in char space and not as a multi fuel
            pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] * pval['fuel_EHV'] - pval['char_mass'] *
                                                            uval['char_lower_heating_value']) * 100
            line = 'TE with char equation: useful energy delivered / (fuel mass * fuel effective heating value - ' \
                   'char mass * char lower heating value) * 100'
            print(line)
            logger.info(line)
            logs.append(line)
        except KeyError:  # if the values above do not exist
            try:  # try multi fuel calculations where EHV includes char production
                pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] * pval['fuel_EHV']) * 100
                line = 'TE with char equation: useful energy delivered / (fuel mass * fuel effective heating value ' \
                       'with char) * 100'
                print(line)
                logger.info(line)
                logs.append(line)
            except KeyError:  # if the values above do not exist
                try:  # try the older spreadsheet where the effective heating value was entered for the fuel
                    pval[name] = pval['useful_energy_delivered'] / \
                                 (pval['fuel_mass'] * uval['fuel_heating_value'] - pval['char_mass'] *
                                  uval['char_lower_heating_value']) * 100    # old datasheet
                    line = 'TE with char equation: useful energy delivered / (fuel mass * fuel heating value ' \
                           '(from entry sheet) - char mass * char lower heating value) *100'
                    print(line)
                    logger.info(line)
                    logs.append(line)
                except KeyError:  # if the values above do not exist
                    try:  # try calculating without the char values (they may not be entered or may be 0)
                        pval[name] = pval['useful_energy_delivered'] / (pval['fuel_mass'] *
                                                                        uval['fuel_heating_value']) * 100
                        # old datasheet when no value for char
                        line = 'TE with char equation: useful energy delivered / fuel mass * fuel heating value ' \
                               '(from entry sheet) * 100'
                        print(line)
                        logger.info(line)
                        logs.append(line)
                    except TypeError:
                        pval[name] = ''
                        line = f'useful_energy_delivered_{phase}, fuel_mass_{phase}, or fuel_heating_value_{phase}' \
                               f'was not calculated correctly. {name}_{phase} was left blank.'
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                except TypeError:
                    pval[name] = ''
                    line = f'useful_energy_delivered_{phase}, fuel_mass_{phase}, fuel_heating_value_{phase}' \
                           f'char_mass_{phase}, or char_lower_heating_value_{phase}' \
                           f'was not calculated correctly. {name}_{phase} was left blank.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
            except TypeError:
                pval[name] = ''
                line = f'useful_energy_delivered_{phase}, fuel_mass_{phase}, or fuel_EHV_{phase}' \
                       f'was not calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
        except TypeError:
            pval[name] = ''
            line = f'useful_energy_delivered_{phase}, fuel_mass_{phase}, fuel_EHV_{phase}, char_mass_{phase},' \
                   f'or char_lower_heating_value_{phase}' \
                   f'was not calculated correctly. {name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        if len(fuels) != 0:  # if multi fuels
            name = 'char_mass'
            if pval[name] == '':
                pval[name] = ufloat(0, 0)
                try:
                    for n, fuel in enumerate(fuels):
                        if uval['fuel_Cfrac_db_' + str(n + 1)].n > 0.75:  # only include fuels where the cfrac
                            # indicates charcoal
                            pval[name] = pval[name] + (uval['fuel_mass_' + phase + '_' + str(n+1)].n * -1)
                except TypeError:
                    pval[name] = ''
                    line = f'fuel_mass_{phase}_{n+1} was not calculated correctly. {name}_{phase} was left blank.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

            name = 'EHV_char'
            units[name] = 'kJ/kg'
            metrics.append(name)
            pval[name] = ufloat(0, 0)
            try:
                for n, fuel in enumerate(fuels):
                    if uval['fuel_Cfrac_db_' + str(n + 1)].n > 0.75:  # include fuels where the cfrac indicates charcoal
                        pval[name] = pval[name] + uval['fuel_effective_calorific_value_' + str(n + 1)] * \
                                     (uval['fuel_mass_' + phase + '_' + str(n + 1)] * -1) / pval['char_mass']
            except TypeError:
                pval[name] = ''
                line = f'fuel_effective_calorific_value_{n+1}, fuel_mass_{phase}_{n+1}, or char_mass_{phase}' \
                       f'was not calculated correctly.. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

        name = 'char_energy_productivity'
        units[name] = '%'
        metrics.append(name)
        # Clause 5.4.6 Formula 8: Echar=C*Qnet,char/B/Qnet,af*100
        try:
            pval[name] = pval['char_mass'] * uval['char_lower_heating_value'] / pval['fuel_mass'] / \
                         pval['fuel_EHV'] * 100
        except KeyError:
            try:
                pval[name] = pval['char_mass'] * uval['char_heating_value'] / pval['fuel_mass'] / \
                             uval['fuel_heating_value'] * 100
            except KeyError:
                try:
                    pval[name] = pval['char_mass'] * pval['EHV_char'] / pval['fuel_mass'] / pval['fuel_EHV'] * 100
                except TypeError:
                    pval[name] = ''
                    line = f'char_mass_{phase}, EHV_char_{phase}, fuel_mass_{phase}, or fuel_EHV_{phase} was not' \
                           f' calculated correctly. {name}_{phase} was left blank.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
            except TypeError:
                pval[name] = ''
                line = f'char_mass_{phase}, char_heating_value_{phase}, fuel_mass_{phase}, or ' \
                       f'fuel_heating_value_{phase} was not' \
                       f' calculated correctly. {name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
        except TypeError:
            pval[name] = ''
            line = f'char_mass_{phase}, char_lower_heating_value_{phase}, fuel_mass_{phase}, or fuel_EHV_{phase} ' \
                   f'was not calculated correctly. {name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')
    
        name = 'char_mass_productivity'
        units[name] = '%'
        metrics.append(name)
        # Clause 5.4.7 Formula 9: mchar=C/B*100
        try:
            pval[name] = pval['char_mass'] / pval['fuel_mass'] * 100
        except TypeError:
            pval[name] = ''
            line = f'char_mass_{phase}, or fuel_mass_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        name = 'burn_rate'  # fuel-burning rate, wet basis
        units[name] = 'g/min'
        metrics.append(name)
        try:
            pval[name] = pval['fuel_mass'] / pval['phase_time'] * 1000
        except TypeError:
            pval[name] = ''
            line = f'phase_time_{phase}, or fuel_mass_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        name = 'burn_rate_dry'  # fuel-burning rate, dry basis
        units[name] = 'g/min'
        metrics.append(name)
        try:
            pval[name] = pval['fuel_dry_mass'] / pval['phase_time'] * 1000
        except TypeError:
            pval[name] = ''
            line = f'phase_time_{phase}, or fuel_dry_mass_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

        name = 'firepower_w_char'
        units[name] = 'kW'
        metrics.append(name)
        try:
            pval[name] = (pval['fuel_mass'] * pval['fuel_EHV'] - pval['char_mass'] * uval[
                'char_lower_heating_value']) / (pval['phase_time'] * 60)
        except KeyError:
            try:
                pval[name] = (pval['fuel_mass'] * pval['fuel_EHV']) / (pval['phase_time'] * 60)
            except KeyError:
                try:
                    pval[name] = pval['cooking_power'] / pval['eff_w_char'] * 100
                except TypeError:
                    pval[name] = ''
                    line = f'cooking_power_{phase}, or eff_w_char_{phase} was not calculated correctly. ' \
                           f'{name}_{phase} was left blank.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
            except TypeError:
                pval[name] = ''
                line = f'fuel_mass_{phase}, fuel_EHV_{phase}, or phase_time_{phase} was not calculated correctly. ' \
                       f'{name}_{phase} was left blank.'
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')
        except TypeError:
            pval[name] = ''
            line = f'fuel_mass_{phase}, fuel_EHV_{phase}, char_mass_{phase}, char_lower_heat_value_{phase},' \
                   f'or phase_time_{phase} was not calculated correctly. ' \
                   f'{name}_{phase} was left blank.'
            logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}_{phase}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')


        for metric in metrics:  # for each metric calculated for the phase
            name = metric+phase_identifier  # add the phase identifier to the variable name
            uval[name] = pval[metric]
            units[name] = units[metric]
            names.append(name)  # add the new full variable name to the list of variables that will be output

    ####################################
    # ISO weighted metrics
    existing_weight_phases = []
    weighted_metrics = ['eff_wo_char', 'eff_w_char', 'char_energy_productivity', 'char_mass_productivity',
                        'cooking_power', 'burn_rate']
    for phase in phases:
        name = 'weight_' + phase
        try:
            if uval[name].n != '':
                existing_weight_phases.append(phase)
        except (KeyError, TypeError):
            if uval[name] != '':
                existing_weight_phases.append(phase)

    for name in weighted_metrics:
        weight_name = name + '_weighted'
        names.append(weight_name)
        units[weight_name] = units[name + '_hp']
        uval[weight_name] = ufloat(0, 0)
        for phase in existing_weight_phases:
            phase_name = name + '_' + phase
            try:
                uval[weight_name] = uval[weight_name] + (uval[phase_name] * uval['weight_' + phase]) / \
                                    uval['weight_total']
            except TypeError:
                pass

    if uval['eff_wo_char_weighted'].n != 0:
        name = 'tier_eff_wo_char'
        names.append(name)
        units[name] = ''
        if uval['eff_wo_char_weighted'].n < 10:
            uval[name] = 'Tier 0'
        elif 10 <= uval['eff_wo_char_weighted'].n < 20:
            uval[name] = 'Tier 1'
        elif 20 <= uval['eff_wo_char_weighted'].n < 30:
            uval[name] = 'Tier 2'
        elif 30 <= uval['eff_wo_char_weighted'].n < 40:
            uval[name] = 'Tier 3'
        elif 40 <= uval['eff_wo_char_weighted'].n < 50:
            uval[name] = 'Tier 4'
        elif uval['eff_wo_char_weighted'].n >= 50:
            uval[name] = 'Tier 5'

    if uval['eff_w_char_weighted'].n != 0:
        name = 'tier_eff_w_char'
        names.append(name)
        units[name] = ''
        if uval['eff_w_char_weighted'].n < 10:
            uval[name] = 'Tier 0'
        elif 10 <= uval['eff_w_char_weighted'].n < 20:
            uval[name] = 'Tier 1'
        elif 20 <= uval['eff_w_char_weighted'].n < 30:
            uval[name] = 'Tier 2'
        elif 30 <= uval['eff_w_char_weighted'].n < 40:
            uval[name] = 'Tier 3'
        elif 40 <= uval['eff_w_char_weighted'].n < 50:
            uval[name] = 'Tier 4'
        elif uval['eff_w_char_weighted'].n >= 50:
            uval[name] = 'Tier 5'

    # end calculations
    ######################################################
    # make output file
    io.write_constant_outputs(outputpath, names, units, val, unc, uval)
    
    log = f'created: {outputpath}'
    print(log)
    logger.info(log)
    logs.append(log)

    end_time = dt.now()
    log = f"Execution time: {end_time - start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    return units, uval, logs


def timeperiod(StartTime, EndTime):
    # function calculates time difference in minutes
    # Inputs start and end times as strings and converts to time objects
    try:
        start_object = dt.strptime(StartTime, '%Y%m%d %H:%M:%S')  # convert the start time string to date object
        end_object = dt.strptime(EndTime, '%Y%m%d %H:%M:%S')  # convert the end time string to date object
    except ValueError:
        start_object = dt.strptime(StartTime, '%H:%M:%S')
        end_object = dt.strptime(EndTime, '%H:%M:%S')
    delta_object = end_object-start_object  # time difference as date object
    Time = delta_object.total_seconds()/60  # time difference as minutes
    return Time
    
#####################################################################
# the following two lines allow the main function to be run as an executable


if __name__ == "__main__":
    LEMS_EnergyCalcs(inputpath, outputpath, logger)
