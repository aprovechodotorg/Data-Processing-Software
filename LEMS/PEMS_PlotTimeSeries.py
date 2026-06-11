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
plt.rcParams.update({'font.size': 10}) #set font size
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

def PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames,
                        nnames, tnames, sennames, opsnames, pnames, plotpath, savefig):
    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(plotpath)
    matplotlib.rcParams['savefig.directory'] = directory

    var = []
    on = {}
    scale = {}
    colors = {}
    order = {} #higher number will plot on top

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
        try:
            order[name] = row[4]
        except IndexError:
            pass
        var.append(name)

    lw = float(2)  # define the linewidth for the data series
    plw = float(2)  # define the linewidth for the bkg and sample period marker
    msize = 30  # marker size for start and end points of each period

    f1, (ax1) = plt.subplots(1, sharex=True, figsize=(3.5,1.25))  # three subplots sharing x axis
    ylimit = (-5, 500)
    # Set y tick markers for every 20 units

    plotnames = []  # Run through names in plotpath csv to see what the user wants plotted
    var.remove(var[0])
    for name in var:
        scale[name] = float(scale[name])
        try:
            order[name] = float(order[name])
        except KeyError:
            pass
        except ValueError:
            order[name] = 1
        if int(on[name]) == 1:
            plotnames.append(name)

    unitstring = ''  # reset the y axis label string

    start = data['datenumbers'][0]
    end = data['datenumbers'][-1]

   # o = 1000 #initialize order counter to a number much higher than the number of lines that could be plotted
    for name in plotnames:
        if colors[name] == '':  # see if the color is not defined
            # if the color is not defined choose a random color
            r = random.random()
            b = random.random()
            g = random.random()
            colors[name] = (r, g, b)
        #if order[name] == '':
            # if order is not defined, put in sequential order with the first name to plot on the top
           # order[name] = o
       # o = o - 1
        if unitstring == '':  # if unitstring is blank
            unitstring = unitstring + units[name] + ' (X' + str(scale[name]) + ')'  # add the units and the scale
        else:  # if unitstring is not blank,
            #if units[name] not in unitstring:  # and the units are not already listed
            unitstring = unitstring + ',' + units[name] + ' (X' + str(
                scale[name]) + ')'  # add a comma and the units and add scale

    # ax1.get_legend().remove()  # clear the old legend
    n = 0
    for name in plotnames:  # Scale plot according to input
        scalar = scale[name]
        print(name)
        y = 0
        for n, x in enumerate(data[name]):
            try:
                float(x)
            except ValueError:
                x = y
            data[name][n] = x * scalar
            y = x
        n += 1

    for i, ax in enumerate(f1.axes):  # for each subplot (but in this case there is only 1 subplot)
        for n in range(len(ax.lines)):  # for each line that was previously drawn
            plt.Artist.remove(ax.lines[0])  # clear the line


        if len(fnames) != 0:  # If there's data from this sensor
            type = 'f'
            plotnames = plototherdatastreams(fnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)
        if len(fcnames) != 0:
            type = 'fc'
            plotnames = plototherdatastreams(fnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)
        if len(exnames) != 0:  # If there's data from this sensor
            type = 'ex'
            plotnames = plototherdatastreams(exnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for scale sensor data (different sample size, so different time series used)
        if len(snames) != 0:  # If there's data from this sensor
            type = 's'
            plotnames = plototherdatastreams(snames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for scale sensor data (different sample size, so different time series used)
        if len(isnames) != 0:  # If there's data from this sensor
            type = 'is'
            plotnames = plototherdatastreams(isnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for scale sensor data (different sample size, so different time series used)
        if len(anames) != 0:  # If there's data from this sensor
            type = 'a'
            plotnames = plototherdatastreams(anames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for scale sensor data (different sample size, so different time series used)
        if len(cnames) != 0:  # If there's data from this sensor
            type = 'c'
            plotnames = plototherdatastreams(cnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for scale sensor data (different sample size, so different time series used)
        if len(mnames) != 0:  # If there's data from this sensor
            type = 'm'
            plotnames = plototherdatastreams(mnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for nano scan sensor data (different sample size, so different time series used)
        if len(nnames) != 0:  # If there's data from this sensor
            type = 'n'
            plotnames = plototherdatastreams(nnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for teom sensor data (different sample size, so different time series used)
        if len(tnames) != 0:  # If there's data from this sensor
            type = 't'
            plotnames = plototherdatastreams(tnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for senserion sensor data (different sample size, so different time series used)
        if len(sennames) != 0:  # If there's data from this sensor
            type = 'sen'
            plotnames = plototherdatastreams(sennames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Plot for senserion sensor data (different sample size, so different time series used)
        if len(opsnames) != 0:  # If there's data from this sensor
            type = 'ops'
            plotnames = plototherdatastreams(opsnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        if len(pnames) != 0:  # If there's data from this sensor
            type = 'p'
            plotnames = plototherdatastreams(pnames, plotnames, data, scale, start, end, ax, lw, type, colors, order)

        # Graph all remaining sensors from PEMS or LEMS
        for name in plotnames:
            try:
                ax.plot(data['datenumbers'], (data[name]), color=colors[name], zorder=order[name], linewidth=lw,
                        label=(name + ' (X' + str(scale[name]) + ')'))  # draw data series
            except KeyError:
                ax.plot(data['datenumbers'], (data[name]), color=colors[name], linewidth=lw,
                        label=(name + ' (X' + str(scale[name]) + ')'))  # draw data series
        ax.set_ylabel(unitstring)

    xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
    # xfmt = matplotlib.dates.DateFormatter('%Y%m%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    # Clear existing y-tick formatting
    # Desired y-tick positions with a 20-unit spacing
    #ytick_positions = range(0, 500, 20)

    # Desired y-tick labels based on ytick_positions
    #ytick_labels = [str(pos) for pos in ytick_positions]
    # Set custom y-tick positions and labels
    #ax.set_yticks(ytick_positions)
    #ax.set_yticklabels(ytick_labels)

    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
    ax1.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), )  # Put a legend to the right of ax1
    #plt.yticks(range(0, 500, 20))
    plt.setp(ax1, ylim=ylimit)
    # Add a title to the plot
    ax1.set_title(filename)
    plt.savefig(savefig, bbox_inches='tight')
    plt.show()


def PEMS_PlotTimeSeries_Grid(names, units, all_data, phases, fnames, fcnames, exnames, snames, isnames, anames, cnames,
                             mnames,
                             nnames, tnames, sennames, opsnames, pnames, plotpath, savefig):
    directory, filename = os.path.split(plotpath)
    matplotlib.rcParams['savefig.directory'] = directory

    var = []
    on = {}
    scale = {}
    colors = {}
    order = {}

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
        try:
            order[name] = row[4]
        except IndexError:
            pass
        var.append(name)

    lw = float(2)

    # Define plot names to be graphed based on CSV
    plotnames_master = []
    var.remove(var[0])
    for name in var:
        scale[name] = float(scale[name])
        try:
            order[name] = float(order[name])
        except KeyError:
            pass
        except ValueError:
            order[name] = 1
        if int(on[name]) == 1:
            plotnames_master.append(name)

    # Generate unit string for y-axis
    unitstring = ''
    for name in plotnames_master:
        if colors[name] == '':
            colors[name] = (random.random(), random.random(), random.random())
        if unitstring == '':
            unitstring = unitstring + units[name] + ' (X' + str(scale[name]) + ')'
        else:
            unitstring = unitstring + ',' + units[name] + ' (X' + str(scale[name]) + ')'

    # EDIT: Create subplots. Vertically aligned, sharing X axis.
    # Height is scaled by the number of phases (e.g., 4 inches per plot) so they stay the same length.
    num_plots = len(all_data)
    f1, axes = plt.subplots(nrows=num_plots, ncols=1, sharex=True, figsize=(10, 4 * num_plots))

    # Ensure axes is iterable even if there is only 1 subplot
    if num_plots == 1:
        axes = [axes]

    ylimit = (-5, 500)

    # EDIT: Iterate over each subplot axis, its corresponding data, and the phase name
    for ax, data, phase in zip(axes, all_data, phases):

        plotnames = list(plotnames_master)  # copy the list for this iteration
        # EDIT: Establish the start time of this specific phase
        phase_start = data['datenumbers'][0]

        # EDIT: Convert absolute datenumbers to Elapsed Hours
        # (date - phase_start) gives days, * 24 gives hours
        elapsed_hours = [(d - phase_start) * 24 for d in data['datenumbers']]

        # Apply scaling to the data
        for name in plotnames:
            scalar = scale[name]
            y = 0
            for n, x in enumerate(data[name]):
                try:
                    float(x)
                except ValueError:
                    x = y
                data[name][n] = x * scalar
                y = x

        # Plot all the special datastreams
        if len(fnames) != 0:
            plotnames = plototherdatastreams(fnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'f', colors, order)
        if len(fcnames) != 0:
            plotnames = plototherdatastreams(fnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'fc', colors, order)
        if len(exnames) != 0:
            plotnames = plototherdatastreams(exnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'ex', colors, order)
        if len(snames) != 0:
            plotnames = plototherdatastreams(snames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 's', colors, order)
        if len(isnames) != 0:
            plotnames = plototherdatastreams(isnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'is', colors, order)
        if len(anames) != 0:
            plotnames = plototherdatastreams(anames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'a', colors, order)
        if len(cnames) != 0:
            plotnames = plototherdatastreams(cnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'c', colors, order)
        if len(mnames) != 0:
            plotnames = plototherdatastreams(mnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'm', colors, order)
        if len(nnames) != 0:
            plotnames = plototherdatastreams(nnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'n', colors, order)
        if len(tnames) != 0:
            plotnames = plototherdatastreams(tnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 't', colors, order)
        if len(sennames) != 0:
            plotnames = plototherdatastreams(sennames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'sen', colors, order)
        if len(opsnames) != 0:
            plotnames = plototherdatastreams(opsnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'ops', colors, order)
        if len(pnames) != 0:
            plotnames = plototherdatastreams(pnames, plotnames, data, scale, phase_start, data['datenumbers'][-1], ax, lw, 'p', colors, order)

        # Plot remaining datastreams
        for name in plotnames:
            try:
                ax.plot(elapsed_hours, (data[name]), color=colors[name], zorder=order[name], linewidth=lw,
                        label=(name + ' (X' + str(scale[name]) + ')'))
            except KeyError:
                ax.plot(elapsed_hours, (data[name]), color=colors[name], linewidth=lw,
                        label=(name + ' (X' + str(scale[name]) + ')'))

        ax.set_ylabel(unitstring)
        ax.set_title(f"Phase: {phase}")  # Subplot title
        plt.setp(ax, ylim=ylimit)

    # EDIT: Formatting the shared x-axis as linear hours instead of time
    axes[-1].set_xlabel("Hours Elapsed since start of Phase")
    # Removed DateFormatter since we are now using floats

    # EDIT: Apply a SINGLE legend to the figure, extracted from the first plot
    handles, labels = axes[0].get_legend_handles_labels()
    f1.legend(handles, labels, fontsize=10, loc='center left', bbox_to_anchor=(1.02, 0.5))

    f1.suptitle(filename)  # Main title at the top
    plt.tight_layout()  # Ensures spacing doesn't overlap
    plt.savefig(savefig, bbox_inches='tight')
    plt.show()

def plototherdatastreams(names, plotnames, data, scale, start, end, ax, lw, type, colors, order):
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
                try:
                    ax.plot(datenumbers, numbers, linewidth=lw, color=colors[name], zorder=order[name], label=(name + ' (X' + str(scale[name]) + ')'))
                except KeyError:
                    ax.plot(datenumbers, numbers, linewidth=lw, color=colors[name],
                            label=(name + ' (X' + str(scale[name]) + ')'))
                plotted.append(name)
    # If anything was graphed from the fuel data, remove the name from plotnames to avoid errors
    for m in plotted:
        try:
            plotnames.remove(m)
        except:
            pass

    return plotnames

#####################################################################
# the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, nnames, tnames, sennames,
                        opsnames, plotpath, savefig)
