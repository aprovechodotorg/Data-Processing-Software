#v0.2 Python3

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
#  Plot to visualize the affects of background adjustment and subtraction
# Outputs:
#    1. Background subtracted time series data file, full length (all phases)
#    2. For each phase, background subtracted time series data file
#    3. For each phase, averages data file of average values of all data channels
#    4. Background subtraction report to terminal and log file

#do: 
#accept date formats in the phase times input file
#add other background subtraction methods: pre,post,offset,realtime
#create blank phase times input file if one does not exist
#move plots to plot library
#add 1 more figure for CH4 and VOC
#add uncertainty for averages

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
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_TimeSeriesData.csv'
#output file of average values for each phase:
aveoutputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
#input file of start and end times for background and test phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def LEMS_SubtractBkg(inputpath,outputpath,aveoutputpath,timespath,logpath):

    logs=[]
    
    potentialBkgNames=['CO','CO2','PM','VOC','CH4'] #define potential channel names that will get background subtraction
    bkgnames=[] #initialize list of actual channel names that will get background subtraction

    #################################################
    
    #read in raw data file
    [names,units,data] = io.load_timeseries(inputpath)
    
    #define which channels will get background subtraction
    #could add easygui multi-choice box here instead so user can pick the channels
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)
        
    #get the date from the time series data
    date=data['time'][0][:8]
    
    #time channel: convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name]='date'
    #names.append(name) #don't add to print list because time object cant print to csv
    data[name]=[]
    for n,val in enumerate(data['time']):
        dateobject=dt.strptime(val, '%Y%m%d  %H:%M:%S')
        data[name].append(dateobject)   
    
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
    #read in input file of start and end times
    [timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)

    line = 'Loaded input file of start and end times:'+timespath
    print(line)
    logs.append(line)
    
    ###############################################

    [validnames,timeobject]=makeTimeObjects(timenames,timestring,date)  #convert time strings to time objects
    
    phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase
    
    phaseindices = findIndices(validnames,timeobject,datenums)  #find the indices in the time data series for the start and stop times of each phase
    
    [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,phases,phaseindices)   #define phase data series for each channel
    
    bkgvalue = calcBkgValue(bkgnames,phasemean)     #calculate the background value for each channel that will get background subtraction
        
    data_new = bkgSubtraction(names,data,bkgnames,bkgvalue) #subtract the background
    
    [phasedatenums,phasedata_new,phasemean_new] = definePhaseData(names,data_new,phases,phaseindices)   #define phase data series after background subtraction
    
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

    f1, (ax1, ax2, ax3) = plt.subplots(3, sharex=True) #three subplots sharing x axis
    plotnames=bkgnames
    for i, ax in enumerate(f1.axes):
        name=plotnames[i]
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
    
    plt.show() #show all figures
    ###############################################################################################
    
    running = 'fun'
    while (running == 'fun'):
        #GUI box to edit input times
        
        zeroline='Edit phase times\n'
        firstline='Time format = '+timeunits['start_time_prebkg']+'\n\n'
        secondline='Click OK to update plot\n'
        thirdline='Click Cancel to exit\n'
        msg=zeroline+firstline+secondline+thirdline
        title = "Gitrdone"
        fieldNames = timenames[1:]
        currentvals=[]
        for name in timenames[1:]:
            currentvals.append(timestring[name])
        newvals = easygui.multenterbox(msg, title, fieldNames,currentvals)  
        if newvals:
            if newvals != currentvals:
                currentvals = newvals
                for n,name in enumerate(timenames[1:]):
                    timestring[name]=currentvals[n]
                io.write_constant_outputs(timespath,timenames,timeunits,timestring,timeunc,timeuval)
                
                line = 'Updated phase times input file:'+timespath
                print(line)
                logs.append(line)
        else:
            running = 'not fun'
 
        [validnames,timeobject]=makeTimeObjects(timenames,timestring,date)  #convert time strings to time objects
    
        phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase
    
        phaseindices = findIndices(validnames,timeobject,datenums)  #find the indices in the time data series for the start and stop times of each phase
    
        [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,phases,phaseindices)   #define phase data series for each channel
        
        #update the data series column named phase
        name='phase'
        data[name]=['none']*len(data['time'])   #clear all values to none
        for n,datenum in enumerate(data['datenumbers']):
            for phase in phases:
                if datenum in phasedatenums[phase]:
                    if data[name][n]=='none':
                        data[name][n]=phase
                    else:
                        data[name][n]=data[name][n]+','+phase
    
        bkgvalue = calcBkgValue(bkgnames,phasemean)     #calculate the background value for each channel that will get background subtraction
        
        data_new = bkgSubtraction(names,data,bkgnames,bkgvalue) #subtract the background
    
        [phasedatenums,phasedata_new,phasemean_new] = definePhaseData(names,data_new,phases,phaseindices)   #define phase data series after background subtraction
        
        reportlogs = printBkgReport(phases,bkgnames,bkgvalue,phasemean,phasemean_new,units)
                     
        ###################################################################
        #update plot
        
        ax1.get_legend().remove()
     
        for i, ax in enumerate(f1.axes):
            for n in range(len(ax.lines)):
                plt.Artist.remove(ax.lines[0])
            name=plotnames[i]
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
        
        f1.canvas.draw()
    
    #output new background subtracted time series data file 
    io.write_timeseries(outputpath,names,units,data_new)
    
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
        
    # output average values  #####################
    phasenames=[]  
    phaseunits={}
    uvals={}
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
    name='variable'    
    phasenames = [name]+phasenames
    phaseunits[name]='units'
    phasemean_new[name]='average'
    unc[name]='uncertainty'
            
    io.write_constant_outputs(aveoutputpath,phasenames,phaseunits,phasemean_new,unc,uvals)    
    
    line='created phase averages data file:\n'+aveoutputpath
    print(line)
    logs.append(line)    
    #############################################
    
    #print final report to logs
    logs=logs+reportlogs
    
    #print to log file
    io.write_logfile(logpath,logs)
    
