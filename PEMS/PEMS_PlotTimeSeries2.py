#v0.1  Python3

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
import PEMS_DataProcessing_IO as io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import random
import easygui

#this plot function is called by PEMS_Plotter1.py
#has gui pop-up list to choose plot channels
#plots all channels on 1 axis
#selecting a channel that ends in '_uc' plots the base channel with a shaded uncertainty band
#########      inputs      ##############
#names: list of channel names
#units: dictionary of channel units
#data: dictionary of times series data including dateobjects and datenumbers channels
##################################

def nominal(vals):
    #return nominal values from a list that may contain ufloats, floats, or nan
    return np.array([v.nominal_value if hasattr(v, 'nominal_value') else v for v in vals], dtype=float)

def stdev(vals):
    #return standard deviations from a list that may contain ufloats (0 for plain floats)
    return np.array([v.std_dev if hasattr(v, 'std_dev') else 0 for v in vals], dtype=float)

def basename(name):
    #strip the '_uc' suffix to get the base channel name
    if name.endswith('_uc'):
        return name[:-3]
    return name

def get_nominal_and_uncertainty(data, name):
    #return nominal values and uncertainty for a channel
    #uses the ufloat std_dev if available, otherwise the separate _uc channel
    base = basename(name)
    if base in data:
        nom = nominal(data[base])
        unc = stdev(data[base])
    else:   #base channel not found, fall back to the _uc channel alone
        nom = nominal(data[name])
        unc = np.zeros(len(nom))
    if not np.any(unc > 0) and base+'_uc' in data:   #no ufloat uncertainty, try the _uc channel
        unc = nominal(data[base+'_uc'])
    return nom, unc

def get_color(colors, name):
    #_uc channels use the same color as their base channel
    base = basename(name)
    if base not in colors:  #if the color is not defined choose a random color
        colors[base] = (random.random(), random.random(), random.random())
    return colors[base]

def make_unitstring(units, plotnames):
    #build the y axis label string
    unitstring = ''
    for name in plotnames:
        unit = units.get(basename(name), units.get(name, ''))
        if unitstring == '':                    #if unitstring is blank
            unitstring = unit                   #add the units
        elif unit not in unitstring:            #if the units are not already listed
            unitstring = unitstring+','+unit    #add a comma and the units
    return unitstring

def draw_channels(ax, data, plotnames, colors, lw):
    #draw each selected channel; '_uc' channels get a shaded uncertainty band
    x = nominal(data['datenumbers'])
    for name in plotnames:
        color = get_color(colors, name)
        if name.endswith('_uc'):
            nom, unc = get_nominal_and_uncertainty(data, name)
            ax.plot(x, nom, color=color, linewidth=lw, label=basename(name)+' ± uc')
            ax.fill_between(x, nom-unc, nom+unc, color=color, alpha=0.25, linewidth=0)
        else:
            ax.plot(x, nominal(data[name]), color=color, linewidth=lw, label=name)

def clear_channels(ax):
    #remove previously drawn lines and uncertainty bands
    for artist in list(ax.lines) + list(ax.collections):
        artist.remove()

def PEMS_PlotTimeSeries(names,units,data,plottitle):
    
    plt.ion()  #turn on interactive plot mode

    lw=float(2)    #define the linewidth for the data series
    plw=float(2)    #define the linewidth for the bkg and sample period marker
    msize=30        #marker size for start and end points of each period
    
    colors={}
    colors['CO']='red'
    colors['CO2']='blue'
    colors['PM'] = 'black'
    colors['GrnAbs'] = 'green'
    colors['RedAbs'] = 'red'
    colors['BluAbs'] = 'blue'
    colors['VOC'] = 'violet'
    colors['HC'] = 'brown'
    colors['CH4'] = 'teal'
    colors['TC2'] = 'black'
    
    #plt.figure(1)
    f1, (ax1) = plt.subplots(1, sharex=True) #three subplots sharing x axis
    
    msg ="Select channels to plot\n(channels ending in _uc plot with a shaded uncertainty band)"
    title = "gitrdone"
    channels = []
    for name in names:  #skip time,headID, seconds
        if name not in ['time','time_uc','ID','ID_uc','seconds','seconds_uc']:
            channels.append(name)
    plotnames = easygui.multchoicebox(msg, title, channels)
    if not plotnames:   #nothing selected
        return
    
    unitstring = make_unitstring(units, plotnames)   #y axis label string
                
    for i, ax in enumerate(f1.axes):        #for each subplot (but in this case there is only 1 subplot)
        draw_channels(ax, data, plotnames, colors, lw)
        ax.tick_params(axis="y", labelsize=15)
        ax.set_ylabel(unitstring, fontsize=20)
        ax.set_title(plottitle)
    
    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    #xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
    #plt.xlabel('time')
    #plt.legend(fontsize=10).get_frame().set_alpha(0.5)
    #plt.legend(fontsize=10).draggable()
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])    #squeeze it down to make room for the legend
    #plt.subplots_adjust(top=.95,bottom=0.1) #squeeze it verically to make room for the long x axis data labels
    ax1.legend(fontsize=20,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
    #ax1.legend()
    plt.show() #show all figures
    #plt.pause(10)
    
    running = 'fun'
    while (running == 'fun'):
    
        msg ="Select channels to plot\n(channels ending in _uc plot with a shaded uncertainty band)\nMinimize this window to see plot\nCancel this window to close plot"
        title = plottitle
        channels = []
        for name in names:  #skip time,headID, seconds
            if name not in ['time','time_uc','ID','ID_uc','seconds','seconds_uc']:
                channels.append(name) 
        plotnames = easygui.multchoicebox(msg, title, channels)
        
        if plotnames: #if any channels are selected
            unitstring = make_unitstring(units, plotnames)   #reset the y axis label string
                        
            ax1.get_legend().remove()   #clear the old legend
     
            for i, ax in enumerate(f1.axes):    #for each subplot (but in this case there is only 1 subplot)
                clear_channels(ax)              #clear old lines and uncertainty bands
                draw_channels(ax, data, plotnames, colors, lw)   # draw data series
                ax.relim()                      #rescale axes to the new data
                ax.autoscale_view()
                ax.tick_params(axis="y", labelsize=15)
                ax.set_ylabel(unitstring,fontsize=20)

            #ax1.legend()
            ax1.legend(fontsize=20,loc='center left', bbox_to_anchor=(1, 0.5),)  # Put a legend to the right of ax1
        
            f1.canvas.draw()        #redraw the plot
               
        else:   #if no channels were selected
            running = 'not fun' #set flag to exit out of while loop
        

  

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_PlotTimeSeries(names,units,data,plottitle)
