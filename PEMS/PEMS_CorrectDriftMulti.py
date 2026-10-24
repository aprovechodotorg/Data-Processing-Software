#v0.1 Python3

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

# Corrects time series data for sensor drift using any number of zero check periods per channel.
#
# The user picks a channel, then clicks the start and end of each zero period on the plot.
# The correction method is set by the number of zero periods selected for the channel:
#    0 zero periods: no correction
#    1 zero period:  constant offset = zero period average (like the old pre or post method)
#    2 zero periods: linear offset through the 2 zero points (like the old prepostlin method)
#    3+ zero periods: piecewise linear offset. Between neighboring zero points the offset is the line
#                     through those 2 points. Before the first zero point the line through zero points 1 and 2
#                     is extended to the start of the data, and after the last zero point the line through the
#                     last 2 zero points is extended to the end of the data.
#    Each zero point is located at the middle time of its zero period, with the value of the zero period average.
#
# Input file:
#    _DriftTimes.csv: start and end time of each zero period, named <channel>_zero1, <channel>_zero2, ...
#    _Header.csv: calibration constants, used to recalculate StakVel, NozVel, and DilRat
# Outputs:
#    1. Drift corrected time series data file, full length
#    2. Updated _DriftTimes.csv input file
#    3. Drift correction report to terminal and log file

import LEMS_DataProcessing_IO as io
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime as dt
import numpy as np
import os
import math

#########      inputs      ##############
testfolder = os.path.join('Data','CrappieCooker','CrappieCooker_test2')
#raw data input file:
inputpath = os.path.join(testfolder,'CrappieCooker_test2_RawData2.csv')
#header input file with calibration constants:
headerpath = os.path.join(testfolder,'CrappieCooker_test2_Header.csv')
#output data file to be created:
outputpath = os.path.join(testfolder,'CrappieCooker_test2_TimeSeriesData.csv')
#input file of start and end times of the zero periods:
driftpath = os.path.join(testfolder,'CrappieCooker_test2_DriftTimes.csv')
logpath = os.path.join(testfolder,'CrappieCooker_test2_log.txt')
##########################################

TIMEFORMAT = '%Y%m%d %H:%M:%S'
ZEROCOLORS = ['r','darkorange','gold','limegreen','deepskyblue','blue','darkviolet','magenta']
NONDATACHANNELS = ('time','dateobjects','datenumbers')

