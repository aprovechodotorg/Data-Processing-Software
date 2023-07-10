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
import numpy as np
from statistics import median
from math import floor


def dev_plot_fuel_data(raw_data):
    """Produces plots to visualize and compare raw and cleaned fuel data during development of this code.

    :param raw_data: Raw fuel data dictionary created by PEMS_FuelLoadData"""

    # Create figure and axes for subplot structure
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    # Plot raw data
    ax1.plot(raw_data['seconds'], raw_data['firewood'])
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Fuel Weight (kg)')
    ax1.set_title('Raw Data')

    # Call to clean_fuel_data function to generate cleaned data
    new_data = alt_clean_fuel_data(raw_data)

    # Plot cleaned data in second subplot
    ax2.plot(raw_data['seconds'], new_data)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Fuel Weight (kg)')
    ax2.set_title('Cleaned Data')

    # Call to fuel_removal function to generate removal events, quantities, and times
    kg_rem, time_rem_act, kg_rem_plot = test_fuel_removal(new_data, fuel_data)
    print(f'Number of fuel removal events using fuel_removal function: {len(kg_rem_plot)}')
    print(f'Total mass of fuel removed using fuel_removal function: {round(sum(kg_rem), 2)} kg')
    mass_removed(new_data)

    # Plot fuel removal data over cleaned data
    ax3.plot(raw_data['seconds'], new_data)
    ax3.plot(time_rem_act, kg_rem_plot, 'ro', mfc='none')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Fuel Weight (kg)')
    ax3.set_title('Fuel Removal Events')
    fig.subplots_adjust(hspace=0.65)
    fig.set_size_inches(6.4, 8)
    plt.show()


def plot_fuel_data(raw_data):
    """Produces a plot showing the cleaned fuel data and highlighting fuel removal events.

    :param raw_data: Raw fuel data dictionary created by PEMS_FuelLoadData"""

    # Create figure and axes for plotting
    fig, ax = plt.subplots(1)

    # Call to clean_fuel_data function to generate cleaned data
    new_data = alt_clean_fuel_data(raw_data)

    # Call to fuel_removal function to generate removal events, quantities, and times
    kg_rem, time_rem_act, kg_rem_plot = fuel_removal(new_data, fuel_data)
    print(f'Number of fuel removal events using fuel_removal function: {len(kg_rem_plot)}')
    print(f'Total mass of fuel removed using fuel_removal function: {round(sum(kg_rem), 2)} kg')
    mass_removed(new_data)

    # Ask user to input the household number for the plot title
    hh = input('Please enter the household number for this data: ')

    # Plot fuel removal data over cleaned data
    ax.plot(raw_data['seconds'], new_data)
    ax.plot(time_rem_act, kg_rem_plot, 'ro', mfc='none')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Fuel Weight (kg)')
    ax.set_title(f'Fuel Removal Events {hh}')
    plt.show()


# *** TO DO: Decide whether to use the backwards-looking moving median or the central moving median.
def clean_fuel_data(raw_data, window_size=30):
    """Use a backwards-looking moving median to remove spikes in the fuel data that may not represent actual loading or
    unloading events.

    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData
    :param window_size: Size of the window for the moving median. Defaults to 30, for a 4-second log rate this gives
        a window size of 2 minutes (15 data points logged per minute)
    :return: smooth_data - Array of the cleaned fuel data"""

    window = []
    fuel = raw_data['firewood']
    smooth_data = []

    for idx, kg in enumerate(fuel):
        # While there are fewer data points than your window size, just take the median of what you have
        if idx < window_size:
            window.append(kg)
            smooth_data.append(median(window))
        # Once you get close to the end of the raw data array, just take the median of what you have again
        elif idx > len(fuel) - window_size:
            window.pop(0)
            smooth_data.append(median(window))
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window.pop(0)
            window.append(kg)
            smooth_data.append(median(window))

    return smooth_data


def alt_clean_fuel_data(raw_data, window_size=30):
    """Use a central moving median to remove spikes in the fuel data that may not represent actual loading or unloading
    events.

    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData
    :param window_size: Size of the window for the moving median. Defaults to 30, for a 4-second log rate this gives
        a window size of 2 minutes (15 data points logged per minute)
    :return: smooth_data - Array of the cleaned fuel data"""

    fuel = raw_data['firewood']
    smooth_data = []

    for idx, kg in enumerate(fuel):
        # While there are fewer data points than your window size, don't take the median
        if idx < floor(window_size/2):
            smooth_data.append(kg)
        # Once you get close to the end of the raw data array, don't take the median again
        elif idx > len(fuel) - floor(window_size/2):
            smooth_data.append(kg)
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window = fuel[idx - floor(window_size/2):idx + floor(window_size/2)]
            smooth_data.append(median(window))

    return smooth_data


