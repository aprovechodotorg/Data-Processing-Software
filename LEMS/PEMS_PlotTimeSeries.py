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
import LEMS_DataProcessing_IO as io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import random
import easygui
import csv
import os

#this plot function is called by PEMS_Plotter1.py
#has gui pop-up list to choose plot channels
#plots all channels on 1 axis
#########      inputs      ##############
#names: list of channel names
#units: dictionary of channel units
#data: dictionary of times series data including dateobjects and datenumbers channels
##################################

def PEMS_PlotTimeSeries(names, units, data, fnames, exnames, snames, nnames, tnames, sennames, plotpath, savefig):

    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(plotpath)
    matplotlib.rcParams['savefig.directory'] = directory

    var = []
    on = {}
    scale = {}
    colors = {}

    #load input file
    stuff=[]
    with open(plotpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    #put inputs in a dictionary
    for row in stuff:
        name = row[0]
        on[name]=row[1]
        scale[name]=row[2]
        colors[name]=row[3]
        var.append(name)

    lw=float(2)    #define the linewidth for the data series
    plw=float(2)    #define the linewidth for the bkg and sample period marker
    msize=30        #marker size for start and end points of each period

    f1, (ax1) = plt.subplots(1, sharex=True) #three subplots sharing x axis
    ylimit = (0, 350)
    plt.setp(ax1, ylim=ylimit)

    plotnames = [] #Run through names in plotpath csv to see what the user wants plotted
    var.remove(var[0])
    for name in var:
        scale[name] = float(scale[name])
        if int(on[name]) == 1:
            plotnames.append(name)

    unitstring = ''  # reset the y axis label string

    start = data['datenumbers'][0]
    end = data['datenumbers'][-1]

    for name in plotnames:
        if colors[name] == '':  # see if the color is not defined
            #if the color is not defined choose a random color
            r = random.random()
            b = random.random()
            g = random.random()
            colors[name] = (r, g, b)

        if unitstring == '':  # if unitstring is blank
            unitstring = unitstring + units[name] + ' (X' + str(scale[name]) + ')' # add the units and the scale
        else:  # if unitstring is not blank,
            if units[name] not in unitstring:  # and the units are not already listed
                unitstring = unitstring + ',' + units[name] + ' (X' + str(scale[name]) + ')'# add a comma and the units and add scale

    #ax1.get_legend().remove()  # clear the old legend
    n = 0
    for name in plotnames:  # Scale plot according to input
        scalar = scale[name]
        data[name] = [x * scalar for x in data[name]]
        n += 1

    for i, ax in enumerate(f1.axes):  # for each subplot (but in this case there is only 1 subplot)
        for n in range(len(ax.lines)):  # for each line that was previously drawn
            plt.Artist.remove(ax.lines[0])  # clear the line

        #Plot for fuel sensor data (different sample size, so different time series used)
        if len(fnames) != 0: #If there's data from this sensor
            type = 'f'
            plotnames = plototherdatastreams(fnames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Plot for exact sensor data (different sample size, so different time series used)
        if len(exnames) != 0:  # If there's data from this sensor
            type = 'ex'
            plotnames = plototherdatastreams(exnames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Plot for scale sensor data (different sample size, so different time series used)
        if len(snames) != 0: #If there's data from this sensor
            type = 's'
            plotnames = plototherdatastreams(snames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Plot for nano scan sensor data (different sample size, so different time series used)
        if len(nnames) != 0: #If there's data from this sensor
            type = 'n'
            plotnames = plototherdatastreams(nnames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Plot for teom sensor data (different sample size, so different time series used)
        if len(tnames) != 0: #If there's data from this sensor
            type = 't'
            plotnames = plototherdatastreams(tnames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Plot for senserion sensor data (different sample size, so different time series used)
        if len(sennames) != 0: #If there's data from this sensor
            type = 'sen'
            plotnames = plototherdatastreams(sennames, plotnames, data, scale, start, end, ax, lw, type, colors)

        #Graph all remaining sensors from PEMS or LEMS
        for name in plotnames:
            ax.plot(data['datenumbers'], (data[name]), color=colors[name], linewidth=lw, label=(name+ ' (X' + str(scale[name]) + ')'))  # draw data series

        ax.set_ylabel(unitstring)

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    plt.savefig(savefig, bbox_inches='tight')
    plt.show()


def plototherdatastreams(names, plotnames, data, scale, start, end, ax, lw, type, colors):
    plotted = []
    for name in plotnames:
        for typename in names:
            if typename == name:
                datenumbers = []
                numbers = []
                for x, date in enumerate(data[type + 'datenumbers']):  # cut data to phase time
                    if start <= date <= end:
                        datenumbers.append(date)
                        numbers.append(data[name][x])
                # If sensor is requested to be graphed, graph and track what was graphed
                ax.plot(datenumbers, numbers, linewidth=lw, color=colors[name] label=(name + ' (X' + str(scale[name]) + ')'))
                plotted.append(name)
    # If anything was graphed from the fuel data, remove the name from plotnames to avoid errors
    for m in plotted:
        try:
            plotnames.remove(m)
        except:
            pass

    return plotnames
  

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_PlotTimeSeries(names, units, data, fnames, exnames, snames, nnames, tnames, sennames, plotpath, savefig)