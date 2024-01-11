# v0.2 Python3

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

# calculates PM mass concentration by gravimetric method
# inputs gravimetric filter weights
# determines which test phases and which flow trains by reading which variable names are present in the grav input file
# inputs phase times input file to calculate phase time length
# outputs filter net mass, flow, duration, and concentration for each phase
# outputs report to terminal and log file

# do:
# add plot of PM scat and grav flows with phase markers as a visual check
# create grav input file to interface with filter log database

import LEMS_DataProcessing_IO as io
# import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from uncertainties import ufloat
import os
import numpy as np
import easygui

#########      inputs      ##############
# Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
# gravimetric filter masses input file:
gravinputpath = 'GravInputs.csv'
# phase averages input data file:
aveinputpath = 'Averages.csv'
# gravimetric output metrics data file:
gravoutputpath = 'GravOutputs.csv'
# input file of start and end times for background and test phase periods
timespath = 'PhaseTimes.csv'
logpath = 'log.txt'


##########################################

def PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath):
    # Function create gravinput file if it doesn't exist, calculates grav data

    ver = '0.3'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_GravCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    outnames = []  # initialize list of variable names for grav output metrics
    outuval = {}  # initialize dictionary for grav output metrics (type: ufloats)
    outunits = {}  # dict of units for grav output metrics
    outval = {}  # only used for output file header
    outunc = {}  # only used for output file header

    # load timeseries data file to get start and end time of data series
    [names, units, data] = io.load_timeseries(timeseriespath)
    line = 'loaded timeseries data file: ' + timeseriespath
    print(line)
    logs.append(line)

    ##############################################
    # check for grav input file
    if os.path.isfile(gravinputpath):
        line = '\nGrav input file already exists:'
        print(line)
        logs.append(line)
    else:  # if input file is not there then create it
        gravnames = ['variable', 'filter_ID', 'tare_mass', 'gross_mass', 'start_time_filter', 'end_time_filter']
        gravunits = {}
        gravval = {}
        gravunc = {}
        gravuval = {}
        # make header
        name = 'variable'
        gravunits[name] = 'units'
        gravval[name] = 'value'
        gravunc[name] = 'uncertainty'
        gravunits['filter_ID'] = 'text'
        gravunits['tare_mass'] = 'mg'
        gravunits['gross_mass'] = 'mg'
        gravunits['start_time_filter'] = 'yyyymmdd hh:mm:ss'
        gravunits['end_time_filter'] = 'yyyymmdd hh:mm:ss'

        # GUI box to edit grav inputs
        zeroline = 'Enter grav input data\n'
        secondline = 'Click OK to continue\n'
        thirdline = 'Click Cancel to exit\n'
        msg = zeroline + secondline + thirdline
        title = "Gitrdone"
        fieldNames = gravnames[1:]
        currentvals = ['', '', '', data['time'][0], data['time'][-1]]
        newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)
        if newvals:
            if newvals != currentvals:
                currentvals = newvals
                for n, name in enumerate(gravnames[1:]):
                    gravval[name] = currentvals[n]
        else:
            line = 'Error: Undefined variables'
            print(line)
            logs.append(line)

        io.write_constant_outputs(gravinputpath, gravnames, gravunits, gravval, gravunc, gravuval)
        line = '\nCreated gravimetric input file:'
        print(line)
        logs.append(line)
    line = gravinputpath
    print(line)
    logs.append(line)

    ###################################################

    # load grav input file
    [gravnames, gravunits, gravval, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
    gravnames = gravnames[1:]  # remove the first name because it is the header

    line = 'Loaded grav input file:' + gravinputpath
    print(line)
    logs.append(line)

    ##########################################
    # read in measurement uncertainty file
    [ucnames, ucunits, ucinputs] = io.load_timeseries(ucpath)

    ############################################
    # find start and end time indices
    starttimeobject = dt.strptime(gravval['start_time_filter'],
                                  '%Y%m%d %H:%M:%S')  # convert the time string to date object
    starttimedatenum = matplotlib.dates.date2num(starttimeobject)  # then to date number
    startindex = data['datenumbers'].index(starttimedatenum)  # find index in datenumber data series

    endtimeobject = dt.strptime(gravval['end_time_filter'], '%Y%m%d %H:%M:%S')  # convert the time string to date object
    endtimedatenum = matplotlib.dates.date2num(endtimeobject)  # then to date number
    endindex = data['datenumbers'].index(endtimedatenum)  # find index in datenumber data series

    # find sample rate
    sample_period = data['seconds'][1] - data['seconds'][0]  # seconds
    sample_rate = 1 / sample_period  # hz

    # calculate metrics

    name = 'net_mass'
    outnames.append(name)
    outunits[name] = 'mg'
    outuval[name] = gravuval['gross_mass'] - gravuval['tare_mass']

    # average filter flow over the sampling duration
    name = 'FiltFlow_tot'
    outnames.append(name)
    outunits[name] = 'ccm'
    try:
        uc = abs(float(ucinputs['F1Flow'][0]) + data['F1Flow'][startindex] * float(ucinputs['F1Flow'][1]))  # relative uncertainty assumes flow is constant
        ave = np.mean(data['F1Flow'][startindex:endindex + 1])
    except:
        uc = abs(float(ucinputs['FiltFlow'][0]) + data['FiltFlow'][startindex] * float(ucinputs['FiltFlow'][1]))  # relative uncertainty assumes flow is constant
        ave = np.mean(data['FiltFlow'][startindex:endindex + 1])

    outuval[name] = ufloat(ave, uc)

    # total flow over the sampling duration based on average flow
    name = 'volume_tot'
    outnames.append(name)
    outunits[name] = 'm^3'
    vol = ufloat(0, 0)
    try:
        vol = outuval['FiltFlow_tot'] * len(data['F1Flow'][startindex:endindex + 1]) * sample_period / 60000000
    except:
        vol = outuval['FiltFlow_tot'] * len(data['FiltFlow'][startindex:endindex + 1]) * sample_period / 60000000
    outuval[name] = vol

    # average mass concentration over the entire sampling duration
    name = 'PMconc_tot'
    outnames.append(name)
    outunits[name] = 'mg/m^3'
    outuval[name] = outuval['net_mass'] / outuval['volume_tot']

    # average scattering over the sampling duration
    name = 'PM_tot'
    outnames.append(name)
    outunits[name] = 'Mm^-1'
    uc = []
    for n, pm in enumerate(data['PM'][startindex:endindex + 1]):
        uc_n = abs(float(ucinputs['PM'][0]) + pm * float(ucinputs['PM'][1]))
        uc.append(uc_n)
    ave = np.mean(data['PM'][startindex:endindex + 1])
    ave_uc = np.mean(uc)
    outuval[name] = ufloat(ave, ave_uc)

    # MSC
    name = 'MSC'
    outnames.append(name)
    outunits[name] = 'm^2/g'
    outuval[name] = outuval['PM_tot'] / outuval['PMconc_tot'] / 1000

    # make time series of PM concentration for each phase
    conc_prebkg = []
    conc_test = []
    conc_postbkg = []
    for n, val in enumerate(data['phase'][startindex:endindex + 1]):
        conc = data['PM'][n] / outuval['MSC'].n / 1000
        if 'prebkg' in val:
            conc_prebkg.append(conc)
        if 'test' in val:
            conc_test.append(conc)
        if 'postbkg' in val:
            conc_postbkg.append(conc)

    name = 'PMconc_prebkg'
    outnames.append(name)
    outunits[name] = 'mg/m^3'
    ave = np.mean(conc_prebkg)
    uc = abs(ave * outuval['PMconc_tot'].s / outuval['PMconc_tot'].n)
    outuval[name] = ufloat(ave, uc)

    name = 'PMconc_test'
    outnames.append(name)
    outunits[name] = 'mg/m^3'
    ave = np.mean(conc_test)
    uc = abs(ave * outuval['PMconc_tot'].s / outuval['PMconc_tot'].n)
    outuval[name] = ufloat(ave, uc)

    name = 'PMconc_postbkg'
    outnames.append(name)
    outunits[name] = 'mg/m^3'
    ave = np.mean(conc_postbkg)
    uc = abs(ave * outuval['PMconc_tot'].s / outuval['PMconc_tot'].n)
    outuval[name] = ufloat(ave, uc)

    ########################################################
    # make header for output file
    name = 'variable_name'
    outnames = [name] + outnames
    outunits[name] = 'units'
    outval[name] = 'value'
    outunc[name] = 'uncertainty'

    # print grav output metrics data file
    io.write_constant_outputs(gravoutputpath, outnames, outunits, outval, outunc, outuval)

    line = '\ncreated gravimetric PM output file:\n' + gravoutputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_GravCalcs(gravinputpath, timeseriespath, ucpath, gravoutputpath, logpath)
