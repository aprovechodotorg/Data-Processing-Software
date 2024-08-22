#v0.4  Python3

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
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg
import matplotlib
import matplotlib.pyplot as plt
import easygui
import numpy as np
from uncertainties import ufloat

inputpath="C:\\Users\\Jaden\\Documents\\DIY Heating Stove\\test\\7.5.24\\7.5.24_QualityControl.csv"
datapath='C:\\Users\\Jaden\\Documents\\DIY Heating Stove\\test\\7.5.24\\7.5.24_RawData_Recalibrated.csv'
savefig='C:\\Users\\Jaden\\Documents\\DIY Heating Stove\\test\\7.5.24\\7.5.24_GasChecks.png'
inputmethod = '1'
def LEMS_GasChecks(inputpath, datapath, savefig, inputmethod):

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #################################################
    running = 'fun'

    # read in raw data file
    [names, units, data] = io.load_timeseries(datapath)

    line = 'loaded: ' + datapath #add to log
    print(line)
    logs.append(line)

    # load quality control data file
    [qnames, qunits, qval, qunc, qmetric] = io.load_constant_inputs(inputpath)

    line = 'loaded: ' + inputpath
    print(line)
    logs.append(line)

    timenames = []
    entry = []

    for name in qnames:
        if 'Time' in name and ('Bias' in name or 'Drift' in name):
            timenames.append(name)
            if qval[name] != '':
                entry.append(qval[name])

    if len(entry) == 0: #If user has not entered times previously, prompt to enter
        qval, running = request_entry(timenames, qunits, qval, running)

        io.write_constant_outputs(inputpath, qnames, qunits, qval, qunc, qmetric)
        message = 'Updated: ' + inputpath
        print(message)
        logs.append(message)

    ##################################################################
    # Convert datetime to readable dateobject
    date = data['time'][0][:8]  # pull date

    name = 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data['time']):
        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)

    name = 'datenumbers'
    units[name] = 'date'
    names.append(name)
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    sample_rate = data['seconds'][1] - data['seconds'][0] #find sample rate

    ucinputs = {}
    for name in names:
        ucinputs[name] = ''

    ######################################################
    cycle = 0
    [phasedatenums, phasedata, phasemean, phases] = run_functions(timenames, qval, qunits, date, datenums, sample_rate, names, data, ucinputs, running)

    if inputmethod == '1': #if in interactive mode
        plt.ion()  #turn on interactive plot mode

        lw=float(5)    #define the linewidth for the data series
        plw=float(5)    #define the linewidth for the bkg and sample period marker
        msize=30        #marker size for start and end pints of each period

        colors={}
        for phase in phases:
            if 'Span' in phase:
                colors[phase] = 'g'
            elif 'Zero' in phase:
                colors[phase] = 'y'

        plt.plot(data['datenumbers'], data['CO'], color='turquoise', linewidth=lw, label='CO (' + units['CO'] + ')')
        plt.plot(data['datenumbers'], data['CO2'], color='plum', linewidth=lw, label='CO2 (' + units['CO2'] + ')')
        for name in names:
            if 'CO' == name or 'CO2' == name:
                for phase in phases:
                    phasename = name + '_' + phase
                    plt.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw, label=phase + name)
        plt.ylabel(units[name])
        plt.title('Gas Checks')
        plt.grid(visible=True, which='major', axis='y')

        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
        plt.gca().xaxis.set_major_formatter(xfmt)
        for tick in plt.gca().get_xticklabels():
            tick.set_rotation(30)

        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])  # squeeze it down to make room for the legend
        ax.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1

        plt.show() #show all figures

        while (running == 'fun'):
            qval, running = request_entry(timenames, qunits, qval, running)

            io.write_constant_outputs(inputpath, qnames, qunits, qval, qunc, qmetric)
            message = 'Updated: ' + inputpath
            print(message)
            logs.append(message)

            [phasedatenums, phasedata, phasemean, phases] = run_functions(timenames, qval, qunits, date, datenums,
                                                                          sample_rate, names, data, ucinputs, running)

            colors = {}
            for phase in phases:
                if 'Span' in phase:
                    colors[phase] = 'g'
                elif 'Zero' in phase:
                    colors[phase] = 'y'

            plt.clf()
            plt.plot(data['datenumbers'], data['CO'], color='turquoise', linewidth=lw, label='CO (' + units['CO'] + ')')
            plt.plot(data['datenumbers'], data['CO2'], color='plum', linewidth=lw, label='CO2 (' + units['CO2'] + ')')
            for name in names:
                if 'CO' == name or 'CO2' == name:
                    for phase in phases:
                        phasename = name + '_' + phase
                        plt.plot(phasedatenums[phase], phasedata[phasename], color=colors[phase], linewidth=plw,
                                 label=phase + name)
            plt.ylabel(units[name])
            plt.title('Gas Checks')
            plt.grid(visible=True, which='major', axis='y')

            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
            # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
            plt.gca().xaxis.set_major_formatter(xfmt)
            for tick in plt.gca().get_xticklabels():
                tick.set_rotation(30)

            ax = plt.gca()
            box = ax.get_position()
            ax.set_position(
                [box.x0, box.y0, box.width * 0.85, box.height])  # squeeze it down to make room for the legend
            ax.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1

            plt.show()  # show all figures
        plt.savefig(savefig)
        plt.ioff()
        plt.close()

    ##########################################################
    #Recalculate pass or fail metrics
    #Span
    #CO
    #Bias
    try:
        span_conc = float(qval['Span_Gas_Actual_CO_Concentration'])
        span_measure = phasemean['CO_Span_Bias']

        bias_CO = ((span_measure - span_conc) / span_conc) * 100

        qval['Span_Bias_CO'] = bias_CO

        if abs(bias_CO) <= 5:
            qval['Span_Gas_Bias_Check_CO'] = 'PASS'
        else:
            qval['Span_Gas_Bias_Check_CO'] = 'FAIL'
    except:
        qval['Span_Bias_CO'] = 'N/A'
        qval['Span_Gas_Bias_Check_CO'] = 'INVALID'

    #drift
    try:
        span_conc = float(qval['Span_Gas_Actual_CO_Concentration'])
        span_measure = phasemean['CO_Span_Drift']

        drift = (((span_measure - span_conc) / span_conc) * 100) - bias_CO

        qval['Span_Drift_CO'] = drift

        if abs(drift) <= 3:
            qval['Span_Gas_Drift_Check_CO'] = 'PASS'
        else:
            qval['Span_Gas_Drift_Check_CO'] = 'FAIL'
    except:
        qval['Span_Drift_CO'] = 'N/A'
        qval['Span_Gas_Drift_Check_CO'] = 'INVALID'
    # CO2
    # Bias
    try:
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])
        span_measure = phasemean['CO2_Span_Bias']

        bias_CO2 = ((span_measure - span_conc) / span_conc) * 100

        qval['Span_Bias_CO2'] = bias_CO2

        if abs(bias_CO2) <= 5:
            qval['Span_Gas_Bias_Check_CO2'] = 'PASS'
        else:
            qval['Span_Gas_Bias_Check_CO2'] = 'FAIL'
    except:
        qval['Span_Bias_CO2'] = 'N/A'
        qval['Span_Gas_Bias_Check_CO2'] = 'INVALID'

    # drift
    try:
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])
        span_measure = phasemean['CO2_Span_Drift']

        drift = (((span_measure - span_conc) / span_conc) * 100) - bias_CO2

        qval['Span_Drift_CO2'] = drift

        if abs(drift) <= 3:
            qval['Span_Gas_Drift_Check_CO2'] = 'PASS'
        else:
            qval['Span_Gas_Drift_Check_CO2'] = 'FAIL'
    except:
        qval['Span_Drift_CO2'] = 'N/A'
        qval['Span_Gas_Drift_Check_CO2'] = 'INVALID'

    # Zero
    # CO
    # Bias
    try:
        zero_conc = float(qval['Zero_Gas_Actual_CO_Concentration'])
        zero_measure = phasemean['CO_Zero_Bias']
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])

        bias_CO_zero = ((zero_measure - zero_conc) / span_conc) * 100

        qval['Zero_Bias_CO'] = bias_CO_zero

        if abs(bias_CO_zero) <= 5:
            qval['Zero_Gas_Bias_Check_CO'] = 'PASS'
        else:
            qval['Zero_Gas_Bias_Check_CO'] = 'FAIL'
    except:
        qval['Zero_Bias_CO'] = 'N/A'
        qval['Zero_Gas_Bias_Check_CO'] = 'INVALID'

    # drift
    try:
        zero_conc = float(qval['Zero_Gas_Actual_CO_Concentration'])
        zero_measure = phasemean['CO_Zero_Drift']
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])

        drift = (((zero_measure - zero_conc) / span_conc) * 100) - bias_CO_zero

        qval['Zero_Drift_CO'] = drift

        if abs(drift) <= 3:
            qval['Zero_Gas_Drift_Check_CO'] = 'PASS'
        else:
            qval['Zero_Gas_Drift_Check_CO'] = 'FAIL'
    except:
        qval['Zero_Drift_CO'] = 'N/A'
        qval['Zero_Gas_Drift_Check_CO'] = 'INVALID'
    # CO2
    # Bias
    try:
        zero_conc = float(qval['Zero_Gas_Actual_CO2_Concentration'])
        zero_measure = phasemean['CO2_Zero_Bias']
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])

        bias_CO2_zero = ((zero_measure - zero_conc) / span_conc) * 100

        qval['Zero_Bias_CO2'] = bias_CO2_zero

        if abs(bias_CO2_zero) <= 5:
            qval['Zero_Gas_Bias_Check_CO2'] = 'PASS'
        else:
            qval['Zero_Gas_Bias_Check_CO2'] = 'FAIL'
    except:
        qval['Zero_Bias_CO2'] = 'N/A'
        qval['Zero_Gas_Bias_Check_CO2'] = 'INVALID'

    # drift
    try:
        zero_conc = float(qval['Zero_Gas_Actual_CO2_Concentration'])
        zero_measure = phasemean['CO2_Zero_Drift']
        span_conc = float(qval['Span_Gas_Actual_CO2_Concentration'])

        drift = (((zero_measure - zero_conc) / span_conc) * 100) - bias_CO2_zero

        qval['Zero_Drift_CO2'] = drift

        if abs(drift) <= 3:
            qval['Zero_Gas_Drift_Check_CO2'] = 'PASS'
        else:
            qval['Zero_Gas_Drift_Check_CO2'] = 'FAIL'
    except:
        qval['Zero_Drift_CO2'] = 'N/A'
        qval['Zero_Gas_Drift_Check_CO2'] = 'INVALID'

    io.write_constant_outputs(inputpath, qnames, qunits, qval, qunc, qmetric)
    message = 'Updated: ' + inputpath
    print(message)
    logs.append(message)

    return qval, qunits, qnames

