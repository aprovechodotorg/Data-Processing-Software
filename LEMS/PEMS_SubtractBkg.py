#v0.5 Python3

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

# Subtracts background values from time series data
# GUI to edit start and end times of each test period, including the background periods
#  Plot to visualize the effects of background adjustment and subtraction
# Outputs:
#    1. Background subtracted time series data file, full length (all phases)
#    2. For each phase, background subtracted time series data file
#    3. For each phase, averages data file of average values of all data channels
#    4. Background subtraction report to terminal and log file

#v0.4: reads time format from energy inputs file and accepts 'hh:mm:ss' for lab tests and 'yyyy:mm:dd hh:mm:ss' for field tests
#v0.4: allows other background subtraction methods: pre,post,prepostave,prepostlin,realtime,none
#v0.4: adds offset to bkg subtraction
#v0.4: fixed slow code to define data['phase'] series
#v0.4: added measurement uncertainty inputs to averages
#v0.5: allows real-time background subtraction for COhi and CO2hi
#v0.6: added savefig to path, worked on issue where plots freeze when closed

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os
from uncertainties import ufloat

#########      inputs      ##############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
#raw data input file:
inputpath=os.path.abspath('RawData.csv')
#output data file to be created:
energyinputpath ='EnergyInputs.csv'
outputpath='TimeSeriesData.csv'
#Uncertainty data
ucpath = 'UCInputs.csv'
#output file of average values for each phase:
aveoutputpath='Averages.csv'
#input file of start and end times for background and test phase periods
timespath='PhaseTimes.csv'
#input file for bkgmethod and offset
bkgmethodspath='BkgMethods.csv'
logpath='log.txt'
##########################################

