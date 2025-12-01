# Python3

#    Copyright (C) 2023 Mountain Air Engineering
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
#    Contact: ryan@mtnaireng.com

import PEMS_DataProcessing_IO as io
import easygui
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import os
from uncertainties import ufloat


#########      inputs      ##############
# inputpath=os.path.join(directory,testname+'_TimeSeries.csv')
# outputpath=os.path.join(directory,testname+'_TimeSeries_wCH4.csv')
# aveinputpath=os.path.join(directory,testname+'_Averages.csv')
# aveoutputpath=os.path.join(directory,testname+'_Averages_wCH4.csv')
# matrixpath = os.path.join(directory,testname+'_CrossSensitivityMatrix.csv')
# ucpath = os.path.join(directory,testname+'_UCInputs.csv')
# logpath='\CrappieCooker_test2_log.txt'
##########################################

def PEMS_AddCH4(inputpath, outputpath, aveinputpath, aveoutputpath, matrixpath, ucpath, logpath):
    interactive = 1;
    ver = '0.8'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_AddCH4 v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    phases = ['prebkg', 'test', 'postbkg']

    #################################################

    # read in averages file
    [avenames, aveunits, aveval, aveunc, aveuval] = io.load_constant_inputs(aveinputpath)
    line = 'loaded averages file: ' + aveinputpath
    print(line)
    logs.append(line)

    ##########################################
    # read in measurement uncertainty file
    [ucnames, ucunits, ucinputs] = io.load_timeseries(ucpath)

    ############################################
    # Read in sensor cross-sensitivity matrix
    # load matrix input file
    [matrixnames, matrixunits, matrixval, matrixunc, matrixuval] = io.load_constant_inputs(matrixpath)
    matrixnames = matrixnames[1:]  # remove the first name because it is the header
    line = 'Loaded matrix input file:' + matrixpath
    print(line)
    logs.append(line)

    try:  # try to read the HC-VOC factor from the cross sensitivity matrix
        correction_factor = float(matrixval['HC_VOC'])
        line = 'Reading cross sensitivity matrix:'
        print(line)
        logs.append(line)
    except:
        correction_factor = float(1)
        line = 'No correction_factor in cross-sensitivity matrix. Using default:'
        print(line)
        logs.append(line)
    line = 'HC-VOC correction_factor = ' + str(correction_factor)
    print(line)
    logs.append(line)
    #####################################################

    # read in time series file
    [names, units, data] = io.load_timeseries(inputpath)

    name = 'CH4'
    units[name] = 'ppm'
    names.append(name)
    data[name] = []

    for n, val in enumerate(data['VOC']):
        # scale the VOC signal to correct for HC cross sensitivity
        # subtract scaled VOC signal from HC signal
        methane = data['HC'][n] - val * correction_factor
        data[name].append(methane)

    io.write_timeseries(outputpath, names, units, data)

    line = 'created time series data file with CH4 channel:\n' + outputpath
    print(line)
    logs.append(line)

    # update the data series for each phase

    newseries = {}
    for phase in phases:
        newseries[phase] = []
        for n, val in enumerate(data['phase']):
            if phase in val:
                newseries[phase].append(data['CH4'][n])

    # output time series data file for each phase
    for phase in phases:
        phaseinputpath = inputpath[
                         :-4] + '_' + phase + '.csv'  # name the input file by inserting the phase name into outputpath
        phaseoutputpath = outputpath[
                          :-4] + '_' + phase + '.csv'  # name the output file by inserting the phase name into outputpath
        [pnames, punits, pdata] = io.load_timeseries(phaseinputpath)
        name = 'CH4'
        pnames.append(name)
        pdata[name] = newseries[phase]
        punits[name] = 'ppm'
        io.write_timeseries(phaseoutputpath, pnames, punits, pdata)

        line = 'created time series data file with CH4 channel:\n' + phaseoutputpath
        print(line)
        logs.append(line)

        # add phase averages
        avename = 'CH4_' + phase
        avenames.append(avename)
        aveunits[avename] = 'ppm'
        val = np.nanmean(pdata[name])
        # use HC uncertainty inputs for CH4 uncertainty
        uc = val * ucinputs['HC'][1] + ucinputs['HC'][0]  # unc = val * relative uncertainty + absolute uncertainty
        aveuval[avename] = ufloat(val, uc)

    io.write_constant_outputs(aveoutputpath, avenames, aveunits, aveval, aveunc, aveuval)
    line = 'created averages data file with CH4:\n' + aveoutputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    ##################################################
    if interactive == 1:
        # plot the data series to inspect the new CH4 channel
        print('Close the plot to continue')
        for n in range(len(data['CO'])):
            data['VOC'][n] = float(data['VOC'][n])  # convert data series to floats
            data['HC'][n] = float(data['HC'][n])  # to remove strings so they will plot
            # data['CH4'][n]=float(data['CH4'][n])
        plt.plot(data['VOC'], label='VOC')
        plt.plot(data['HC'], label='HC')
        plt.plot(data['CH4'], label='CH4')
        plt.xlabel('data points')
        plt.ylabel(units[name])
        plt.legend()
        plt.show()
        # end of figure
    #######################################################################
    # end of function


#########################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    PEMS_AddCH4(inputpath, outputpath, aveinputpath, aveoutputpath, matrixpath, ucpath, logpath)