def run_functions(timenames, qval, qunits, date, datenums, sample_rate, names, data, ucinputs, running):
    # Convert datetime str to readable value time objects
    [validnames, timeobject] = bkg.makeTimeObjects(timenames, qval, date)
    phaseindices = bkg.findIndices(validnames, timeobject, datenums,
                               sample_rate)  # find the indices in the time data series for the start and stop times of each phase
    phases = set(())
    for name in timenames:
        if qval[name] != '':
            if name.startswith('Span') and name.endswith('Bias'):
                phases.add('Span_Bias')
            elif name.startswith('Span') and name.endswith('Drift'):
                phases.add('Span_Drift')
            elif name.startswith('Zero') and name.endswith('Bias'):
                phases.add('Zero_Bias')
            elif name.startswith('Zero') and name.endswith('Drift'):
                phases.add('Zero_Drift')

    try:
        [phasedatenums, phasedata, phasemean, phases] = definePhaseData(names, data, phases, phaseindices,
                                                                ucinputs, timenames)  # define phase data series for each channel
    except KeyError as e:
        e = str(e)
        message = f"Variable: {e} was entered incorrectly or is outside of the measured time period\n" \
                  f"* Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                  f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                  f"    * Check that the entered time exist within the data\n" \
                  f"    * Check that the time has not been left blank when there should be an entry.\n"
        title = "ERROR"
        easygui.msgbox(message, title, "OK")
        qval = request_entry(timenames, qunits, qval, running)
        [phasedatenums, phasedata, phasemean, phases] = run_functions(timenames, qval, qunits, date, datenums, sample_rate, names, data, ucinputs,running)

    return phasedatenums, phasedata, phasemean, phases
