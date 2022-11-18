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
import numpy as np

########### inputs (only used if this script is run as executable) #############
inputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData2.csv'
outputpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawDataOutput.csv'
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_log.txt'

##################################

def LEMS_plot_test(inputpath,outputpath,logpath):
    ver = '0.0'
    
    logs=[]  #initialize a list to print to the log file
    
    [names,units,data] = io.load_timeseries(inputpath)

    #x = np.linspace(0, 10*np.pi, 100)
    #y = np.sin(x)
    
    x = [0,1,2,3,4,5,6,7]
    y = [5,3,4,6,7,2,3,8]

    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    line1, = ax.plot(x, y, 'b-')

    #for phase in np.linspace(0, 10*np.pi, 100):
    #    line1.set_ydata(np.sin(0.5 * x + phase))
    #    fig.canvas.draw()
    
    while len(x) < 20:
        var = input("Enter value:")
        x.append(x[-1]+1)
        y.append(int(var))
        line1.set_xdata(x)        
        line1.set_ydata(y)
        fig.canvas.draw()
    

    
    #io.write_timeseries(outputpath,names,units,data)
    
    #line = 'created: '+outputpath
    #print(line)
    #logs.append(line)
    
    #print to log file
    io.write_logfile(logpath,logs)

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_plot_test(inputpath,outputpath,logpath)