#v0.0 Python3

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

import LEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
import numpy as np

#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_RawData2.csv'
#output data file to be created:
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_DataSeries_BkgSubtracted.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def LEMS_SubtractBkg(inputpath,outpath,timespath,logpath):

    timeobject={}
    datenumbers={}
    datenumseries={}
    indices={}
    phasedata={}
    phasemean={}
    bkgvalue={}
    logs=[]
    
    data_new={}
    phasedata_new={}
    phasemean_new={}
    
    potentialBkgNames=['CO','CO2','PM','VOC','CH4'] #define potential channel names that will get background subtraction
    bkgnames=[] #initialize list of actual channel names that will get background subtraction

    #################################################
    #read in raw data file
    
    [names,units,data] = io.load_timeseries(inputpath)
    
     ##############################################
    #read in input file of start and end times
    [timenames,timeunits,timeval,timeunc,timeuval] = io.load_constant_inputs(timespath)

    line = 'Loaded input file of start and end times:'+timespath
    print(line)
    logs.append(line)
    
    ###############################################
    #prep the data for background subtraction
    
    #define which channels will get background subtraction
    #could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)
    
    #get the date from the time series data
    date=data['time'][0][:8]
    
    goodnames=[] #initialize a list of time names that have a valid time entered
    for name in timenames:
        datestring=date+' '+timeval[name] #add the date to the time string
        #convert the time strings to date objects   
        try:
            timeobject[name]=dt.strptime(datestring, '%Y%m%d  %H:%M:%S')
            goodnames.append(name)
        except:
            pass
        
    for name in goodnames:
        #convert the start and stop date objects to date numbers for plotting
        datenumbers[name]=matplotlib.dates.date2num(timeobject[name])
        
    #convert date strings from the time data series to date numbers for plotting
    dateobjects=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
        dateobjects.append(dateobject)   
    datenums=matplotlib.dates.date2num(dateobjects)
    datenums=list(datenums)     #convert ndarray to a list in order to use index function

    phases=[] #initialize a list of test phases (prebkg, low power, med power, high power, post bkg)
    for name in goodnames:
        #find the data series indices of the start and stop times
        indices[name]=datenums.index(datenumbers[name]) 
        
        #define the phases
        spot=name.rindex('_')
        phase=name[spot+1:]
        if phase not in phases:
            phases.append(phase)
    

    for phase in phases: #for each test phase
        #make data series of date numbers
        key='start_time_'+phase
        startindex=indices[key]
        key='end_time_'+phase
        endindex=indices[key]
        datenumseries[phase]=datenums[startindex:endindex+1]

        #make data series for each data channel
        for name in names:
            keyname=name+'_'+phase
            phasedata[keyname]=data[name][startindex:endindex+1]
            
            #calculate average value
            if name != 'time':
                if all(np.isnan(phasedata[keyname])):
                    phasemean[keyname]=np.nan
                else:
                    phasemean[keyname]=np.nanmean(phasedata[keyname])
            
    #end of data preparation for background subtraction
    #########################################################  
    #subtract the background
    for name in bkgnames:    #for each channel that will get background subtraction
        data_new[name]=[]
        bkgvalue[name]=np.mean([phasemean[name+'_prebkg'],phasemean[name+'_postbkg']])         #pre-post method
        for n,val in enumerate(data[name]):
            newval=val-bkgvalue[name]
            data_new[name].append(newval)   

    for phase in phases:   
        #make new background subtracted data series for each data channel
        key='start_time_'+phase
        startindex=indices[key]
        key='end_time_'+phase
        endindex=indices[key]
        for name in bkgnames:
            keyname=name+'_'+phase
            phasedata_new[keyname]=data_new[name][startindex:endindex+1]
            
            #calculate average value
            if name != 'time':
                if all(np.isnan(phasedata_new[keyname])):
                    phasemean_new[keyname]=np.nan
                else:
                    phasemean_new[keyname]=np.nanmean(phasedata_new[keyname])           

    ##########################################
    #print report
    print('')
    line= 'background subtraction report:'
    print(line)
    print('')
    print('phase averages before background subtraction:')
    line1='channel'.ljust(10)+'units'.ljust(10)
    line2='-------'.ljust(10)+'-----'.ljust(10)
    for phase in phases:
        line1=line1+phase.ljust(10)
        line2=line2+'------'.ljust(10)
    line1=line1+'prepost'.ljust(10)
    line2=line2+'------'.ljust(10)
    print(line1)
    print(line2)
    for name in bkgnames:
        line=name.ljust(10)+str(units[name]).ljust(10)
        for phase in phases:
            keyname=name+'_'+phase
            line=line+str(round(phasemean[keyname],1)).ljust(10)
        line=line+str(round(bkgvalue[name],1)).ljust(10)
        print(line)
        
    print('')
    print('phase averages after background subtraction:')
    print(line1)
    print(line2)
    for name in bkgnames:
        line=name.ljust(10)+str(units[name]).ljust(10)
        for phase in phases:
            keyname=name+'_'+phase
            line=line+str(round(phasemean_new[keyname],1)).ljust(10)
        line=line+'0.0'.ljust(10)
        print(line)
    #end of report
    ###################################################################
    
    #plot
    #################################################### 
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

    ############ figure 1 ########################################
    f1, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex=True) #four subplots sharing x axis
    name='CO'
    ax1.plot(datenums,data_new[name],color='k',linewidth=lw)   #data series
    for phase in phases:
        keyname=name+'_'+phase
        ax1.plot(datenumseries[phase],phasedata_new[keyname],color=colors[phase],linewidth=plw,label=phase)                       
        ax1.plot([datenumseries[phase][0],datenumseries[phase][-1]],[phasedata_new[keyname][0],phasedata_new[keyname][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    ax1.set_ylabel(units[name])
    ax1.set_title(name)
    name='CO2'
    ax2.plot(datenums,data_new[name],color='k',linewidth=lw)
    for phase in phases:
        keyname=name+'_'+phase
        ax2.plot(datenumseries[phase],phasedata_new[keyname],color=colors[phase],linewidth=plw)                       
        ax2.plot([datenumseries[phase][0],datenumseries[phase][-1]],[phasedata_new[keyname][0],phasedata_new[keyname][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    ax2.set_ylabel(units[name])
    ax2.set_title(name)
    name='VOC'
    ax3.plot(datenums,data_new[name],color='k',linewidth=lw)
    for phase in phases:
        keyname=name+'_'+phase
        ax3.plot(datenumseries[phase],phasedata_new[keyname],color=colors[phase],linewidth=plw)                       
        ax3.plot([datenumseries[phase][0],datenumseries[phase][-1]],[phasedata_new[keyname][0],phasedata_new[keyname][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    ax3.set_ylabel(units[name])
    ax3.set_title(name)
    name='PM'
    ax4.plot(datenums,data_new[name],color='k',linewidth=lw)
    for phase in phases:
        keyname=name+'_'+phase
        ax4.plot(datenumseries[phase],phasedata_new[keyname],color=colors[phase],linewidth=plw)                       
        ax4.plot([datenumseries[phase][0],datenumseries[phase][-1]],[phasedata_new[keyname][0],phasedata_new[keyname][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    ax4.set_ylabel(units[name])
    ax4.set_title(name)
    
    xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax4.xaxis.set_major_formatter(xfmt)
    for tick in ax4.get_xticklabels():
        tick.set_rotation(30)
    #plt.xlabel('time')
    #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
    #plt.legend(fontsize=10).draggable()
    box = ax4.get_position()
    ax4.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
    plt.subplots_adjust(top=.95,bottom=0.2) #squeeze it verically to make room for the long x axis data labels
    #ax1.legend(['prebkg','hp','mp','lp','postbkg'])
    ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
        
    ################ end figure 1  ###########
    
    #plt.show() #show all figures
    
    f1.canvas.draw()
    
    ax1.plot(datenums,data['CO'],color='gray',linewidth=lw)   #data series
    
    f1.canvas.draw()

    #GUI box to edit input times
    firstline='Time format = '+timeunits['start_time_prebkg']
    msg=firstline
    title = "Gitrdone"
    fieldNames = timenames[1:]
    currentvals=[]
    for name in timenames[1:]:
        currentvals.append(timeval[name])
    newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
    if newvals:
        if newvals != currentvals:
            currentvals = newvals
            for n,name in enumerate(timenames[1:]):
                timeval[name]=currentvals[n]
            io.write_constant_outputs(timespath,timenames,timeunits,timeval,timeunc,timeuval)
            line = 'Updated input file of start and end times:'+timespath
            print(line)
            logs.append(line)
    
    #output new background subtracted time series data file 
    
    #print final report to logs
    
    #print to log file
    io.write_logfile(logpath,logs)
    
        #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_SubtractBkg(inputpath,outputpath,timespath,logpath)

