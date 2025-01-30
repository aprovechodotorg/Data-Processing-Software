# v0.0 Python3

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

import math
import easygui
import LEMS_DataProcessing_IO as io
import numpy as np
from uncertainties import ufloat
from datetime import datetime as dt
from datetime import timedelta
import os
import matplotlib
import subprocess
import sys

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_TimeSeries.csv'  # read
energypath = 'foldername_EnergyOutputs.csv'  # read
gravinputpath = 'foldername_GravOutputs.csv'  # read
aveinputpath = 'folderpath_Averages.csv'  # read
emisoutputpath = 'foldername_EmissionOutputs.csv'  # write
alloutputpath = 'foldername_AllOutputs.csv'  # write
logger = 'logging Python package'
timespath = 'foldername_PhaseTimes.csv'  # read
versionpath = 'foldername_SensorboxVersion.csv'  # read
fuelpath = 'foldername_FormattedFuelData.csv'  # read
fuelmetricpath = 'foldername_FuelMetrics.csv'  # read
exactpath = 'foldername_FormattedExactData.csv'  # read
scalepath = 'foldername_FormattedScaleData.csv'  # read
nanopath = 'foldername_FormattedNanoscanData.csv'  # read
TEOMpath = 'foldername_FormattedTEOMData.csv'  # read
senserionpath = 'foldername_FormattedSenserionData.csv'  # read
OPSpath = 'foldername_FormattedOPSData.csv'  # read
Picopath = 'foldername_FormattedPicoData.csv'  # read
emissioninputpath = 'foldername_EmissionInputs.csv'  # read/write
bcoutputpath = 'foldername_BCOutputs.csv'  # read
inputmethod = '0'  # (non-interactive) or 1 (interactive)