def PEMS_CorrectDriftMulti(inputpath,headerpath,outputpath,driftpath,logpath):
    ver = '0.1'

    timestampstring = dt.now().strftime(TIMEFORMAT)    #get timestamp from operating system for log file
    line = 'PEMS_CorrectDriftMulti v'+ver+'   '+timestampstring
    print(line)
    logs = [line]

    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)

    #if the drift times input file doesn't exist yet, create a blank one
    if not os.path.isfile(driftpath):
        io.write_constant_outputs(driftpath,['point'],{'point':'starttime'},{'point':'endtime'},{'point':'unc'},{'point':'uval'})
        line = 'created blank drift times input file:\n'+driftpath
        print(line)
        logs.append(line)

    #time channel: convert date strings to date numbers for plotting
    date = data['time'][0][:8]
    data['dateobjects'] = [dt.strptime(val,TIMEFORMAT) for val in data['time']]
    units['dateobjects'] = 'date'
    data['datenumbers'] = list(matplotlib.dates.date2num(data['dateobjects']))
    units['datenumbers'] = 'date'
    if 'datenumbers' not in names:
        names.append('datenumbers')
    datenums = np.array(data['datenumbers'],dtype=float)

    #read in the zero periods
    [timenames,starttimes,endtimes,timeunc,timeuval] = io.load_constant_inputs(driftpath)
    zeroperiods = readZeroPeriods(timenames,starttimes,endtimes,date,names)
    #zeroperiods[channel] = list of [starttimestring,endtimestring], in the order they were picked

    data_new = dict(data)   #corrected data. Channels without correction point to the raw data series
    baselines = {}          #baselines[channel] = drift data series that gets subtracted
    zeropoints = {}         #zeropoints[channel] = list of dicts describing each zero point

    def updateChannel(name):   #recompute the drift correction for one channel from its zero periods
        periods = zeroperiods.get(name,[])
        if len(periods) == 0:
            data_new[name] = data[name]
            baselines.pop(name,None)
            zeropoints.pop(name,None)
            zeroperiods.pop(name,None)
            return
        raw = toFloatArray(data[name])
        [baseline,corrected,points] = correctChannel(raw,datenums,periods)
        baselines[name] = baseline
        data_new[name] = corrected.tolist()
        zeropoints[name] = points

    for name in list(zeroperiods.keys()):   #apply corrections already defined in the input file
        updateChannel(name)

    ###############################################################
    #plotting

    lw = float(3)    #linewidth for the data series
    msize = 10       #marker size for the zero points

    def drawChannelPlot(name):   #draw (or redraw) the plot for a given channel
        f1, ax = plt.subplots(1)
        raw = toFloatArray(data[name])
        ax.plot(datenums,raw,color='silver',linewidth=lw,label='raw')
        if name in baselines:
            ax.plot(datenums,baselines[name],color='cornflowerblue',linewidth=2,linestyle='--',label='drift')
        if data_new[name] is not data[name]:
            ax.plot(datenums,toFloatArray(data_new[name]),color='k',linewidth=2,label='corrected')
        if name in zeropoints:
            for k,point in enumerate(zeropoints[name]):
                color = ZEROCOLORS[k % len(ZEROCOLORS)]
                ax.axvspan(datenums[point['istart']],datenums[point['iend']],color=color,alpha=0.25)
                ax.plot(point['x'],point['mean'],color=color,marker='o',markersize=msize,linestyle='none',label='zero'+str(k+1))

        ax.set_ylabel(units[name])
        ax.set_title(name)
        ax.grid(visible=True,which='major',axis='y')
        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
        box = ax.get_position()
        ax.set_position([box.x0,box.y0,box.width*0.85,box.height])    #squeeze it down to make room for the legend
        plt.subplots_adjust(top=.95,bottom=0.1)    #make room for the long x axis data labels
        ax.legend(fontsize=10,loc='center left',bbox_to_anchor=(1,0.5))   #legend to the right of the plot
        return f1,ax

    def redraw(name,f1):
        plt.close(f1)
        f1,ax = drawChannelPlot(name)
        plt.show(block=False)
        plt.pause(0.1)
        return f1,ax

    def pickPeriod(name,k,f1,ax):   #let the user click a start and stop point for zero period k
        print(name+' zero period '+str(k)+'. Select start and stop times on the plot (or press Esc on the plot to cancel):')
        timestamps = []
        cancel = [False]

        def onclick(event):
            toolbar = f1.canvas.toolbar
            if toolbar is not None and toolbar.mode != '':   #ignore clicks made while zoom/pan tool is active
                return
            if event.inaxes != ax or event.xdata is None:
                return
            ax.axvline(event.xdata,color='blue',linewidth=1.5)   #mark the clicked time
            f1.canvas.draw()
            timestampstr = matplotlib.dates.num2date(event.xdata).strftime(TIMEFORMAT)
            timestamps.append(timestampstr)
            if len(timestamps) == 1:
                print(timestampstr,end=', ')
            else:
                print(timestampstr)

        def onkey(event):
            if event.key == 'escape':
                cancel[0] = True

        cid = f1.canvas.mpl_connect('button_press_event',onclick)
        kid = f1.canvas.mpl_connect('key_press_event',onkey)
        while len(timestamps) < 2 and not cancel[0] and plt.fignum_exists(f1.number):
            plt.pause(0.1)   #pump the GUI event loop while waiting for clicks
        if plt.fignum_exists(f1.number):
            f1.canvas.mpl_disconnect(cid)
            f1.canvas.mpl_disconnect(kid)
        if len(timestamps) < 2:
            print('zero period '+str(k)+' cancelled')
            return []
        return sorted(timestamps)   #in case the end was clicked before the start

    ###############################################################
    #command line prompt to choose which channel to correct
    datachannels = [name for name in names if name not in NONDATACHANNELS]
    running = True
    while running:
        channelinput = input('Enter channel name to correct drift, done to exit: ').strip()
        if channelinput == 'done':
            running = False
            continue
        if channelinput not in datachannels:
            print(channelinput+' not found. Valid channels: '+', '.join(datachannels))
            continue
        name = channelinput

        f1,ax = drawChannelPlot(name)
        plt.show(block=False)
        plt.pause(0.1)

        periods = list(zeroperiods.get(name,[]))
        if len(periods) > 0:
            ans = input(name+' has '+str(len(periods))+' zero periods. [enter] keep, [a] add more, [r] reselect all: ').strip().lower()
            if ans == 'r':
                periods = []
                zeroperiods.pop(name,None)
                updateChannel(name)
                f1,ax = redraw(name,f1)
                picking = True
            elif ans == 'a':
                picking = True
            else:
                picking = False
        else:
            picking = True

        while picking:
            timestamps = pickPeriod(name,len(periods)+1,f1,ax)
            if len(timestamps) == 2:
                periods.append(timestamps)
                zeroperiods[name] = periods
                updateChannel(name)
            f1,ax = redraw(name,f1)   #redraw to show the new correction (or clear cancelled click marks)
            print(name+': '+str(len(periods))+' zero periods selected, method = '+methodName(len(periods)))
            ans = input('[s] select another zero period, [u] undo last zero period, [enter] calculate and finish: ').strip().lower()
            if ans == 's':
                continue
            elif ans == 'u':
                if len(periods) > 0:
                    removed = periods.pop()
                    print('removed zero period '+removed[0]+' - '+removed[1])
                    zeroperiods[name] = periods
                    updateChannel(name)
                    f1,ax = redraw(name,f1)
                ans = input('[s] select another zero period, [enter] calculate and finish: ').strip().lower()
                if ans != 's':
                    picking = False
            else:
                picking = False

        printDriftReport([name],data,data_new,units,zeroperiods,zeropoints)
        print('Close plot to continue')
        plt.show()   #keep the plot open until the user closes it

    ###############################################################
    #write the updated zero periods back to the input file
    outnames = ['point']
    outstart = {'point':'starttime'}
    outend = {'point':'endtime'}
    outunc = {'point':'unc'}
    outuval = {'point':'uval'}
    for name in names:
        if name in zeroperiods:
            for k,period in enumerate(sortPeriods(zeroperiods[name])):
                key = name+'_zero'+str(k+1)
                outnames.append(key)
                outstart[key] = period[0]
                outend[key] = period[1]
                outunc[key] = timeunc.get(key,'')
                outuval[key] = timeuval.get(key,'')
    io.write_constant_outputs(driftpath,outnames,outstart,outend,outunc,outuval)
    line = 'updated drift times input file:\n'+driftpath
    print(line)
    logs.append(line)

    #recalculate channels that depend on the corrected channels
    corrnames = [name for name in names if name in zeroperiods]
    recalcedchannels = []
    if len(corrnames) > 0:
        if os.path.isfile(headerpath):
            [headernames,headerunits,A,B,C,D,const] = io.load_header(headerpath)
            recalcedchannels = recalcChannels(data_new,corrnames,const)
            for name in recalcedchannels:
                line = name+' recalculated'
                print(line)
                logs.append(line)
                f1,ax = drawChannelPlot(name)
                plt.show()   #keep the plot open until the user closes it, then move to the next
        else:
            line = 'header file not found, StakVel/NozVel/DilRat not recalculated:\n'+headerpath
            print(line)
            logs.append(line)

    #output new time series data file
    io.write_timeseries(outputpath,names,units,data_new)
    line = 'created drift-corrected time series data file:\n'+outputpath
    print(line)
    logs.append(line)

    #print final report to logs
    reportlogs = printDriftReport(corrnames,data,data_new,units,zeroperiods,zeropoints)
    logs = logs+reportlogs
    io.write_logfile(logpath,logs)

