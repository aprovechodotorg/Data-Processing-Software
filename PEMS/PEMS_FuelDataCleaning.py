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
from datetime import datetime as dt
from datetime import datetime, timedelta
import os
from PEMS_FuelLoadData import load_fuel_data
from PEMS_FuelLoadData import load_exact_data
import numpy as np
from statistics import median
from math import floor


def dev_plot_fuel_data(raw_fuel_data, raw_exact_data):
    """Produces plots to visualize and compare raw and cleaned FUEL data during development of this code.

    :param raw_fuel_data: Raw FUEL data dictionary created by PEMS_FuelLoadData
    :param raw_exact_data: Raw EXACT data dictionary created by PEMS_FuelLoadData"""

    # Create figure and axes for subplot structure
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)

    # Plot raw data
    ax1.plot(raw_fuel_data['seconds'], raw_fuel_data['firewood'])
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Fuel Weight (kg)')
    ax1.set_title('Raw Data')

    # Call to clean_fuel_data function to generate cleaned data
    new_data = alt_clean_fuel_data(raw_fuel_data)

    # Plot cleaned data in second subplot
    ax2.plot(raw_fuel_data['seconds'], new_data)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Fuel Weight (kg)')
    ax2.set_title('Cleaned Data')

    # Call to fuel_removal function to generate removal events, quantities, and times
    kg_rem, time_rem, removal_start, removal_end, rem_timestamp, load_freq = fuel_removal(new_data, fuel_data,
                                                                                          exact_data)
    print(f'Number of fuel removal events using fuel_removal function: {len(removal_start)}')
    print(f'Total mass of fuel removed using fuel_removal function: {round(sum(kg_rem), 2)} kg')
    mass_removed(new_data)

    # Plot fuel removal data over cleaned data
    ax3.plot(raw_fuel_data['seconds'], new_data)
    ax3.plot(time_rem, removal_start, 'ro', mfc='none')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Fuel Weight (kg)')
    ax3.set_title('Fuel Removal Events')

    # Plot EXACT data
    ax4.plot(raw_exact_data['seconds'], raw_exact_data['Temperature'], 'tab:orange')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Temperature (C)')
    ax4.set_title('Stove Temperature (gage)')
    fig.subplots_adjust(hspace=0.65)
    fig.set_size_inches(6.4, 11)
    plt.show()


def plot_fuel_data(raw_fuel_data):
    """Produces a plot showing the cleaned FUEL data and highlighting fuel removal events.

    :param raw_fuel_data: Raw FUEL data dictionary created by PEMS_FuelLoadData"""

    # Create figure and axes for plotting
    fig, ax = plt.subplots(1)

    # Call to clean_fuel_data function to generate cleaned data
    new_data = alt_clean_fuel_data(raw_fuel_data)

    # Call to fuel_removal function to generate removal events, quantities, and times
    kg_rem, time_rem_act, removal_start, removal_end, rem_timestamp, load_freq = fuel_removal(new_data, fuel_data,
                                                                                              exact_data)
    print(f'Number of fuel removal events using fuel_removal function: {len(removal_start)}')
    print(f'Total mass of fuel removed using fuel_removal function: {round(sum(kg_rem), 2)} kg')
    mass_removed(new_data)

    # Ask user to input the household number for the plot title
    # *** don't need this later - should be able to read in hh number from data entry sheet
    hh = input('Please enter the household number for this data: ')

    # Plot fuel removal data over cleaned data
    ax.plot(raw_fuel_data['seconds'], new_data)
    ax.plot(time_rem_act, removal_start, 'ro', mfc='none')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Fuel Weight (kg)')
    ax.set_title(f'Fuel Removal Events {hh}')
    fig.set_size_inches(10, 5)
    plt.savefig(f'C:\\Users\\kiern\\Downloads\\GP003\\3.8.23\\{hh}.png')


# *** TO DO: Decide whether to use the backwards-looking moving median or the central moving median.
def clean_fuel_data(raw_fuel_data, window_size=30):
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
        # Once you get close to the end of the raw data array, just take the median of what you have again
        elif idx > len(fuel) - window_size:
            window.pop(0)
            smooth_fuel_data.append(median(window))
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window.pop(0)
            window.append(kg)
            smooth_fuel_data.append(median(window))

    return smooth_fuel_data


