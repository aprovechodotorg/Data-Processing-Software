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


# *** TO DO: Update code to produce more polished plots. The current plots are helpful for development, we probably
#               only want to output a single plot with multiple things on it when development is done. If we make the
#               plot big enough maybe we can include the timestamps of the removal events? Otherwise, think of how to
#               present that data.
def plot_fuel_data(raw_data):
    """Produces plots to visualize and compare raw and cleaned fuel data.

    :param raw_data: Raw fuel data dictionary created by PEMS_FuelLoadData"""

    # Create figure and axes for subplot structure
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    # Plot raw data
    ax1.plot(raw_data['seconds'], raw_data['firewood'])
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Fuel Weight (kg)')
    ax1.set_title('Raw Data')

    # Call to clean_fuel_data function to generate cleaned data
    new_data = clean_fuel_data(raw_data)

    # Plot cleaned data in second subplot
    ax2.plot(raw_data['seconds'], new_data)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Fuel Weight (kg)')
    ax2.set_title('Cleaned Data')

    # Call to fuel_removal function to generate removal events, quantities, and times
    kg_rem, time_rem, kg_ind = fuel_removal(new_data, fuel_data)
    print(len(kg_rem), len(time_rem))
    print(sum(kg_rem))

    # Plot fuel removal data over cleaned data
    ax3.plot(raw_data['seconds'], new_data)
    ax3.plot(time_rem, kg_ind, 'ro', mfc='none')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Fuel Weight (kg)')
    ax3.set_title('Fuel Removal Events')
    fig.subplots_adjust(hspace=0.65)
    fig.set_size_inches(6.4, 8)
    plt.show()


# *** TO DO: Decide if the current running median code is appropriate for cleaning the data. Alternative ideas include
#              using a central running median (the current code looks backwards), or using Grant's technique of moving
#              the entire window one block at a time (e.g., window1=[1-15] window2=[16-30] etc.)
def clean_fuel_data(raw_data, window_size=30):
    """Use a running median to remove spikes in the fuel data that may not represent actual loading or unloading events.

    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData
    :param window_size: Size of the window for the running median. Defaults to 30, for a 4-second log rate this gives
        a window size of 2 minutes (15 data points logged per minute)
    :return: smooth_data - Array of the cleaned fuel data"""

    # Initialize arrays and count variable
    window = []
    count = 0
    fuel = raw_data['firewood']
    smooth_data = []

    for kg in fuel:
        # While there are fewer data points than your window size, just take the median of what you have
        if count < window_size:
            window.append(kg)
            smooth_data.append(median(window))
        # Once you get close to the end of the raw data array, just take the median of what you have again
        elif count > len(fuel) - window_size:
            window.pop(0)
            smooth_data.append(median(window))
        # Once there are enough elements to fill your window, take the median of your whole window size
        else:
            window.pop(0)
            window.append(kg)
            smooth_data.append(median(window))
        count += 1

    return smooth_data


# *** TO DO: Think of a better way to find removal events. With the current code, looking at the plots it seems like
#               some removal events have been categorized as multiple events. Adjusting the threshold and timescale
#               that we are using to define a removal event could help address this.
#            Add code that finds the time in between removal events and saves these time differences to an array. What
#               should we do with those time differences?
#            Add code that takes the index of a removal event and gets the timestamp from the raw data. What should we
#               do with the timestamps once we have them?
def fuel_removal(smooth_data, raw_data, threshold=0.5):
    """*function should create arrays of fuel removal events and time when the event happened*

    :param smooth_data: Array of cleaned fuel data created with clean_fuel_data
    :param raw_data: Raw fuel data dictionary loaded in with PEMS_FuelLoadData, used here for the 'seconds' values
    :param threshold: Threshold value for defining a real fuel removal event, defaults to 0.5 kg
    :return: *return items here*"""

    fuel = smooth_data
    time = raw_data['seconds']
    kg_removed = []
    time_removed = []
    time_index = []

    # Loop through each element in the cleaned data from clean_fuel_data
    for idx, kg in enumerate(fuel):
        if idx < len(fuel) - 1:
            # If the change in fuel weight from this data point to the next is greater than your threshold value,
            # it is a fuel removal event. Save the weight change (kg of fuel removed) and time (both index and value)
            if (kg - fuel[idx + 1]) > threshold:
                kg_removed.append(kg - fuel[idx + 1])
                time_removed.append(time[idx])
                time_index.append(idx)

    # Use time_index to find data points where fuel removal occurred, so we can plot them later
    kg_index = []
    for i in time_index:
        kg_index.append(fuel[i])

    return kg_removed, time_removed, kg_index


def mass_removed(smooth_data):
    """Takes in cleaned data and finds total mass of fuel removed.

    :param smooth_data: Array of cleaned fuel data created with clean_fuel_data
    :return: mass - Each element in this array contains the mass of fuel removed during one logging event. Sum this
        array to calculate the total mass of fuel removed, in kg, during the study period."""

    # Initialize cleaned data and difference arrays
    fuel = smooth_data
    diff = []

    # Loop through each element in the cleaned data. Starting with the second element, take the difference between the
    # current and previous element and save it to the difference array.
    for idx, kg in enumerate(fuel):
        if idx == 0:
            diff.append(kg)
        else:
            diff.append(kg - fuel[idx - 1])

    mass = []

    # Loop through each element in the difference array. If the current element is negative, then fuel has been removed.
    # Save this element to the mass array.
    for kg in diff:
        if kg < 0:
            mass.append(abs(kg))

    print(f'Total mass of fuel removed: {round(sum(mass), 2)} kg')
    return mass


if __name__ == "__main__":
    # Run tests for this script here
    # # Ask user to input path to FUEL .csv file
    # sheetinputpath = input("Input path of _FuelData.csv file:\n")

    # Hardcoded input path for testing
    sheetinputpath = "D:\\School Stuff\\MS Research\\3.14.23\\3.14.23_FuelData.csv"
    directory, filename = os.path.split(sheetinputpath)
    data_directory, testname = os.path.split(directory)

    inputpath = os.path.join(directory, testname + '_FuelData.csv')
    fueloutputpath = os.path.join(directory, testname + '_FuelDataCleaned.csv')

    # Get fuel data and seconds array
    fuel_data = load_fuel_data(inputpath)

    # Clean data and show plots
    plot_fuel_data(fuel_data)

    # # Test cleaning function
    # new_data = clean_fuel_data(fuel_data)
    # print(len(fuel_data['firewood']))
    # print(len(new_data))

    # # Test removal function
    # kg_rem, time_rem, kg_ind = fuel_removal(new_data, fuel_data)
    # print(len(kg_rem), len(time_rem))

    # # Test mass_removed function
    # m = mass_removed(new_data)
