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
def LEMS_SensorAssignment(versionpath, instrumentpath, datapath):

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

    if os.path.isfile(instrumentpath):
        # load instrumentation version file
        [inames, iunits, ival, iunc, imetric] = io.load_constant_inputs(instrumentpath)
        TC_names = inames
        defualts = []
        for name in TC_names:
            defualts.append(ival[name])
    else:
        # load data file to find number of thermocouples
        [tnames, tunits, tdata] = io.load_timeseries(datapath)

        TC_names = []
        TC_names.append('Instrument_Version')

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
                    defaults.append('')

    # Create gui entry box
    text = f"Enter Thermocouple Locations for sensorbox {vval['SB']}\n" \
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

#######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_SensorAssignment(versionpath, instrumentpath, datapath)

