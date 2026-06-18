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

import csv
import os.path
from datetime import datetime as dt
from datetime import datetime, timedelta

import easygui
import math

import LEMS_DataProcessing_IO as io

inputpath = "/Users/user/Documents/stove_tests_CURRENT/ecosafi 2026/big pot 10241033-34/06.16.26C/06.16.26C_EcosafiRawData.csv"
outputpath = "/Users/user/Documents/stove_tests_CURRENT/ecosafi 2026/big pot 10241033-34/06.16.26C/06.16.26C_FormattedEcosafiData.csv"
logpath = "/Users/user/Documents/stove_tests_CURRENT/ecosafi 2026/big pot 10241033-34/06.16.26C/06.16.26C_log.txt"

def LEMS_Ecosafi(inputpath, outputpath, seninputs, logpath, inputmethod):
    #Function takes in Ecosafi data and reformats to be readable for the rest of the program and adds total flow

    ver = '0.1'
    timestampobject = dt.now()
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Ecosafi v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    # --- UPDATED LOADING SECTION ---
    # Detect if the file is a clean CSV or has comment/calibration headers
    try:
        has_headers = False
        with open(inputpath, 'r', encoding='utf-8-sig') as f:
            for line_val in f:
                if line_val.strip().startswith('#'):
                    has_headers = True
                break
        
        if has_headers:
            names, units, data, A, B, C, D, const, f_ver = io.load_timeseries_with_header(inputpath, logpath)
        else:
            names = []
            units = {}
            data = {}
            A = {}
            B = {}
            C = {}
            D = {}
            const = {}
            f_ver = ''
            
            with open(inputpath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader)
                names = [col.strip().rstrip('\\') for col in header]
                for name in names:
                    units[name] = ''
                    data[name] = []
                    A[name] = None
                    B[name] = None
                    C[name] = None
                    D[name] = None
                
                for line_num, row in enumerate(reader, start=2):
                    if not row: continue
                    row_vals = [val.strip().rstrip('\\') for val in row]
                    if len(row_vals) < len(names):
                        logs.append(f"Line {line_num}: Skipped incomplete row")
                        continue
                    for n, name in enumerate(names):
                        val = row_vals[n]
                        try:
                            data[name].append(float(val))
                        except ValueError:
                            data[name].append(val)
    except Exception as e:
        error_msg = f"Critical Error loading file: {e}"
        print(error_msg)
        logs.append(error_msg)
        io.write_logfile(logpath, logs)
        return logs

    # We still need to find the specific computer vs sensor timestamps for offset if they exist
    computer = 0
    computertime = None
    sensortime = None

    if has_headers:
        # Quick peek at header for sync timestamps (prevents hanging on large files)
        with open(inputpath, 'r') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i > 100 or computer == 2: break
                if not row: continue

                if 'Timestamp' in row[0] and computer == 0:
                    parts = row[0].split(" ")
                    try:
                        ts = parts[2] if len(parts) > 2 else parts[1]
                        computertime = datetime.strptime(ts.strip(), "%Y%m%d%H%M%S")
                        computer = 1
                    except:
                        pass
                elif 'Timestamp' in row[0] and computer == 1:
                    parts = row[0].split(" ")
                    try:
                        sensortime = datetime.strptime(parts[1] + ' ' + parts[2], "%Y%m%d %H:%M:%S")
                        computer = 2
                    except:
                        pass

    flows = []
    temps = []
    pressures =  []
    idx = []
    for n, name in enumerate(names):
        if 'Flow' in name or 'RPM' in name:  # find flow channels
            flows.append(name)
            idx.append(n)
        if 'TC' in name or 'temp' in name or 'Temp' in name: # find temp channels
            temps.append(name)
        if 'deltaP' in name: # find temp channels
            pressures.append(name)

    # Check if flow and temperature assignment file exists
    if os.path.isfile(seninputs):
        [snames, sunits, sval, sunc, suval] = io.load_constant_inputs(seninputs)
        # Ensure time_offset is present in the loaded settings
        if 'time_offset' not in snames:
            name = 'time_offset'
            snames.append(name)
            sunits[name] = 'seconds'
            sval[name] = '0'
            sunc[name] = ''
            suval[name] = 0.0
            # Save the updated inputs file
            io.write_constant_outputs(seninputs, snames, sunits, sval, sunc, suval)
    else:
        snames = []  # list of variable names
        sunits = {}  # Dictionary of units, key is names
        sval = {}  # Dictionary of values, key is names
        sunc = {}  # Dictionary of uncertainties, key is names
        suval = {}  # Dictionary of values and uncertainties as ufloats, key is names

        # Make a header
        name = 'variable'
        snames.append(name)
        sunits[name] = 'units'
        sval[name] = 'value'

        for name in flows:
            snames.append(name)
            sunits[name] = 'Primary/Secondary'
            sval[name] = 'Primary'

            dia_name = f'{name}_dia'
            snames.append(dia_name)
            sunits[dia_name] = 'cm'
            sval[dia_name] = ''

            hole_name = f'{name}_num'
            snames.append(hole_name)
            sunits[hole_name] = 'number'
            sval[hole_name] = ''

        for name in temps:
            snames.append(name)
            sunits[name] = 'text'
            sval[name] = ''

        for name in pressures:
            snames.append(name)
            sunits[name] = 'text'
            sval[name] = ''

        # Add time_offset line
        name = 'time_offset'
        snames.append(name)
        sunits[name] = 'seconds'
        sval[name] = '0'
        sunc[name] = ''
        suval[name] = 0.0
        
        # Save the default inputs file
        io.write_constant_outputs(seninputs, snames, sunits, sval, sunc, suval)

    if inputmethod == '1':
        # Separate flow-related names and temp-related names
        flow_names = []
        temp_names = []
        for name in snames[1:]:  # skip header row
            if name == 'time_offset':
                flow_names.append(name)
            elif name in temps:
                temp_names.append(name)
            else:
                flow_names.append(name)

        # First popup: Flows
        flow_defaults = [sval[name] for name in flow_names]
        msg_flows = (
            "Designate fan flows as either Primary or Secondary to calculate total flows.\n"
            "Describe the hole diameter and number of holes to calculate velocity."
        )
        title_flows = 'Define Fans'
        new_flow_vals = easygui.multenterbox(msg_flows, title_flows, flow_names, values=flow_defaults)
        if not new_flow_vals:
            line = 'Error: Undefined variables in flow section'
            print(line)
            logs.append(line)
        else:
            for n, name in enumerate(flow_names):
                sval[name] = new_flow_vals[n]

        # Second popup: Temps
        temp_defaults = [sval[name] for name in temp_names]
        msg_temps = (
            "Describe the location of each thermocouple."
        )
        title_temps = 'Define Thermocouples'
        new_temp_vals = easygui.multenterbox(msg_temps, title_temps, temp_names, values=temp_defaults)
        if not new_temp_vals:
            line = 'Error: Undefined variables in temperature section'
            print(line)
            logs.append(line)
        else:
            for n, name in enumerate(temp_names):
                sval[name] = new_temp_vals[n]

        # Save both sets of updated values
        io.write_constant_outputs(seninputs, snames, sunits, sval, sunc, suval)
        line = f'Created/Updated sensor designation file: {seninputs}'
        print(line)
        logs.append(line)

    # Determine the time offset to use
    if computertime and sensortime:
        timeoffset = (computertime - sensortime).total_seconds()
    else:
        try:
            timeoffset = float(sval.get('time_offset', 0))
        except (ValueError, TypeError):
            timeoffset = 0.0

    # Apply time offset to the 'time' list in our data dictionary
    if has_headers:
        raw_times = data['time']  # These are the strings loaded by IO
        data['temptime'] = raw_times  # Keep compatibility with original script
        data['time'] = []
        for temptime in raw_times:
            try:
                convertedtime = datetime.strptime(temptime, '%Y%m%d %H:%M:%S')
                data['time'].append(convertedtime + timedelta(seconds=timeoffset))
            except:
                data['time'].append(None)
    else:
        raw_dates = data.get('Controller Date', [])
        raw_times = data.get('Controller Time', [])
        data['time'] = []
        
        # Ensure 'time' is the first column in the names list
        if 'time' not in names:
            names.insert(0, 'time')
            units['time'] = 'YYYY%m%d %H:%M:%S'
            
        for idx in range(len(raw_dates)):
            date_str = str(raw_dates[idx]).strip()
            time_str = str(raw_times[idx]).strip()
            try:
                # Format in raw file: date is 6/16/26, time is 10:53:30 AM
                convertedtime = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%y %I:%M:%S %p")
                data['time'].append(convertedtime + timedelta(seconds=timeoffset))
            except Exception:
                try:
                    # Fallback standard format
                    convertedtime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                    data['time'].append(convertedtime + timedelta(seconds=timeoffset))
                except Exception:
                    data['time'].append(None)

    # Calculate Primary flow
    name = 'PrimaryFlow'
    names.append(name)
    units[name] = units[flows[0]] if flows else ''
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if 'primary' in sval[flow].lower() and data[flow][n] != 999:
                # 999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)


    name = 'ave_temp'
    temp_results = []

    try:
        # Perform calculation into a local list first
        for n, _ in enumerate(data['time']):
            t1 = data.get('body_temp', data.get('TC1_bm x100', data.get('TC1_bm', [0]*len(data['time']))))[n]
            t2 = data.get('Chimney_T', data.get('TC2_tp x100', data.get('TC2_tp', [0]*len(data['time']))))[n]
            t3 = data.get('snorkel_T', data.get('TC_PCB', [0]*len(data['time'])))[n]
            aveT = (t1 + t2 + t3) / 3
            temp_results.append(aveT)

        # If we reached here, the calculation succeeded. Now "commit" the data.
        names.append(name)
        units[name] = 'degC'
        data[name] = temp_results

    except KeyError as e:
        print(f"Missing data column: {e}")
    except ZeroDivisionError:
        print("Error: Check your data for null values.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Calculate Secondary flow
    name = 'SecondaryFlow'
    names.append(name)
    units[name] = units[flows[0]] if flows else ''
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if 'secondary' in sval[flow].lower() and data[flow][n] != 999:
                sum = sum + data[flow][n]
        data[name].append(sum)

    name = 'TotalFlow' #caculate total from all sensors
    names.append(name)
    data[name] = []
    units[name] = units[flows[0]] if flows else ''
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if data[flow][n] != 999: #999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

    if 'Lambda' in data:
        name = 'SenO2Percent'
        names.append(name)
        data[name] = []
        units[name] = '%'
        for val in data['Lambda']:
            data[name].append((val - 1) / ((1/3) + 4.77 * val) * 100)
    else:
        print('lamda sensor not present')

    for name in flows:
        try:
            diameter = float(sval[f'{name}_dia'])
            number = float(sval[f'{name}_num'])
            area = ((math.pi * ((diameter /100) / 2) ** 2) * number)  # cm to m
            vel_name = f'{name}_velocity'
            names.append(vel_name)
            data[vel_name] = []
            units[vel_name] = 'm/s'
            for val in data[name]:
                flow = val / (1000 * 60) # LPM to m^3/s
                velocity = flow / area
                data[vel_name].append(velocity)

        except (ValueError, TypeError, KeyError):
            pass

    # write formatted data to output path
    io.write_timeseries(outputpath, names, units, data)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    return logs

# run function as executable if not called by another function
if __name__ == "__main__":
    seninputs = "/Users/user/Documents/UCET software/Data-Processing-Software/test/06.16.26A_EcosafiInputs.csv"
    inputmethod = '1'
    LEMS_Ecosafi(inputpath, outputpath, seninputs, logpath, inputmethod)
