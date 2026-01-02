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

import csv
import re
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta
import os
from PEMS_FuelLoadData import load_fuel_data
from PEMS_FuelLoadData import load_exact_data
import numpy as np
from statistics import mean, median
from math import floor


def dev_plot_fuel_data(raw_fuel_data, raw_exact_data, firebox_size):
    """Produces plots to visualize and compare raw and cleaned FUEL data during development of this code.

    :param raw_fuel_data: Raw FUEL data dictionary created by PEMS_FuelLoadData
    :param raw_exact_data: Raw EXACT data dictionary created by PEMS_FuelLoadData
    :param firebox_size: Volume of firebox (lb/ft^3) for use in calculating loading density, does not exist by default
    """

    plt.close('all')
    # Create figure and axes for subplot structure
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)

    # Plot raw data
    ax1.plot(raw_fuel_data['seconds'], raw_fuel_data['firewood'])
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Fuel Weight (kg)')
    ax1.set_title('Raw Data')

    # Clean fuel data
    new_data = fuel_central_moving_median(raw_fuel_data)

    # Plot cleaned data in second subplot
    ax2.plot(raw_fuel_data['seconds'], new_data)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Fuel Weight (kg)')
    ax2.set_title('Cleaned Data')

    # Generate removal events, quantities, and times
    (kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq, load_density, rem_temp, cold_start,
     cs_density, cs_freq, second_load, sl_density, sl_freq, third_load, tl_density, tl_freq, final_load, fl_density,
     fl_freq) = fuel_removal(raw_fuel_data, raw_exact_data, firebox_size)
    print(f'Number of fuel loading events: {len(removal_start)}')
    print(f'Total mass of fuel loaded into stove: {round(sum(kg_rem), 2)} kg')
    mass_removed(raw_fuel_data)
    print(f'Removal start points: {removal_start}')
    print(f'Removal endpoints: {removal_end}')

    # Plot fuel removal data over cleaned data
    ax3.plot(raw_fuel_data['seconds'], new_data)
    ax3.plot(time_rem, removal_start, 'ro', mfc='none')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Fuel Weight (kg)')
    ax3.set_title('Fuel Removal Events')

    # Plot EXACT data
    ax4.plot(raw_exact_data['seconds'][:len(raw_exact_data['Temperature'])], raw_exact_data['Temperature'],
             'tab:orange')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Temperature (C)')
    ax4.set_title('Stove Temperature (gage)')
    if raw_exact_data['time'][1] - raw_exact_data['time'][0] == timedelta(seconds=4):
        ax4.set_xlim(right=raw_fuel_data['seconds'][-1])
    fig.subplots_adjust(hspace=0.65)
    fig.set_size_inches(6.4, 11)

    # xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')

    # for ax in fig.axes:
    #     ax.xaxis.set_major_formatter(xfmt)
    #     for tick in ax.get_xticklabels():
    #         tick.set_rotation(30)
    # plt.show()
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)

    return (kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq, load_density, rem_temp, cold_start,
            second_load, final_load)


