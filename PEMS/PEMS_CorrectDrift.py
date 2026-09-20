#v0.9 Python3

#    Copyright (C) 2026 Mountain Air Engineering 
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
#    Contact: ryan@mtnaireng.com

# Corrects time series data for temperature drift

# started with subtract bkg function so drift correction is treated as bkg subtraction
#  Plot to visualize the effects of background adjustment and subtraction
# Outputs:
#    1. Background subtracted time series data file, full length (all phases)
#    2. For each phase, background subtracted time series data file
#    3. For each phase, averages data file of average values of all data channels
#    4. Background subtraction report to terminal and log file

# v0.8 for Possum1
# v0.9 for Possum2

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
try:
    import readline   #enables editable default text in input() prompts; not available on plain Windows without pyreadline3
    def input_with_prefill(prompt,prefill=''):
        readline.set_startup_hook(lambda: readline.insert_text(prefill))
        try:
            return input(prompt)
        finally:
            readline.set_startup_hook()
except ImportError:
    def input_with_prefill(prompt,prefill=''):   #fallback: show the default and use it if the user just presses enter
        result = input(prompt+'['+prefill+']: ')
        return result if result else prefill
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os
from uncertainties import ufloat
import math

#########      inputs      ##############
#raw data input file:
inputpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_RawData2.csv'
#output data file to be created:
outputpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_TimeSeriesData.csv'
#output file of average values for each phase:
aveoutputpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
#input file of start and end times for background and test phase periods
timespath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def PEMS_CorrectDrift(inputpath,headerpath,outputpath,timespath,methodspath,logpath):
    ver = '0.9'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CorrectDrift v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    #################################################
    
    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)
    
    #if the phase times input file doesn't exist yet, create a blank one
    if not os.path.isfile(timespath):
        timenames = ['point']
        starttimes = {'point':'starttime'}
        endtimes = {'point':'endtime'}
        timeunc = {'point':'unc'}
        timeuval = {'point':'uval'}
        io.write_constant_outputs(timespath, timenames, starttimes, endtimes, timeunc, timeuval)
        line = 'created blank phase times input file:\n'+timespath
        print(line)
        logs.append(line)

    #if the drift methods input file doesn't exist yet, create a blank one
    if not os.path.isfile(methodspath):
        channames = ['point']
        methodsdict = {'point':'method'}
        offsetsdict = {'point':'offset'}
        methodsuncdict = {'point':'unc'}
        methodsuvaldict = {'point':'uval'}
        io.write_constant_outputs(methodspath, channames, methodsdict, offsetsdict, methodsuncdict, methodsuvaldict)
        line = 'created blank drift methods input file:\n'+methodspath
        print(line)
        logs.append(line)

    if os.path.isfile(timespath) and os.path.isfile(methodspath):
    
        #get the date from the time series data
        date=data['time'][0][:8]
    
        #time channel: convert date strings to date numbers for plotting
        name = 'dateobjects'
        units[name]='date'
        #names.append(name) #don't add to print list because time object cant print to csv
        data[name]=[]
        for n,val in enumerate(data['time']):
            dateobject=dt.strptime(val, '%Y%m%d %H:%M:%S')
            data[name].append(dateobject)   
    
        name='datenumbers'
        units[name]='date'
        names.append(name)
        datenums=matplotlib.dates.date2num(data['dateobjects'])
        datenums=list(datenums)     #convert ndarray to a list in order to use index function
        data['datenumbers']=datenums
  
        #####################################################

        #read in input file of phase start and end times
        [timenames,starttimes,endtimes,timeunc,timeuval] = io.load_constant_inputs(timespath)

        #read in input file of subtraction methods
        [channels,methods,offsets,methodsunc,methodsuval] = io.load_constant_inputs(methodspath)
        #convert offsets from str to float
        for channel in channels:
            try:
                offsets[channel]=float(offsets[channel])
            except:
                pass
        originalchannels = list(channels)   #remember which channels already had a method/offset defined in the input file
        ###############################################
    
        [validnames,starttimeobjects,endtimeobjects]=makeTimeObjects(timenames,starttimes,endtimes,date)  #convert time strings to time objects
        #validnames = list of valid timenames
        phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase
        #phases = list of phase names = ['pre,'post']
    
        #validnames = list of valid timenames
        #starttimeobjects[validnames] = dictionary of time objects for timenames
        #datenums = time data series
        startindices = findIndices(validnames,starttimeobjects,datenums)  #find the indices in the time data series for the start times 
        #startindices[validnames] = dictionary of indices

        #endtimeobjects[validnames] = dictionary of time objects for timenames
        endindices = findIndices(validnames,endtimeobjects,datenums)  #find the indices in the time data series for the stop times
        #endindices[validnames] = dictionary of indices

        [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,validnames,startindices,endindices)   #define phase data series for each channel
        #phasedatenums[validnames] = dictionary of datenumber series
        #phasedata[validnames] = dictionary of data series
        #phasemean[validnames] = dictionary of mean values 
    
        [bkgvalue,data_bkg, data_new] = bkgSubtraction(names,data,channels,phasemean,startindices,endindices,methods,offsets) #subtract the background

        [phasedatenums,phasedata_new,phasemean_new] = definePhaseData(names,data_new,validnames,startindices,endindices)   #define phase data series after background subtraction

        bkgnames=channels[1:]

        #print the drift correction report before plotting
        reportlogs = printBkgReport(phases,bkgnames,bkgvalue,phasemean,phasemean_new,units,methods,offsets)
                 
        ##################################################################
        #recalculate some channels
        #open header file and read in new cal params
        [headernames,headerunits,A,B,C,D,const] = io.load_header(headerpath)

        def recalcChannels():
            recalcedchannels = []

            for checkname in ['Pitot','Pamb','TCnoz']:
                if checkname in bkgnames:
                    name='StakVel'
                    recalcedchannels.append(name)
                    #StakVel=Cp*Kp*sqrt(Pres1*(TCnoz+273)/Pamb/MolWt)
                    data_new[name]=[]
                    Kp=float(129)
                    Cpitot = const['Cpitot(-)']
                    MolWt = const['MolWt(g/mol)']
                    for n in range(len(data[name])):
                        Pres1val=float(data_new['Pitot'][n])
                        Pambval=float(data_new['Pamb'][n])
                        TCnozval=data_new['TCnoz'][n]
                        if TCnozval=='nan':
                            newval='nan'
                        else:
                            TCnozval=float(TCnozval)
                            if Pres1val < 0:
                                Pres1val = -Pres1val
                                newval=-Cpitot*Kp*math.sqrt(Pres1val*(TCnozval+273.15)/Pambval/MolWt)
                            else:
                                newval=Cpitot*Kp*math.sqrt(Pres1val*(TCnozval+273.15)/Pambval/MolWt)
                        data_new[name].append(newval) 
                    print (name+' recalculated')
                    break

            for checkname in ['F1Flow','F2Flow','FiltFlow','SampFlow','TapFlow','UsampFlow','DilFlow','Pamb','TCnoz']:
                if checkname in bkgnames:
                    name='NozVel'   #NozVel=(F1Flow+F2Flow+GasFlow+TAPflow+IsoFlow-DilFlow)*101325/Pamb*(TCnoz+273)/293/60*4/pi/NozDiam^2
                    data_new[name]=[]
                    recalcedchannels.append(name)
                    NozDiam = const['NozDiam(mm)']
                    Pstd=float(101325)
                    Tstd=float(293)
                    for n in range(len(data[name])):
                        F1Flowval=float(data_new['F1Flow'][n])
                        F2Flowval=float(data_new['F2Flow'][n])
                        GasFlowval=float(data_new['SampFlow'][n])
                        TAPflowval=float(data_new['TAPflow'][n])
                        IsoFlowval=float(data_new['USampFlow'][n])
                        DilFlowval=float(data_new['DilFlow'][n])
                        nozzleflow=F1Flowval+F2Flowval+GasFlowval+TAPflowval+IsoFlowval-DilFlowval
                        Pambval=float(data_new['Pamb'][n])
                        TCnozval=data_new['TCnoz'][n]
                        if TCnozval=='nan':
                            newval='nan'
                        else:
                            TCnozval=float(TCnozval)
                            newval=nozzleflow*Pstd/Pambval*(TCnozval+273)/Tstd/60*4/math.pi/math.pow(NozDiam,2)
                        data_new[name].append(newval)
                    print(name+' recalculated')
                    break

            for checkname in ['F1Flow','F2Flow','FiltFlow','SampFlow','TapFlow','UsampFlow','DilFlow']:
                if checkname in bkgnames:
                    name='DilRat'
                    #DilRat=DilFlow/(F1Flow+F2Flow+GasFlow+TAPflow-DilFlow)
                    data_new[name]=[]
                    recalcedchannels.append(name)
                    for n in range(len(data[name])):
                        F1Flowval=float(data_new['F1Flow'][n])
                        F2Flowval=float(data_new['F2Flow'][n])
                        GasFlowval=float(data_new['SampFlow'][n])
                        TAPflowval=float(data_new['TAPflow'][n])
                        DilFlowval=float(data_new['DilFlow'][n])
                        denominator= F1Flowval+F2Flowval+GasFlowval+TAPflowval-DilFlowval
                        if denominator == 0:
                            newval = float(0.001)
                        else:
                            newval=DilFlowval/(F1Flowval+F2Flowval+GasFlowval+TAPflowval-DilFlowval)
                        data_new[name].append(newval)
                    print(name+' recalculated')
                    break

            return recalcedchannels

        recalcedchannels = recalcChannels()
    
        #plot the old and new data series to inspect the differences 

        lw=float(3)    #define the linewidth for the data series
        plw=float(2)    #define the linewidth for the bkg and sample period marker
        msize=30        #marker size for start and end points of each period

        colors={}
        for phase in phases:
            if phase == 'pre':
                colors[phase] = 'r'
            elif phase == 'post':
                colors[phase] = 'darkred'
            elif phase == 'mp':
                colors[phase] = 'orange'
            elif phase == 'lp':
                colors[phase] = 'y'
            else:
                colors[phase]='lawngreen'
        
        plotchannels =  bkgnames+recalcedchannels    
        for name in names: #for each channel, convert data series to floats so they will plot
            if name in ('time','dateobjects','datenumbers'):
                continue
            for n in range(len(data[name])):
                try:
                    data[name][n]=float(data[name][n])          # convert old and new data series to floats 
                    data_new[name][n]=float(data_new[name][n])      # to remove strings so they will plot
                except (ValueError,TypeError):
                    pass

        def drawChannelPlot(name):   #draw (or redraw) the plot for a given channel
            f1, (ax1) = plt.subplots(1, sharex=True) #1 subplot sharing x axis

            for i, ax in enumerate(f1.axes):        #for each subplot (but in this case there is only 1 subplot)
                if name in bkgnames:
                    ax.plot(data['datenumbers'],data_bkg[name],color='lavender',linewidth=lw,label='drift')   #bkg data series
                ax.plot(data['datenumbers'],data[name],color='silver',linewidth=lw, label='raw')   #original data series
                ax.plot(data['datenumbers'],data_new[name],color='k',linewidth=lw,label='corrected')   #bkg subtracted data series
                if name in bkgnames:
                    for phase in phases:
                        key = name+'_'+phase
                        if key not in phasedata:   #skip phases that haven't been picked for this channel yet
                            continue
                        ax.plot(phasedatenums[key],phasedata[key],color=colors[phase],linewidth=plw,label=phase)    #original          
                        ax.plot([phasedatenums[key][0],phasedatenums[key][-1]],[phasedata[key][0],phasedata[key][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                        ax.plot([phasedatenums[key][0],phasedatenums[key][-1]],[phasedata[key][0],phasedata[key][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                        ax.plot(phasedatenums[key],phasedata_new[key],color=colors[phase],linewidth=plw)    #bkg shifted          
                        ax.plot([phasedatenums[key][0],phasedatenums[key][-1]],[phasedata_new[key][0],phasedata_new[key][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
                        ax.plot([phasedatenums[key][0],phasedatenums[key][-1]],[phasedata_new[key][0],phasedata_new[key][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    
                ax.set_ylabel(units[name])
                ax.set_title(name)
                ax.grid(visible=True, which='major', axis='y')

            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
            ax.xaxis.set_major_formatter(xfmt)
            for tick in ax.get_xticklabels():
                tick.set_rotation(30)
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
            plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it verically to make room for the long x axis data labels
            ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
            return f1,ax

        def pickPeriod(name,phase,f1,ax):   #let the user click a start and stop point for a phase period on the given plot
            label = {'pre':'pre-test zero check period','post':'post-test zero check period'}.get(phase,phase+' ref check period')
            print(name+' '+label+'. Select start and stop times on the plot (or press Esc on the plot to keep existing times):')
            timestamps = []
            skip = [False]

            def onclick(event):
                toolbar = f1.canvas.toolbar
                if toolbar is not None and toolbar.mode != '':   #ignore clicks made while zoom/pan tool is active
                    return
                if event.inaxes != ax or event.xdata is None:
                    return
                xclick,yclick = event.xdata,event.ydata
                ax.plot(xclick,yclick,marker='x',color='blue',markersize=12,markeredgewidth=2)   #mark the clicked point
                f1.canvas.draw()
                clickdate = matplotlib.dates.num2date(xclick)
                timestampstr = clickdate.strftime('%Y%m%d %H:%M:%S')
                timestamps.append(timestampstr)
                if len(timestamps) == 1:
                    print(timestampstr, end=', ')
                else:
                    print(timestampstr)

            def onkey(event):
                if event.key == 'escape':
                    skip[0] = True

            cid = f1.canvas.mpl_connect('button_press_event', onclick)
            kid = f1.canvas.mpl_connect('key_press_event', onkey)
            while len(timestamps) < 2 and not skip[0] and plt.fignum_exists(f1.number):
                plt.pause(0.1)   #pump the GUI event loop while waiting for clicks
            f1.canvas.mpl_disconnect(cid)
            f1.canvas.mpl_disconnect(kid)
            if skip[0]:
                print('kept existing '+phase+' times for '+name)
                return []
            return timestamps

        def updatePeriod(name,phase,timestamps):   #store the picked timestamps and recompute the drift correction to reflect them
            key = name+'_'+phase
            starttimes[key] = timestamps[0]
            endtimes[key] = timestamps[1]
            if key not in timenames:
                timenames.append(key)
                timeunc[key] = ''
                timeuval[key] = ''
            if key not in validnames:
                validnames.append(key)
            if phase not in phases:
                phases.append(phase)
            if phase not in colors:
                if phase == 'pre':
                    colors[phase] = 'r'
                elif phase == 'post':
                    colors[phase] = 'darkred'
                elif phase == 'mp':
                    colors[phase] = 'orange'
                elif phase == 'lp':
                    colors[phase] = 'y'
                else:
                    colors[phase] = 'lawngreen'

            startindices.update(findIndices([key],{key: dt.strptime(timestamps[0],'%Y%m%d %H:%M:%S')},datenums))
            endindices.update(findIndices([key],{key: dt.strptime(timestamps[1],'%Y%m%d %H:%M:%S')},datenums))

            [newphasedatenums,newphasedata,newphasemean] = definePhaseData(names,data,[key],startindices,endindices)
            phasedatenums.update(newphasedatenums)
            phasedata.update(newphasedata)
            phasemean.update(newphasemean)

            [bkgvalue2,data_bkg2,data_new2] = bkgSubtraction(names,data,channels,phasemean,startindices,endindices,methods,offsets)
            data_bkg.update(data_bkg2)
            data_new.update(data_new2)

            [newphasedatenums2,newphasedata_new,newphasemean_new] = definePhaseData(names,data_new,[key],startindices,endindices)
            phasedata_new.update(newphasedata_new)
            phasemean_new.update(newphasemean_new)

        #command line prompt to choose which channel to plot
        running = True
        while running:
            channelinput = input("Enter channel name to correct drift, done to exit: ")
            if channelinput == 'done':
                running = False
            elif channelinput not in names:
                print(channelinput+' not found. Valid channels: '+', '.join(names))
            else:
                name = channelinput

                #if this channel isn't already tracked for background subtraction, register it now
                #with a placeholder method so pre/post picks show up on the plot right away
                if name not in channels:
                    channels.append(name)
                    methods[name] = 'none'
                    offsets[name] = float(0)
                    methodsunc[name] = ''
                    methodsuval[name] = ''
                if name not in bkgnames:
                    bkgnames.append(name)

                #make sure data_bkg/data_new have entries for this channel before the first draw
                [bkgvalue_tmp,data_bkg2,data_new2] = bkgSubtraction(names,data,channels,phasemean,startindices,endindices,methods,offsets)
                bkgvalue.update(bkgvalue_tmp)
                data_bkg.update(data_bkg2)
                data_new.update(data_new2)

                f1,ax = drawChannelPlot(name)
                plt.show(block=False)

                pretimestamps = pickPeriod(name,'pre',f1,ax)
                if len(pretimestamps) == 2:
                    updatePeriod(name,'pre',pretimestamps)
                    plt.close(f1)
                    f1,ax = drawChannelPlot(name)
                    plt.show(block=False)

                posttimestamps = pickPeriod(name,'post',f1,ax)
                if len(posttimestamps) == 2:
                    updatePeriod(name,'post',posttimestamps)
                    plt.close(f1)
                    f1,ax = drawChannelPlot(name)
                    plt.show(block=False)

                #resolve the default (used if the user types esc) - existing values for a known channel, else prepostlin/0
                if name in originalchannels:
                    currentmethod = methods[name]
                    currentoffset = offsets[name]
                else:
                    currentmethod = 'prepostlin'
                    currentoffset = 0
                promptstr = name+' correction method, offset ='+str(currentmethod)+','+str(currentoffset)+'. Update: '
                methodinput = input(promptstr)
                if methodinput.strip() == '':
                    methods[name] = currentmethod
                    try:
                        offsets[name] = float(currentoffset)
                    except ValueError:
                        offsets[name] = float(0)
                    print('kept existing method/offset for '+name)
                else:
                    parts = [p.strip() for p in methodinput.split(',')]
                    method = parts[0] if len(parts) >= 1 and parts[0] else 'none'
                    offsetstr = parts[1] if len(parts) >= 2 else '0'
                    methods[name] = method
                    try:
                        offsets[name] = float(offsetstr)
                    except ValueError:
                        offsets[name] = float(0)

                #recompute the background subtraction for this channel with the new method/offset
                [bkgvalue2,data_bkg2,data_new2] = bkgSubtraction(names,data,channels,phasemean,startindices,endindices,methods,offsets)
                bkgvalue.update(bkgvalue2)
                data_bkg.update(data_bkg2)
                data_new.update(data_new2)

                [newphasedatenums3,newphasedata_new3,newphasemean_new3] = definePhaseData(names,data_new,validnames,startindices,endindices)
                phasedata_new.update(newphasedata_new3)
                phasemean_new.update(newphasemean_new3)

                plt.close(f1)
                f1,ax = drawChannelPlot(name)
                plt.show(block=False)

                #reprint the drift correction report to reflect the new method/offset
                reportlogs = printBkgReport(phases,bkgnames,bkgvalue,phasemean,phasemean_new,units,methods,offsets)
                print('Close plot to continue')

                plt.show()   #keep the plot open until the user closes it

        #write the updated phase times and drift methods back to the input files
        io.write_constant_outputs(timespath,timenames,starttimes,endtimes,timeunc,timeuval)
        line = 'updated phase times input file:\n'+timespath
        print(line)
        logs.append(line)

        io.write_constant_outputs(methodspath,channels,methods,offsets,methodsunc,methodsuval)
        line = 'updated drift methods input file:\n'+methodspath
        print(line)
        logs.append(line)

        #recompute and plot any recalculated channels (StakVel/NozVel/DilRat) to reflect the final corrections
        recalcedchannels = recalcChannels()
        for name in recalcedchannels:
            f1,ax = drawChannelPlot(name)
            plt.show()   #keep the plot open until the user closes it, then move to the next
    
    else:   #if no drift correction input file      
        line = 'SKIP. Missing input files:'
        print(line)
        logs.append(line)
        print(timespath)
        logs.append(timespath)
        print(methodspath)
        logs.append(methodspath)
        data_new = data
        reportlogs =[]
    
    #output new time series data file 
    io.write_timeseries(outputpath,names,units,data_new)
    
    line='created drift-corrected time series data file:\n'+outputpath
    print(line)
    logs.append(line)
    
    #print final report to logs
    logs=logs+reportlogs
    
    #print to log file
    io.write_logfile(logpath,logs)
    
def makeTimeObjects(Timenames,Starttimes,Endtimes,Date):
    Starttimeobjects={}   #initialize a dictionary of time objects
    Endtimeobjects={}   #initialize a dictionary of time objects
    Validnames_start = [] #initialize list start times that have a valid time entered
    Validnames_end = [] #initialize list end times that have a valid time entered
    Validnames=[] #initialize a list of time names that have a valid time entered
    for Name in Timenames:
        if len(Starttimes[Name]) == 8:  #if time format
            Startdatestring=Date+' '+Starttimes[Name]    #add the date to the time string
        else:   #if already date format
            Startdatestring = Starttimes[Name]   #use it as is
        if len(Endtimes[Name]) == 8:  #if time format
            Enddatestring=Date+' '+Endtimes[Name]    #add the date to the time string
        else:   #if already date format
            Enddatestring = Endtimes[Name]   #use it as is
        
        try:
            Starttimeobjects[Name]=dt.strptime(Startdatestring, '%Y%m%d %H:%M:%S')                #convert the time string to date object
            Validnames_start.append(Name)
        except:
            print(Name+' error reading in start time')
            
        try:
            Endtimeobjects[Name]=dt.strptime(Enddatestring, '%Y%m%d %H:%M:%S')                #convert the time string to date object
            Validnames_end.append(Name)
        except:
            print(Name+' error reading in end time')
            
        if Name in Validnames_start or Name in Validnames_end:
            Validnames.append(Name)
    return Validnames,Starttimeobjects,Endtimeobjects
        
def definePhases(Timenames):
    Phases=[] #initialize a list of test phases (prebkg, low power, med power, high power, post bkg)    
    for Name in Timenames:
        spot=Name.rindex('_')           #locate the last underscore
        Phase=Name[spot+1:]         #grab the string after the last underscore
        if Phase not in Phases:             #if it is a new phase
            Phases.append(Phase)            #add to the list of phases
    return Phases
           
def findIndices(InputTimeNames,InputTimeObject,Datenums):
    InputTimeDatenums={}
    Indices={}
    for Name in InputTimeNames:
        InputTimeDatenums[Name]=matplotlib.dates.date2num(InputTimeObject[Name])
        Indices[Name]=Datenums.index(InputTimeDatenums[Name])
    return Indices
        
def definePhaseData(Names,Data,Phases,StartIndices,EndIndices):
    Phasedatenums={}
    Phasedata={}
    Phasemean={}
    for Phase in Phases: #for each test phase
        #make data series of date numbers
        key=Phase
        startindex=StartIndices[key]
        key=Phase
        endindex=EndIndices[key]
        Phasedatenums[Phase]=Data['datenumbers'][startindex:endindex+1]    
        #make phase data series for each data channel
        spot=Phase.index('_')    #locate the '_'
        Name=Phase[:spot]  #grab the string before the spot
        
        Phasedata[Phase]=Data[Name][startindex:endindex+1]
            
        #calculate average value
        if all(np.isnan(Phasedata[Phase])):
            Phasemean[Phase]=np.nan
        else:
            Phasemean[Phase]=np.nanmean(Phasedata[Phase])

    return Phasedatenums,Phasedata,Phasemean
         
def bkgSubtraction(Names,Data,Bkgnames,Phasemean,StartIndices,EndIndices,Methods,Offsets):
    Bkgvalue={}                 #dictionary of constant bkg values
    Data_bkgseries={}                   #data series that will get subtracted
    Data_bkgsubtracted={}           #new data series after bkg subtraction
    for Name in Names:    #for each channel 
        Data_bkgsubtracted[Name]=[]
        if Name in Bkgnames:    # that will get background subtraction
            #make bkg series
            Data_bkgseries[Name]=[] 
            if Methods[Name] == 'pre':
                Bkgvalue[Name] = Phasemean[Name+'_pre']-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'post':
                Bkgvalue[Name] = Phasemean[Name+'_post']-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostave':
                Bkgvalue[Name]=np.mean([Phasemean[Name+'_pre'],Phasemean[Name+'_post']])-Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            elif Methods[Name] == 'prepostlin':
                Bkgvalue[Name] = -Offsets[Name]
                x1 = int((StartIndices[Name+'_pre']+EndIndices[Name+'_pre']+1)/2) #middle index of prebkg 
                y1 = Phasemean[Name+'_pre']      #prebkg average value
                x2 = int((StartIndices[Name+'_post']+EndIndices[Name+'_post']+1)/2) #middle index of postbkg 
                y2 = Phasemean[Name+'_post']     #post bkg average value
                #equation of line from 2 points, y=mx+b
                m = (y2-y1)/(x2-x1)
                b = y1-x1*(y2-y1)/(x2-x1)
                for x,val in enumerate(Data[Name]):
                    y = m*x+b 
                    Data_bkgseries[Name].append(y+Bkgvalue[Name])
            elif Methods[Name] == 'realtime':
                Bkgvalue[Name] = -Offsets[Name]
                #define the name of the background data series here
                #do: add input to pass this variable to the function
                bkgseriesname = Name

                for x,val in enumerate(Data[bkgseriesname+'bkg']):      #realtime bkg series
                    Data_bkgseries[Name].append(val+Bkgvalue[Name])
            else:
                Bkgvalue[Name] = -Offsets[Name]
                for n in Data[Name]:
                    Data_bkgseries[Name].append(Bkgvalue[Name])
            
            #subtract bkg data series        
            for n,val in enumerate(Data[Name]):
                newval=val-Data_bkgseries[Name][n]
                Data_bkgsubtracted[Name].append(newval)  

        else:   #if no bkg subtraction
            Data_bkgsubtracted[Name]=Data[Name]
            
    return Bkgvalue, Data_bkgseries, Data_bkgsubtracted
    
def printBkgReport(Phases,Bkgnames,Bkgvalue,Phasemean,Phasemean_new,Units,Methods,Offsets):  #add arg to print to log file        
    Reportlogs=[]
    line= '\ndrift correction report:'
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
            line=line+str(round(Phasemean[Phasename],1)).ljust(10)
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
            line=line+str(round(Phasemean_new[Phasename],1)).ljust(10)
        #line=line+'0.0'.ljust(10)
        print(line)
        Reportlogs.append(line)
        
    return Reportlogs
    
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_CorrectDrift(inputpath,headerpath,outputpath,timespath,methodspath,logpath)