def LEMS_EmissionCalcs_ISO(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath, logger,
                           timespath, versionpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath,
                           senserionpath, OPSpath, Picopath, emissioninputpath, inputmethod, bcoutputpath):
    # Function purpose: Intake time series and energy data and calculate emission metrics for all species measured.
    # create averages of emission metrics and timeseries calculations. Output a file with all metrics calcualted
    # from all steps before

    # Inputs:
    # Time series data that's bee background subtracted and split into each phase
    # Energy calculations
    # Gravimetric calculations
    # Averages of all sensor box sensors
    # Python logging function
    # Start and end times of each phase
    # Sensor box version
    # Time series data from the FUEL sensor data
    # Calculated metrics from the FUEL sensor data
    # Time series data from the EXACT sensor data
    # Time series data from a live recording scale
    # Time series data from a nanoscan sensor
    # Time series data from a TEOM sensor
    # Time series data from a controller suite of sensierion sensors
    # Time series data from an OPS sensor
    # Time series data from a PICO sensor
    # Metrics for black carbon
    # Inputs on duct size, velocity traverse values, and default MSC value (if exists)
    # Inputmethod: 0 (non-interactive) or 1 (interactive)

    # Outputs:
    # Timeseries data of all sensor data and calculated emissions metrics as a full timeseries and for each phase
    # Inputs on duct size, velocity traverse values, and default MSC value
    # All metrics calcualated from all steps (energy calc, grav, and emissions)

    logs = []  # List of notable functions, errors, and calculations recorded for reviewing past processing of data

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

    metricnames = []  # List of variables that will be calculated
    pmetric = {}  # Dictionary of all metrics calculated within a phase, keys are metric names

    allnames = []  # List of all names for all pases
    allunits = {}  # Dictionary of units, keys are all names
    allval = {}  # Dictionary of values, keys are all names
    allunc = {}  # Dictionary of uncertainty values, keys are all names
    alluval = {}  # Dictionary of values and uncertainty values as ufloats, keys are all names

    emissions = ['CO', 'CO2', 'CO2v', 'PM', 'VOC']  # emission species that will get metric calculations

    phases = ['hp', 'mp', 'lp']

    MW = {}  # Dictionary of molecular weights
    MW['C'] = float(12.01)  # molecular weight of carbon (g/mol)
    MW['CO'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['CO2'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['CO2v'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['SO2'] = float(64.07)  # molecular weight of sulfur dioxide (g/mol)
    MW['NO'] = float(30.01)  # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2'] = float(46.01)  # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S'] = float(34.1)  # molecular weight of hydrogen sulfide (g/mol)
    MW['VOC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['CH4'] = float(16.04)  # molecular weight of methane (g/mol)
    MW['air'] = float(29)  # molecular weight of air (g/mol)
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    # load phase averages data file
    [metricnamesall, metricunits, metricval, metricunc, metric] = io.load_constant_inputs(
        aveinputpath)  # these are not used but copied to the output
    line = f'Loaded: {aveinputpath} for transfer to {alloutputpath}'
    print(line)
    logger.info(line)
    logs.append(line)

    # Check for IDC test ###########
    if 'seconds_L1' in metricnamesall:
        phases.insert(0, 'L1')
    if 'seconds_L5' in metricnamesall:
        phases.append('L5')
    if 'CO2v_prebkg' in metricnamesall:  # check if CO2v is present
        emissions.remove('CO2')  # only run CO2v if present
    else:
        emissions.remove('CO2v')
    if 'VOC_prebkg' in metricnamesall:  # check if VOC is present
        pass
    else:
        emissions.remove('VOC')

    for em in emissions:  # Pull out phase averages from average print out. Ignore bkg data
        for phase in phases:
            for name in metricnamesall:
                if em + '_' in name and phase in name:
                    metricnames.append(name)
    line = 'Loaded phase averages: ' + aveinputpath
    print(line)
    logger.info(line)
    logs.append(line)

    # load energy metrics data file
    [enames, eunits, emetrics, eunc, euval] = io.load_constant_inputs(energypath)
    line = 'Loaded energy metrics: ' + energypath
    print(line)
    logs.append(line)

    [vnames, vunits, vval, vunc, vuval] = io.load_constant_inputs(versionpath)  # Load sensor version
    msg = 'loaded: ' + versionpath
    print(msg)
    logger.info(msg)
    logs.append(msg)

    firmware_version = vval['SB']  # Find the firmware version of the sensorbox

    if os.path.isfile(emissioninputpath):  # If user has already entered emission inputs before
        [emnames, emunits, emval, emunc, emuval] = io.load_constant_inputs(emissioninputpath)
        line = f"Loaded previous inputs from: {emissioninputpath}"
        print(line)
        logger.info(line)
        logs.append(line)
    else:
        emnames = []  # List of names for emission entry
        emunits = {}  # Dictionary of units, key is emnames
        emval = {}  # Dictionary of values, key is enames
        emunc = {}  # Dictionary of uncertainties, key is enames
        emuval = {}  # Dictionary of values and uncertainties as ufloats, key is enames

        # make a header
        name = 'variable'
        emnames.append(name)
        emunits[name] = 'units'
        emval[name] = 'value'
        emunc[name] = 'uncertainty'

        if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':
            # Heating stove lab has a slightly different system and requires different inputs, ask user for more inputs
            name = 'Cp'  # Pitot probe correction factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'velocity_traverse'  # Velocity traverse correction factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 0.975

            name = 'flowgrid_cal_factor'  # flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'factory_flow_cal'  # factory flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 62.8

            name = 'duct_diameter'  # Diameter of ducts
            emnames.append(name)
            emunits[name] = 'inches'
            emval[name] = 12.0

            name = 'MSC_default'  # Default MSC value (used for changing or replacing calculated MSC value)
            emnames.append(name)
            emunits[name] = 'm^2/g'
            emval[name] = 3

        else:
            name = 'flowgrid_cal_factor'  # flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'factory_flow_cal'  # factory flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 15.3

            name = 'duct_diameter'  # Diameter of ducts
            emnames.append(name)
            emunits[name] = 'inches'
            emval[name] = 6.0

            name = 'MSC_default'  # Default MSC value (used for changing or replacing calculated MSC value)
            emnames.append(name)
            emunits[name] = 'm^2/g'
            emval[name] = 3

    if inputmethod == '1':  # If in interactive mode
        fieldnames = []
        defaults = []
        if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':
            # For heating stove lab, more is asked and explained
            for name in emnames:
                if name != 'variable':
                    fieldnames.append(name)
                    defaults.append(emval[name])

            # GUI box to edit emissions
            zeroline = f'Enter emissions input data (g)\n\n' \
                       f'MSC_default may be used to more accurately calculate PM2.5 data when:\n' \
                       f'a) A filter is not used (use a historical MSC from a similar stove)\n' \
                       f'b) PM data could not be correctly backgound subtracted (use a historical MSC from a similar ' \
                       f'stove)\n' \
                       f'c) There is a desire to cut some PM data from final calcualtions (calculalte MSC using full ' \
                       f'data series, manipulate PM data and then entre previous MSC.\n\n' \
                       f'IF USING YOU ARE USING A FILTER AND DO NOT FALL INTO ONE OF THE SCENARIOS ABOVE, DO NOT ' \
                       f'CHANGE MSC_default.\n\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit'
            msg = zeroline + secondline + thirdline
            title = 'Enter Values'
            newvals = easygui.multenterbox(msg, title, fieldnames, values=defaults)
            if newvals:
                if newvals != defaults:  # If user entered new values
                    defaults = newvals
                    for n, name in enumerate(emnames[1:]):
                        emval[name] = defaults[n]
            else:
                line = 'Error: Undefined variables'
                print(line)
                logger.error(line)
                logs.append(line)
        else:
            # otherwise for all other SB versions only show MSC default
            fieldnames.append('MSC_default')
            for name in emnames[1:]:
                defaults.append(emval[name])

            # GUI box to edit emissions
            zeroline = f'Enter emissions input data (g)\n\n' \
                       f'MSC_default may be used to more accurately calculate PM2.5 data when:\n' \
                       f'a) A filter is not used (use a historical MSC from a similar stove)\n' \
                       f'b) PM data could not be correctly backgound subtracted (use a historical MSC from a ' \
                       f'similar stove)\n' \
                       f'c) There is a desire to cut some PM data from final calcualtions (calculalte MSC using ' \
                       f'full data series, manipulate PM data and then entre previous MSC.\n\n' \
                       f'IF USING YOU ARE USING A FILTER AND DO NOT FALL INTO ONE OF THE SCENARIOS ABOVE, DO NOT ' \
                       f'CHANGE MSC_default.\n\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit'
            msg = zeroline + secondline + thirdline
            title = 'Enter Values'
            newvals = easygui.multenterbox(msg, title, fieldnames, values=[emval['MSC_default']])
            if newvals:
                if newvals != [emval['MSC_default']]:
                    emval['MSC_default'] = newvals[0]
                    for n, name in enumerate(emnames[1:]):
                        emval[name] = defaults[n]
            else:
                line = 'Error: Undefined variables'
                print(line)
                logger.error(line)
                logs.append(line)
        io.write_constant_outputs(emissioninputpath, emnames, emunits, emval, emunc, emuval)
        line = 'Created emissions input file: ' + emissioninputpath
        print(line)
        logger.info(line)
        logs.append(line)
    else:
        line = 'Used old/default inputs from input file: ' + emissioninputpath
        print(line)
        logger.info(line)
        logs.append(line)

    for name in emnames[1:]:
        emval[name] = float(emval[name])

    # load grav metrics data file
    name = 'MSC'
    metricunits[name] = 'm^2/g'
    try:
        [gravnames, gravunits, gravmetrics, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
        # MSC is not in gravoutputs
        line = 'Loaded gravimetric PM metrics:' + gravinputpath
        print(line)
        logs.append(line)
        pmetric[name] = 0
    except FileNotFoundError:
        line = 'No gravimetric data, using default MSC'
        print(line)
        logs.append(line)
        pmetric[name] = emval['MSC_default']

    # ambient pressure from energy metrics data file (hPa converted here to Pa)
    name = 'P_amb'
    metricnames.append(name)
    metricunits[name] = 'Pa'
    try:
        metric[name] = ((euval['initial_pressure'] + euval['final_pressure']) * 33.86) / 2 * 100  # Pa
    except TypeError:
        try:
            metric[name] = euval['initial_pressure'] * 33.86 * 100
        except TypeError:
            try:
                metric[name] = euval['final_pressure'] * 33.86 * 100
            except TypeError:
                metric[name] = ''
                line = f"Value for initial_pressure or final_pressure was not entered correctly or both were" \
                       f"left blank. {name} was left blank."
                logger.error(line)
        except Exception as e:
            logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                         f'{sys.exc_info()[2].tb_lineno}')

    # absolute duct pressure, Pa
    try:
        metric[name] = metric['P_amb'].n
    except AttributeError:
        metric[name] = metric['P_amb']

    for phase in phases:  # For each phase
        pmetricnames = []  # initialize a list of metric names for each phase
        # read in time series data file of the specific phase
        phaseinputpath = inputpath[:-4] + '_' + phase + '.csv'

        if os.path.isfile(phaseinputpath):  # Check that time series path exists
            [names, units, data] = io.load_timeseries(phaseinputpath)
            line = 'Loaded phase time series data: ' + phaseinputpath
            print(line)
            logger.info(line)
            logs.append(line)

            # MSC mass scattering cross-section (constant)
            name = 'MSC'
            pmetricnames.append(name)

            try:  # backwards compatable for MSC not being in previous inputs
                emval['MSC_default']
            except KeyError:
                emval['MSC_default'] = 3

            if pmetric[name] != emval['MSC_default']:
                conc = gravuval['PMmass_' + phase]  # average PM mass concentration ug/m^3
                scat = metric['PM_' + phase]  # average scattering value Mm^-1 %needs to be per phase
                try:
                    pmetric[name] = scat / conc
                except TypeError:
                    pmetric[name] = ufloat(np.nan, np.nan)
                    line = f'PMmass_{phase} or PM_{phase} is not a number. {name}_{phase} entered as NaN.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

            # calculate mass concentration data series
            for species in emissions:  # for each emission species that will get metrics
                name = species + 'mass'
                names.append(name)
                units[name] = 'gm^-3'
                data[name] = []
                for n, val in enumerate(data[species]):
                    try:
                        if species == 'PM':
                            result = val / pmetric['MSC'] / 1000000  # MSC needs to be different for each phase
                        else:  # from ppm and ideal gas law
                            result = val * MW[species] * metric['P_duct'] / (data['FLUEtemp'][n] + 273.15) / 1000000 / R
                    except TypeError:
                        result = ''
                        line = f'Value for {species} at line {n}, value of MSC, value of P-duct, or value of FLUEtemp' \
                               f'at line {n} is not a number. Data for {name} at line {n} was left blank'
                        logger.error(line)
                    except Exception as e:
                        result = ''
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # Carbon concentration
            name = 'Cmass'
            names.append(name)
            units[name] = 'gm^-3'
            data[name] = []
            for n, val in enumerate(data['COmass']):
                try:
                    data[name].append(val * MW['C'] / MW['CO'] + data['CO2vmass'][n] * MW['C'] / MW['CO2v'])
                except KeyError:
                    data[name].append(val * MW['C'] / MW['CO'] + data['CO2mass'][n] * MW['C'] / MW['CO2'])

            # MCE
            name = 'MCE'
            names.append(name)
            units[name] = 'mol/mol'
            data[name] = []
            try:
                for n, val in enumerate(data['CO2v']):
                    result = val / (val + data['CO'][n])
                    data[name].append(result)
            except KeyError:
                for n, val in enumerate(data['CO2']):
                    result = val / (val + data['CO'][n])
                    data[name].append(result)

            # flue gas molecular weight
            name = 'MW_duct'
            names.append(name)
            units[name] = 'g/mol'
            data[name] = []
            for n, val in enumerate(data['time']):
                result = MW['air']
                data[name].append(result)

            # flue gas density
            name = 'density'
            names.append(name)
            units[name] = 'gm^-3'
            data[name] = []
            for n, val in enumerate(data['MW_duct']):
                result = val * metric['P_duct'] / R / (data['FLUEtemp'][n] + 273.15)
                data[name].append(result)

            if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':
                # Heating stove lab has specific calculations that must be done

                # Smooth Pitot Data
                n = 10  # boxcar length
                name = 'Flow_smooth'
                names.append(name)
                units[name] = 'mmH2O'
                data[name] = []
                for m, val in enumerate(data['Flow']):
                    if m == 0:
                        newval = val
                    else:
                        if m >= n:
                            boxcar = data['Flow'][m - n:m]
                        else:
                            boxcar = data['Flow'][:m]
                        newval = sum(boxcar) / len(boxcar)
                    data[name].append(newval)
                msg = 'Smoothed flow data'
                print(msg)
                logger.info(msg)
                logs.append(msg)

                # Duct velocity
                # V = Cp * (2 deltaP / density) ^1/2
                # Use ideal gas law: Pamb = density * (R/M) * T
                name = 'DuctFlow'
                names.append(name)
                units[name] = 'm/sec'
                data[name] = []

                for n, val in enumerate(data['Flow_smooth']):
                    Flow_Pa = val * 9.80665  # mmH2O to Pa
                    Pduct_Pa = data['AmbPres'][n] * 100  # hPa to Pa
                    TC_K = data['FLUEtemp'][n] + 273.15  # C to K
                    inner = (Flow_Pa * 2 * R * TC_K) / (Pduct_Pa * MW['air'] / 1000)
                    velocity = emval['Cp'] * math.sqrt(inner)
                    data[name].append(velocity)

                # Volumetric flowrate
                name = 'vol_flow_ASTM'
                names.append(name)
                units[name] = 'm^3/s'
                data[name] = []

                duct_diameter = emval['duct_diameter'] / 39.37  # m
                duct_area = (np.pi * duct_diameter * duct_diameter) / 4  # m^2

                for n, val in enumerate(data['DuctFlow']):
                    data[name].append(val * duct_area * emval['velocity_traverse'])

                # Mass flow rate
                name = 'mass_flow_ASTM'
                names.append(name)
                units[name] = 'g/sec'
                data[name] = []

                for n, val in enumerate(data['vol_flow_ASTM']):
                    data[name].append(val * data['density'][n])

                # mole flow of air and pollutants through dilution tunnel
                name = 'mole_flow_ASTM'
                names.append(name)
                units[name] = 'mol/sec'
                data[name] = []
                for n, val in enumerate(data['mass_flow_ASTM']):
                    result = val / data['MW_duct'][n]
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

                # cumulative volume through dilution tunnel
                name = 'totvol_ASTM'
                names.append(name)
                units[name] = 'm^3'
                data[name] = []
                sample_period = data['seconds'][3] - data['seconds'][2]
                for n, val in enumerate(data['vol_flow_ASTM']):
                    if n == 0:
                        result = val
                    else:
                        result = data[name][n - 1] + val * sample_period
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

                # emission rates g/sec
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_ASTM'
                    names.append(name)
                    units[name] = 'g/sec'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        try:
                            result = val * data['vol_flow_ASTM'][n]
                        except TypeError:
                            pass  # Previous result will be used for data point if there's an invalid entry
                        try:
                            data[name].append(result.n)
                        except AttributeError:
                            data[name].append(result)

                # carbon burn rate
                name = 'C_ER_ASTM'
                names.append(name)
                units[name] = 'g/sec'
                data[name] = []
                try:
                    for n, val in enumerate(data['CO2v_ER_ASTM']):
                        try:
                            result = val * MW['C'] / MW['CO2v'] + data['CO_ER_ASTM'][n] * MW['C'] / MW['CO']
                        except TypeError:
                            result = ''
                            line = f"Value of CO_ER_ASTM or CO2v_ER_ASTM at line {n} is not a number. Data of {name} " \
                                   f"at line {n} was left blank."
                            logger.error(line)
                        except Exception as e:
                            logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                         f'{sys.exc_info()[2].tb_lineno}')
                        data['C_ER_ASTM'].append(result)
                except KeyError:  # still needed something if CO2v doesn't exist
                    for n, val in enumerate(data['CO2_ER_ASTM']):
                        try:
                            result = val * MW['C'] / MW['CO2'] + data['CO_ER_ASTM'][n] * MW['C'] / MW['CO']
                        except TypeError:
                            result = ''
                            line = f"Value of CO_ER_ASTM or CO2_ER_ASTM at line {n} is not a number. Data of {name} " \
                                   f"at line {n} was left blank."
                            logger.error(line)
                        except Exception as e:
                            logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                         f'{sys.exc_info()[2].tb_lineno}')
                        data['C_ER_ASTM'].append(result)

                # emission rates g/min
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_min_ASTM'
                    names.append(name)
                    units[name] = 'g/min'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        result = val * data['vol_flow_ASTM'][n] * 60
                        try:
                            data[name].append(result.n)
                        except AttributeError:
                            data[name].append(result)

                # emission rates g/hr
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_hr_ASTM'
                    names.append(name)
                    units[name] = 'g/hr'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        result = val * data['vol_flow_ASTM'][n] * 60 * 60
                        try:
                            data[name].append(result.n)
                        except AttributeError:
                            data[name].append(result)

                # emission factors (ish)
                for species in emissions:
                    ERname = species + '_ER_hr_ASTM'
                    name = species + '_EF_ASTM'
                    names.append(name)
                    units[name] = 'g/kg_C'  # gram per kilogram carbon
                    data[name] = []
                    for n, val in enumerate(data[ERname]):
                        if data['C_ER_ASTM'][n] == 0:
                            data['C_ER_ASTM'][n] = 0.001  # Avoid division by 0 errors
                        result = val / (data['C_ER_ASTM'][n] * 3600 / 1000)  # g/sec to kg/hr
                        try:
                            data[name].append(result.n)
                        except:
                            data[name].append(result)

            # mass flow of air and pollutants through dilution tunnel
            name = 'mass_flow'
            names.append(name)
            units[name] = 'g/sec'
            data[name] = []
            for n, val in enumerate(data['Flow']):
                try:
                    result = emval['factory_flow_cal'] * emval['flowgrid_cal_factor'] * \
                             (val / 25.4 * metric['P_duct'] / (data['FLUEtemp'][n] + 273.15)) ** 0.5
                    # convert val from in H2O to mm H2O
                except TypeError:
                    result = 0
                    line = f'factory_flow_cal, flowgrid_cal_factor, Flow at line {n}, or FLUEtemp at line {n} is' \
                           f'not a valid number. Data of {name} at {n} was entered as 0.'
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

                try:
                    data[name].append(result.n)
                except AttributeError:
                    data[name].append(result)

            # volume flow of air and pollutants through dilution tunnel
            name = 'vol_flow'
            names.append(name)
            units[name] = 'm^3/sec'
            data[name] = []
            for n, val in enumerate(data['mass_flow']):
                try:
                    result = val / data['density'][n]
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)
                except TypeError:
                    data[name].append(0)
                    line = f"Data of mass_flow or density at line {n} is not a number. Data of {name} at line {n} left" \
                           f"blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

            # mole flow of air and pollutants through dilution tunnel
            name = 'mole_flow'
            names.append(name)
            units[name] = 'mol/sec'
            data[name] = []
            for n, val in enumerate(data['mass_flow']):
                result = val / data['MW_duct'][n]
                try:
                    data[name].append(result.n)
                except AttributeError:
                    data[name].append(result)

            # cumulative volume through dilution tunnel
            name = 'totvol'
            names.append(name)
            units[name] = 'm^3'
            data[name] = []
            sample_period = data['seconds'][3] - data['seconds'][2]
            for n, val in enumerate(data['vol_flow']):
                if n == 0:
                    result = val
                else:
                    result = data[name][n - 1] + val * sample_period
                try:
                    data[name].append(result.n)
                except AttributeError:
                    data[name].append(result)

            # emission rates g/sec
            for species in emissions:
                concname = species + 'mass'
                name = species + '_ER'
                names.append(name)
                units[name] = 'g/sec'
                data[name] = []
                for n, val in enumerate(data[concname]):
                    result = val * data['vol_flow'][n]
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # carbon burn rate
            name = 'C_ER'
            names.append(name)
            units[name] = 'g/sec'
            data[name] = []
            try:
                for n, val in enumerate(data['CO2v_ER']):
                    try:
                        result = val * MW['C'] / MW['CO2v'] + data['CO_ER'][n] * MW['C'] / MW['CO']
                    except TypeError:
                        result = ''
                        line = f"Data for CO_ER or CO2v_ER at line {n} is not a number. Data of {name} for line {n}" \
                               f"was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                    data['C_ER'].append(result)
            except KeyError:  # still needed something if CO2v doesn't exist
                for n, val in enumerate(data['CO2_ER']):
                    try:
                        result = val * MW['C'] / MW['CO2'] + data['CO_ER'][n] * MW['C'] / MW['CO']
                    except TypeError:
                        result = ''
                        line = f"Data for CO_ER or CO2_ER at line {n} is not a number. Data of {name} for line {n}" \
                               f"was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                    data['C_ER'].append(result)
            # emission rates g/min
            for species in emissions:
                concname = species + 'mass'
                name = species + '_ER_min'
                names.append(name)
                units[name] = 'g/min'
                data[name] = []
                for n, val in enumerate(data[concname]):
                    result = val * data['vol_flow'][n] * 60
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # emission rates g/hr
            for species in emissions:
                concname = species + 'mass'
                name = species + '_ER_hr'
                names.append(name)
                units[name] = 'g/hr'
                data[name] = []
                for n, val in enumerate(data[concname]):
                    result = val * data['vol_flow'][n] * 60 * 60
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # emission factors (ish)
            for species in emissions:
                ERname = species + '_ER_hr'
                name = species + '_EF'
                names.append(name)
                units[name] = 'g/kg_C'  # gram per kilogram carbon
                data[name] = []
                for n, val in enumerate(data[ERname]):
                    if data['C_ER'][n] == 0:
                        data['C_ER'][n] = 0.001  # Avoid division by 0 errors
                    result = val / (data['C_ER'][n] * 3600 / 1000)  # g/sec to kg/hr
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # firepower
            wood_Cfrac = 0.5  # carbon fraction of fuel (should be an input in energy inputs
            name = 'firepower_carbon'
            names.append(name)
            units[name] = 'W'
            data[name] = []
            for n, val in enumerate(data['C_ER']):
                try:
                    result = val / wood_Cfrac * float(emetrics['fuel_heating_value'])  # old spreadsheet
                except KeyError:
                    try:
                        result = val / float(emetrics['fuel_Cfrac_' + phase]) * float(
                            emetrics['fuel_EHV_' + phase])  # new spreadsheet
                    except TypeError:
                        result = ''
                        line = f"Data for C_ER at line {n}, value for fuel_Cfrac_{phase}, or fuel_EHV_{phase} is" \
                               f"not a number. Data for {name} at line {n} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                except TypeError:
                    result = ''
                    line = f"Data for C_ER at line {n}, value for fuel_Cfrac_{phase}, or fuel_heating_value_{phase} is" \
                           f"not a number. Data for {name} at line {n} was left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
                try:
                    data[name].append(result.n)
                except AssertionError:
                    data[name].append(result)

            # cumulative mass
            for species in emissions:
                ername = species + '_ER'
                name = species + '_totmass'
                names.append(name)
                units[name] = 'g'
                data[name] = []
                for n, val in enumerate(data[ername]):
                    if n == 0:
                        result = val
                    else:
                        result = data[name][n - 1] + val * sample_period
                    try:
                        data[name].append(result.n)
                    except AttributeError:
                        data[name].append(result)

            # output time series data file
            phaseoutputpath = inputpath[:-4] + 'Metrics_' + phase + '.csv'
            io.write_timeseries_without_uncertainty(phaseoutputpath, names, units, data)

            line = 'created phase time series data file with processed emissions:\n' + phaseoutputpath
            print(line)
            logs.append(line)

            # phase average emission metrics  ####################
            # MCE
            name = 'MCE'
            pmetricnames.append(name)
            metricunits[name] = 'mol/mol'
            try:
                pmetric[name] = metric['CO2v_' + phase] / (metric['CO2v_' + phase] + metric['CO_' + phase])
            except KeyError:
                pmetric[name] = metric['CO2_' + phase] / (metric['CO2_' + phase] + metric['CO_' + phase])

            for name in ['MW_duct', 'density', 'mass_flow', 'mole_flow', 'vol_flow']:
                pmetricnames.append(name)
                metricunits[name] = units[name]
                pmetric[name] = sum(data[name]) / len(data[name])

            # cumulative volume
            name = 'totvol'
            pmetricnames.append(name)
            metricunits[name] = 'm^3'
            pmetric[name] = data[name][-1]

            for species in emissions:
                # mass concentration
                name = species + 'mass'
                pmetricnames.append(name)
                metricunits[name] = 'gm^-3'
                pmetric[name] = sum(data[name]) / len(data[name])

                # total mass
                name = species + '_total_mass'
                pmetricnames.append(name)
                metricunits[name] = 'g'
                try:
                    pmetric[name] = data[species + '_totmass'][-1]
                except KeyError:
                    pmetric[name] = ''
                    line = f"Data of {species}_totmass does not exist. {name}_{phase} left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

                # emission factor dry fuel
                name = species + '_fuel_dry_mass'
                pmetricnames.append(name)
                metricunits[name] = 'g/kg'
                try:
                    pmetric[name] = pmetric[species + '_total_mass'] / euval['fuel_dry_mass_' + phase]
                except TypeError:
                    pmetric[name] = ''
                    line = f"{species}_total_mass_{phase} or fuel_dry_mass_{phase} is not a number. {name}_{phase}" \
                           f"left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

                # emission factor energy
                name = species + '_fuel_energy'
                pmetricnames.append(name)
                metricunits[name] = 'g/MJ'
                try:  # old spreadsheet
                    pmetric[name] = pmetric[species + '_total_mass'] / euval['fuel_mass_' + phase] / \
                                    euval['fuel_heating_value'] * 1000
                except KeyError:
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / euval['fuel_mass_wo_char_' + phase] / euval[
                            'fuel_EHV_wo_char_' + phase] * 1000
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase}, fuel_mass_{phase}, or fuel_EHV_wo_char_{phase} is not" \
                               f"a number. {name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                except TypeError:
                    pmetric[name] = ''
                    line = f"{species}_total_mass_{phase}, fuel_mass_{phase}, or fuel_heating value_{phase} is not" \
                           f"a number. {name}_{phase} was left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

                # emission factor energy with energy credit for char
                name = species + '_fuel_energy_w_char'
                pmetricnames.append(name)
                metricunits[name] = 'g/MJ'
                try:  # old spreadsheet
                    pmetric[name] = pmetric[species + '_total_mass'] / (
                                euval['fuel_mass_' + phase] * euval['fuel_heating_value'] -
                                euval['char_mass_' + phase] * euval['char_heating_value']) * 1000
                except KeyError:
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / euval['fuel_mass_' + phase] * euval[
                            'fuel_EHV_' + phase]  # Fuel EHV includes char
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase}, fuel_mass_wo_char_{phase}, or fuel_EHV_{phase} is" \
                               f"not a number. {name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                except TypeError:
                    pmetric[name] = ''
                    line = f"{species}_total_mass_{phase}, fuel_mass_{phase}, fuel_heating_value," \
                           f"char_mass_{phase}, or char_heating_value is" \
                           f"not a number. {name}_{phase} was left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')

                # emission factor useful energy delivered
                name = species + '_useful_eng_deliver'
                pmetricnames.append(name)
                if species == 'PM':
                    metricunits[name] = 'mg/MJ'
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / euval[
                            'useful_energy_delivered_' + phase] * 1000 * 1000
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase} or useful_energy_delivered_{phase} is not a number." \
                               f"{name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                else:
                    metricunits[name] = 'g/MJ'
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / euval[
                            'useful_energy_delivered_' + phase] * 1000
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase} or useful_energy_delivered_{phase} is not a number." \
                               f"{name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')

                # emission rate
                name = species + '_mass_time'
                pmetricnames.append(name)
                if species == 'PM':
                    metricunits[name] = 'mg/min'
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / len(data['time']) / sample_period * 60 * 1000
                        name = species + '_heat_mass_time'
                        pmetricnames.append(name)
                        metricunits[name] = 'g/hr'
                        pmetric[name] = pmetric[species + '_total_mass'] / len(data['time']) / sample_period * 60 * 60
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase} is not a number. {name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                else:
                    metricunits[name] = 'g/min'
                    try:
                        pmetric[name] = pmetric[species + '_total_mass'] / len(data['time']) / sample_period * 60
                    except TypeError:
                        pmetric[name] = ''
                        line = f"{species}_total_mass_{phase} is not a number. {name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')

            # Carbon emission rate
            name = 'C_mass_time'
            pmetricnames.append(name)
            metricunits[name] = 'g/min'
            try:
                pmetric[name] = pmetric['CO2v_mass_time'] * MW['C'] / MW['CO2v'] + pmetric['CO_mass_time'] * MW['C'] / \
                                MW['CO']
            except KeyError:
                pmetric[name] = pmetric['CO2_mass_time'] * MW['C'] / MW['CO2'] + pmetric['CO_mass_time'] * MW['C'] / MW[
                    'CO']

            # Emission factor
            for species in emissions:
                ERname = species + '_mass_time'
                name = species + '_EF'
                pmetricnames.append(name)
                metricunits[name] = 'g/kg_C'  # gram per kilogram carbon
                if species == 'PM':
                    pmetric[name] = (pmetric[ERname] / 1000) / (
                                pmetric['C_mass_time'] / 1000)  # mg/min to g/min, g/min tp kg/min
                else:
                    pmetric[name] = pmetric[ERname] / (pmetric['C_mass_time'] / 1000)  # g/min to kg/min

            name = 'firepower_carbon'
            pmetricnames.append(name)
            metricunits[name] = 'W'
            try:
                pmetric[name] = sum(data['firepower_carbon']) / len(data['firepower_carbon'])
            except TypeError:
                pmetric[name] = ''
                line = f"Could not sum time series data for firepower_carbon. {name}_{phase} was left blank."
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            # add phase identifier to metric names
            for name in pmetricnames:  # for each metric calculated for the phase
                metricname = name + '_' + phase  # add the phase identifier to the variable name
                metric[metricname] = pmetric[name]
                metricunits[metricname] = metricunits[name]
                metricnames.append(
                    metricname)  # add the new full variable name to the list of variables that will be output

            ###################################################
            # carbon in
            name = 'carbon_in_' + phase
            metricnames.append(name)
            metricunits[name] = 'g'
            try:
                if emetrics['final_char_mass_' + phase] != '':  # if char was entered in old data sheet
                    try:
                        metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_mass_' + phase])
                                        - 0.81 * float(emetrics['char_mass_' + phase])) * 1000
                    except KeyError:
                        metric[name] = (0.5 * float(emetrics['fuel_mass_' + phase]) - 0.81 *
                                        float(emetrics['char_mass_' + phase])) * 1000
                        line = 'Used assumed wood carbon fraction of 0.5 g/g for carbon in calculations'
                        print(line)
                        logs.append(line)
                    except TypeError:
                        metric[name] = ''
                        line = f"fuel_Cfrac_{phase}, fuel_mass_{phase}, or char_mass_{phase} is not a number." \
                               f" {name}_{phase} was left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
                else:
                    try:
                        metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_mass_' + phase])) \
                                       * 1000
                    except KeyError:
                        metric[name] = (0.5 * float(emetrics['fuel_mass_' + phase])) * 1000
                        line = 'Used assumed wood carbon fraction of 0.5 g/g for carbon in calculations'
                        print(line)
                        logs.append(line)
                    except TypeError:
                        metric[name] = ''
                        line = f"fuel_Cfrac_{phase} or fuel_mass_{phase} is not a number. {name}_{phase} was " \
                               f"left blank."
                        logger.error(line)
                    except Exception as e:
                        logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                     f'{sys.exc_info()[2].tb_lineno}')
            except KeyError:  # new spreadsheet considers charcoal as a multi-fuel input
                try:
                    metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(
                        emetrics['fuel_mass_' + phase])) * 1000  # kg to g
                except TypeError:
                    metric[name] = ''
                    line = f"fuel_Cfrac_{phase} or fuel_mass_{phase} is not a number. {name}_{phase} was left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
            # carbon out
            name = 'carbon_out_' + phase
            metricnames.append(name)
            metricunits[name] = 'g'
            try:  # this needs an expection for SB with only CO2 sensor
                metric[name] = (
                            metric['CO_total_mass_' + phase] * MW['C'] / MW['CO'] + metric['CO2v_total_mass_' + phase] *
                            MW['C'] / MW['CO2v'] + 0.91 * metric['PM_total_mass_' + phase])
            except KeyError:
                try:
                    metric[name] = (metric['CO_total_mass_' + phase] * MW['C'] / MW['CO'] + metric[
                        'CO2_total_mass_' + phase] * MW['C'] / MW['CO2'] + 0.91 * metric['PM_total_mass_' + phase])
                except TypeError:
                    metric[name] = ''
                    line = f"CO_total_mass_{phase}, CO2_total_mass_{phase}, or PM_total_mass_{phase} is not a" \
                           f"number. {name} was left blank."
                    logger.error(line)
                except Exception as e:
                    logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                                 f'{sys.exc_info()[2].tb_lineno}')
            except TypeError:
                metric[name] = ''
                line = f"CO_total_mass_{phase}, CO2_total_mass_{phase}, or PM_total_mass_{phase} is not a" \
                       f"number. {name} was left blank."
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

            # carbon out/in
            name = 'C_Out_In_' + phase
            metricnames.append(name)
            metricunits[name] = 'g/g'
            try:
                metric[name] = metric['carbon_out_' + phase] / metric['carbon_in_' + phase]
            except TypeError:
                metric[name] = ''
                line = f"carbon_out or carbon_in is not a number. {name} was left blank"
                logger.error(line)
            except Exception as e:
                logger.error(f'Unexpected error calculating {name}: {str(e)} at line '
                             f'{sys.exc_info()[2].tb_lineno}')

    ###########################################
    # ISO weighted metrics
    existing_weight_phases = []
    weighted_metrics = ['CO_useful_eng_deliver', 'PM_useful_eng_deliver', 'PM_mass_time', 'PM_heat_mass_time',
                        'CO_mass_time']

    for phase in phases:
        name = 'weight_' + phase
        try:
            if emetrics[name].n != '':
                existing_weight_phases.append(phase)
        except AttributeError:
            if emetrics[name] != '':
                existing_weight_phases.append(phase)

    for name in weighted_metrics:
        weight_name = name + '_weighted'
        metricnames.append(weight_name)
        try:
            metricunits[weight_name] = metricunits[name + '_hp']
        except KeyError:
            try:
                metricunits[weight_name] = metricunits[name + '_mp']
            except KeyError:
                try:
                    metricunits[weight_name] = metricunits[name + '_lp']
                except KeyError:
                    try:
                        metricunits[weight_name] = metricunits[name + '_L1']
                    except KeyError:
                        metricunits[weight_name] = metricunits[name + '_L5']

        metric[weight_name] = ufloat(0, 0)
        for phase in existing_weight_phases:
            phase_name = name + '_' + phase
            try:
                metric[weight_name] = metric[weight_name] + (metric[phase_name] * euval['weight_' + phase]) / \
                                      euval['weight_total']
            except (KeyError, ValueError):
                pass

    if metric['CO_useful_eng_deliver_weighted'].n != 0:
        name = 'tier_CO_useful_eng_deliver'
        metricnames.append(name)
        metricunits[name] = ''
        metric[name] = 'nan'
        if metric['CO_useful_eng_deliver_weighted'].n > 18.3:
            metric[name] = 'Tier 0'
        elif 18.3 >= metric['CO_useful_eng_deliver_weighted'].n > 11.5:
            metric[name] = 'Tier 1'
        elif 11.5 >= metric['CO_useful_eng_deliver_weighted'].n > 7.2:
            metric[name] = 'Tier 2'
        elif 7.2 >= metric['CO_useful_eng_deliver_weighted'].n > 4.4:
            metric[name] = 'Tier 3'
        elif 4.4 >= metric['CO_useful_eng_deliver_weighted'].n > 3:
            metric[name] = 'Tier 4'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 3:
            metric[name] = 'Tier 5'

    if metric['PM_useful_eng_deliver_weighted'].n != 0:
        name = 'tier_PM_useful_eng_deliver'
        metricnames.append(name)
        metricunits[name] = ''
        metric[name] = 'nan'
        if metric['PM_useful_eng_deliver_weighted'].n > 1030:
            metric[name] = 'Tier 0'
        elif 1030 >= metric['PM_useful_eng_deliver_weighted'].n > 481:
            metric[name] = 'Tier 1'
        elif 481 >= metric['PM_useful_eng_deliver_weighted'].n > 218:
            metric[name] = 'Tier 2'
        elif 218 >= metric['PM_useful_eng_deliver_weighted'].n > 62:
            metric[name] = 'Tier 3'
        elif 62 >= metric['PM_useful_eng_deliver_weighted'].n > 5:
            metric[name] = 'Tier 4'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 5:
            metric[name] = 'Tier 5'

    # print phase metrics output file
    io.write_constant_outputs(emisoutputpath, metricnames, metricunits, metricval, metricunc, metric)

    line = 'Created emission metrics output file: ' + emisoutputpath
    print(line)
    logger.info(line)
    logs.append(line)

    # print all metrics output file (energy, grav, emissions)    ######################
    # add the energy outputs
    for name in enames:
        allnames.append(name)
        allunits[name] = eunits[name]
        allval[name] = emetrics[name]
        allunc[name] = eunc[name]

    # add the grav outputs, if they are present
    if pmetric['MSC'] != emval['MSC_default']:
        for name in gravnames[1:]:  # skip first line because it is the header
            allnames.append(name)
            allunits[name] = gravunits[name]
            allval[name] = gravmetrics[name]
            allunc[name] = gravunc[name]

    # add emissions outputs
    for name in metricnames[1:]:  # skip first line because it is the header
        allnames.append(name)
        allunits[name] = metricunits[name]
        allval[name] = metricval[name]
        allunc[name] = metricunc[name]
        alluval[name] = metric[name]

    # add lems averages outputs
    for name in metricnamesall[1:]:  # skip first line because it is the header
        allnames.append(name)
        allunits[name] = metricunits[name]
        allval[name] = metricval[name]
        allunc[name] = metricunc[name]
        alluval[name] = metric[name]

    # average other sensors by phase and add to alloutputs
    timenames, timeunits, timeval, timeunc, timeuval = io.load_constant_inputs(timespath)

    sensorpaths = []
    # Read in additional sensor data and add it to dictionary
    if os.path.isfile(fuelpath):
        sensorpaths.append(fuelpath)

    if os.path.isfile(fuelmetricpath):
        sensorpaths.append(fuelmetricpath)

    if os.path.isfile(exactpath):
        sensorpaths.append(exactpath)

    if os.path.isfile(scalepath):
        sensorpaths.append(scalepath)

    if os.path.isfile(nanopath):
        sensorpaths.append(nanopath)

    if os.path.isfile(TEOMpath):
        sensorpaths.append(TEOMpath)

    if os.path.isfile(senserionpath):
        sensorpaths.append(senserionpath)

    if os.path.isfile(OPSpath):
        sensorpaths.append(OPSpath)

    if os.path.isfile(Picopath):
        sensorpaths.append(Picopath)

    # phases.remove('full')

    for path in sensorpaths:
        try:
            [snames, sunits, sdata] = io.load_timeseries(path)

            name = 'dateobjects'
            snames.append(name)
            sunits[name] = 'date'
            sdata[name] = []
            for n, val in enumerate(sdata['time']):
                try:
                    dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
                except ValueError:
                    dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
                sdata[name].append(dateobject)

            name = 'datenumbers'
            snames.append(name)
            sunits[name] = 'date'
            sdatenums = matplotlib.dates.date2num(sdata['dateobjects'])
            sdatenums = list(sdatenums)
            sdata[name] = sdatenums

            samplerate = sdata['seconds'][1] - sdata['seconds'][0]  # find sample rate
            date = data['time'][0][0:8]

            for phase in phases:
                start = timeval['start_time_' + phase]
                end = timeval['end_time_' + phase]

                if start != '':
                    if len(start) < 10:
                        start = date + ' ' + start
                        end = date + ' ' + end
                    try:
                        startdateobject = dt.strptime(start, '%Y%m%d %H:%M:%S')
                    except ValueError:
                        startdateobject = dt.strptime(start, '%Y-%m-%d %H:%M:%S')
                    try:
                        enddateobject = dt.strptime(end, '%Y%m%d %H:%M:%S')
                    except ValueError:
                        enddateobject = dt.strptime(end, '%Y-%m-%d %H:%M:%S')

                    phasedata = {}
                    for name in snames:
                        try:
                            phasename = name + '_' + phase
                            m = 1
                            ind = 0
                            while m <= samplerate + 1 and ind == 0:
                                try:
                                    startindex = sdata['dateobjects'].index(startdateobject)
                                    ind = 1
                                except (ValueError, IndexError):
                                    startdateobject = startdateobject + timedelta(seconds=1)
                                    m += 1
                            m = 1
                            ind = 0
                            while m <= samplerate + 1 and ind == 0:
                                try:
                                    endindex = sdata['dateobjects'].index(enddateobject)
                                    ind = 1
                                except (ValueError, IndexError):
                                    enddateobject = enddateobject + timedelta(seconds=1)
                                    m += 1

                            phasedata[phasename] = sdata[name][startindex:endindex + 1]

                            if 'seconds' in name:
                                phaseaverage = phasedata[phasename][-1] - phasedata[phasename][0]
                                allnames.append(phasename)
                                allunits[phasename] = sunits[name]
                                allval[phasename] = phaseaverage
                                allunc[phasename] = ''
                                alluval[phasename] = ''
                            elif 'TC' in name:
                                phaseaverage = sum(phasedata[phasename]) / len(phasedata[phasename])
                                allnames.append('S' + phasename)
                                allunits['S' + phasename] = sunits[name]
                                allval['S' + phasename] = phaseaverage
                                allunc['S' + phasename] = ''
                                alluval['S' + phasename] = ''
                            elif 'time' not in name and 'date' not in name:
                                phaseaverage = sum(phasedata[phasename]) / len(phasedata[phasename])
                                allnames.append(phasename)
                                allunits[phasename] = sunits[name]
                                allval[phasename] = phaseaverage
                                allunc[phasename] = ''
                                alluval[phasename] = ''
                        except ValueError:
                            phaseaverage = ''
                            allnames.append(phasename)
                            allunits[phasename] = sunits[name]
                            allval[phasename] = phaseaverage
                            allunc[phasename] = ''
                            alluval[phasename] = ''
            line = 'Added sensor data from: ' + path + 'to: ' + alloutputpath
            print(line)
            logger.info(line)
            logs.append(line)
        except UnboundLocalError:
            message = 'Data from: ' + path + ' could not be cut to the same time as sensorbox data.'
            print(message)
            logger.error(line)
            logs.append(message)

    if os.path.isfile(bcoutputpath):
        [bcnames, bcunits, bcvals, bcunc, bcuval] = io.load_constant_inputs(bcoutputpath)
        for name in bcnames:
            allnames.append(name)
            allunits[name] = bcunits[name]
            allval[name] = bcvals[name]

        line = 'Added black carbon data from: ' + bcoutputpath
        print(line)
        logs.append(line)
        logger.info(line)

    io.write_constant_outputs(alloutputpath, allnames, allunits, allval, allunc, alluval)
    line = 'Created all metrics output file: ' + alloutputpath
    print(line)
    logger.info(line)
    logs.append(line)

    #############################################################
    # create a full timeseries with metrics
    combined_names = []
    combined_units = {}
    combined_data = {}
    # compile full timeseries file
    for phase in phases:
        # read in time series data file
        phaseinputpath = inputpath[:-4] + 'Metrics_' + phase + '.csv'

        if os.path.isfile(phaseinputpath):  # check that time series path exists
            [names, units, data] = io.load_timeseries(phaseinputpath)

            # combine names, units, and data
            for name in names:
                if name not in combined_names:
                    combined_names.append(name)
                    combined_units[name] = units[name]
                if name in combined_data:
                    combined_data[name] += data[name]  # Append to existing data if name already exists
                else:
                    combined_data[name] = data[name]  # Initialize  data if name is new

    # output time series data file
    phaseoutputpath = inputpath[
                      :-4] + 'Metrics_full.csv'  # name the output file by removing 'Data.csv' and inserting
    # 'Metrics' and the phase name into inputpath
    io.write_timeseries_without_uncertainty(phaseoutputpath, combined_names, combined_units, combined_data)

    line = 'Created phase time series data file with processed emissions for all phases: ' + phaseoutputpath
    print(line)
    logger.info(line)
    logs.append(line)

    end_time = dt.now()
    log = f"Execution time: {end_time - start_time}"
    print(log)
    logger.info(log)
    logs.append(log)
    return logs, metricval, metricunits


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_EmissionCalcs_ISO(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath, logger,
                           timespath, versionpath, fuelpath, fuelmetricpath, exactpath, scalepath, nanopath, TEOMpath,
                           senserionpath, OPSpath, Picopath, emissioninputpath, inputmethod, bcoutputpath)