def plot_fuel_data(raw_fuel_data, raw_exact_data, plot_output_path, firebox_size, threshold=0.125, slope_window=15):
    """Produces a plot showing the cleaned FUEL data and highlighting fuel removal events.

    :param raw_fuel_data: Raw FUEL data dictionary created by PEMS_FuelLoadData
    :param raw_exact_data: Raw EXACT data dictionary created by PEMS_FuelLoadData
    :param plot_output_path: File name to save plot with
    :param firebox_size: Volume of firebox (lb/ft^3) for use in calculating loading density
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :param slope_window: Window size for checking if a removal event has ended (sensor is steady), defaults to 15
    """
    plt.close('all')

    # Create figure and axes for plotting
    fig, (ax1, ax2) = plt.subplots(2, 1)

    # Generate cleaned data
    new_data = fuel_central_moving_median(raw_fuel_data)

    # Generate removal events, quantities, and times
    (kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq, load_density, rem_temp, cold_start,
     cs_density, cs_freq, second_load, sl_density, sl_freq, third_load, tl_density, tl_freq, final_load, fl_density,
     fl_freq) = fuel_removal(raw_fuel_data, raw_exact_data, firebox_size, threshold, slope_window)
    print(f'Number of fuel loading events: {len(removal_start)}')
    print(f'Total mass of fuel loaded into stove: {round(sum(kg_rem), 2)} kg')
    mass_removed(raw_fuel_data)
    print(f'Removal start points: {removal_start}')
    print(f'Removal endpoints: {removal_end}')

    # Plot fuel removal data over cleaned data
    ax1.plot(raw_fuel_data['seconds'], new_data)
    ax1.plot(time_rem, removal_start, 'ro', mfc='none')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Fuel Weight (kg)')
    hh_number = re.search("GP...", plot_output_path)
    try:
        ax1.set_title(f'{hh_number.group(0)} Fuel Removal Events')
    except:
        ax1.set_title('Fuel Removal Events')
    fig.set_size_inches(10, 5)

    # Plot EXACT data
    try:
        ax2.plot(raw_exact_data['seconds'][:len(raw_exact_data['Temperature'])], raw_exact_data['Temperature'],
                'tab:orange')
    except KeyError:
        ax2.plot(raw_exact_data['seconds'][:len(raw_exact_data[' Temperature (EXACT 3947)'])], raw_exact_data[' Temperature (EXACT 3947)'],
                'tab:orange')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Temperature (C)')
    ax2.set_title('Stove Temperature Relative to Ambient')
    if raw_exact_data['time'][1] - raw_exact_data['time'][0] == timedelta(seconds=4):
        ax2.set_xlim(right=raw_fuel_data['seconds'][-1])

    fig.subplots_adjust(hspace=0.5)
    fig.set_size_inches(8, 7)
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.savefig(plot_output_path)
    # plt.show()

    return (kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq, load_density, rem_temp, cold_start,
            second_load, final_load)


# *** TO DO: Decide whether to use the backwards-looking moving median or the central moving median. Currently using
#            the central moving median.
def fuel_backwards_moving_median(raw_fuel_data, window_size=30):
    """Use a backwards-looking moving median to remove spikes in the FUEL data that may not represent actual loading or
    unloading events.

    :param raw_fuel_data: Raw FUEL data dictionary loaded in with PEMS_FuelLoadData
    :param window_size: Size of the window for the moving median. Defaults to 30, for a 4-second log rate this gives
        a window size of 2 minutes (15 data points logged per minute)
    :return: smooth_fuel_data - Array of the cleaned FUEL data"""

    window = []
    fuel = raw_fuel_data['firewood']
    smooth_fuel_data = []

    for idx, kg in enumerate(fuel):
        # While there are fewer data points than your window size, just take the median of what you have
        if idx < window_size:
            window.append(kg)
            smooth_fuel_data.append(median(window))
        elif idx > len(fuel) - window_size:
            window.pop(0)
            smooth_fuel_data.append(median(window))
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window.pop(0)
            window.append(kg)
            smooth_fuel_data.append(median(window))

    return smooth_fuel_data


def fuel_central_moving_median(raw_fuel_data, window_size=30):
    """Use a central moving median to remove spikes in the FUEL data that may not represent actual loading or unloading
    events.

    :param raw_fuel_data: Raw FUEL data dictionary loaded in with PEMS_FuelLoadData
    :param window_size: Size of the window for the moving median. Defaults to 30, for a 4-second log rate this gives
        a window size of 2 minutes (15 data points logged per minute)
    :return: smooth_fuel_data - Array of the cleaned FUEL data"""

    fuel = raw_fuel_data['firewood']
    smooth_fuel_data = []

    for idx, kg in enumerate(fuel):
        # While there are fewer data points than your window size, don't take the median
        if idx < floor(window_size/2):
            smooth_fuel_data.append(kg)
        elif idx > len(fuel) - floor(window_size/2):
            smooth_fuel_data.append(kg)
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window = fuel[idx - floor(window_size/2):idx + floor(window_size/2)]
            smooth_fuel_data.append(median(window))

    return smooth_fuel_data