# *** TO DO: Figure out how to find masses for each individual removal event
#            Add code that finds the time in between removal events and saves these time differences to an array. What
#               should we do with those time differences?
#            Add code that takes the index of a removal event and gets the timestamp from the raw data. What should we
#               do with the timestamps once we have them?
def fuel_removal(smooth_data, raw_data, threshold=0.25):
    """Locates fuel removal events and saves them to arrays that can be used to calculate the total amount of fuel
    removed in kg, as well as be used for plotting.

    :param smooth_data: Array of cleaned fuel data created with clean_fuel_data
    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData, used here for the 'seconds' values
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :return: kg_removed - Mass of fuel removed in kg;
             time_removed - Array with times of fuel removal events in seconds;
             kg_rem_plot - Array with mass values of fuel removal events in kg for plotting"""

    fuel = smooth_data
    time = raw_data['seconds']
    kg_removed = []
    removal_event = []

    # Loop through each element in the cleaned data from clean_fuel_data
    for idx, kg in enumerate(fuel):
        if idx < len(fuel) - 1:
            # If the change in fuel weight from this data point to the next is greater than your threshold value,
            # it is a fuel removal event. Save the weight change (kg of fuel removed), time (both index and value), and
            # label this as a potential removal event
            if (kg - fuel[idx + 1]) > threshold:
                kg_removed.append(kg - fuel[idx + 1])
                removal_event.append(1)
            else:
                removal_event.append(0)
    removal_event.append(0)

    # This next piece of code checks to see if removal events are too close together (e.g., there was only one removal
    # event, but the prior code categorized it as two or three events) and merges them into a single event. Based on
    # the cooking event merge algorithm in Fire Finder
    merge_threshold = 30
    removal_time = 0
    time_since_no_removal = 0
    removal = False

    # Go through the loop once for each element in the fuel data
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

    # Use removal event indices to find when fuel was removed and how much fuel was removed at that time (for plotting)
    time_removed = []
    kg_rem_plot = []
    for idx in removal_index:
        time_removed.append(time[idx])
        kg_rem_plot.append(fuel[idx])

    return kg_removed, time_removed, kg_rem_plot


# *** I am using this function to test adding the capability to get fuel removal load size as an output
# *** TO DO: Figure out how to use smooth data instead of raw data and still get accurate load size
#            See if I can improve how the algorithm finds removal endpoints, this should give more accurate output
def test_fuel_removal(smooth_data, raw_data, threshold=0.25, window_size=30):
    """Locates fuel removal events and saves them to arrays that can be used to calculate the total amount of fuel
    removed in kg, as well as be used for plotting.

    :param smooth_data: Array of cleaned fuel data created with clean_fuel_data
    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData, used here for the 'seconds' values
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :return: kg_removed - Mass of fuel removed in kg;
             time_removed - Array with times of fuel removal events in seconds;
             kg_rem_plot - Array with mass values of fuel removal events in kg for plotting"""

    # *** Using raw data instead of smooth data right now, need to fix this
    fuel = smooth_data
    time = raw_data['seconds']
    kg_removed = []
    removal_event = []

    # Loop through each element in the cleaned data from clean_fuel_data
    for idx, kg in enumerate(fuel):
        if idx < len(fuel) - 1:
            # If the change in fuel weight from this data point to the next is greater than your threshold value,
            # it is a fuel removal event. Save the weight change (kg of fuel removed), time (both index and value), and
            # label this as a potential removal event
            if (kg - fuel[idx + 1]) > threshold:
                kg_removed.append(kg - fuel[idx + 1])
                removal_event.append(1)
            else:
                removal_event.append(0)
    removal_event.append(0)

    # This next piece of code checks to see if removal events are too close together (e.g., there was only one removal
    # event, but the prior code categorized it as two or three events) and merges them into a single event. Based on
    # the cooking event merge algorithm in Fire Finder
    merge_threshold = 30
    removal_time = 0
    time_since_no_removal = 0
    removal = False

    # Go through the loop once for each element in the fuel data
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

    # Use removal event indices to find when fuel was removed and how much fuel was removed at that time (for plotting)
    time_removed = []
    kg_rem_plot = []
    for idx in removal_index:
        time_removed.append(time[idx])
        kg_rem_plot.append(fuel[idx])

    # Use removal event indices to find endpoints of removal events for calculating load size
    removal_endpoint = []
    for i in removal_index:
        # Starting at the beginning of a removal event, look forward to find where the slope smooths out and save this
        # point as the endpoint of the removal event
        for j, kg in enumerate(fuel[i:i + floor(window_size/2)]):
            if -0.05 < kg - fuel[i + 3] < 0.05:
                removal_endpoint.append(kg)
                break

    print(kg_rem_plot)
    print(removal_endpoint)

    removal_difference = []
    for i, j in enumerate(kg_rem_plot):
        removal_difference.append(round(j - removal_endpoint[i], 2))

    print(removal_difference)
    print(sum(removal_difference))
    print(f'Number of removal endpoints found: {len(removal_endpoint)}')

    return kg_removed, time_removed, kg_rem_plot


def mass_removed(smooth_data):
    """Takes in cleaned data and finds total mass of fuel removed.

    :param smooth_data: Array of cleaned fuel data created with clean_fuel_data
    :return: mass - Each element in this array contains the mass of fuel removed during one logging event. Sum this
        array to calculate the total mass of fuel removed, in kg, during the study period."""

    fuel = smooth_data
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

    print(f'Total mass of fuel removed using mass_removed function: {round(sum(mass), 2)} kg')
    return mass


if __name__ == "__main__":
    # Run tests for this script here

    # Hardcoded input path for testing
    sheetinputpath = "D:\\School Stuff\\MS Research\\3.14.23\\3.14.23_FuelData.csv"
    # sheetinputpath = "D:\\School Stuff\\MS Research\\3.21.23\\3.21.23_FuelData.csv"
    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelDataCleaned.csv')

    # Get fuel data and seconds array
    fuel_data = load_fuel_data(inputpath)

    # Clean data and show plots
    dev_plot_fuel_data(fuel_data)

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
