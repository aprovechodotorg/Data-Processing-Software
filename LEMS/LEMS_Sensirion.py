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

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_SenserionRawData.txt"
outputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_FormattedSenserionData.csv"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\test\\test_log.txt"

def LEMS_Senserion(inputpath, outputpath, seninputs, logpath, inputmethod):
    #Function takes in senserion data and reformats to be readable for the rest of the program and adds total flow

    ver = '0.1'
    timestampobject = dt.now()
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Senserion v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    # --- UPDATED LOADING SECTION ---
    # This replaces your old 'with open' and 'for' loops.
    # It handles empty lines and "port in use" errors internally.
    try:
        # We catch the 10 variables returned by the updated IO function
        names, units, data, A, B, C, D, const, f_ver = io.load_timeseries_with_header(inputpath,logpath)
    except Exception as e:
        error_msg = f"Critical Error loading file: {e}"
        print(error_msg)
        logs.append(error_msg)
        io.write_logfile(logpath, logs)
        return logs

    # We still need to find the specific computer vs sensor timestamps for offset
    computer = 0
    computertime = None
    sensortime = None

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

    # Apply time offset to the 'time' list in our data dictionary
    if computertime and sensortime:
        timeoffset = (computertime - sensortime).total_seconds()
        raw_times = data['time']  # These are the strings loaded by IO
        data['temptime'] = raw_times  # Keep compatibility with your original script
        data['time'] = []
        for temptime in raw_times:
            try:
                convertedtime = datetime.strptime(temptime, '%Y%m%d %H:%M:%S')
                data['time'].append(convertedtime + timedelta(seconds=timeoffset))
            except:
                data['time'].append(None)
    flows = []
    temps = []
    idx = []
    for n, name in enumerate(names):
        if 'Flow' in name:  # find flow channels
            flows.append(name)
            idx.append(n)
        if 'TC' in name: # fine temp channels
            temps.append(name)

    # Check if flow and temperature assignment file exists
    if os.path.isfile(seninputs):
        [snames, sunits, sval, sunc, suval] = io.load_constant_inputs(seninputs)
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

    if inputmethod == '1':
        # Separate flow-related names and temp-related names
        flow_names = []
        temp_names = []
        for name in snames[1:]:  # skip header row
            if name in temps:
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
        line = f'Created sensor designation file: {seninputs}'
        print(line)
        logs.append(line)

    # Calculate Primary flow
    name = 'PrimaryFlow'
    names.append(name)
    units[name] = units[flows[0]]
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if sval[flow] == 'Primary' or sval[flow] == 'primary' or sval[flow] == 'PRIMARY' and data[flow][n] != 999:
                # 999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

    # Calculate difference between snorkel and chimney temperature
    name = 'snorkel-chim'
    names.append(name)
    units[name] = 'degC'
    data[name] = []
    diff = 0
    for n, row in enumerate(data['time']):

        diff = data['snorkel_T'][n] - data['Chimney_T'][n]
        data[name].append(diff)

    # Calculate average body temperature
    name = 'body_temp'
    names.append(name)
    units[name] = 'degC'
    data[name] = []
    diff = 0
    for n, row in enumerate(data['time']):

        body = (data['TC4'][n] + data['TC7'][n]+ data['TC8'][n])/3
        data[name].append(body)

    # Calculate average temperature of the stove including snorkel and chimney
    name = 'ave_temp'
    names.append(name)
    units[name] = 'degC'
    data[name] = []
    diff = 0
    for n, row in enumerate(data['time']):

        aveT = (data['body_temp'][n] + data['Chimney_T'][n]+ data['snorkel_T'][n])/3
        data[name].append(aveT)

    # Calculate Secondary flow
    name = 'SecondaryFlow'
    names.append(name)
    units[name] = units[flows[0]]
    data[name] = []
    for n, row in enumerate(data['time']):
        sum = 0
        for flow in flows:
            if sval[flow] == 'Secondary' or sval[flow] == 'secondary' or sval[flow] == 'SECONDARY' and \
                    data[flow][n] != 999:  # 999 signals the sensor is unplugged
                sum = sum + data[flow][n]
        data[name].append(sum)

    name = 'TotalFlow' #caculate total from all sensors
    names.append(name)
    data[name] = []
    units[name] = units[flows[0]]
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

        except (ValueError):
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
    LEMS_Senserion(inputpath, outputpath, logpath)

