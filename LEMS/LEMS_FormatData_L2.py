#v0 Python3
#Master program to calculate stove test energy metrics following ISO 19867

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

inputpath2 =['Data/yatzo alcohol/yatzo_test1/yatzo_test1_EnergyOutputs.csv']
outputpath2 ='Data/yatzo alcohol/yatzo_L2_FormattedData.csv'
logpath = 'Data/yatzo alcohol/yatzo_L2_log.txt'
testnum = 1
testname = ['yatzo_1', 'yatzo_2']

import pandas as pd
import LEMS_DataProcessing_IO as io
import csv

def LEMS_FormatData_L2(inputpath2, outputpath2, logpath, testnum, testname):
    logs = []
    names = []  # list of variable names
    outputnames = []  # list of variable names for the output file
    units = {}  # dictionary of units, keys are variable names
    val = {}  # dictionary of nominal values, keys are variable names
    unc = {}  # dictionary of uncertainty values, keys are variable names
    uval = {}  # dictionary of values as ufloat pairs, keys are variable names
    test = []


    stove = 'Stove type/model'
    name.append(stove)
    ############################################################
    #Thermal Efficiency

    name = 'Thermal Efficiency With Char'
    names.append(name)
    units[name] = '%'

    #valdict=[]
    for path in inputpath2:
        #valdict.append = 'val_' + path
        testdict = {}
        testname = 'val_' + path



        ###############################################
        # load input file and store values in dictionaries
        [names, units, testdict, unc, uval] = io.load_constant_inputs(path)
        line = 'loaded: ' + path
        print(line)
        logs.append(line)


        #######################################################
        test = testname[x]
        names.append(test)
        [enames, eunits, emetrics, eunc, euval] = io.load_constant_inputs(inputpath2[x])
        #values.append(float(emetrics['eff_w_char_hp']))
        TE = ((float(emetrics['eff_w_char_hp']) * float(emetrics['weight_hp'])) + (float(emetrics['eff_w_char_mp']) * float(emetrics['weight_lp'])) + (float(emetrics['eff_w_char_mp']) * float(emetrics['weight_lp']))) / float(emetrics['weight_total'])
        val[test]=TE
        #print to the output file
        #with open(outputpath2, 'w') as csvfile:
            #writer = csv.writer(csvfile)
            #writer.writerow(header)
            #writer.writerow(values)
            #csvfile.close()
        val.append(testname, testdict)

    io.write_constant_outputs(outputpath2, names, units, val, unc, uval)

    #raw = pd.read_csv(inputpath2)
    #comp = pd.read_csv(outputpath2)
    #blank = pd.read_csv(outputpath2)

    # adding header
    #headerList = ['Test Run', 'Thermal Efficiency With Char', 'Thermal Efficiency Without Char']

    # converting data frame to csv
    #blank.to_csv(outputpath2, header=headerList, index=False)

    # display modified csv file
    #comp = pd.read_csv(outputpath2)
    #print('\nModified file:')
    #print(comp)

    #blank.loc[testnum, 'Test Run'] = testnum
    #blank.to_csv(outputpath2, index=False)
    #dict = {"Thermal Efficiency With Char" : [],
            #"Thermal Efficiency Without Char" : []}
    #print(raw.columns)

#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_FormatData_L2(inputpath2,outputpath2,logpath, testnum, testname)


