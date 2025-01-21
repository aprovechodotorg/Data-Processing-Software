#v0.0  Python3
import csv
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
import os
import matplotlib
import matplotlib.pyplot as plt
import easygui
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from easygui import choicebox

inputpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_TimeSeriesMetrics_hp.csv"
fuelpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedFuelData.csv"
exactpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedExactData.csv"
scalepath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedScaleData.csv"
nanopath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedNanoscanData.csv"
TEOMpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedTEOMData.csv"
senserionpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_FormattedSenserionData.csv"
regressionpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_Regressions.csv"
savefigpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23"
logpath = "C:\\Users\\Jaden\\Documents\\DOE Baseline\\Unit Tests\\11.7.23\\11.7.23_log.txt"
phase = 'hp'
def LEMS_customscatterplot(inputpath, fuelpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, regressionpath,
                          phase, savefigpath, logpath):
    # Set the default save directory for GUI interface of matplotlib
    directory, filename = os.path.split(logpath)
    plt.rcParams['savefig.directory'] = directory

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_customscatterplot v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of Unit Tests names
    units = {}
    names = [] #list of variable names

    if os.path.isfile(inputpath):
        [dnames, units, data] = io.load_timeseries(inputpath)
        line = 'loaded processed data file without header = names, units: ' + inputpath
        print(line)
        logs.append(line)
        for name in dnames:
            names.append(name)

    if os.path.isfile(fuelpath):
        [fnames, funits, fdata] = io.load_timeseries(fuelpath)
        line = 'loaded processed data file without header = names, units: ' + fuelpath
        print(line)
        logs.append(line)
        type = 'f'
        names, units, data = loaddatastream(fnames, funits, fdata, names, units, data, type)

    if os.path.isfile(exactpath):
        [exnames, exunits, exdata] = io.load_timeseries(exactpath)
        line = 'loaded processed data file without header = names, units: ' + exactpath
        print(line)
        logs.append(line)
        type = 'ex'
        names, units, data = loaddatastream(exnames, exunits, exdata, names, units, data, type)

    if os.path.isfile(scalepath):
        [snames, sunits, sdata] = io.load_timeseries(scalepath)
        line = 'loaded processed data file without header = names, units: ' + scalepath
        print(line)
        logs.append(line)
        type = 's'
        names, units, data = loaddatastream(snames, sunits, sdata, names, units, data, type)

    if os.path.isfile(nanopath):
        [nnames, nunits, ndata] = io.load_timeseries(nanopath)
        line = 'loaded processed data file without header = names, units: ' + nanopath
        print(line)
        logs.append(line)
        type = 'n'
        names, units, data = loaddatastream(nnames, nunits, ndata, names, units, data, type)

    if os.path.isfile(TEOMpath):
        [tnames, tunits, tdata] = io.load_timeseries(TEOMpath)
        line = 'loaded processed data file without header = names, units: ' + TEOMpath
        print(line)
        logs.append(line)
        type = 't'
        names, units, data = loaddatastream(tnames, tunits, tdata, names, units, data, type)

    if os.path.isfile(senserionpath):
        [sennames, senunits, sendata] = io.load_timeseries(senserionpath)
        line = 'loaded processed data file without header = names, units: ' + senserionpath
        print(line)
        logs.append(line)
        type = 'sen'
        names, units, data = loaddatastream(sennames, senunits, sendata, names, units, data, type)

    selected_X_variable = easygui.choicebox("Select a variable for the x axis", choices=names)
    selected_Y_variable = easygui.choicebox("Select a variable to compare for the y axis", choices=names)

    # Convert date strings to date numbers for plotting
    name = 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data['time']):
        try:
            dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        except:
            dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)

    name = 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    LEMS_start = data['datenumbers'][0]
    LEMS_end = data['datenumbers'][-1]

    #The following variables my need to be made longer if they have different sample rates than LEMS
    try:
        if selected_X_variable in fnames:
            type = 'f'
            x = createvavrlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    try:
        if selected_X_variable in exnames:
            type = 'ex'
            x = createvarlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    try:
        if selected_X_variable in snames:
            type = 's'
            x = creatvarlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    try:
        if selected_X_variable in nnames:
            type = 'n'
            x = createvarlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    try:
        if selected_X_variable in tnames:
            type = 't'
            x = createvarlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    try:
        if selected_X_variable in sennames:
            type = 'sen'
            x = createvarlist(data, LEMS_start, LEMS_end, type, selected_X_variable)
    except:
        pass

    ###########################Y
    try:
        if selected_Y_variable in fnames:
            type = 'f'
            y = createvavrlist(data, LEMS_start, LEMS_end, type, selected_Y_variable_variable)
    except:
        pass

    try:
        if selected_Y_variable in exnames:
            type = 'ex'
            y = createvarlist(data, LEMS_start, LEMS_end, type, selected_Y_variable)
    except:
        pass

    try:
        if selected_Y_variable in snames:
            type = 's'
            y = creatvarlist(data, LEMS_start, LEMS_end, type, selected_Y_variable)
    except:
        pass

    try:
        if selected_Y_variable in nnames:
            type = 'n'
            y = createvarlist(data, LEMS_start, LEMS_end, type, selected_Y_variable)
    except:
        pass

    try:
        if selected_Y_variable in tnames:
            type = 't'
            y = createvarlist(data, LEMS_start, LEMS_end, type, selected_Y_variable)
    except:
        pass

    try:
        if selected_Y_variable in sennames:
            type = 'sen'
            y = createvarlist(data, LEMS_start, LEMS_end, type, selected_Y_variable)
    except:
        pass

    if selected_X_variable in dnames:
        x = data[selected_X_variable]
        try:
            if len(x) > len(y):
                x = x[0 : len(y)]
        except:
            pass

    if selected_Y_variable in dnames:
        y = data[selected_Y_variable]
        try:
            if len(y) > len(x):
                y = y[0:len(x)]
            if len(x) > len(y):
                x = x[0:len(y)]
        except:
            pass

    ################################
    #Linear regression
    arrayx = np.array(x).reshape((-1, 1))
    model = LinearRegression().fit(arrayx, y) #calculate optimal values of the weights b0 and b1
    r_sq = model.score(arrayx, y) #calculate r squared value

    m = model.coef_
    b = model.intercept_

    line = ("r squared value of the linear regression of " + selected_X_variable + " vs. " + selected_Y_variable + " is: "
            + str(r_sq))
    print(line)

    plt.scatter(x, y)
    plt.xlabel(selected_X_variable + ' (' + units[selected_X_variable] + ')')
    plt.ylabel(selected_Y_variable + ' (' + units[selected_Y_variable] + ')')

    #plot linear regression line
    linx = np.linspace(int(min(x)), int(max(x)), (int(max(x)) - int(min(x))) + 1)
    plt.plot(linx, m * linx + b, linestyle='solid', color='black')
    r_sq = round(r_sq, 4)
    plt.text(min(x), max(y), "r-squared = " + str(r_sq))#display r squared value on plot

    savefigpath = savefigpath + '_' + selected_X_variable + selected_Y_variable + '_' + phase + '.png'
    plt.savefig(savefigpath)
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    ###########################################
    #writing or creating regression value log
    #if the log already exists, check if regression has already been done, either rewrite it or add new regression
    if os.path.isfile(regressionpath):
        new = 0
        stuff = []
        #load input file
        with open(regressionpath) as f:
            reader = csv.reader(f)
            for row in reader:
                stuff.append(row)

        #put inputs into a dictionary
        names =stuff[0]
        data={}
        for n, name in enumerate(names):
            data[name] = [x[n] for x in stuff[1:]]

        done = 0
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y %H:%M:%S")
        #check if regression has been done before
        for n, value in enumerate(data['X_names']):
            if selected_X_variable in value and selected_Y_variable in data['Y_names'][n] and data['phase'][n] == phase:
                done = 1
                data['r_sq'][n] = r_sq  # update r squared value
                data['date'][n] = now_str  # update date
                data['y=mx+b'][n] = 'y=' + str(m) + 'x+' + str(b)

    else: #if file doesn't exist, establish how to write it
        new = 1
        done = 0
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y %H:%M:%S")
        names = ['date', 'phase', 'X_names', 'Y_names', 'r_sq', 'y=mx+b']
        data = {}
        for name in names:
            data[name] = []

    if done == 0: #add new row to file
        data['X_names'].append(selected_X_variable + ' (' + units[selected_X_variable] + ')')
        data['Y_names'].append(selected_Y_variable + ' (' + units[selected_Y_variable] + ')')
        data['date'].append(now_str)
        data['r_sq'].append(r_sq)
        data['phase'].append(phase)
        data['y=mx+b'].append('y=' + str(m) + 'x+' + str(b))

    #establish output rows
    output = []
    output.append(names)
    for n, val in enumerate(data['date']):
        row = []
        for name in names:
            row.append(data[name][n])
        output.append(row)

    #write to csv
    with open(regressionpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)

    if new == 1:
        line = 'Regression file created: ' + regressionpath
        print(line)
        logs.append(line)
    elif new == 0:
        line = 'Regression file updates: ' + regressionpath
        print(line)
        logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)