def request_entry(timenames, qunits, qval, running):
    # GUI box to edit input times
    zeroline = 'Enter start and end times for gas check bias and drift periods\n'
    firstline = 'Time format = ' + qunits[timenames[0]] + '\n\n'
    secondline = 'Click OK to confirm entered values\n'
    thirdline = 'Click Cancel to exit\n'
    msg = zeroline + firstline + secondline + thirdline
    title = "Gitrdone"
    currentvals = []
    for name in timenames:
        currentvals.append(qval[name])
    newvals = easygui.multenterbox(msg, title, timenames, currentvals)  # save new vals from user input
    test = 1
    if newvals:
        if newvals != currentvals:
            for n, name in enumerate(timenames):
                qval[name] = newvals[n]
    else:
        running = 'not fun'

    return qval, running
def definePhaseData(Names, Data, Phases, Indices, Ucinputs, timenames):
    Phasedatenums = {}
    Phasedata = {}
    Phasemean = {}
    startindex = {}
    endindex = {}
    sections = ['Span_Bias', 'Span_Drift', 'Zero_Bias', 'Zero_Drift']
    for name in Indices:
        key = name
        if 'Start' in name:
            if 'Span' in name:
                if 'Bias' in name:
                    startindex['Span_Bias'] = Indices[key]
                elif 'Drift' in name:
                    startindex['Span_Drift'] = Indices[key]
            elif 'Zero' in name:
                if 'Bias' in name:
                    startindex['Zero_Bias'] = Indices[key]
                elif 'Drift' in name:
                    startindex['Zero_Drift'] = Indices[key]
        elif 'End' in name:
            if 'Span' in name:
                if 'Bias' in name:
                    endindex['Span_Bias'] = Indices[key]
                elif  'Drift' in name:
                    endindex['Span_Drift'] = Indices[key]
            elif 'Zero' in name:
                if 'Bias' in name:
                    endindex['Zero_Bias'] = Indices[key]
                elif 'Drift' in name:
                    endindex['Zero_Drift'] = Indices[key]
    for Phase in Phases:
        Phasedatenums[Phase] = Data['datenumbers'][startindex[Phase]:endindex[Phase] + 1]
        # make phase data series for each data channel
        for Name in Names:
            Phasename = Name + '_' + Phase
            Phasedata[Phasename] = Data[Name][startindex[Phase]:endindex[Phase] + 1]

            remove = []
            for n, val in enumerate(Phasedata[Phasename]):
                if val == '':
                    remove.append(n)
            if len(remove) != 0:
                for n in remove:
                    for Name in Names:
                        Phasedata[Name + '_' + Phase].pop(n)
            # calculate average value
            if Name != 'time' and Name != 'phase':
                non_nan_values = [value for value in Phasedata[Phasename] if not np.isnan(value)]
                if len(non_nan_values) == 0:
                    Phasemean[Phasename] = np.nan
                else:
                    ave = np.mean(non_nan_values)
                    if Name == 'datenumbers':
                        Phasemean[Phasename] = ave
                    else:
                        Phasemean[Phasename] = ave

        # time channel: use the mid-point time string
        Phasename = 'datenumbers_' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean, Phases
#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_GasChecks(inputpath, datapath, savefig,inputmethod='1')