def PEMS_SubtractBkg(inputpath,energyinputpath,ucpath,outputpath,aveoutputpath,timespath,bkgmethodspath,logpath,
                     savefig1, savefig2, inputmethod, bkgoutputs):
    ver = '0.7'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_SubtractBkg v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    potentialBkgNames=['CO','CO2', 'CO2v','PM','COhi','CO2hi', 'VOC', 'CH4'] #define potential channel names that will get background subtraction
    bkgnames=[] #initialize list of actual channel names that will get background subtraction

    #################################################
    
    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)

    sample_rate = data['seconds'][1] - data['seconds'][0] #check the sample rate (time between seconds)
    ##############################################
     #check for measurement uncertainty input file
    if os.path.isfile(ucpath):
        line='\nMeasurement uncertainty input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        ucinputs={}
        for name in names:
            if name == 'time':
                ucinputs[name]=['absolute uncertainty','relative uncertainty']
            else:
                ucinputs[name] = [0,0]
        io.write_timeseries(ucpath,names,units,ucinputs)
    
        line='created measurement uncertainty input file:\n'+ucpath
        print(line)
        logs.append(line)
    
    #define which channels will get background subtraction
    #could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)

    #get the date from the time series data
    date=data['time'][0][:8]
    print(len(data['time']))
    
    #time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name]='date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name]=[]
    remove = []
    for n, val in enumerate(data['time']):
        try:
            dateobject=dt.strptime(val, '%Y%m%d %H:%M:%S')
            data[name].append(dateobject)
        except:
            remove.append(n)
    if len(remove) != 0:
        for n in remove:
            for name in names:
                data[name].pop(n)
            line = 'Removed line ' + str(n) + ' from data due to invalid time format'
            print(line)
            logs.append(line)

    name='datenumbers'
    units[name]='date'
    names.append(name)
    datenums=matplotlib.dates.date2num(data['dateobjects'])
    datenums=list(datenums)     #convert ndarray to a list in order to use index function
    data['datenumbers']=datenums
    
    #add phase column to time series data
    name='phase'
    names.append(name)
    units[name]='text'
    data[name]=['none']*len(data['time'])
    
    ##############################################
     #check for phase times input file
    if os.path.isfile(timespath):
        line='\nPhaseTimes input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        # load EnergyInputs file
        [enames,eunits,eval,eunc,euval] = io.load_constant_inputs(energyinputpath) 
        line = 'loaded energy input file to get phase start and end times: '+ energyinputpath
        print(line)
        logs.append(line)
        timenames = [enames[0]] #start with header
        
        #get the time format from the units label in the energyinputs file, should be date and time (for field tests), or just time (for lab tests)
        #for name in enames[1:]:
            #if 'start_time' in name or 'end_time' in name:
                #timeformatstring = eunits[name]
                #break
        for name in enames[1:]:
            if 'start_time' in name or 'end_time' in name:
                try: #dynamically test what format the times are written in
                    test=dt.strptime(eval[name], '%Y%m%d %H:%M:%S') #test to see if format works
                    timeformatstring = 'yyyymmdd hh:mm:ss'
                    break
                except:
                    try:
                        test=dt.strptime(eval[name], '%H:%M:%S') #test to see if format works
                        timeformatstring = 'hh:mm:ss'
                        break
                    except Exception as e:
                        print(e)

        #add prebkg start time
        name='start_time_prebkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            dateobject=data['dateobjects'][0]+timedelta(hours=0, minutes=4)     # time series data start time plus 4 minutes
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except:
            eval[name] = ''
        eunc[name] = ''
        
        #add prebkg end time
        name='end_time_prebkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            dateobject=data['dateobjects'][0] + timedelta(hours=0, minutes=14) # time series data start time plus 14 minutes
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except:
            eval[name] = ''
        eunc[name] = ''
        if 'start_time_lp' in enames: #if low power lab test
            starttime = eval['start_time_lp']
        if 'start_time_mp' in enames: #if medium power lab test
            starttime = eval['start_time_mp']  
        if 'start_time_hp' in enames: #if high power lab test
            starttime = eval['start_time_hp']
        if 'start_time_L1' in enames: #if IDC test
            starttime = eval['start_time_L1']
        if 'start_time_L5' in enames:
            starttime = eval['start_time_L5']
        if 'start_time_test' in enames: # if field test with one test phase
            starttime = eval['start_time_test']
        
        #add start and end times of test phases from the energy inputs file
        for name in enames[1:]:
            print(name)
            if 'start_time' in name or 'end_time' in name:
                timenames.append(name)
            else:
                try:
                    eval.pop(name)      #remove dictionary entry if variable is not a start or end time
                    eunc.pop(name)
                except:
                    pass
       
        #add post bkg start time
        name='start_time_postbkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            dateobject=data['dateobjects'][-1]-timedelta(hours=0, minutes=12)     # time series data end time minus 12 minutes
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except:
            eval[name] = ''
        eunc[name] = ''
        
        #add post bkg end time
        name='end_time_postbkg'
        timenames.append(name)
        eunits[name] = timeformatstring
        try:
            dateobject=data['dateobjects'][-1]-timedelta(hours=0, minutes=2)     # time series data end time minus 2 minutes
            if timeformatstring == 'hh:mm:ss':
                eval[name] = dateobject.strftime('%H:%M:%S')
            else:
                eval[name] = dateobject.strftime('%Y%m%d %H:%M:%S')
        except:
            eval[name] = ''
        eunc[name] = ''
        
        #GUI box to edit input times (for adding bkg times)
        zeroline='Enter background start and end times. If start and end times are unknown, verify that suggested ' \
                 'inputs are valid times within the data series and press ok. You will be given a chance to modify them later.\n'
        firstline='Time format = '+eunits['start_time_prebkg']+'\n\n'
        secondline='Click OK to continue\n'
        thirdline='Click Cancel to exit\n'
        msg=zeroline+firstline+secondline+thirdline
        title = "Gitrdone"
        fieldNames = timenames[1:]
        currentvals=[]
        for name in timenames[1:]:
            currentvals.append(eval[name])
        newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
        if newvals:
            if newvals != currentvals:
                currentvals = newvals
                for n,name in enumerate(timenames[1:]):
                    eval[name]=currentvals[n]
        else:
            line = 'Undefined variables: start_time_prebkg, end_time_prebkg, start_time_postbkg, end_time_postbkg'
            print(line)
            logs.append(line)
        io.write_constant_outputs(timespath,timenames,eunits,eval,eunc,euval)
        line = '\nCreated phase times input file:'
        print(line)
        logs.append(line)
    line=timespath
    print(line)
    logs.append(line)
    
     ##############################################

    #create background methods
    check = 0
    logs = bkgmethods(bkgmethodspath, logs, check, bkgnames)
    
    #########################################################
    
    #read in measurement uncertainty file
    [ucnames,ucunits,ucinputs] = io.load_timeseries(ucpath)
    
    #read in input file of phase start and end times
    [timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)
    
    #read in input file of background subtraction methods
    [channels,methods,offsets,methodsunc,methodsuval] = io.load_constant_inputs(bkgmethodspath)
    #convert offsets from str to float
    for channel in channels:
        try:
            offsets[channel]=float(offsets[channel])
        except:
            pass
    ###############################################
    try: #checking that all bkgseries exist in methods document(some were added later on)
        Data_bkgsubtracted = {}
        for name in names:    #for each channel
            Data_bkgsubtracted[name]=[]
            if name in bkgnames:    # that will get background subtraction
                #make bkg series
                Data_bkgsubtracted[name]= 1
                if methods[name] == 'pre':
                    pass
    except: #if a bkgseries doesn't exist, rerun methods document but make sure recreate it even if it exists
        check = 1
        logs = bkgmethods(bkgmethodspath, logs, check, bkgnames)
        # read in input file of background subtraction methods
        [channels, methods, offsets, methodsunc, methodsuval] = io.load_constant_inputs(bkgmethodspath)
        for channel in channels:
            try:
                offsets[channel] = float(offsets[channel])
            except:
                pass
    ######################################################
    cycle = 0
    (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
     offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases, phaseindices,
     phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new,
     phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs,
                                    timeunits, channels,
                                    methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, cycle, timespath, bkgmethodspath)

    if inputmethod == '1': #If in interactive mode
        #plot data to check bkg and test periods

        plt.ion()  #turn on interactive plot mode

        lw=float(5)    #define the linewidth for the data series
        plw=float(2)    #define the linewidth for the bkg and sample period marker
        msize=30        #marker size for start and end pints of each period

        colors={}
        for phase in phases:
            if phase == 'prebkg' or phase == 'postbkg':
                colors[phase] = 'r'
            elif phase == 'mp':
                colors[phase] = 'orange'
            elif phase == 'lp':
                colors[phase] = 'y'
            else:
                colors[phase]='lawngreen'

        f1, (ax1, ax2, ax3) = plt.subplots(3, sharex=True) # subplots sharing x axis
        plotnames=bkgnames
        for i, ax in enumerate(f1.axes):
            name=plotnames[i]
            ax.plot(data['datenumbers'],data_bkg[name],color='lavender',linewidth=lw,label='bkg_series')   #bkg data series
            ax.plot(data['datenumbers'],data[name],color='silver',linewidth=lw, label='raw_data')   #original data series
            ax.plot(data['datenumbers'],data_new[name],color='k',linewidth=lw,label='bkg_subtracted')   #bkg subtracted data series
            for phase in phases:
                phasename=name+'_'+phase
                ax.plot(phasedatenums[phase],phasedata[phasename],color=colors[phase],linewidth=plw,label=phase)    #original
                ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                ax.plot(phasedatenums[phase],phasedata_new[phasename],color=colors[phase],linewidth=plw)    #bkg shifted
                ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
            ax.set_ylabel(units[name])
            ax.set_title(name)
            ax.grid(visible=True, which='major', axis='y')

        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
        #plt.xlabel('time')
        #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
        #plt.legend(fontsize=10).draggable()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
        plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it verically to make room for the long x axis data labels
        ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1

        #####################################################
        #second figure for 3 more subplots
        f2, (ax4, ax5, ax6) = plt.subplots(3, sharex=True) # subplots sharing x axis
        try:
            for i, ax in enumerate(f2.axes):
                name=plotnames[i+3]
                ax.plot(data['datenumbers'],data_bkg[name],color='lavender',linewidth=lw,label='bkg_series')   #bkg data series
                ax.plot(data['datenumbers'],data[name],color='silver',linewidth=lw, label='raw_data')   #original data series
                ax.plot(data['datenumbers'],data_new[name],color='k',linewidth=lw,label='bkg_subtracted')   #bkg subtracted data series
                for phase in phases:
                    phasename=name+'_'+phase
                    ax.plot(phasedatenums[phase],phasedata[phasename],color=colors[phase],linewidth=plw,label=phase)    #original
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                    ax.plot(phasedatenums[phase],phasedata_new[phasename],color=colors[phase],linewidth=plw)    #bkg shifted
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                ax.set_ylabel(units[name])
                ax.set_title(name)
                ax.grid(visible=True, which='major', axis='y')
        except:
            print('3 plots created')
        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
        #plt.xlabel('time')
        #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
        #plt.legend(fontsize=10).draggable()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
        plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it vertically to make room for the long x axis data labels
        ax4.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1

        plt.show() #show all figures
        ###############################################################################################

        running = 'fun'
        while (running == 'fun'):
            #GUI box to edit input times

            zeroline='Edit phase times\n'
            firstline='Time format = '+timeunits['start_time_prebkg']+'\n\n'
            nextline=f'Edit background subtraction methods\nFormat = method,offset\nMethods: pre,post,prepostave,' \
                     f'prepostlin,none\n\n'\
                     f'Pre finds the average value from the background period before the test and subtracts that value from ' \
                     f'all values. Post does the same with the background period after the test. Prepoststave finds the mean ' \
                     f'between the pre and post background periods and subtracts that from all values. Prepostlin finds the ' \
                     f'linear equation between the pre and post background periods and uses that to subtract from all value.\n' \
                     f'IF BOTH PRE AND POST BACKGROUND PERIODS ARE FLAT, THE PREFERED METHOD IS PREPOSTLIN.\n' \
                     f'Offsets: Offset by a specified value (add value to every number in data series)\n\n'
            secondline='Click OK to update plot\n'
            thirdline='Click Cancel to exit\n'
            msg=zeroline+firstline+nextline+secondline+thirdline
            title = "Gitrdone"
            fieldNames = timenames[1:]
            currentvals=[]
            for name in timenames[1:]:
                currentvals.append(timestring[name])
            #append methods and offsets
            for name in channels[1:]:
                fieldNames.append(name)
                methodstring=methods[name]+','+str(offsets[name])
                currentvals.append(methodstring)
            newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)
            if newvals:
                if newvals != currentvals:
                    currentvals = newvals
                    for n,name in enumerate(fieldNames):
                        if 'time' in name:
                            timestring[name]=currentvals[n]
                        else:
                            try:
                                spot=currentvals[n].index(',')    #locate the comma
                                methods[name]=currentvals[n][:spot]  #grab the string before the comma
                                offsets[name] = currentvals[n][spot+1:]  #grab the string after the comma
                            except ValueError:
                                message = f"Background method for {name} was not entered correctly. The Expected format is method,offset. Previous working methods will be shown again. When entering a new method please ensure the comma remains."
                                title = "ERROR"
                                easygui.msgbox(message, title, "OK")
                                (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits,
                                 channels, methods,
                                 offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames,
                                 timeobject, phases,
                                 phaseindices,
                                 phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums,
                                 phasedata_new,
                                 phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate,
                                                                names, data, ucinputs,
                                                                timeunits, channels,
                                                                methods, offsets, methodsunc, methodsuval, timeunc,
                                                                timeuval, logs,
                                                                bkgnames, cycle, timespath, bkgmethodspath)

                    io.write_constant_outputs(bkgmethodspath,channels,methods,offsets,methodsunc,methodsuval)
                    line = 'Updated background subtraction methods input file:'+bkgmethodspath
                    print(line)
                    logs.append(line)

                    #convert offsets from str to float
                    for channel in channels:
                        try:
                            offsets[channel]=float(offsets[channel])
                        except:
                            pass

                    io.write_constant_outputs(timespath,timenames,timeunits,timestring,timeunc,timeuval)
                    line = 'Updated phase times input file:'+timespath
                    print(line)
                    logs.append(line)
            else:
                running = 'not fun'
                #plt.ioff()  # turn off interactive plot
                #plt.close(f1)  # close plot
                #plt.close(f2)

            cycle = 1
            (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
             offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases,
             phaseindices,
             phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new,
             phasemean_new) = run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs,
                                            timeunits, channels,
                                            methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs,
                                            bkgnames, cycle, timespath, bkgmethodspath)

            reportlogs = printBkgReport(phases, bkgnames, bkgvalue, phasemean, phasemean_new, units, methods, offsets)

            ###################################################################

            #update plot

            ax1.get_legend().remove()

            for i, ax in enumerate(f1.axes):
                for n in range(len(ax.lines)):
                    plt.Artist.remove(ax.lines[0])
                name=plotnames[i]
                ax.plot(data['datenumbers'],data_bkg[name],color='lavender',linewidth=lw,label='bkg_series')   #bkg data series
                ax.plot(data['datenumbers'],data[name],color='silver',linewidth=lw,label='raw_data')   #original data series
                ax.plot(data['datenumbers'],data_new[name],color='k',linewidth=lw,label='bkg_subtracted')   #bkg subtracted data series
                for phase in phases:
                    phasename=name+'_'+phase
                    ax.plot(phasedatenums[phase],phasedata[phasename],color=colors[phase],linewidth=plw,label=phase)    #original
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)

                    ax.plot(phasedatenums[phase],phasedata_new[phasename],color=colors[phase],linewidth=plw)    #bkg shifted
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                    ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)

            ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1

            f1.savefig(savefig1, bbox_inches='tight')
            f1.canvas.draw()
            #plt.show(f1, block=None)
            #f1.show()
            #######################################################
            #second figure for 3 more subplots
            ax4.get_legend().remove()
            try:
                for i, ax in enumerate(f2.axes):
                    for n in range(len(ax.lines)):
                        plt.Artist.remove(ax.lines[0])
                    name=plotnames[i+3]
                    ax.plot(data['datenumbers'],data_bkg[name],color='lavender',linewidth=lw,label='bkg_series')   #bkg data series
                    ax.plot(data['datenumbers'],data[name],color='silver',linewidth=lw,label='raw_data')   #original data series
                    ax.plot(data['datenumbers'],data_new[name],color='k',linewidth=lw,label='bkg_subtracted')   #bkg subtracted data series
                    for phase in phases:
                        phasename=name+'_'+phase
                        ax.plot(phasedatenums[phase],phasedata[phasename],color=colors[phase],linewidth=plw,label=phase)    #original
                        ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                        ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)

                        ax.plot(phasedatenums[phase],phasedata_new[phasename],color=colors[phase],linewidth=plw)    #bkg shifted
                        ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                        ax.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata_new[phasename][0],phasedata_new[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
            except:
                print('3 plots created')
            ax4.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
            f2.savefig(savefig2, bbox_inches='tight')
            f2.canvas.draw()
            #plt.show(f2, block=None)
            #f2.show()
    elif inputmethod == '2':
        reportlogs = []
    #output new background subtracted time series data file 
    #first add the background data series that were used for the subtraction    
    newnames=[]
    for name in names:
        newnames.append(name)
    for name in bkgnames:
        addname = name+'_bkg'
        newnames.append(addname)
        data_new[addname]=data_bkg[name]
        units[addname]=units[name]

    io.write_timeseries(outputpath,newnames,units,data_new)
    
    line='created background-corrected time series data file:\n'+outputpath
    print(line)
    logs.append(line)
    
    #output time series data file for each phase
    for phase in phases:
        phaseoutputpath=outputpath[:-4]+'_'+phase+'.csv'    #name the output file by inserting the phase name into the outputpath
        phasedataoutput={}  #initialize a dictionary of phase time series data for the output file
        for name in names:
            phasename=name+'_'+phase      
            phasedataoutput[name]=phasedata_new[phasename]
        io.write_timeseries(phaseoutputpath,names,units,phasedataoutput)
    
        line='created background-corrected time series data file:\n'+phaseoutputpath
        print(line)
        logs.append(line)

    # output background concs pre and post, times, and methods
    outnames = []
    outunits = {}
    outvals = {}
    outunc = {}
    outdata = {}

    name = 'variable'
    outnames.append(name)
    outunits[name] = 'units'
    outvals[name] = 'value'
    outunc[name] = 'uncertainty'

    name = 'start_time_prebkg'
    outnames.append(name)
    outunits[name] = timeunits[name]
    outvals[name] = timestring[name]

    name = 'end_time_prebkg'
    outnames.append(name)
    outunits[name] = timeunits[name]
    outvals[name] = timestring[name]

    name = 'start_time_postbkg'
    outnames.append(name)
    outunits[name] = timeunits[name]
    outvals[name] = timestring[name]

    name = 'end_time_postbkg'
    outnames.append(name)
    outunits[name] = timeunits[name]
    outvals[name] = timestring[name]

    for b in bkgnames:
        name = f'{b}_method'
        outnames.append(name)
        outunits[name] = ''
        outvals[name] = methods[b]

        name = f'{b}_offset'
        outnames.append(name)
        outunits[name] = ''
        outvals[name] = offsets[b]

        name = f'{b}_prebkg_conc'
        outnames.append(name)
        outunits[name] = units[b]
        outvals[name] = phasemean[f'{b}_prebkg'].n
        outdata[name] = phasemean[f'{b}_prebkg']

        name = f'{b}_postbkg_conc'
        outnames.append(name)
        outunits[name] = units[b]
        outvals[name] = phasemean[f'{b}_postbkg'].n
        outdata[name] = phasemean[f'{b}_postbkg']

    io.write_constant_outputs(bkgoutputs, outnames, outunits, outvals, outunc, outdata)
    line = f"Created outputs of background values and method used: {bkgoutputs}"
    print(line)
    logs.append(line)

    # output average values  #####################
    phasenames=[]  
    phaseunits={}
    vals={}
    unc={}
    
    for phase in phases:
        for name in names:
            phasename=name+'_'+phase     
            phasenames.append(phasename)
            if name=='time':
                phaseunits[phasename]='yyyymmdd hh:mm:ss'
            else:
                phaseunits[phasename]=units[name]
    
    #make header for averages file
    name='variable_name'    
    phasenames = [name]+phasenames
    phaseunits[name]='units'
    phasemean_new[name]='average'
    unc[name]='uncertainty'
            
    io.write_constant_outputs(aveoutputpath,phasenames,phaseunits,vals,unc,phasemean_new)    
    
    line='created phase averages data file:\n'+aveoutputpath
    print(line)
    logs.append(line)    
    #############################################
    
    #print final report to logs
    logs=logs+reportlogs
    
    #print to log file
    io.write_logfile(logpath,logs)

    return logs, methods, timestring, phasemean_new

def run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels,
                  methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, cycle, timespath, bkgmethodspath):
    [validnames, timeobject] = makeTimeObjects(timenames, timestring, date)  # convert time strings to time objects

    phases = definePhases(validnames)  # read the names of the start and end times to get the name of each phase

    phaseindices = findIndices(validnames, timeobject, datenums,
                               sample_rate)  # find the indices in the time data series for the start and stop times of each phase

    try:
        [phasedatenums, phasedata, phasemean] = definePhaseData(names, data, phases, phaseindices,
                                                                ucinputs)  # define phase data series for each channel
    except KeyError as e:
        e = str(e)
        message = f"Variable: {e} was entered incorrectly or is outside of the measured time period\n" \
                  f"* Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                  f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                  f"    * Check that the entered time exist within the data\n" \
                  f"    * Check that the time has not been left blank when there should be an entry.\n"
        title = "ERROR"
        easygui.msgbox(message, title, "OK")
        timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs = request_entry(
            timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval,
            logs, timespath, bkgmethodspath)
        (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
            offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases, phaseindices,
            phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new, phasemean_new) =run_functions(timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels,
                  methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, cycle, timespath, bkgmethodspath)

    if cycle == 1:
        # update the data series column named phase
        name = 'phase'
        data[name] = ['none'] * len(data['time'])  # clear all values to none
        for phase in phases:
            for n, val in enumerate(data['time']):
                if n >= phaseindices['start_time_' + phase] and n <= phaseindices['end_time_' + phase]:
                    if data[name][n] == 'none':
                        data[name][n] = phase
                    else:
                        data[name][n] = data[name][n] + ',' + phase

    [bkgvalue, data_bkg, data_new] = bkgSubtraction(names, data, bkgnames, phasemean, phaseindices, methods,
                                                    offsets)  # subtract the background

    [phasedatenums, phasedata_new, phasemean_new] = definePhaseData(names, data_new, phases, phaseindices,
                                                                    ucinputs)  # define phase data series after background subtraction
    io.write_constant_outputs(bkgmethodspath, channels, methods, offsets, methodsunc, methodsuval)
    return (timenames, timestring, date, datenums, sample_rate, names, data, ucinputs, timeunits, channels, methods,
            offsets, methodsunc, methodsuval, timeunc, timeuval, logs, bkgnames, validnames, timeobject, phases, phaseindices,
            phasedatenums, phasedata, phasemean, bkgvalue, data_bkg, data_new, phasedatenums, phasedata_new, phasemean_new)

    