def makeTimeObjects(Timenames,Timestring,Date):
    Timeobject={}   #initialize a dictionary of time objects
    Validnames=[] #initialize a list of time names that have a valid time entered
    for Name in Timenames:
        Datestring=Date+' '+Timestring[Name]    #add the date to the time string
        try:
            Timeobject[Name]=dt.strptime(Datestring, '%Y%m%d  %H:%M:%S')                #convert the time string to date object
            Validnames.append(Name)
        except:
            pass
    return Validnames,Timeobject
        
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
        
def definePhaseData(Names,Data,Phases,Indices):
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
            
            #calculate average value
            if Name != 'time' and Name != 'phase':
                if all(np.isnan(Phasedata[Phasename])):
                    Phasemean[Phasename]=np.nan
                else:
                    Phasemean[Phasename]=np.nanmean(Phasedata[Phasename])
        
        #time channel: use the mid-point time string
        Phasename='datenumbers_'+Phase
        Dateobject=matplotlib.dates.num2date(Phasemean[Phasename]) #convert mean date number to date object
        Phasename='time_'+Phase
        Phasemean[Phasename]=Dateobject.strftime('%Y%m%d  %H:%M:%S')  
        
        #phase channel: use phase name
        Phasename='phase_'+Phase
        Phasemean[Phasename]=Phase
        
    return Phasedatenums,Phasedata,Phasemean
    
def calcBkgValue(Bkgnames,Phasemean):
    Bkgvalue = {}
    for Name in Bkgnames:
        Bkgvalue[Name]=np.mean([Phasemean[Name+'_prebkg'],Phasemean[Name+'_postbkg']])         #pre-post method
    return Bkgvalue
         
def bkgSubtraction(Names,Data,Bkgnames,Bkgvalue):
    Data_bkgsubtracted={}
    for Name in Names:    #for each channel that will get background subtraction
        if Name in Bkgnames:
            Data_bkgsubtracted[Name]=[]
            for n,val in enumerate(Data[Name]):
                newval=val-Bkgvalue[Name]
                Data_bkgsubtracted[Name].append(newval)   
        else:
            Data_bkgsubtracted[Name] = Data[Name]
    return Data_bkgsubtracted
    
def printBkgReport(Phases,Bkgnames,Bkgvalue,Phasemean,Phasemean_new,Units):  #add arg to print to log file        
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
    line1=line1+'bkgValue'.ljust(10)
    line2=line2+'------'.ljust(10)
    print(line1)
    Reportlogs.append(line1)
    print(line2)
    Reportlogs.append(line2)
    for Name in Bkgnames:
        line=Name.ljust(10)+str(Units[Name]).ljust(10)
        for Phase in Phases:
            Phasename=Name+'_'+Phase
            line=line+str(round(Phasemean[Phasename],1)).ljust(10)
        line=line+str(round(Bkgvalue[Name],1)).ljust(10)
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
        line=line+'0.0'.ljust(10)
        print(line)
        Reportlogs.append(line)
        
    return Reportlogs
    
    #######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_SubtractBkg(inputpath,outputpath,aveoutputpath,timespath,logpath)