def fuel_removal(raw_fuel_data, raw_exact_data, firebox_size, threshold=0.125, slope_window=15):
    """Locates fuel removal events and uses EXACT data to verify that they are also loading events. Saves events to
    arrays that can be used to calculate the total mass of fuel removed (kg) and be used for plotting.

    :param raw_fuel_data: Raw FUEL data dictionary loaded in with PEMS_FuelLoadData
    :param raw_exact_data: Raw EXACT data dictionary loaded in with PEMS_FuelLoadData
    :param firebox_size: Volume of firebox (lb/ft^3) for use in calculating loading density
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :param slope_window: Window size for checking if a removal event has ended (sensor is steady), defaults to 15
    :return: kg_removed - Array containing mass values (kg) of fuel removed per event;
             time_removed - Array with times of fuel removal events in seconds;
             removal_startpoint - Array with mass values (kg) at the start of fuel removal events for plotting;
             removal_endpoint - Array with mass values (kg) at the end of fuel removal events for plotting;
             removal_timestamp - Array with timestamps at the start of fuel removal events;
             loading_frequency - Array with time (s) between each loading event;
             load_density - Array with loading density of the stove (lb/ft^3) if firebox size is known;
             rem_temp - Array with temperature of the stove (C) at the time of removal;
             cold_start - Array with load sizes if the load was a cold start, 'NA' if not;
             second_load - Array with load sizes if the load immediately followed a kindling event, 'NA' if not;
             final_load - Array with load sizes if the load is the last of a day or firing period, 'NA' if not"""

    fuel = fuel_central_moving_median(raw_fuel_data)
    fuel_time = raw_fuel_data['seconds']
    fuel_timestamps = raw_fuel_data['time']
    removal_event = []
    try:
        exact = raw_exact_data['Temperature']
    except KeyError:
        exact = raw_exact_data[' Temperature (EXACT 3947)']
    exact_timestamps = raw_exact_data['time']

    # First pass: Loop through each element in the cleaned data from fuel_central_moving_median
    for idx, kg in enumerate(fuel):
        if idx < len(fuel) - 1:
            # If the change in fuel weight from this data point to the next is greater than your threshold value, this
            # is the start of a potential removal event
            if (kg - fuel[idx + 1]) > threshold:
                # If the EXACT log rate is 1 minute
                if exact_timestamps[1] - exact_timestamps[0] == timedelta(minutes=1):
                    load_event = False
                    for i, ts in enumerate(exact_timestamps):
                        # Because the EXACT log rate is 1 minute and the FUEL log rate is 4 seconds, the timestamps will
                        # not line up. Find an EXACT data point collected within 28 seconds of a FUEL data point
                        # (through testing, I found this to be the timedelta value that made the removal array the same
                        # length as the fuel data array).
                        if abs(ts - fuel_timestamps[idx]) < timedelta(seconds=32):
                            # Check the stove temperature in the next 25 minutes (or less if near the end of the data).
                            # If the temperature is zero, the stove is off. If it is greater than zero, the stove is on.
                            if i < len(exact) - 375:
                                for j in range(375):
                                    if exact[i + j] > 0:
                                        load_event = True
                                        break
                                # If the stove is on, this is a loading event
                                if load_event:
                                    removal_event.append(1)
                                else:
                                    removal_event.append(0)
                            else:
                                for j in range(len(exact) - i):
                                    if exact[i + j] > 0:
                                        load_event = True
                                        break
                                if load_event:
                                    removal_event.append(1)
                                else:
                                    removal_event.append(0)
                # If the EXACT log rate is 4 seconds
                elif exact_timestamps[1] - exact_timestamps[0] == timedelta(seconds=4):
                    for i, ts in enumerate(exact_timestamps):
                        load_event = False
                        # If the EXACT and FUEL sensors have the same log rate, find data points with the same timestamp
                        if ts == fuel_timestamps[idx]:
                            if i < len(exact) - 375:
                                for j in range(375):
                                    if exact[i + j] > 0:
                                        load_event = True
                                        break
                                if load_event:
                                    removal_event.append(1)
                                else:
                                    removal_event.append(0)
                            else:
                                for j in range(len(exact) - i):
                                    if exact[i + j] > 0:
                                        load_event = True
                                        break
                                if load_event:
                                    removal_event.append(1)
                                else:
                                    removal_event.append(0)
            else:
                removal_event.append(0)

    # If the EXACT data log rate is less than that of the FUEL data, need to pad the end of the removal event array
    if len(fuel) - len(removal_event) > 0:
        for i in range(len(fuel) - len(removal_event)):
            removal_event.append(0)
    else:
        removal_event.append(0)
    print(f'Number of removal events found in first pass: {sum(removal_event)}')

    # Second pass: This piece of code finds removal events, then looks ahead in the data to find when the removal event
    # ends (the slope becomes steady for a period of slope_window). Removal events in this period are removed, keeping
    # only the removal event at the start of the removal period.
    for i in range(len(fuel)):
        if removal_event[i] == 1:
            for j, kg in enumerate(fuel[i:]):
                if -0.05 < kg - fuel[i + j + slope_window - 1] < 0.05:
                    for k in range(j):
                        removal_event[i + k + 1] = 0
                    break

    # Get indices of removal event elements
    removal_index = []
    for idx, rem in enumerate(removal_event):
        if rem == 1:
            removal_index.append(idx)

    # Use removal event indices to find when fuel was removed, the mass of fuel at that time for plotting, and the
    # timestamp of that fuel removal event
    time_removed = []
    removal_startpoint = []
    removal_timestamp = []
    for idx in removal_index:
        time_removed.append(fuel_time[idx])
        removal_startpoint.append(fuel[idx])
        removal_timestamp.append((raw_fuel_data['time'][idx]))

    # Use removal event indices to find endpoints of removal events for calculating load size
    removal_endpoint = []
    for i in removal_index:
        # Starting at the beginning of a removal event, look forward to find where the slope smooths out and save this
        # point as the endpoint of the removal event. The slope should be steady for a period of slope_window
        for j, kg in enumerate(fuel[i:]):
            if -0.05 < kg - fuel[i + j + slope_window - 1] < 0.05:
                removal_endpoint.append(kg)
                break

    # Take the difference between removal start and endpoints to find the mass of fuel removed (kg) per loading event
    kg_removed = []
    for idx, rem_start in enumerate(removal_startpoint):
        kg_removed.append(round(rem_start - removal_endpoint[idx], 2))

    # Take the difference between each removal start time (s) to find loading frequency
    loading_frequency = [0]
    for i in range(len(time_removed) - 1):
        loading_frequency.append(time_removed[i + 1] - time_removed[i])

    # If firebox size is given as an input, calculate loading density
    # *** Need to know units! If firebox size is given in ft^3 either convert to m^3 or convert loads to lbm.
    # *** Here I am converting the load sizes to lbm.
    load_density = []
    for kg in kg_removed:
        if firebox_size <= 0:
            load_density.append('NA')
        else:
            load_density.append(kg * 2.2 / firebox_size)

    # Save the stove temperature at the beginning of removal events
    rem_temp = []
    temp_index = []
    for idx in removal_index:
        if exact_timestamps[1] - exact_timestamps[0] == timedelta(minutes=1):
            for i, ts in enumerate(exact_timestamps):
                if abs(ts - fuel_timestamps[idx]) < timedelta(seconds=32):
                    rem_temp.append(exact[i])
                    temp_index.append(i)
        elif exact_timestamps[1] - exact_timestamps[0] == timedelta(seconds=4):
            for i, ts in enumerate(exact_timestamps):
                if ts == fuel_timestamps[idx]:
                    rem_temp.append(exact[i])
                    temp_index.append(i)

    # Find cold starts and second, third, and final loads of each firing period or day
    cold_start = ['NA'] * len(kg_removed)
    cs_density = ['NA'] * len(kg_removed)
    cs_freq = ['NA'] * len(kg_removed)
    second_load = ['NA'] * len(kg_removed)
    sl_density = ['NA'] * len(kg_removed)
    sl_freq = ['NA'] * len(kg_removed)
    third_load = ['NA'] * len(kg_removed)
    tl_density = ['NA'] * len(kg_removed)
    tl_freq = ['NA'] * len(kg_removed)
    final_load = ['NA'] * len(kg_removed)
    fl_density = ['NA'] * len(kg_removed)
    fl_freq = ['NA'] * len(kg_removed)

    for i in range(len(kg_removed)):
        if loading_frequency[i] == 0 and rem_temp[i] == 0:
            cold_start[i] = kg_removed[i]
            cs_density[i] = load_density[i]
            cs_freq[i] = loading_frequency[i]/3600
            if len(loading_frequency) > 1 and loading_frequency[i + 1]/3600 <= 7.5:
                second_load[i + 1] = kg_removed[i + 1]
                sl_density[i + 1] = load_density[i + 1]
                sl_freq[i + 1] = loading_frequency[i + 1]/3600
            if len(loading_frequency) > 1 and loading_frequency[i + 2] / 3600 <= 7.5 and second_load[i + 1] != 'NA':
                third_load[i + 2] = kg_removed[i + 2]
                tl_density[i + 2] = load_density[i + 2]
                tl_freq[i + 2] = loading_frequency[i + 2]/3600
        # If more than 7.5 hours have passed between removal events, this is a new firing period or day
        elif loading_frequency[i]/3600 > 7.5 and rem_temp[i] == 0:
            cold_start[i] = kg_removed[i]
            cs_density[i] = load_density[i]
            cs_freq[i] = loading_frequency[i]/3600
            if i > 1:
                final_load[i - 1] = kg_removed[i - 1]
                fl_density[i - 1] = load_density[i - 1]
                fl_freq[i - 1] = loading_frequency[i - 1]/3600
            if i < len(kg_removed) - 1 and loading_frequency[i + 1]/3600 <= 7.5:
                second_load[i + 1] = kg_removed[i + 1]
                sl_density[i + 1] = load_density[i + 1]
                sl_freq[i + 1] = loading_frequency[i + 1]/3600
            if i < len(kg_removed) - 2 and loading_frequency[i + 2]/3600 <= 7.5 and second_load[i + 1] != 'NA':
                third_load[i + 2] = kg_removed[i + 2]
                tl_density[i + 2] = load_density[i + 2]
                tl_freq[i + 2] = loading_frequency[i + 2]/3600

    # print(loading_frequency)
    # print(final_load)
    # print(cold_start)
    # print(second_load)

    return (kg_removed, time_removed, removal_startpoint, removal_endpoint, removal_timestamp, loading_frequency,
            load_density, rem_temp, cold_start, cs_density, cs_freq, second_load, sl_density, sl_freq, third_load,
            tl_density, tl_freq, final_load, fl_density, fl_freq)