def makeTimeObjects(Timenames,Timestring,Date):
    Timeobject={}   #initialize a dictionary of time objects
    Validnames=[] #initialize a list of time names that have a valid time entered
    for Name in Timenames:
        if len(Timestring[Name]) == 8:  #if time format
            Datestring=Date+' '+Timestring[Name]    #add the date to the time string
        else:   #if already date format
            Datestring = Timestring[Name]   #use it as is
        try:
            Timeobject[Name]=dt.strptime(Datestring, '%Y%m%d %H:%M:%S')                #convert the time string to date object
            Validnames.append(Name)
        except:
            try:
                Timeobject[Name] = dt.strptime(Datestring, '%Y-%m-%d %H:%M:%S')  # convert the time string to date object
                Validnames.append(Name)
            except:
                pass
    return Validnames,Timeobject

def request_entry(timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc,
                  timeuval, logs, timespath, bkgmethodspath):
    zeroline = f'ONE OR MORE INVALID PHASE TIMES.\n' \
               f"EDIT PHASE TIMES AND TRY AGAIN\n"
    firstline = 'Time format = ' + timeunits['start_time_prebkg'] + '\n\n'
    nextline = f'Edit background subtraction methods\nFormat = method,offset\nMethods: pre,post,prepostave,prepostlin,none\n\n' \
               f'Pre finds the average value from the background period before the test and subtracts that value from ' \
               f'all values. Post does the same with the background period after the test. Prepoststave finds the mean ' \
               f'between the pre and post background periods and subtracts that from all values. Prepostlin finds the ' \
               f'linear equation between the pre and post background periods and uses that to subtract from all value.\n' \
               f'IF BOTH PRE AND POST BACKGROUND PERIODS ARE FLAT, THE PREFERED METHOD IS PREPOSTLIN.\n' \
               f'Offsets: Offset by a specified value (add value to every number in data series)\n\n'
    secondline = 'Click OK to update plot\n'
    thirdline = 'Click Cancel to exit\n'
    msg = zeroline + firstline + nextline + secondline + thirdline
    title = "Gitrdone"
    fieldNames = timenames[1:]
    currentvals = []
    for name in timenames[1:]:
        currentvals.append(timestring[name])
    # append methods and offsets
    for name in channels[1:]:
        fieldNames.append(name)
        methodstring = methods[name] + ',' + str(offsets[name])
        currentvals.append(methodstring)
    newvals = easygui.multenterbox(msg, title, fieldNames, currentvals)
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
            for n, name in enumerate(fieldNames):
                if 'time' in name:
                    timestring[name] = currentvals[n]
                else:
                    spot = currentvals[n].index(',')  # locate the comma
                    methods[name] = currentvals[n][:spot]  # grab the string before the comma
                    offsets[name] = currentvals[n][spot + 1:]  # grab the string after the comma

            io.write_constant_outputs(bkgmethodspath, channels, methods, offsets, methodsunc, methodsuval)
            line = 'Updated background subtraction methods input file:' + bkgmethodspath
            print(line)
            logs.append(line)

            # convert offsets from str to float
            for channel in channels:
                try:
                    offsets[channel] = float(offsets[channel])
                except:
                    pass

            io.write_constant_outputs(timespath, timenames, timeunits, timestring, timeunc, timeuval)
            line = 'Updated phase times input file:' + timespath
            print(line)
            logs.append(line)

    return timeunits, timenames, timestring, channels, methods, offsets, methodsunc, methodsuval, timeunc, timeuval, logs
        