###################################################################
#helper functions

def methodName(n):
    if n == 0:
        return 'none'
    elif n == 1:
        return 'constant'
    elif n == 2:
        return 'linear'
    else:
        return 'piecewise linear'

def toFloatArray(series):   #convert a data series to a float array, with nan for anything that isn't a number
    out = np.full(len(series),np.nan)
    for n,val in enumerate(series):
        try:
            out[n] = float(val)
        except (ValueError,TypeError):
            pass
    return out

def sortPeriods(periods):   #sort zero periods by start time
    return sorted(periods,key=lambda p: dt.strptime(p[0],TIMEFORMAT))

def readZeroPeriods(timenames,starttimes,endtimes,date,names):
    #read the drift times input file entries into zeroperiods[channel] = list of [starttimestring,endtimestring]
    zeroperiods = {}
    for key in timenames:
        if key == 'point' or '_' not in key:
            continue
        name = key[:key.rindex('_')]   #channel name is the string before the last underscore
        if name not in names:
            print(key+': channel '+name+' not in data file, skipped')
            continue
        period = []
        for timestr in (starttimes[key],endtimes[key]):
            timestr = timestr.strip()
            if len(timestr) == 8:   #if time only format, add the date
                timestr = date+' '+timestr
            try:
                dt.strptime(timestr,TIMEFORMAT)
                period.append(timestr)
            except ValueError:
                print(key+' error reading in time: '+timestr)
        if len(period) == 2:
            zeroperiods.setdefault(name,[]).append(sorted(period))
    return zeroperiods

