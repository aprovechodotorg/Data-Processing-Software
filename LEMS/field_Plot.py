import LEMS_DataProcessing_IO as io
import field_plot_IO as plot

import csv

inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_TimeSeriesShifted.csv'

def field_Plot(inputpath):
    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    potentialBkgNames = ['CO', 'CO2']  # define potential channel names that will get background subtraction
    names, data = plot.subtract_background(names, data, potentialBkgNames)

    plots = ['COhi', 'CO2hi', 'O2', 'PM'] #define what will be plotted
    y_label = 'Emission'
    plot.field_plot_data(data, units, plots, y_label) #Send to plot function

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_Plot(inputpath)