def definePhases(Timenames):
    Phases=[] #initialize a list of test phases (prebkg, low power, med power, high power, post bkg)    
    for Name in Timenames:
        spot=Name.rindex('_')           #locate the last underscore
        Phase=Name[spot+1:]         #grab the string after the last underscore
        if Phase not in Phases:             #if it is a new phase
            Phases.append(Phase)            #add to the list of phases
    return Phases
           
def findIndices(InputTimeNames,InputTimeObject,Datenums, Sample_Rate):
    InputTimeDatenums={}
    Indices={}
    for Name in InputTimeNames:
        m = 0
        ind = 0
        while m <= (Sample_Rate * 2) + 1 and ind == 0:
            try:
                InputTimeDatenums[Name] = matplotlib.dates.date2num(InputTimeObject[Name])
                Indices[Name]=Datenums.index(InputTimeDatenums[Name])
                ind = 1
            except:
                print(InputTimeObject[Name])
                InputTimeObject[Name] = InputTimeObject[Name] + timedelta(seconds=1)
                m += 1
    return Indices
        
def definePhaseData(Names,Data,Phases,Indices,Ucinputs):
    Phasedatenums={}
    Phasedata={}
    Phasemean={}
    for Phase in Phases: #for each test phase
        #make data series of date numbers
        key='start_time_'+Phase
        startindex=Indices[key]
        key='end_time_'+Phase
        endindex=Indices[key]
        Phasedatenums[Phase]=Data['datenumbers'][startindex:endindex+1]    
        #make phase data series for each data channel

        for Name in Names:
            Phasename=Name+'_'+Phase
            Phasedata[Phasename]=Data[Name][startindex:endindex+1]

            remove = []
            for n, val in enumerate(Phasedata[Phasename]):
                if val == '':
                    remove.append(n)
            if len(remove) != 0:
                for n in remove:
                    for name in Names:
                        Phasedata[Name + '_' + Phase].pop(n)
            #calculate average value
            if Name != 'time' and Name != 'phase':
                non_nan_values = [value for value in Phasedata[Phasename] if not np.isnan(value)]
                if len(non_nan_values) == 0:
                    Phasemean[Phasename] = np.nan
                else:
                    ave = np.mean(non_nan_values)
                    if Name == 'datenumbers':
                        Phasemean[Phasename] = ave
                    else:
                        uc = abs(float(Ucinputs[Name][0]) + ave * float(Ucinputs[Name][1]))
                        Phasemean[Phasename] = ufloat(ave, uc)
                    
        #time channel: use the mid-point time string
        Phasename='datenumbers_'+Phase
        Dateobject=matplotlib.dates.num2date(Phasemean[Phasename]) #convert mean date number to date object
        Phasename='time_'+Phase
        Phasemean[Phasename]=Dateobject.strftime('%Y%m%d %H:%M:%S')  

        #phase channel: use phase name
        Phasename='phase_'+Phase
        Phasemean[Phasename]=Phase

    return Phasedatenums,Phasedata,Phasemean
         