def nearestIndex(datenums,timestr):   #index of the data point closest to a time string
    target = matplotlib.dates.date2num(dt.strptime(timestr,TIMEFORMAT))
    return int(np.argmin(np.abs(datenums-target)))

def calcZeroPoints(raw,datenums,periods):
    #zero point = middle time of the zero period, with the zero period average value
    points = []
    for period in sortPeriods(periods):
        istart = nearestIndex(datenums,period[0])
        iend = nearestIndex(datenums,period[1])
        segment = raw[istart:iend+1]
        if len(segment) == 0 or np.all(np.isnan(segment)):
            print('zero period '+period[0]+' - '+period[1]+' has no valid data, skipped')
            continue
        points.append({'start':period[0],'end':period[1],'istart':istart,'iend':iend,
                       'x':(datenums[istart]+datenums[iend])/2,'mean':float(np.nanmean(segment))})
    return points

def driftBaseline(x,zx,zy):
    #drift data series from the zero points (zx,zy). zx must be in increasing order
    x = np.asarray(x,dtype=float)
    n = len(zx)
    if n == 0:
        return np.zeros(len(x))
    if n == 1:   #constant offset
        return np.full(len(x),zy[0])
    baseline = np.interp(x,zx,zy)   #linear between each pair of neighboring zero points
    mfirst = (zy[1]-zy[0])/(zx[1]-zx[0])   #extend the first segment back to the start of the data
    before = x < zx[0]
    baseline[before] = zy[0]+mfirst*(x[before]-zx[0])
    mlast = (zy[-1]-zy[-2])/(zx[-1]-zx[-2])   #extend the last segment forward to the end of the data
    after = x > zx[-1]
    baseline[after] = zy[-1]+mlast*(x[after]-zx[-1])
    return baseline

def correctChannel(raw,datenums,periods):
    points = calcZeroPoints(raw,datenums,periods)
    zx = [p['x'] for p in points]
    zy = [p['mean'] for p in points]
    baseline = driftBaseline(datenums,zx,zy)
    corrected = raw-baseline
    return baseline,corrected,points

def printDriftReport(corrnames,data,data_new,units,zeroperiods,zeropoints):
    reportlogs = []
    def out(line):
        print(line)
        reportlogs.append(line)

    out('\ndrift correction report:')
    out('channel'.ljust(12)+'units'.ljust(10)+'method'.ljust(18)+'zero'.ljust(8)+'start'.ljust(19)+'end'.ljust(19)+'raw ave'.ljust(12)+'corr ave'.ljust(12))
    out('-------'.ljust(12)+'-----'.ljust(10)+'------'.ljust(18)+'----'.ljust(8)+'-----'.ljust(19)+'---'.ljust(19)+'-------'.ljust(12)+'--------'.ljust(12))
    for name in corrnames:
        n = len(zeroperiods.get(name,[]))
        points = zeropoints.get(name,[])
        if len(points) == 0:
            out(name.ljust(12)+str(units[name]).ljust(10)+methodName(n).ljust(18))
            continue
        corrected = toFloatArray(data_new[name])
        for k,point in enumerate(points):
            corrave = np.nanmean(corrected[point['istart']:point['iend']+1])
            prefix = name.ljust(12)+str(units[name]).ljust(10)+methodName(n).ljust(18) if k == 0 else ''.ljust(40)
            out(prefix+('zero'+str(k+1)).ljust(8)+point['start'].ljust(19)+point['end'].ljust(19)
                +str(round(point['mean'],3)).ljust(12)+str(round(corrave,3)).ljust(12))
    return reportlogs