def write_fuel_outputs(raw_fuel_data, raw_exact_data, fuel_output_path, firebox_size, threshold=0.125, slope_window=15):
    """Runs fuel removal function and writes final and intermediate outputs to .csv file for later analysis.

    :param raw_fuel_data: Raw FUEL data dictionary loaded in with PEMS_FuelLoadData
    :param raw_exact_data: Raw EXACT data dictionary loaded in with PEMS_FuelLoadData
    :param fuel_output_path: File name to write data to
    :param firebox_size: Volume of firebox (lb/ft^3) for use in calculating loading density
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :param slope_window: Window size for checking if a removal event has ended (sensor is steady), defaults to 15
    """

    (kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq, load_density, rem_temp, cold_start,
     cs_density, cs_freq, second_load, sl_density, sl_freq, third_load, tl_density, tl_freq, final_load, fl_density,
     fl_freq) = fuel_removal(raw_fuel_data, raw_exact_data, firebox_size, threshold, slope_window)

    hh_number = re.search("GP...", fuel_output_path)

    fuel_headers = ['Household Number', 'Timestamp',  'Loading Frequency (hours)', 'Removal Start (kg)',
                    'Removal End (kg)', 'Fuel Removed (kg)', 'Loading Density (lb/ft^3)', 'Stove Temperature (C)',
                    'Maximum Stove Temperature (C)', 'Normalized Stove Temperature (C)', 'Cold Start (kg)',
                    'Cold Start Density (lb/ft^3)', 'Cold Start Frequency (hours)', 'Second Load (kg)',
                    'Second Load Density (lb/ft^3)', 'Second Load Frequency (hours)', 'Third Load (kg)',
                    'Third Load Density (lb/ft^3)', 'Third Load Frequency (hours)', 'Final Load (kg)',
                    'Final Load Density (lb/ft^3)', 'Final Load Frequency (hours)']

    with open(fuel_output_path, 'w', newline='') as csvfile:
        fuel_writer = csv.writer(csvfile, delimiter=',')
        fuel_writer.writerow(fuel_headers)

        for i in range(len(kg_rem)):
            fuel_writer.writerow([hh_number.group(0), rem_timestamp[i], load_freq[i]/3600, removal_start[i],
                                  removal_end[i], kg_rem[i], load_density[i], rem_temp[i],
                                  max(raw_exact_data['Temperature']), rem_temp[i]/max(raw_exact_data['Temperature']),
                                  cold_start[i],  cs_density[i], cs_freq[i], second_load[i], sl_density[i], sl_freq[i],
                                  third_load[i], tl_density[i], tl_freq[i], final_load[i], fl_density[i], fl_freq[i]])