def bkgSubtraction(Names,Data,Bkgnames,Phasemean,Indices,Methods,Offsets):
    Bkgvalue={}                 #dictionary of constant bkg values
    Data_bkgseries={}                   #data series that will get subtracted
    Data_bkgsubtracted={}           #new data series after bkg subtraction

    for Name in Names:
        remove = []
        for n, val in enumerate(Data[Name]):
            if val == '':
                remove.append(n)
        if len(remove) != 0:
            for Name in Names:
                for n in remove:
                    Data[Name].pop(n)
    for Name in Names:    #for each channel
        Data_bkgsubtracted[Name]=[]
        if Name in Bkgnames:    # that will get background subtraction
            #make bkg series
            Data_bkgseries[Name]=[]
            if Methods[Name] == 'pre':
                Bkgvalue[Name] = Phasemean[Name+'_prebkg'].n-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'post':
                Bkgvalue[Name] = Phasemean[Name+'_postbkg'].n-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostave':
                Bkgvalue[Name]=np.mean([Phasemean[Name+'_prebkg'].n,Phasemean[Name+'_postbkg'].n])-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostlin':
                Bkgvalue[Name] = -Offsets[Name]
                x1 = int((Indices['start_time_prebkg']+Indices['end_time_prebkg']+1)/2) #middle index of prebkg
                y1 = Phasemean[Name+'_prebkg'].n      #prebkg average value
                x2 = int((Indices['start_time_postbkg']+Indices['end_time_postbkg']+1)/2) #middle index of postbkg
                y2 = Phasemean[Name+'_postbkg'].n     #post bkg average value
                #equation of line from 2 points, y=mx+b
                m = (y2-y1)/(x2-x1)
                b = y1-x1*(y2-y1)/(x2-x1)
                for x,val in enumerate(Data[Name]):
                    y = m*x+b
                    Data_bkgseries[Name].append(y+Bkgvalue[Name])
            elif Methods[Name] == 'realtime':
                Bkgvalue[Name] = -Offsets[Name]
                if 'hi' in Name:
                    bkgseriesname = Name[:-2]
                else:
                    bkgseriesname = Name

                for x,val in enumerate(Data[bkgseriesname+'bkg']):      #realtime bkg series
                    Data_bkgseries[Name].append(val+Bkgvalue[Name])
            else:
                Bkgvalue[Name] = -Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])

            #subtract bkg data series
            for n,val in enumerate(Data[Name]):

                try:
                    newval=val-Data_bkgseries[Name][n]
                    Data_bkgsubtracted[Name].append(newval)
                except:
                    print('Val')
                    print(val)
                    print('Data')
                    print(Data_bkgseries[Name][n])
                    Data[Name].pop(n)
        else:   #if no bkg subtraction
            Data_bkgsubtracted[Name]=Data[Name]

    return Bkgvalue, Data_bkgseries, Data_bkgsubtracted
    