def recalcChannels(data_new,corrnames,const):
    #recalculate channels that are calculated from corrected channels
    recalced = []
    npts = len(data_new['time'])

    def val(ch,n,default=float('nan')):   #float value of a channel, or default if missing or not a number
        try:
            return float(data_new[ch][n])
        except (KeyError,ValueError,TypeError,IndexError):
            return default

    def triggered(checknames):
        return any(name in corrnames for name in checknames)

    #StakVel=Cp*Kp*sqrt(Pitot*(TCnoz+273)/Pamb/MolWt)
    if 'StakVel' in data_new and triggered(['Pitot','Pamb','TCnoz','FlueTemp']):
        Kp = float(129)
        Cpitot = float(const['Cpitot(-)'])
        MolWt = float(const['MolWt(g/mol)'])
        newseries = []
        for n in range(npts):
            pitot = val('Pitot',n)
            pamb = val('Pamb',n)
            temp = val('FlueTemp',n)    #hack! hard coded for firmware possum2.6 (TCnoz is not logged)
            if np.isnan(pitot) or np.isnan(pamb) or np.isnan(temp):
                newseries.append(float('nan'))
            else:
                newseries.append(math.copysign(1,pitot)*Cpitot*Kp*math.sqrt(abs(pitot)*(temp+273.15)/pamb/MolWt))
        data_new['StakVel'] = newseries
        recalced.append('StakVel')

    flownames = ['F1Flow','F2Flow','FiltFlow','SampFlow','TAPflow','TapFlow','USampFlow','UsampFlow','DilFlow']

    #NozVel=(F1Flow+F2Flow+FiltFlow+SampFlow+TAPflow+USampFlow-DilFlow)*101325/Pamb*(TCnoz+273)/293/60*4/pi/NozDiam^2
    if 'NozVel' in data_new and triggered(flownames+['Pamb','TCnoz','FlueTemp']):
        NozDiam = float(const['NozDiam(mm)'])
        Pstd = float(101325)
        Tstd = float(293)
        newseries = []
        for n in range(npts):
            nozzleflow = (val('F1Flow',n,0)+val('F2Flow',n,0)+val('FiltFlow',n,0)+val('SampFlow',n,0)
                          +val('TAPflow',n,0)+val('USampFlow',n,0)-val('DilFlow',n,0))
            pamb = val('Pamb',n)
            temp = val('FlueTemp',n)    #hack! hard coded for firmware possum2.6 (TCnoz is not logged)
            if np.isnan(pamb) or np.isnan(temp):
                newseries.append(float('nan'))
            else:
                newseries.append(nozzleflow*Pstd/pamb*(temp+273)/Tstd/60*4/math.pi/math.pow(NozDiam,2))
        data_new['NozVel'] = newseries
        recalced.append('NozVel')

    #DilRat=DilFlow/(F1Flow+F2Flow+FiltFlow+SampFlow+TAPflow-DilFlow)
    if 'DilRat' in data_new and triggered(flownames):
        newseries = []
        for n in range(npts):
            dilflow = val('DilFlow',n,0)
            denominator = val('F1Flow',n,0)+val('F2Flow',n,0)+val('FiltFlow',n,0)+val('SampFlow',n,0)+val('TAPflow',n,0)-dilflow
            if denominator == 0:
                newseries.append(float(0.001))
            else:
                newseries.append(dilflow/denominator)
        data_new['DilRat'] = newseries
        recalced.append('DilRat')

    return recalced

    #######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_CorrectDriftMulti(inputpath,headerpath,outputpath,driftpath,logpath)
