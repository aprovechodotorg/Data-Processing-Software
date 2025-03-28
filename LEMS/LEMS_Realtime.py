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
import csv
import numpy as np
import math
import uncertainties as unumpy
import matplotlib
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg

########### inputs (only used if this script is run as executable) #############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
inputpath='TimeSeriesMetrics.csv'
energypath='EnergyOutputs.csv'
graninputpath = 'GravOutputs.csv'
empath = 'EmissionOutputs.csv'
periodpath = 'AveragingPeriod.csv'
outputpath = 'RealtimeOutputs.csv'
averageoutputpath = 'AveragingPeriodOutputs.csv'
averagecalcoutputpath = 'AveragingPeriodCalcs.csv'
fullaverageoutputpath = 'RealtimeAveragesOutputs.csv'
phasepath = 'PhaseTimes.csv'
savefig = 'averagingperiod.png'
logpath='log.txt'
##################################

def LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath, savefig,
                  choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                  nanopath, TEOMpath, senserionpath, OPSpath, Picopath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #################################################
    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    line = 'loaded: ' + inputpath #add to log
    print(line)
    logs.append(line)

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'loaded: ' + energypath
    print(line)
    logs.append(line)
    ######################################################################
    sensorpaths = []
    #Read in additional sensor data and add it to dictionary
    if os.path.isfile(fuelpath):
        sensorpaths.append(fuelpath)

    if os.path.isfile(fuelmetricpath):
        sensorpaths.append(fuelmetricpath)

    if os.path.isfile(exactpath):
        sensorpaths.append(exactpath)

    if os.path.isfile(scalepath):
        sensorpaths.append(scalepath)

    if os.path.isfile(intscalepath):
        sensorpaths.append(intscalepath)

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

    #######################################################################
    #Check if average period times file exists
    if os.path.isfile(periodpath):
        line = 'Average Period time file already exists: ' + periodpath
        print(line)
        logs.append(line)
    else:
        # Read in averaging period start and end times (phase start and end time)
        [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(phasepath)

        line = 'loaded: ' + phasepath
        print(line)
        logs.append(line)
        request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval)
    ##################################################################
    ################################################################
    # Read in averaging period start and end times
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

    line = 'loaded: ' + periodpath
    print(line)
    logs.append(line)

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
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    samplerate = data['seconds'][1] - data['seconds'][0] #find sample rate

    [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval)

    for n, name in enumerate(names):
        phasename = name + '_' + choice
        try:
            avgdata[name] = avgdata[phasename]
        except:
            pass

    # Write cut values into a file
    io.write_timeseries(outputpath, names, units, avgdata)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    #################### #############################################
    # Create period averages
    #list of data that needs period weighting
    emweightavg = ['CO_ER', 'CO2v_ER' 'PM_ER', 'VOC_ER', 'C_ER', 'CO_ER_min',
                   'CO2v_ER_min', 'PM_ER_min', 'VOC_ER_min', 'CO_ER_hr', 'CO2v_ER_hr', 'PM_ER_hr', 'VOC_ER_hr', 'CO_EF',
                   'CO2v_EF', 'PM_EF', 'VOC_EF'] #emissions factors are on basis of carbon

    calcavg = {}
    unc = {}
    uval = {}
    for name in names:
        if name not in emweightavg:  # only for series needing time weighted data
            if name == 'seconds':
                calc = avgdata['seconds'][-1] - avgdata['seconds'][0]
                try:
                    calcavg[name] = calc.n  # check for uncertainty
                except:
                    calcavg[name] = calc
                unc[name] = ''
                uval[name] = ''
            else:
                # Try creating averages of values, nan value if can't
                try:
                    calc = sum(avgdata[name]) / len(avgdata[name])  # time weighted average
                    try:
                        calcavg[name] = calc.n  # check for uncertainty
                    except:
                        calcavg[name] = calc
                except:
                    calcavg[name] = ''
                unc[name] = ''
                uval[name] = ''

    for name in names:
        if name in emweightavg:  # only for series needing emission weighted data currently contains emissions rates and emissions factors
            top = 0
            try:
                for n, val in enumerate(data[name]):
                    top = (val * (data['Cmass'][n] / calcavg['Cmass'])) + top
                calc = top / len(data[name])
                try:
                    calcavg[name] = calc.n  # check for uncertainty
                    unc[name] = ''
                    uval[name] = ''
                except:
                    calcavg[name] = calc
                    uval[name] = ''
                    unc[name] = ''
            except:
                calcavg[name] = ''
                unc[name] = ''
                uval[name] = ''

    #Add other sensor data
    for path in sensorpaths:

        [snames, sunits, sdata] = io.load_timeseries(path)

        # Convert datetime to readable dateobject
        date = sdata['time'][0][:10]  # pull date

        name = 'dateobjects'
        snames.append(name)
        sunits[name] = 'date'
        sdata[name] = []
        for n, val in enumerate(sdata['time']):
            try:
                dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
            except:
                dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
            sdata[name].append(dateobject)

        name = 'datenumbers'
        snames.append(name)
        sunits[name] = 'date'
        sdatenums = matplotlib.dates.date2num(sdata['dateobjects'])
        sdatenums = list(sdatenums)
        sdata[name] = sdatenums

        samplerate = (sdata['seconds'][1] - sdata['seconds'][0]) * 4  # find sample rate

        # find indicieds in the data for start and end
        indices = bkg.findIndices(validnames, timeobject, sdatenums, samplerate)

        try:
            # Define averaging data series
            [adddatenums, adddata, addmean] = definePhaseData(snames, sdata, phases, indices)

            snames.remove('dateobjects')
            snames.remove('time')
            snames.remove('seconds')
            snames.remove('datenumbers')

            for n, name in enumerate(snames):
                if 'TC' in name:
                    name = 'S' + name
                try:
                    phasename = name + '_' + choice
                    if 'TC' in name:
                        calcavg[name] = sum(adddata[phasename[1:]]) / len(adddata[phasename[1:]])
                        avgdata[phasename] = adddata[phasename[1:]]
                    else:
                        calcavg[name] = sum(adddata[phasename]) / len(adddata[phasename])
                        avgdata[phasename] = adddata[phasename]
                    units[name] = sunits[name]
                    uval[name] = ''
                    names.append(name)
                except:
                    pass
        except:
            pass
    # create file of averages for averaging period
    io.write_constant_outputs(averageoutputpath, names, units, calcavg, unc, uval)

    allnames = []
    for name in names:
        allnames.append(name)

    for path in sensorpaths:
        [snames, sunits, sdata] = io.load_timeseries(path)
        for name in snames:
            if 'TC' in name:
                name = 'S' + name
            if name in names and 'time' != name and 'seconds' not in name:
                names.remove(name)

    line = 'created: ' + averageoutputpath
    print(line)
    logs.append(line)

    ###############################################################
    #plot timeseries data
    if inputmethod == '1':
        plt.ion() #trun on interactive plot mode

        fig, ax = plt.subplots()

        scalar = 10

        scaledPM = []
        for val in data['PM']:
            scaledPM.append(val/scalar)

        scaledavgPM = []
        for val in avgdata['PM_' + choice]:
            scaledavgPM.append(val/scalar)

        #Plot PM
        ax.plot(data['datenumbers'], scaledPM, color = 'yellow', label = 'Full period PM')
        ax.plot(avgdatenums[choice], scaledavgPM, color='blue', label='Cut Period PM')

        TC2 = True

        try:
            #Plot TC2 - This can be changed for another variable for other analysis, just
            ax.plot(data['datenumbers'], data['TC2'], color = 'red', label = 'Full period TC2')
            ax.plot(avgdatenums[choice], avgdata['TC2_' + choice], color = 'green', label='Cut Period TC2')
        except:
            variable = easygui.choicebox("Select a variable to plot", choices=allnames)
            ax.plot(data['datenumbers'], data[variable], color='red', label=f'Full period {variable}')
            ax.plot(avgdatenums[choice], avgdata[variable + '_' + choice], color='green', label=f'Cut Period {variable}')
            TC2 = False

        ax.legend()
        ax.set(ylabel='PM(Mm-1)/10, TC2(C)', title='Please confirm the time period displayed is correct')

        #Format x axis to readable times
        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S') #pull and format time data
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)

        ################################################################
        #Replot for new inputs
        running = 'fun'
        while (running == 'fun'):

            startname = 'start_time_' + choice
            endname = 'end_time_' + choice

            #GUI box to edit input times
            zeroline = 'Edit averaging period\n'
            firstline = 'Time format = ' + timeunits[startname] + '\n\n'
            secondline = 'Click OK to update plot\n'
            thirdline = 'Click Cancel to exit\n'
            msg = zeroline + firstline + secondline + thirdline
            title = "Gitrdone"

            fieldnames = titlenames
            currentvals = []

            for name in fieldnames:
                currentvals.append(timestring[name])

            newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)  # save new vals from user input

            if newvals:
                if newvals != currentvals: #reassign user input to current vals
                    currentvals = newvals
                    eval[startname] = currentvals[0]
                    eval[endname] = currentvals[1]
                    timestring[startname] = currentvals[0]
                    timestring[endname] = currentvals[1]

                    #record new values in averagingperiod for next time
                    io.write_constant_outputs(periodpath, titlenames, eunits, eval, eunc, emetric)
                    line = 'Updated averaging period file:' + periodpath
                    print(line)
                    logs.append(line)
            else:
                running = 'not fun'
                savefigpath = savefig[:-4] + '_' + choice + '.png'
                plt.savefig(savefigpath, bbox_inches='tight')
                plt.close()
                plt.ioff()  # turn off interactive plot
                #plt.close()  # close plot

            #####################################################################
            #Updata values of new cut period
            [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval)

            for n, name in enumerate(names):
                phasename = name + '_' + choice
                try:
                    avgdata[name] = avgdata[phasename]
                except:
                    pass

            # Write cut values into a file
            io.write_timeseries(outputpath, names, units, avgdata)

            line = 'created: ' + outputpath
            print(line)
            logs.append(line)

            #################### #############################################
            # Create period averages
            calcavg = {}
            unc = {}
            uval = {}
            for name in names:
                if name not in emweightavg:  # only for series needing time weighted data
                    if name == 'seconds':
                        calc = avgdata['seconds'][-1] - avgdata['seconds'][0]
                        try:
                            calcavg[name] = calc.n  # check for uncertainty
                        except:
                            calcavg[name] = calc
                        unc[name] = ''
                        uval[name] = ''
                    else:
                        # Try creating averages of values, nan value if can't
                        try:
                            calc = sum(avgdata[name]) / len(avgdata[name])  # time weighted average
                            try:
                                calcavg[name] = calc.n  # check for uncertainty
                            except:
                                calcavg[name] = calc
                        except:
                            calcavg[name] = ''
                        unc[name] = ''
                        uval[name] = ''

            for name in names:
                if name in emweightavg:  # only for series needing emission weighted data
                    top = 0
                    try:
                        for n, val in enumerate(data[name]):
                            top = (val * (data['Cmass'][n] / calcavg['Cmass'])) + top
                        calc = top / len(data[name])
                        try:
                            calcavg[name] = calc.n  # check for uncertainty
                            unc[name] = ''
                            uval[name] = ''
                        except:
                            calcavg[name] = calc
                            uval[name] = ''
                            unc[name] = ''
                    except:
                        calcavg[name] = ''
                        unc[name] = ''
                        uval[name] = ''

            # Add other sensor data
            for path in sensorpaths:

                [snames, sunits, sdata] = io.load_timeseries(path)

                # Convert datetime to readable dateobject
                date = sdata['time'][0][:10]  # pull date

                name = 'dateobjects'
                snames.append(name)
                sunits[name] = 'date'
                sdata[name] = []
                for n, val in enumerate(sdata['time']):
                    try:
                        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
                    except:
                        dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
                    sdata[name].append(dateobject)

                name = 'datenumbers'
                snames.append(name)
                sunits[name] = 'date'
                sdatenums = matplotlib.dates.date2num(sdata['dateobjects'])
                sdatenums = list(sdatenums)
                sdata[name] = sdatenums

                samplerate = (sdata['seconds'][1] - sdata['seconds'][0]) * 4  # find sample rate

                # find indicieds in the data for start and end
                indices = bkg.findIndices(validnames, timeobject, datenums, samplerate)

                try:
                    # Define averaging data series
                    [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

                    snames.remove('dateobjects')
                    snames.remove('time')
                    snames.remove('seconds')
                    snames.remove('datenumbers')

                    for n, name in enumerate(snames):
                        if 'TC' in name:
                            name = 'S' + name
                        try:

                            phasename = name + '_' + choice
                            if 'TC' in name:
                                calcavg[name] = sum(adddata[phasename[1:]]) / len(adddata[phasename[1:]])
                                avgdata[phasename] = adddata[phasename[1:]]
                            else:
                                calcavg[name] = sum(adddata[phasename]) / len(adddata[phasename])
                                avgdata[phasename] = adddata[phasename]
                            units[name] = sunits[name]
                            uval[name] = ''
                            names.append(name)
                        except:
                            pass
                except:
                    pass
            # create file of averages for averaging period
            io.write_constant_outputs(averageoutputpath, names, units, calcavg, unc, uval)

            for path in sensorpaths:
                [snames, sunits, sdata] = io.load_timeseries(path)
                for name in snames:
                    if 'TC' in name:
                        name = 'S' + name
                    if name in names and 'time' != name and 'seconds' not in name:
                        names.remove(name)

            line = 'created: ' + averageoutputpath
            print(line)
            logs.append(line)

            ############################################################################################
            #Update Plot
            scaledPM = []
            for val in data['PM']:
                scaledPM.append(val / scalar)

            scaledavgPM = []
            for val in avgdata['PM_' + choice]:
                scaledavgPM.append(val / scalar)

            ax.cla()

            #Plot PM
            ax.plot(data['datenumbers'], scaledPM, color = 'yellow', label = 'Full period PM')
            ax.plot(avgdatenums[choice], scaledavgPM, color = 'blue', label = 'Cut Period PM')

            try:
                #Plot TC2 - This can be changed for another variable for other analysis, just
                ax.plot(data['datenumbers'], data['TC2'], color = 'red', label = 'Full period TC2')
                ax.plot(avgdatenums[choice], avgdata['TC2_' + choice], color = 'green', label = 'Cut Period TC2')
            except:
                ax.plot(data['datenumbers'], data[variable], color='red', label=f'Full period {variable}')
                ax.plot(avgdatenums[choice], avgdata[variable + '_' + choice], color='green', label=f'Cut Period {variable}')

            ax.legend()
            ax.set(ylabel='PM(Mm-1)/10, TC2(C)', title='Please confirm the time period displayed is correct')

            # Format x axis to readable times
            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
            ax.xaxis.set_major_formatter(xfmt)
            for tick in ax.get_xticklabels():
                tick.set_rotation(30)

            #fig.canvas.draw()

        # print to log file
        io.write_logfile(logpath, logs)

        return calcavg, units, logs, timestring

def definePhaseData(Names, Data, Phases, Indices):
    Phasedatenums = {}
    Phasedata = {}
    Phasemean = {}
    for Phase in Phases:  # for each test phase
        # make data series of date numbers
        key = 'start_time_' + Phase
        startindex = Indices[key]
        key = 'end_time_' + Phase
        endindex = Indices[key]

        Phasedatenums[Phase] = Data['datenumbers'][startindex:endindex + 1]
        # make phase data series for each data channel
        for Name in Names:
            Phasename = Name + '_' + Phase
            Phasedata[Phasename] = Data[Name][startindex:endindex + 1]

            # calculate average value
            if Name != 'time' and Name != 'phase':
                print(Name)
                try:
                    print('1')
                    if all(np.isnan(Phasedata[Phasename])):
                        pass
                        #Phasemean[Phasename] = np.nan
                    else:
                        ave = np.nanmean(Phasedata[Phasename])
                        if 'datenumbers' in Name:
                            Phasemean[Phasename] = ave
                except:
                    nominals = []
                    print('2')
                    for uval in Phasedata[Phasename]:
                        try:
                            nominals.append(uval.n)
                        except:
                            pass
                    print('3')
                    if all(np.isnan(nominals)):
                        Phasemean[Phasename] = np.nan
                    else:
                        ave = sum(nominals) / len(nominals)
                        if 'datenumbers' in Name:
                            Phasemean[Phasename] = ave

        # time channel: use the mid-point time string
        Phasename = 'datenumbers_' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean

def loaddatastream(new_names, new_units, new_data, names, units, data):
    for name in new_names:
        # add new values to dictionary
        # Time is already in dictionary, rename to not overwrite data
        if name == 'time':
            newname = type + 'time'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # seconds is already in dictionary, rename to not overwrite data
        elif name == 'seconds':
            newname = type + 'seconds'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # all other data can be added without ov
        elif 'TC' in name: #senserion data also has TC channels - rename so they don't get mixed up
            newname = 'S' + name
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        else:
            names.append(name)
            data[name] = new_data[name]
            units[name] = new_units[name]

    # Convert date strings to date numbers for plotting
    name = type + 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data[type + 'time']):
        dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        data[name].append(dateobject)

    name = type + 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data[type + 'dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    return names, units, data


def run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval):
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath) 
    # Convert datetime str to readable value time objects
    [validnames, timeobject] = bkg.makeTimeObjects(titlenames, timestring, date)

    # Find 'phase' averging period
    phases = bkg.definePhases(validnames)

    # find indicieds in the data for start and end
    indices = bkg.findIndices(validnames, timeobject, datenums, samplerate)

    try:
        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

    except KeyError as e:
        e = str(e)
        message = f"Variable: {e} was entered incorrectly or is outside of the measured time period\n" \
                  f"* Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                  f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                  f"    * Check that the entered time exist within the data\n" \
                  f"    * Check that the time has not been left blank when there should be an entry.\n"
        title = "ERROR"
        easygui.msgbox(message, title, "OK")

        request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval)
        # Read in averaging period start and end times
        [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

        line = 'loaded: ' + periodpath
        print(line)
        logs.append(line)

        [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval)

    return avgdatenums, avgdata, avgmean, validnames, timeobject, phases

def request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval):

    startname = 'start_time_' + choice
    endname = 'end_time_' + choice

    start = timestring[startname]
    end = timestring[endname]
    periodnames = [startname, endname]

    # GUI box to edit input times
    zeroline = 'Enter start and end times for averaging period\n'
    firstline = 'Time format =' + eunits[startname] + '\n\n'
    secondline = 'Click OK to confirm entered values\n'
    thirdline = 'Click Cancel to exit\n'
    msg = zeroline + firstline + secondline + thirdline
    title = "Gitrdone"
    fieldnames = ['start_time', 'end_time']
    currentvals = [start, end]  # default values are phase start and end time
    newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)  # save new vals from user input
    if newvals:
        if newvals != currentvals:  # reassign user input to current vals
            currentvals = newvals
            eval[startname] = currentvals[0]
            eval[endname] = currentvals[1]
        else:
            line = 'Undefiend Variables'
            print(line)

    # Create new file with start and end times
    io.write_constant_outputs(periodpath, periodnames, eunits, eval, eunc, emetric)
    line = 'Created averaging times input file: ' + periodpath
    print(line)
    logs.append(line)