def printBkgReport(Phases,Bkgnames,Bkgvalue,Phasemean,Phasemean_new,Units,Methods,Offsets):  #add arg to print to log file        
    Reportlogs=[]
    line= '\nbackground subtraction report:'
    print(line)
    Reportlogs.append(line)
    line='\nphase averages before background subtraction:'
    print(line)
    Reportlogs.append(line)
    line1='channel'.ljust(10)+'units'.ljust(10)
    line2='-------'.ljust(10)+'-----'.ljust(10)
    for Phase in Phases:
        line1=line1+Phase.ljust(10)
        line2=line2+'------'.ljust(10)
    line1=line1+'bkgValue'.ljust(10)+'offset'.ljust(10)+'method'.ljust(10)
    line2=line2+'------'.ljust(10)+'------'.ljust(10)+'------'.ljust(10)
    print(line1)
    Reportlogs.append(line1)
    print(line2)
    Reportlogs.append(line2)
    for Name in Bkgnames:
        line=Name.ljust(10)+str(Units[Name]).ljust(10)
        for Phase in Phases:
            Phasename=Name+'_'+Phase
            line=line+str(round(Phasemean[Phasename].n,1)).ljust(10)
        line=line+str(round(Bkgvalue[Name],1)).ljust(10)+str(round(Offsets[Name],1)).ljust(10)+Methods[Name].ljust(10)
        print(line)
        Reportlogs.append(line)
        
    line='\nphase averages after background subtraction:'
    print(line)
    Reportlogs.append(line)
    print(line1)
    Reportlogs.append(line1)
    print(line2)
    Reportlogs.append(line2)
    for Name in Bkgnames:
        line=Name.ljust(10)+str(Units[Name]).ljust(10)
        for Phase in Phases:
            Phasename=Name+'_'+Phase
            line=line+str(round(Phasemean_new[Phasename].n,1)).ljust(10)
        #line=line+'0.0'.ljust(10)
        print(line)
        Reportlogs.append(line)
        
    return Reportlogs