def alt_clean_fuel_data(raw_fuel_data, window_size=30):
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
        # Once you get close to the end of the raw data array, don't take the median again
        elif idx > len(fuel) - floor(window_size/2):
            smooth_fuel_data.append(kg)
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window = fuel[idx - floor(window_size/2):idx + floor(window_size/2)]
            smooth_fuel_data.append(median(window))

    return smooth_fuel_data


# *** TO DO: Use EXACT data to determine whether removal events represent fuel being loaded into the fire
def fuel_removal(smooth_fuel_data, raw_fuel_data, raw_exact_data, threshold=0.25, merge_threshold=15):
    """Locates fuel removal events and saves them to arrays that can be used to calculate the total mass of fuel
    removed (kg) and be used for plotting.

    :param smooth_fuel_data: Array of cleaned FUEL data created with clean_fuel_data
    :param raw_fuel_data: Raw FUEL data dictionary loaded in with PEMS_FuelLoadData, used here for the 'seconds' values
    :param raw_exact_data: Raw EXACT data dictionary loaded in with PEMS_FuelLoadData
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :param merge_threshold: Window size for merging removal events, defaults at 15 (1 minute for a 4-second log rate)
    :return: kg_removed - Array containing mass values (kg) of fuel removed per event;
             time_removed - Array with times of fuel removal events in seconds;
             removal_startpoint - Array with mass values (kg) at the start of fuel removal events for plotting;
             removal_endpoint - Array with mass values (kg) at the end of fuel removal events for plotting;
             removal_timestamp - Array with timestamps at the start of fuel removal events;
             loading_frequency - Array with time (s) between each loading event"""

    fuel = smooth_fuel_data
    fuel_time = raw_fuel_data['seconds']
    removal_event = []
    exact = []
    exact_time = []

    # Get usage data from EXACT dictionary
    raw_exact_sorted = sorted(raw_exact_data.keys())
    raw_exact_usage = raw_exact_data[raw_exact_sorted[0]]
    exact_usage = []

    # If the EXACT log rate was 1 minute, copy each data point 15 times to make the data usable with the FUEL data
    if len(raw_exact_data['seconds']) <= len(fuel_time)/4:
        for temp in raw_exact_data['Temperature']:
            for i in range(15):
                exact.append(temp)
        for use in raw_exact_usage:
            for j in range(15):
                exact_usage.append(use)
        for sec in raw_exact_data['seconds']:
            exact_time.append(sec)
            for k in range(14):
                sec += 4
                exact_time.append(sec)

    # Now check to see if the EXACT data arrays are the same length as the FUEL data arrays. If not, add to the arrays
    # to make them the same length as the FUEL arrays
    if len(exact) < len(fuel):
        for i in range(len(fuel) - len(exact)):
            exact.append(exact[-1])
    if len(exact_usage) < len(fuel):
        for j in range(len(fuel) - len(exact_usage)):
            exact_usage.append(exact_usage[-1])
    if len(exact_time) < len(fuel_time):
        for k in range(len(fuel_time) - len(exact_time)):
            exact_time.append(exact_time[-1] + 4)

    # First pass: Loop through each element in the cleaned data from clean_fuel_data
    for idx, kg in enumerate(fuel):
        if idx < len(fuel) - 1:
            # If the change in fuel weight from this data point to the next is greater than your threshold value,
            # it is a fuel removal event. Save the weight change (kg of fuel removed), time (both index and value), and
            # label this as a potential removal event
            if (kg - fuel[idx + 1]) > threshold:
                removal_event.append(1)
            else:
                removal_event.append(0)
    removal_event.append(0)

    # Second pass: This next piece of code checks to see if removal events are too close together (e.g., there was only
    # one removal event, but the prior code categorized it as two or three events) and merges them into a single event.
    # Based on the cooking event merge algorithm in Fire Finder
    removal_time = 0
    time_since_no_removal = 0
    removal = False

    # Go through the loop once for each element in the FUEL data
    for i in range(len(fuel)):
        # If no fuel was removed, increase time since last removal event
        if removal_event[i] == 0:
            time_since_no_removal += 1
            removal = False
        elif removal_event[i] == 1:
            # If fuel was removed now but not in the previous data point, check if less time than merge_threshold has
            # passed and some time has passed since a removal event. If so, remove prior removal events in this window
            if not removal and time_since_no_removal < merge_threshold and removal_time > 0:
                for j in range(time_since_no_removal):
                    removal_event[i - j] = 0
            # If fuel was removed now and in the previous data point, as well as the other criteria above, remove the
            # current removal event
            elif removal and time_since_no_removal < merge_threshold and removal_time > 0:
                removal_event[i] = 0
            removal = True
            time_since_no_removal = 0
            removal_time += 1

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
        # point as the endpoint of the removal event
        for j, kg in enumerate(fuel[i:i + merge_threshold - 1]):
            if -0.05 < kg - fuel[i + 3] < 0.05:
                removal_endpoint.append(kg)
                break

    # Take the difference between removal start and endpoints to find the mass of fuel removed (kg) per loading event
    kg_removed = []
    for i, j in enumerate(removal_startpoint):
        kg_removed.append(round(j - removal_endpoint[i], 2))

    # Take the difference between each removal start time (s) to find loading frequency
    loading_frequency = []
    for i in range(len(time_removed) - 1):
        loading_frequency.append(time_removed[i + 1] - time_removed[i])

    return kg_removed, time_removed, removal_startpoint, removal_endpoint, removal_timestamp, loading_frequency


