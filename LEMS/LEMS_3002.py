#v0.2 Python3

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

import csv
from datetime import datetime, timedelta
from datetime import  datetime as dt
import LEMS_DataProcessing_IO as io

##################____Inputs________###############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#Raw data input file
inputpath = "C:\\Users\\Jaden\\Documents\\Test\\3002\\3002_RawData.csv"
#Created output
outputpath = 'C:\\Users\\Jaden\\Documents\\Test\\3002\\3002_RawData_Recalibrated.csv'
#log
logpath = 'C:\\Users\\Jaden\\Documents\\Test\\3002\\3002_log.txt'
#################################################

def LEMS_3002(Inputpath, outputpath, logpath):

    # This function was made for LEMS sensor box 3002. Raw data from SB is taken in and reformatted into a readable
    # Format for the rest of the functions to take in

    ver = '0.2' # Updated for high-performance loading

    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_3002 v'+ver+'   '+timestampstring #add to log
    print(line)
    logs=[line]

    line = 'firmware version = 3002, reformatting raw data input'
    print(line)
    logs.append(line)

    # --- HIGH PERFORMANCE DATA LOAD ---
    # This call replaces the manual 'stuff' list and multiple loops.
    # It automatically handles "port in use" and empty lines.
    try:
        names, units, data, A, B, C, D, const, version = io.load_timeseries_with_header(Inputpath, logpath)
        # In 3002 files, the '# 0' row contains the multipliers.
        # Our function maps '# 0' to the 'A' dictionary.
        multi = A
        logs.append(f"Successfully loaded {len(data['seconds'])} rows from {Inputpath}")
    except Exception as e:
        logs.append(f"Critical Load Error: {e}")
        io.write_logfile(logpath, logs)
        return logs



    metric = {} #Recalcualted corrected data. Key is names

    #FOR MORE CHANNELS, CHANGE HERE - NAMES MUST MATCH NAMES FROM LEMS 4003 DATA - NAME ORDER IS HOW COLUMNS ARE WRITTEN
    names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'COtemp', 'TC1', 'dP2', 'O2_1', 'O2_2', 'O2_3', 'O2_4'] #New list for names

    scat_eff = 3

    # --- CHANNEL CALCULATIONS & CORRECTED MAPPING ---
    # We map the raw 'data' dictionary into our 'metric' dictionary using 3002-specific logic.
    for name in names_new:
        if name == 'time':
            continue

        # Determine which raw data key corresponds to the new name
        raw_key = name  # Default
        if name == 'CO':
            raw_key = 'co'
        elif name == 'CO2':
            raw_key = 'co2'
        elif name == 'PM':
            raw_key = 'pm'
        elif name == 'Flow':
            raw_key = 'flue flow'
        elif name == 'FLUEtemp':
            raw_key = 'flue T'
        elif name == 'COtemp':
            raw_key = 'gas T'
        elif name == 'H2Otemp':
            raw_key = 'tc h2o'
        elif name == 'TC1':
            raw_key = 'tc pitot'
        elif name == 'dP2':
            raw_key = 'flow pito'
        elif name == 'O2_1':
            raw_key = 'O2 ch1'
        elif name == 'O2_2':
            raw_key = 'O2 ch2'
        elif name == 'O2_3':
            raw_key = 'O2 ch3'
        elif name == 'O2_4':
            raw_key = 'O2 ch4'

        # Process values with multipliers where applicable
        if raw_key in data:
            if name == 'CO':
                metric[name] = [val * multi.get('co', 1) if isinstance(val, (int, float)) else val for val in
                                data['co']]
            elif name == 'CO2':
                metric[name] = [val * multi.get('co2', 1) if isinstance(val, (int, float)) else val for val in
                                data['co2']]
            elif name == 'PM':
                metric[name] = [val * multi.get('pm', 1) * scat_eff if isinstance(val, (int, float)) else val for val in
                                data['pm']]
            elif name == 'Flow':
                metric[name] = [val * 25.4 if isinstance(val, (int, float)) else val for val in data['flue flow']]
            elif name == 'FLUEtemp':
                metric[name] = [val * multi.get('flue T', 1) if isinstance(val, (int, float)) else val for val in
                                data['flue T']]
            elif name == 'dP2':
                metric[name] = [val * 25.4 if isinstance(val, (int, float)) else val for val in data['flow pito']]
            else:
                # Direct mapping for non-multiplied channels
                metric[name] = data[raw_key]
        else:
            # Handle missing channels by filling with 'nan' or 0
            metric[name] = ['nan'] * len(data.get('seconds', []))

    # --- TIME SYNCHRONIZATION ---
    # Peek at header for start time and date since 'stuff' is no longer in memory.
    start_time_str = ""
    date_str = ""
    with open(Inputpath, 'r') as f:
        reader = csv.reader(f)
        header_peek = [next(reader) for _ in range(50)]
        for i, row in enumerate(header_peek):
            if row and row[0] == '#headers: ':
                start_time_str = header_peek[i - 1][1]
                date_str = header_peek[i - 2][1]

    try:
        # Formatting date
        x = date_str.replace("-", "/").split("/")
        if len(x[0]) == 1: x[0] = '0' + x[0]
        if len(x[1]) == 1: x[1] = '0' + x[1]

        # Determine if format is YYYYMMDD or MMDDYYYY
        if len(x[0]) == 4:
            date_clean = x[0] + x[1] + x[2]
        else:
            date_clean = x[2] + x[0] + x[1]

        base_dt = datetime.strptime(date_clean + ' ' + start_time_str, '%Y%m%d %H:%M:%S')

        # Generate reformatted time strings
        metric['time'] = [str(base_dt + timedelta(seconds=s)).replace("-", "") for s in data['seconds']]
        units['time'] = 'yyyymmdd hhmmss'
    except Exception as e:
        logs.append(f"Warning: Time synchronization failed: {e}")

    # Assign hardcoded units
    units.update({
        'seconds': 's', 'CO': 'ppm', 'CO2': 'ppm', 'PM': 'Mm^-1',
        'Flow': 'mmH2O', 'FLUEtemp': 'C', 'H2Otemp': 'C', 'RH': '%',
        'COtemp': 'C', 'TC1': 'C', 'dP2': 'mmH2O',
        'O2_1': 'lambda', 'O2_2': 'lambda', 'O2_3': 'lambda', 'O2_4': 'lambda'
    })

    ######################################################################
    # Write cut data to outputpath - Data isn't recalibrated just named that for next steps
    io.write_timeseries(outputpath, names_new, units, metric)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    ##############################################
    #print to log file
    io.write_logfile(logpath,logs)

    #######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_3002(inputpath,outputpath, logpath)



