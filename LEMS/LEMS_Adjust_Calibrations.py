# v1 Python3

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

import os
import numpy as np
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
from LEMS_3015 import LEMS_3015
import subprocess
try:
    from LEMS_RedoFirmwareCalcs import RedoFirmwareCalcs
except ImportError:
    from LEMS.LEMS_RedoFirmwareCalcs import RedoFirmwareCalcs
try:
    from PEMS_2041 import PEMS_2041
except ImportError:
    from LEMS.PEMS_2041 import PEMS_2041
try:
    from LEMS_3002 import LEMS_3002
except ImportError:
    from LEMS.LEMS_3002 import LEMS_3002
try:
    from LEMS_3001 import LEMS_3001
except ImportError:
    from LEMS.LEMS_3001 import LEMS_3001
try:
    from LEMS_3009 import LEMS_3009
except ImportError:
    from LEMS.LEMS_3009 import LEMS_3009
try:
    from LEMS_Possum2 import LEMS_Possum2
except ImportError:
    from LEMS.LEMS_Possum2 import LEMS_Possum2

# inputs (which files are being pulled and written) #############
inputpath = 'foldername_RawData.csv'  # read
versionpath = 'foldername_SensorboxVersion.csv'  # read/write
outputpath = 'RawData_Recalibrated.csv'  # write
headerpath = 'header.csv'  # write/read
logger = 'logging Python package'
inputmethod = '0'  # (non-interactive) or 1 (interactive)
##########################################


