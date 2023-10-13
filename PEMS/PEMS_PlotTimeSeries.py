# v0.0  Python3

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
from matplotlib.ticker import MultipleLocator


# this plot function is called by PEMS_Plotter1.py
# has gui pop-up list to choose plot channels
# plots all channels on 1 axis
#########      inputs      ##############
# names: list of channel names
# units: dictionary of channel units
# data: dictionary of times series data including dateobjects and datenumbers channels
##################################

def PEMS_PlotTimeSeries(names, units, data, plotpath, savefig):
    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(plotpath)
    matplotlib.rcParams['savefig.directory'] = directory

    var = []
    on = {}
    scale = {}
    colors = {}

    # load input file
    stuff = []
    with open(plotpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # put inputs in a dictionary
    for row in stuff:
        name = row[0]
        on[name] = row[1]
        scale[name] = row[2]
        colors[name] = row[3]
        var.append(name)

    lw = float(2)  # define the linewidth for the data series
    plw = float(2)  # define the linewidth for the bkg and sample period marker
    msize = 30  # marker size for start and end points of each period

    f1, (ax1) = plt.subplots(1, sharex=True)  # three subplots sharing x axis
    ylimit = (-5, 500)
    # Set y tick markers for every 20 units

    plotnames = []  # Run through names in plotpath csv to see what the user wants plotted
    var.remove(var[0])
    for name in var:
        scale[name] = float(scale[name])
        if int(on[name]) == 1:
            plotnames.append(name)

    unitstring = ''  # reset the y axis label string

    for name in plotnames:
        if colors[name] == '':  # see if the color is not defined
            # if the color is not defined choose a random color
            r = random.random()
            b = random.random()
            g = random.random()
            colors[name] = (r, g, b)

        if unitstring == '':  # if unitstring is blank
            unitstring = unitstring + units[name] + ' (X' + str(scale[name]) + ')'  # add the units and the scale
        else:  # if unitstring is not blank,
            if units[name] not in unitstring:  # and the units are not already listed
                unitstring = unitstring + ',' + units[name] + ' (X' + str(
                    scale[name]) + ')'  # add a comma and the units and add scale

    # ax1.get_legend().remove()  # clear the old legend
    n = 0
    for name in plotnames:  # Scale plot according to input
        scalar = int(scale[name])
        data[name] = [x * scalar for x in data[name]]
        n += 1

    for i, ax in enumerate(f1.axes):  # for each subplot (but in this case there is only 1 subplot)
        for n in range(len(ax.lines)):  # for each line that was previously drawn
            plt.Artist.remove(ax.lines[0])  # clear the line

        # Plot for fuel sensor data (different sample size, so different time series used)
        fnames = ['Battery level', 'firewood']  # Sensor names in fuel sensor
        f = []
        # Check if fuel data is requested to be graphed
        for name in plotnames:
            for fname in fnames:
                if fname == name:
                    # If sensor is requested to be graphed, graph and track what was graphed
                    ax.plot(data['fdatenumbers'], data[name], color=colors[name], linewidth=lw,
                            label=(name + ' (X' + str(scale[name]) + ')'))
                    f.append(name)
                    ax.set_ylabel(unitstring)
        # If anything was graphed from the fuel data, remove the name from plotnames to avoid errors
        for m in f:
            try:
                plotnames.remove(m)
            except:
                pass

        # Plot for exact sensor data (different sample size, so different time series used)
        exnames = ['Usage', 'Temperature']
        ex = []
        # Check if exact data is requested to be graphed
        for name in plotnames:
            for exname in exnames:
                if exname == name:
                    # If sensor is requested to be graphed, graph and track what was graphed
                    ax.plot(data['exdatenumbers'], data[name], color=colors[name], linewidth=lw,
                            label=(name + ' (X' + str(scale[name]) + ')'))
                    ex.append(name)
                    ax.set_ylabel(unitstring)
        # If anything was graphed from the exact data, remove the name from plotnames to avoid errors
        for m in ex:
            try:
                plotnames.remove(m)
            except:
                pass
        r = []
        rnames = ['Hour Loading Frequency', 'Minute Loading Frequency', 'Second Loading Frequency', 'Removal Start',
                  'Removal End',
                  'Fuel Removed', 'Loading Density', 'Stove Temperature', 'Maximum Stove Temperature',
                  'Normalized Stove Temperature']
        for name in plotnames:
            for rname in rnames:
                if rname == name:
                    # If outputs are requested to be graphed
                    ax.plot(data['rdatenumbers'], data[name], color=colors[name], linewidth=lw,
                            label=(name + ' (X' + str(scale[name]) + ')'))
                    ax.scatter(data['rdatenumbers'], data[name], color='indianred',
                               marker='o')  # plot o markers for data set
                    r.append(name)
                    ax.set_ylabel(unitstring)
        # If anything was graphed from the exact data, remove the name from plotnames to avoid errors
        for q in r:
            try:
                plotnames.remove(q)
            except:
                pass
        # Graph all remaining sensors from PEMS or LEMS
        for name in plotnames:
            ax.plot(data['datenumbers'], (data[name]), color=colors[name], linewidth=lw,
                    label=(name + ' (X' + str(scale[name]) + ')'))  # draw data series
            ax.set_ylabel(unitstring)

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    # Clear existing y-tick formatting
    # Desired y-tick positions with a 20-unit spacing
    ytick_positions = range(0, 500, 20)

    # Desired y-tick labels based on ytick_positions
    ytick_labels = [str(pos) for pos in ytick_positions]
    # Set custom y-tick positions and labels
    ax.set_yticks(ytick_positions)
    ax.set_yticklabels(ytick_labels)

    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    plt.yticks(range(0, 500, 20))
    plt.setp(ax1, ylim=ylimit)
    plt.savefig(savefig, bbox_inches='tight')
    plt.show()


#####################################################################
# the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_PlotTimeSeries(names, units, data)