def bkgmethods(bkgmethodspath, logs, check, bkgnames):
     #check for background subtraction methods input file
    if os.path.isfile(bkgmethodspath) and check != 1:
        line='\nBackground subtraction methods input file already exists:'
        print(line)
        logs.append(line)
    else:   #if input file is not there then create it
        working = False
        while working == False:
            #GUI box to edit background subtraction methods
            zeroline='Enter background subtraction: method,offset\n\n'
            firstline='methods: pre, post, prepostave, prepostlin, realtime, none\n\n'
            secondline='Click OK to continue\n'
            thirdline='Click Cancel to exit\n'
            msg=zeroline+firstline+secondline+thirdline
            title = "Gitrdone"
            fieldNames = bkgnames
            currentvals=[]
            for name in fieldNames:
                currentvals.append('pre,0')
            newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)
            if newvals:
                if newvals != currentvals:
                    currentvals = newvals
            else:
                line = 'Error: Undefined background subtraction methods'
                print(line)
                logs.append(line)
            methods={}   #initialize dictionary of background subtraction methods
            offsets={}   #initialize dictionary of background subtraction offsets
            blank={}    #initialize dictionary of blank values
            fieldNames=['channel']+fieldNames   #add header
            methods['channel']='method'  #add header
            offsets['channel']='offset'      #add header
            error = 0
            for n,name in enumerate(fieldNames[1:]):    #for each channel
                try:
                    spot=currentvals[n].index(',')    #locate the comma
                    methods[name]=currentvals[n][:spot]  #grab the string before the comma
                    offsets[name] = currentvals[n][spot+1:]  #grab the string after the comma
                    blank[name] = ''
                except ValueError:
                    message = f"Background method for {name} was entered incorrectly. Correct format is method,offset. Default will be shown again, when entering a new method please ensure comma remains."
                    title = "ERROR"
                    easygui.msgbox(message, title, "OK")
                    error = 1
            if error != 1:
                working = True
        io.write_constant_outputs(bkgmethodspath,fieldNames,methods,offsets,blank,blank)
        line = '\nCreated background subtraction methods input file:'
        print(line)
        logs.append(line)
    line=bkgmethodspath
    print(line)
    logs.append(line)

    return logs
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_SubtractBkg(inputpath,energyinputpath,ucpath,outputpath,aveoutputpath,timespath,bkgmethodspath,logpath)