def mass_removed(raw_fuel_data):
    """Takes in cleaned data and finds an overestimate of the total mass of fuel removed.

    :param raw_fuel_data: Array of raw FUEL data
    :return: mass - Each element in this array contains the mass of fuel removed during one logging event. Sum this
        array to calculate the total mass of fuel removed, in kg, during the study period."""

    fuel = fuel_central_moving_median(raw_fuel_data)
    diff = []

    # Loop through each element in the cleaned data. Starting with the second element, take the difference between the
    # current and previous element and save it to the difference array.
    for idx, kg in enumerate(fuel):
        if idx == 0:
            diff.append(kg)
        # # Exclude the last minute of sensing data, assuming any removal events may be part of shutting down the sensor
        # elif idx > len(fuel) - 15:
        #     pass
        else:
            diff.append(kg - fuel[idx - 1])

    # Loop through each element in the difference array. If the current element is negative, then fuel has been removed.
    # Save this element to the mass array.
    mass = []
    for kg in diff:
        if kg < 0:
            mass.append(abs(kg))

    print(f'Overestimate of fuel mass removed: {round(sum(mass), 2)} kg')
    return mass


if __name__ == '__main__':
    # Run tests for this script here

    # Hardcoded input paths for testing
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP001\\3.16.23\\3.16.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP003\\2.15.23\\2.15.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP003\\3.8.23\\3.8.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP004\\3.14.23\\3.14.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP007\\3.15.23\\3.15.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP010\\3.16.23\\3.16.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP016\\4.7.23\\4.7.23_FuelData.csv"
    # Note for GP019 2.10.23: Large periods of time pass between fuel removal and stove temperature increases. Few fuel
    # removal events are found and recorded.
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP019\\2.10.23\\2.10.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP020\\3.28.23\\3.28.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP026\\4.11.23\\4.11.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP027\\4.13.23\\4.13.23_FuelData.csv"

    # Lab testing for verification, with fuel weights recorded manually for comparison
    sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP100\\4.19.23\\4.19.23_FuelData.csv"

    # Data from GP021
    # Note for GP021 test 2.2.23: Initial load sensitive to threshold, requires threshold of 0.01 kg to capture max
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.1.23\\2.1.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.2.23\\2.2.23_FuelData.csv"
    # Note for GP021 test 2.4.23: Final load not captured because temperature does not show stove as "on" for over an
    # hour after final load is removed. Ask Sam about this
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.3.23\\2.3.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.5.23\\2.5.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.13.23\\2.13.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.14.23\\2.14.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.16.23\\2.16.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.18.23\\2.18.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\2.21.23\\2.21.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.9.23\\3.9.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.10.23\\3.10.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.11.23\\3.11.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.12.23\\3.12.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.13.23\\3.13.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.15.23\\3.15.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.16.23\\3.16.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.17.23\\3.17.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.18.23\\3.18.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.20.23\\3.20.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.21.23\\3.21.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.24.23\\3.24.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.25.23\\3.25.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.26.23\\3.26.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.27.23\\3.27.23_FueLData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.30.23\\3.30.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\3.31.23\\3.31.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.1.23\\4.1.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.2.23\\4.2.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.4.23\\4.4.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.5.23\\4.5.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.9.23\\4.9.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.11.23\\4.11.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\Data\\GP021\\4.13.23\\4.13.23_FuelData.csv"

    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    exactpath = os.path.join(directory, testname + '_ExactData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelRemovalOutputs.csv')
    plotoutputpath = os.path.join(directory, testname + '_RemovalEventsPlot.png')

    # Load FUEL and EXACT data
    fuel_data = load_fuel_data(inputpath)
    exact_data = load_exact_data(exactpath)

    # Clean data and show plots
    # dev_plot_fuel_data(fuel_data, exact_data)
    plot_fuel_data(fuel_data, exact_data, plotoutputpath, firebox_size=0)

    # Test writing fuel outputs to .csv file
    # GP001: firebox size is 1.5 ft^3
    # GP003: firebox size is 1.625 ft^3
    # GP004: firebox size is 1.6 ft^3
    # GP007: firebox size is 3.157407407 ft^3
    # GP010: firebox size is 2.03125 ft^3
    # GP012: firebox size is 2.03125 ft^3
    # GP016: firebox size is 2.03125 ft^3
    # GP019: firebox size is ___ ft^3
    # GP020: firebox size is 2.33333 ft^3
    # GP021: firebox size is 2.0 ft^3
    # GP026: firebox size is 1.62037037 ft^3
    # GP027: firebox size is 1.859375 ft^3
    # write_fuel_outputs(fuel_data, exact_data, fueloutputpath, firebox_size=0)