def loaddatastream(new_names, new_units, new_data, names, units, data, type):
    for name in new_names:
        # add new values to dictionary
        # Time is already in dictionary, rename to not overwrite data
        if name == 'time':
            newname = type + 'time'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # seconds is already in dictionary, rename to not overwrite data
        elif name == 'seconds':
            newname = type + 'seconds'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # all other data can be added without ov
        else:
            names.append(name)
            data[name] = new_data[name]
            units[name] = new_units[name]
    return names, units, data
def createvarlist(data, LEMS_start, LEMS_end, type, selected_ax_variable):
    # Convert date strings to date numbers for plotting
    name = type + 'dateobjects'
    data[name] = []
    for n, val in enumerate(data[type + 'time']):
        dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        data[name].append(dateobject)

    name = type + 'datenumbers'
    datenums = matplotlib.dates.date2num(data[type + 'dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    default_samplerate = data[type + 'dateobjects'][2] - data[type + 'dateobjects'][1]
    default_delta_seconds = default_samplerate.total_seconds()

    cutdata = []
    cutdate = []
    for n, date in enumerate(data[type + 'datenumbers']):  # cut data to phase time
        if LEMS_start <= date <= LEMS_end:
            cutdata.append(data[selected_ax_variable][n])
            cutdate.append(date)

    ax = []
    for n, num in enumerate(cutdata):
        if n == 0:
            ax.append(num)
        else:
            c = 1
            try:
                samplerate = [cutdate[n] - cutdate[n-1]]
                delta_seconds = samplerate.totalseconds()
            except:
                delta_seconds = default_delta_seconds
            while c <= delta_seconds:
                ax.append(num)
                c += 1

    return ax

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_customscaterplot(inputpath, fuelpath, exactpath, scalepath, nanopath, TEOMpath, senserionpath, regressionpath,
                          phase, savefigpath, logpath)