def mass_removed(smooth_fuel_data):
    """Takes in cleaned data and finds an overestimate of the total mass of fuel removed.

    :param smooth_fuel_data: Array of cleaned FUEL data created with clean_fuel_data
    :return: mass - Each element in this array contains the mass of fuel removed during one logging event. Sum this
        array to calculate the total mass of fuel removed, in kg, during the study period."""

    fuel = smooth_fuel_data
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

    print(f'Total mass of fuel removed using mass_removed function: {round(sum(mass), 2)} kg (overestimate)')
    return mass


if __name__ == "__main__":
    # Run tests for this script here

    # Hardcoded input path for testing
    sheetinputpath = "D:\\School Stuff\\MS Research\\3.14.23\\3.14.23_FuelData.csv"
    # sheetinputpath = "C:\\Users\\kiern\\Downloads\\GP001\\3.16.23\\3.16.23_FuelData.csv"
    # sheetinputpath = "C:\\Users\\kiern\\Downloads\\GP003\\2.15.23\\2.15.23_FuelData.csv"
    # sheetinputpath = "C:\\Users\\kiern\\Downloads\\GP003\\3.8.23\\3.8.23_FuelData.csv"
    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    exactpath = os.path.join(directory, testname+'_ExactData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelDataCleaned.csv')
    exactoutputpath = os.path.join(directory, testname+'_ExactDataCut.csv')

    # Get FUEL and EXACT data
    fuel_data = load_fuel_data(inputpath)
    exact_data = load_exact_data(exactpath)
    if len(exact_data['Temperature']) < len(exact_data['seconds']):
        exact_data['seconds'] = exact_data['seconds'][:len(exact_data['Temperature'])]
    print(f"FUEL: {len(fuel_data['seconds'])} EXACT: {len(exact_data['seconds'])}")

    # Clean data and show plots
    dev_plot_fuel_data(fuel_data, exact_data)

    # # Show final polished plot
    # plot_fuel_data(fuel_data)

    # # Test cleaning function
    # new_data = clean_fuel_data(fuel_data)
    # print(len(fuel_data['firewood']))
    # print(len(new_data))

    # # # Test alternate cleaning function
    # new_data = alt_clean_fuel_data(fuel_data)
    # print(len(fuel_data['firewood']))
    # print(len(new_data))

    # # Test removal function
    # kg_rem, time_rem, kg_ind, rem_plot = fuel_removal(new_data, fuel_data)
    # print(len(kg_rem), len(time_rem), len(kg_ind), len(rem_plot))

    # # Test mass_removed function
    # m = mass_removed(new_data)
