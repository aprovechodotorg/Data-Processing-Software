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

from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import os
from easygui import *

versionpath = "C:\\Users\\Jaden\\Documents\\Heating Stoves\\test\\7.14.25\\7.14.25_SensorboxVersion.csv"
instrumentpath = "C:\\Users\\Jaden\\Documents\\Heating Stoves\\test\\7.14.25\\7.14.25_InstrumentVersion.csv"
datapath = "C:\\Users\\Jaden\\Documents\\Heating Stoves\\test\\7.14.25\\7.14.25_RawData_Recalibrated.csv"

def LEMS_SensorAssignment(versionpath, instrumentpath, datapath, logpath):

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_SensorAssignment v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    units = {}
    val = {}
    unc = {}
    uval = {}

    #load sensorbox version file
    [vnames,vunits,vval,vunc,vmetric]=io.load_constant_inputs(versionpath)
    line = f"LEMS sensor box version detected: {vval['SB']}"
    print(line)
    logs.append(line)

    if os.path.isfile(instrumentpath):
        # load instrumentation version file
        [inames, iunits, ival, iunc, imetric] = io.load_constant_inputs(instrumentpath)
        line = f"Loaded existing instrumentation file from path: {instrumentpath}"
        print(line)
        logs.append(line)
        TC_names = inames
        defaults = []
        for name in TC_names:
            defaults.append(ival[name])
    else:
        line = f"Instrumentation file not found. Creating file based on defaults."
        print(line)
        logs.append(line)
        # load data file to find number of thermocouples
        [tnames, tunits, tdata] = io.load_timeseries(datapath)

        TC_names = []
        TC_names.append('Version')

        for name in tnames:
            if 'temp' in name or 'TC' in name:
                TC_names.append(name)

        # create defaults based on sensorbox version
        defaults = []

        if '4003' in vval['SB']:
            for name in TC_names:
                if name == 'FLUEtemp':
                    defaults.append('Duct')
                elif name == 'H2Otemp':
                    defaults.append('Ambient')
                elif name == 'COtemp':
                    defaults.append('COtemp')
                elif name == 'CH4temp':
                    defaults.append('CH4temp')
                elif name == 'TC1':
                    defaults.append('Upper Back')
                elif name == 'TC2':
                    defaults.append('Upper Stack')
                elif name == 'TC6':
                    defaults.append('Upper Front')
                elif 'Version' in name:
                    defaults.append('1')
                else:
                    defaults.append(f"{vval['stove_type/model']}1.1.1")
        elif 'possum' in vval['SB'] or 'Possum' in vval['SB']:
            for name in TC_names:
                if name == 'FLUEtemp':
                    defaults.append('Duct')
                elif name == 'TCnoz':
                    defaults.append('Upper Stack')
                elif name == 'TC4':
                    defaults.append('Lower Stack')
                elif 'Version' in name:
                    defaults.append(f"{vval['stove_type/model']}1.1.1")

    # Create gui entry box
    text = f"Enter Thermocouple Locations for sensorbox {vval['SB']}\n" \
           f"Version order is written as " \
           f"stove_type.stove_version.lems_instrumentation_version.sensirion_instrumentation_version" \
           f"Click OK to continue\n" \
           f"Click Cancel to exit"
    title = "Sensor Assignment"
    output = multenterbox(text, title, TC_names, defaults)

    if output:
        defaults = output

    for n, name in enumerate(TC_names):
        val[name] = defaults[n]
        if 'TC' in name or 'temp' in name:
            units[name] = 'C'
        else:
            units[name] = ''


    io.write_constant_outputs(instrumentpath, TC_names, units, val, unc, uval)
    line = f'Created: {instrumentpath}'
    print(line)
    logs.append(line)

    io.write_logfile(logpath, logs)

    return val

#######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_SensorAssignment(versionpath, instrumentpath, datapath)