def LEMS_Adjust_Calibrations(inputpath, versionpath, outputpath, headerpath, logger, inputmethod):

    # Function purpose: load in raw data, create a header, allow user to edit calibration parameters in header, reformat
    # raw data to a uniform script, recalculate data to proper units, perform firmware calibrations

    # Inputs:
    # Raw data file from LEMS 3000 or 4000 series
    # Sensorbox version file (if existant)
    # Python logging function
    # Inputmethod: 0 (non-interactive) or 1 (interactive)

    # Outputs:
    # Uniform raw data file with no logunits and calibrated numbers, header with calibration numbers
    # Sensorbox version file
    # Header file with stored, chanagable calibration constants
    # logs: list of important events

    # Called by: LEMS_DataEntry_IDC_L1, LEMS_DataEntry_IDC_L2, LEMS_DataEntry_L1, LEMS_DataEntry_L2,
    # LEMSDataCruncher_IDC, LEMSDataCruncher_ISO, LEMSDataCrucnher_L2, LEMSDataCruncher_L2_ISO

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
    
    #################################################
    try:
        # read in raw data file with header if it exists
        [names, units, data_old, A_old, B_old, C_old, D_old, const_old, version] = \
            io.load_timeseries_with_header(inputpath)
        ##############################################
        # check for header input file
        if os.path.isfile(headerpath):
            line = f'Header file already exists: {headerpath}'
            print(line)
            logger.info(line)
            logs.append(line)
        else:   # if header file is not there then create it by printing the existing header from raw data file
            io.write_header(headerpath, names, units, A_old, B_old, C_old, D_old)
            line = f'Header file created: {headerpath}'
            print(line)
            logger.info(line)
            logs.append(line)

        if inputmethod == '1':  # Only show in interactive mode
            # give instructions
            line = f'Open the Header input file and edit the desired calibration parameters if needed:\n\n' \
                 f'{headerpath}\n\n' \
                 f'Save and close the Header input file then click OK to continue'
            msgtitle = 'Edit Header'
            easygui.msgbox(msg=line, title=msgtitle)

        # open header file and read in new cal params
        [names_new, units_new, A_new, B_new, C_new, D_new, const_new] = io.load_header(headerpath)
    except (FileNotFoundError, ImportError):
        version = ''
        if not os.path.isfile(inputpath):  # test to check that input exists
            raise FileNotFoundError
    ###########################################################

    # check sensorbox version
    vnames = []
    vunits = {}
    vval = {}
    vunc = {}
    vuval = {}
    if os.path.isfile(versionpath):
        [vnames, vunits, vval, vunc, vuval] = io.load_constant_inputs(versionpath)  # Load sensor version

    if 'SB' in vnames:  # if SB was selected before, make selection new default
        firmware_version = vval['SB']
    else:
        if version != 0:
            firmware_version = version  # try to grab version from header
        else:
            # define firmware version for recalculations
            firmware_version = 'SB4003.16'  # default if nothing was entered before

    default_firmware_version = 'SB4003.16'

    if inputmethod == '1':  # Only show in interactive mode
        # Ask user for sensor box version
        msgstring = f'Enter sensorbox firmware version. \n\n' \
                    f'Firmware version may be found labeled on the box or printed in the data under version.\n\n' \
                    f'Current supported software versions are: SB4003, SB4005, SB4007, SB4008, SB2041, SB3001, ' \
                    f'SB3002, SB3009, SB3015, SB3016, Possum2. \n\n' \
                    f'Entering an unsuported firmware will not recalibrate the data and may lead to errors down the ' \
                    f'line.\n\n'
        boxtitle = 'Enter Version'
        entered_firmware_version = easygui.enterbox(msg=msgstring, title=boxtitle, default=firmware_version, strip=True)
        if entered_firmware_version != firmware_version:  # if a new SB was selected
            if 'SB' in vnames:  # check if SB was previously assigned
                vval['SB'] = entered_firmware_version
            else:  # write new values to energy outputs
                name = 'SB'
                vnames.append(name)
                vunits[name] = ''
                vval[name] = entered_firmware_version
            ######################################################
        else:
            name = 'SB'
            vnames.append(name)
            vunits[name] = ''
            vval[name] = firmware_version
        # make output file
        io.write_constant_outputs(versionpath, vnames, vunits, vval, vunc, vuval)

        line = f'Sensor box version for recalibration: {firmware_version}'
        print(line)
        logger.info(line)
        logs.append(line)

    elif inputmethod == '2':  # In reprocessing mode, use last selected SB
        entered_firmware_version = firmware_version
        line = f'Sensor box version for recalibration: {firmware_version}'
        print(line)
        logger.info(line)
        logs.append(line)
    if entered_firmware_version == default_firmware_version or '4003' in entered_firmware_version or \
            '4005' in entered_firmware_version or '4008' in entered_firmware_version or \
            '4002' in entered_firmware_version or '4007 ':
        firmware_version = entered_firmware_version #Only runs adjustments for SB4003.16 currently. Passes for any other SB
    
        line = 'firmware_version='+firmware_version  # add to log
        print(line)
        logs.append(line)

        ############################################################
        # redo firmware calculations
        [data_new, add_logs] = RedoFirmwareCalcs(names, A_old, B_old, const_old, data_old, A_new, B_new, const_new,
                                                 units, logger)
        logs = logs + add_logs

        ###############################################################
        # document which parameters were changed
        for name in names:
            if A_old[name] != A_new[name] and not np.isnan(A_old[name]) and not np.isnan(A_new[name]):
                line = f'{name}: A old = {A_old[name]}, A new = {A_new[name]}'
                print(line)
                logger.info(line)
                logs.append(line)
            if B_old[name] != B_new[name] and not np.isnan(B_old[name]) and not np.isnan(B_new[name]):
                line = f'{name}: B old = {B_old[name]}, B new = {B_new[name]}'
                print(line)
                logger.info(line)
                logs.append(line)
            # C and D are not currently handled in Redo Firmware Calcs
            # if D_old[name] != D_new[name] and not np.isnan(D_old[name]) and not np.isnan(D_new[name]):
                # line = f'Constant: {C_old[name]}: D old = {D_old[name]}, D new = {D_new[name]}'
                # print(line)
                # logger.info(line)
                # logs.append(line)

        ###############################################################
        # print updated time series data file
        io.write_timeseries(outputpath, names, units, data_new)

        line = f'Created: {outputpath}'  # add to log
        print(line)
        logger.info(line)
        logs.append(line)

    ######################################################
    # For other sensorbox versions, the data will need to be recalibrated and rewritten to a standardized format
    elif '2041' in entered_firmware_version:
        add_logs = PEMS_2041(inputpath, outputpath, headerpath, logger)
        logs = logs + add_logs
    elif '3002' in entered_firmware_version:
        add_logs = LEMS_3002(inputpath, outputpath, headerpath, logger)
        logs = logs + add_logs
    elif '3001' in entered_firmware_version:
        LEMS_3001(inputpath, outputpath, logpath)
    elif '3009' in entered_firmware_version:
        LEMS_3009(inputpath, outputpath, logpath)
        add_logs = LEMS_3001(inputpath, outputpath, headerpath, logger)
        logs = logs + add_logs
    elif '3015' in entered_firmware_version or '3016' in entered_firmware_version:
        add_logs = LEMS_3015(inputpath, outputpath, headerpath, logger)
        logs = logs + add_logs
    elif entered_firmware_version == 'POSSUM2' or entered_firmware_version == 'Possum2' or \
            entered_firmware_version == 'possum2':
        add_logs = LEMS_Possum2(inputpath, outputpath, headerpath, logger)
        logs = logs + add_logs
    else:  # if entered firmware version isn't a supported version
        line = f'Firmware version: {entered_firmware_version} does not currently exist as a recalibration version, ' \
               f'nothing was recalibrated\n' \
               f'Current supported firmware versions: SB4003, SB4005, SB4007, SB4008, SB2041, SB3001, SB3002, SB3009,' \
               f' SB3015, SB3016, Possum2'
        print(line)
        logger.error(line)
        logs.append(line)

        ###############################################################
        # Load in raw data and print it out as the same data
        try:
            [names, units, data_old, A_old, B_old, C_old, D_old, const_old] = io.load_timeseries_with_header(inputpath)
        except (TypeError, ValueError):
            [names, units, data_old] = io.load_timeseries(inputpath)

        # print time series data file
        io.write_timeseries(outputpath, names, units, data_old)

        line = f'Created: {outputpath} with no recalibrated values'  # add to log
        print(line)
        logger.info(line)
        logs.append(line)

    end_time = dt.now()
    log = f"Execution time: {end_time - start_time}"
    print(log)
    logger.info(log)
    logs.append(log)

    return logs, entered_firmware_version

#######################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_Adjust_Calibrations(inputpath, versionpath, outputpath, headerpath, logger, inputmethod)

    