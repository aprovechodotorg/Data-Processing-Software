#v0.0  Python3

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
from UCET import LEMS_DataProcessing_IO as io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

########### inputs (only used if this script is run as executable) #############
#########      inputs      ##############
#raw data input file:
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_DataSeries_BkgSubtracted.csv'
#output data file to be created:
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_DataSeries_BkgSubtracted.csv'
#input file of start and end times for background and Unit Tests phase periods
timespath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################
##################################

def LEMS_plot_test(inputpath,timespath):
    ver = '0.0'
    
    logs=[]  #initialize a list to print to the log file
    
    [names,units,data] = io.load_timeseries(inputpath)
    
    #get the date from the time series data
    date=data['time'][0][:8]
    
     #read in input file of start and end times
    [timenames,timeunits,timestring,timeunc,timeuval] = io.load_constant_inputs(timespath)

    [validnames,timeobject]=makeTimeObjects(timenames,timestring,date)  #convert time strings to time objects
    
    phases = definePhases(validnames)   #read the names of the start and end times to get the name of each phase
    
    phaseindices = findIndices(validnames,timeobject,data['datenumbers'])  #find the indices in the time data series for the start and stop times of each phase
    
    [phasedatenums,phasedata,phasemean] = definePhaseData(names,data,phases,phaseindices)   #define phase data series for each channel
    
    plt.ion()  #turn on interactive plot mode

    lw=float(5)    #define the linewidth for the data series
    plw=float(2)    #define the linewidth for the bkg and sample period marker
    msize=30        #marker size for start and end points of each period
    
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

    plt.figure(1)
    plotnames=['CO']
    colors['CO']='silver'
    for name in plotnames:
        plt.plot(data['datenumbers'],data[name],color=colors[name],linewidth=lw, label='raw_data')  
  #      for phase in phases:
 #           phasename=name+'_'+phase        
  #          plt.plot(phasedatenums[phase],phasedata[phasename],color=colors[phase],linewidth=plw,label=phase)    
  #          plt.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
    #        plt.plot([phasedatenums[phase][0],phasedatenums[phase][-1]],[phasedata[phasename][0],phasedata[phasename][-1]],color=colors[phase],linestyle='none',marker='|',markersize=msize)
        #ax.set_ylabel(units[name])
        #plt.set_title(name)
    
    #xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    #plt.xaxis.set_major_formatter(xfmt)
    #for tick in plt.get_xticklabels():
     #   tick.set_rotation(30)
    plt.legend()    
        
    #plt.xlabel('time')
    #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
    #plt.legend(fontsize=10).draggable()
    #box = plt.get_position()
    #ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
    #plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it verically to make room for the long x axis data labels
    #ax1.legend(fontsize=10,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
    
      
     #   for (fignum,name) in enumerate(updated_channels): #for each channel that was changed
     #       for n in range(len(data_old[name])):
   #             data_old[name][n]=float(data_old[name][n])          # convert old and new data series to floats 
     #           data_new[name][n]=float(data_new[name][n])      # to remove strings so they will plot
     #       plt.figure(fignum+1)
      #      old=plt.plot(data_old[name], label=name + ' old')
       #     new=plt.plot(data_new[name], label=name + ' new')
      #      plt.xlabel('data points')
      #      plt.ylabel(units[name])
      #      plt.legend()
     #   plt.show()
    plt.show() #show all figures
    plt.pause(10)

    
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
    Phases=[] #initialize a list of Unit Tests phases (prebkg, low power, med power, high power, post bkg)
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
    for Phase in Phases: #for each Unit Tests phase
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
            if Name != 'time':
                if all(np.isnan(Phasedata[Phasename])):
                    Phasemean[Phasename]=np.nan
                else:
                    Phasemean[Phasename]=np.nanmean(Phasedata[Phasename])
        
    return Phasedatenums,Phasedata,Phasemean

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_plot_test(inputpath,timespath)