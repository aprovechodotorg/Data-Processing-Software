#v0.0 Python3
import math
import easygui

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


#do: 
#add time series for Volume flow QC, Flow RE, and Re QC
#add performance tiers
#add input for duct static pressure to calculate duct pressure instead of ambient pressure
# add input for flow grid calibration factor
# add firepower and carbon balance data series
# add other desired output metrics from old data processing spreadsheet Results tab
# Resolve emission metric name discrepancy with 'upload_template from christian.csv'
    #  One metric is listed in the upload template that is not output by this script: CO2_useful_eng, CO_useful_eng, PM_useful_eng (not sure how to calculate it)

import LEMS_DataProcessing_IO as io
import numpy as np
from uncertainties import ufloat
from datetime import datetime as dt
from datetime import timedelta
import os
import matplotlib

#########      inputs      ##############
#Inputs below will only be used when this script is run directly. To run different inputs use LEMSDataCruncher_ISO.py
#For single test evaluation or LEMSDataCruncher_L2.py for multitest evaluation and comparision
#time series data file:
inputpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_TimeSeries_Shifted.csv'
#energy metrics data file:
energypath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_EnergyOutputs.csv'
#phase averages input data file:
aveinputpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_Averages.csv'
#gravimetric PM metrics data file:
gravinputpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_GravOutputs.csv'
#phase emission metrics output data file:
emisoutputpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_EmissionOutputs.csv'
#all metrics output data file:
alloutputpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_AllOutputs.csv'
#input file of start and end times for background and test phase periods
logpath='Data/CrappieCooker/CrappieCooker_test2/CrappieCooker_log.csv'
##########################################



def LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath, timespath, versionpath,
                       fuelpath, fuelmetricpath, exactpath, scalepath,nanopath, TEOMpath, senserionpath, OPSpath, Picopath, emissioninputpath, inputmethod):
    
    ver = '0.2'
    
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_EmissionCalcs v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    pmetricnames=[]
    pmetric={}
    
    allnames=[]
    allunits={}
    allval={}
    allunc={}
    alluval={}
    
    flowgrid_cal_factor = 1 
    
    emissions=['CO','CO2', 'CO2v','PM','VOC']     #emission species that will get metric calculations

    phases=['hp','mp','lp']

    #Tstd=float(293)     #define standard temperature in Kelvin
    #Pstd=float(101325)   #define standard pressure in Pascals

    MW={}
    MW['C']=float(12.01)    # molecular weight of carbon (g/mol)
    MW['CO']=float(28.01)   # molecular weight of carbon monoxide (g/mol)
    MW['CO2']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['CO2v']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['SO2']=float(64.07)   # molecular weight of sulfur dioxide (g/mol)
    MW['NO']=float(30.01)   # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2']=float(46.01)   # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S']=float(34.1)   # molecular weight of hydrogen sulfide (g/mol)
    MW['VOC']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['CH4']=float(16.04) # molecular weight of methane (g/mol)
    MW['air']=float(29) #molecular weight of air (g/mol)
    R=float(8.314)     #universal gas constant (m^3Pa/mol/K)

    #load phase averages data file
    [metricnamesall,metricunits,metricval,metricunc,metric]=io.load_constant_inputs(aveinputpath)  #these are not used but copied to the output

    #############Check for IDC test
    if 'seconds_L1' in metricnamesall:
        phases.insert(0, 'L1')
    if 'seconds_L5' in metricnamesall:
        phases.append('L5')
    if 'CO2v_prebkg' in metricnamesall: #check if CO2v is present
        emissions.remove('CO2') #only run CO2v if present
    else:
        emissions.remove('CO2v')
    if 'VOC_prebkg' in metricnamesall:  # check if VOC is present
        pass
    else:
        emissions.remove('VOC')
    metricnames = []
    for em in emissions: #Pull out phase averages from average print out. Ignore bkg data
        for phase in phases:
            for name in metricnamesall:
                if em+'_' in name and phase in name:
                    metricnames.append(name)
    line = 'Loaded phase averages:'+aveinputpath
    print(line)
    logs.append(line)

    #load energy metrics data file
    [enames,eunits,emetrics,eunc,euval]=io.load_constant_inputs(energypath)
    line = 'Loaded energy metrics:'+energypath
    print(line)
    logs.append(line)

    [vnames, vunits, vval, vunc, vuval] = io.load_constant_inputs(versionpath)  # Load sensor version
    msg = 'loaded: ' + versionpath
    print(msg)
    logs.append(msg)

    firmware_version = vval['SB']

    if os.path.isfile(emissioninputpath):
        [emnames, emunits, emval, emunc, emuval] = io.load_constant_inputs(emissioninputpath)
    else:
        emnames = []
        emunits = {}
        emval = {}
        emunc = {}
        emuval = {}

        # make a header
        name = 'variable'
        emnames.append(name)
        emunits[name] = 'units'
        emval[name] = 'value'
        emunc[name] = 'uncertainty'

        if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':

            name = 'Cp'  # Pitot probe correction factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'velocity_traverse'  # Veloctiy traverse correction factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 0.975

            name = 'flowgrid_cal_factor'  # flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'factory_flow_cal'  # factory flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 62.8

            name = 'duct_diameter'
            emnames.append(name)
            emunits[name] = 'inches'
            emval[name] = 12.0

            name = 'MSC_default'
            emnames.append(name)
            emunits[name] = 'm^2/g'
            emval[name] = 3

        else:
            name = 'flowgrid_cal_factor'  # flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 1.0

            name = 'factory_flow_cal'  # factory flow grid calibration factor
            emnames.append(name)
            emunits[name] = ''
            emval[name] = 15.3

            name = 'duct_diameter'
            emnames.append(name)
            emunits[name] = 'inches'
            emval[name] = 6.0

            name = 'MSC_default'
            emnames.append(name)
            emunits[name] = 'm^2/g'
            emval[name] = 3

    if inputmethod == '1':
        fieldnames = []
        defaults = []
        if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':
            for name in emnames:
                if name != 'variable':
                    fieldnames.append(name)
                    defaults.append(emval[name])

            # GUI box to edit emissions
            zeroline = f'Enter emissions input data (g)\n\n' \
                       f'MSC_default may be used to more accurately calculate PM2.5 data when:\n' \
                       f'a) A filter is not used (use a historical MSC from a similar stove)\n' \
                       f'b) PM data could not be correctly backgound subtracted (use a historical MSC from a similar stove)\n' \
                       f'c) There is a desire to cut some PM data from final calcualtions (calculalte MSC using full data \n' \
                       f'   series, manipulate PM data and then entre previous MSC.\n\n' \
                       f'IF USING YOU ARE USING A FILTER AND DO NOT FALL INTO ONE OF THE SCENARIOS ABOVE, DO NOT CHANGE MSC_default.\n\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit'
            msg = zeroline + secondline + thirdline
            title = 'Gitdone'
            newvals = easygui.multenterbox(msg, title, fieldnames, values=defaults)
            if newvals:
                if newvals != defaults:
                    defaults = newvals
                    for n, name in enumerate(emnames[1:]):
                        emval[name] = defaults[n]
            else:
                line = 'Error: Undefined variables'
                print(line)
                logs.append(line)
        else:
            #otherwise for all other SB versions only show MSC default
            fieldnames.append('MSC_default')
            for name in emnames[1:]:
                defaults.append(emval[name])

            # GUI box to edit emissions
            zeroline = f'Enter emissions input data (g)\n\n' \
                       f'MSC_default may be used to more accurately calculate PM2.5 data when:\n' \
                       f'a) A filter is not used (use a historical MSC from a similar stove)\n' \
                       f'b) PM data could not be correctly backgound subtracted (use a historical MSC from a similar stove)\n' \
                       f'c) There is a desire to cut some PM data from final calcualtions (calculalte MSC using full data \n' \
                       f'   series, manipulate PM data and then entre previous MSC.\n\n' \
                       f'IF USING YOU ARE USING A FILTER AND DO NOT FALL INTO ONE OF THE SCENARIOS ABOVE, DO NOT CHANGE MSC_default.\n\n'
            secondline = 'Click OK to continue\n'
            thirdline = 'Click Cancel to exit'
            msg = zeroline + secondline + thirdline
            title = 'Gitdone'
            newvals = easygui.multenterbox(msg, title, fieldnames, values=[emval['MSC_default']])
            if newvals:
                if newvals != [emval['MSC_default']]:
                    emval['MSC_default'] = newvals[0]
                    for n, name in enumerate(emnames[1:]):
                        emval[name] = defaults[n]
            else:
                line = 'Error: Undefined variables'
                print(line)
                logs.append(line)
        io.write_constant_outputs(emissioninputpath, emnames, emunits, emval, emunc, emuval)
        line = '\nCreated emissions input file: ' + emissioninputpath
        print(line)
        logs.append(line)
    else:
        line = '\nUsed old/default inputs from input file: ' + emissioninputpath
        print(line)
        logs.append(line)

    for name in emnames[1:]:
        emval[name] = float(emval[name])

    #load grav metrics data file
    name = 'MSC'
    #pmetricnames.append(name)
    #metricnames.append(name)
    metricunits[name] = 'm^2/g'
    try:
        [gravnames,gravunits,gravmetrics,gravunc,gravuval]=io.load_constant_inputs(gravinputpath) #MSC is not in gravoutputs
        line = 'Loaded gravimetric PM metrics:'+gravinputpath
        print(line)
        logs.append(line)
        pmetric[name] = 0
    except:
        line = 'No gravimetric data, using default MSC'
        print(line)
        logs.append(line)
        pmetric[name] = emval['MSC_default']
    
    #ambient pressure from energy metrics data file (hPa converted here to Pa)
    name='P_amb'
    metricnames.append(name)
    metricunits[name]='Pa'
    try:
        metric[name]=((euval['initial_pressure']+euval['final_pressure']) * 33.86)/2*100  #Pa
    except:
        try:
            metric[name]=euval['initial_pressure']*33.86*100
        except:
            metric[name]=euval['final_pressure']*33.86*100
            
    #absolute duct pressure, Pa
    name='P_duct'
    metricnames.append(name)
    metricunits[name]='Pa'
    metric[name]=metric['P_amb']
            
    for phase in phases:
        pmetricnames=[]                                 #initialize a list of metric names for each phase
        #read in time series data file
        phaseinputpath=inputpath[:-4]+'_'+phase+'.csv'

        if os.path.isfile(phaseinputpath): #check that time series path exists
            [names,units,data] = io.load_timeseries(phaseinputpath)
        
            line = 'Loaded phase time series data:'+phaseinputpath
            print(line)
            logs.append(line)


            #MSC mass scattering cross-section (constant)
    
            name='MSC'
            pmetricnames.append(name)

            try: #backwards compatable for MSC not being in previous inputs
                emval['MSC_default']
            except:
                emval['MSC_default'] = 3

            if pmetric[name] != emval['MSC_default']:
                #if phase == 'full':
                    #conc = 0
                   # for p in phases:
                        #if p != 'full':
                            #try:
                                #gra = gravuval['PMmass_'+p]   #average PM mass concentration ug/m^3 reading from gravoutputs
                                #conc = conc + gra #sum of all PM mass concentrations from all phases
                                #scat = sum(data['PM'])/len(data['PM'])
                            #except:
                                #pass
                #else:
                conc=gravuval['PMmass_'+phase]   #average PM mass concentration ug/m^3
                scat = metric['PM_' + phase]  # sum(data['PM_' + phase])/len(data['PM_' + phase])    #average scattering value Mm^-1 %needs to be per phase

                try:
                    pmetric[name]=scat/conc
                    #metric[name] = scat / conc
                except:
                    pmetric[name]=ufloat(np.nan,np.nan)
                    #metric[name] = ufloat(np.nan, np.nan)

            #calculate mass concentration data series
            for species in emissions:   #for each emission species that will get metrics
                name=species+'mass'
                names.append(name)
                units[name]='gm^-3'
                data[name]=[]
                for n,val in enumerate(data[species]):
                    try:
                        if species == 'PM':
                            result=val/pmetric['MSC']/1000000 #MSC needs to be different for each phase
                        else:   #from ppm and ideal gas law
                            result=val*MW[species]*metric['P_duct']/(data['FLUEtemp'][n]+273.15)/1000000/R
                    except:
                        result=''
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #Carbon concentration
            name = 'Cmass'
            names.append(name)
            units[name] = 'gm^-3'
            data[name] = []
            for n, val in enumerate(data['COmass']):
                try:
                    data[name].append(val * MW['C'] / MW['CO'] + data['CO2vmass'][n] * MW['C'] / MW['CO2v'])
                except:
                    data[name].append(val * MW['C'] / MW['CO'] + data['CO2mass'][n] * MW['C'] / MW['CO2'])


            #MCE
            name='MCE'
            names.append(name)
            units[name]='mol/mol'
            data[name]=[]
            try:
                for n,val in enumerate(data['CO2v']):
                    result=val/(val+data['CO'][n])
                    data[name].append(result)
            except:
                for n,val in enumerate(data['CO2']):
                    result=val/(val+data['CO'][n])
                    data[name].append(result)

            #flue gas molecular weight
            name='MW_duct'
            names.append(name)
            units[name]='g/mol'
            data[name]=[]
            for n,val in enumerate(data['time']):
                result=MW['air']
                data[name].append(result)

            #flue gas density
            name='density'
            names.append(name)
            units[name]='gm^-3'
            data[name]=[]
            for n,val in enumerate(data['MW_duct']):
                result=val*metric['P_duct']/R/(data['FLUEtemp'][n]+273.15)
                data[name].append(result)

            if firmware_version == 'POSSUM2' or firmware_version == 'Possum2' or firmware_version == 'possum2':
                ####Smooth Pitot Data
                n = 10 #boxcar length
                name = 'Flow_smooth'
                names.append(name)
                units[name] = 'mmH2O'
                data[name] = []
                for m, val in enumerate(data['Flow']):
                    if m == 0:
                        newval = val
                    else:
                        if m >=n:
                            boxcar = data['Flow'][m - n:m]
                        else:
                            boxcar = data['Flow'][:m]
                        newval = sum(boxcar) / len(boxcar)
                    data[name].append(newval)
                msg = 'smoothed flow data'
                print(msg)
                logs.append(msg)

                ######Duct velocity
                # V = Cp * (2 deltaP / density) ^1/2
                # Use ideal gas law: Pamb = density * (R/M) * T
                name = 'DuctFlow'
                names.append(name)
                units[name] = 'm/sec'
                data[name] = []

                for n, val in enumerate(data['Flow_smooth']):
                    Flow_Pa = val * 9.80665 #mmH2O to Pa
                    Pduct_Pa = data['AmbPres'][n] * 100 #hPa to Pa
                    TC_K = data['FLUEtemp'][n] + 273.15 # C to K
                    inner = (Flow_Pa * 2 * R * TC_K) / (Pduct_Pa * MW['air'] / 1000)
                    velocity = emval['Cp'] * math.sqrt(inner)
                    data[name].append(velocity)

                name = 'vol_flow_ASTM'
                names.append(name)
                units[name] = 'm^3/s'
                data[name] = []

                duct_diameter = emval['duct_diameter'] / 39.37 #m
                duct_area = (np.pi * duct_diameter * duct_diameter) / 4 #m^2

                for n, val in enumerate(data['DuctFlow']):
                    data[name].append(val * duct_area * emval['velocity_traverse'])

                name = 'mass_flow_ASTM'
                names.append(name)
                units[name] = 'g/sec'
                data[name] = []

                for n, val in enumerate(data['vol_flow_ASTM']):
                    data[name].append(val * data['density'][n])

                # mole flow of air and pollutants through dilution tunnel
                name = 'mole_flow_ASTM'
                names.append(name)
                units[name] = 'mol/sec'
                data[name] = []
                for n, val in enumerate(data['mass_flow_ASTM']):
                    result = val / data['MW_duct'][n]
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

                # cumulative volume through dilution tunnel
                name = 'totvol_ASTM'
                names.append(name)
                units[name] = 'm^3'
                data[name] = []
                sample_period = data['seconds'][3] - data['seconds'][2]
                for n, val in enumerate(data['vol_flow_ASTM']):
                    if n == 0:
                        result = val
                    else:
                        result = data[name][n - 1] + val * sample_period
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

                # emission rates g/sec
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_ASTM'
                    names.append(name)
                    units[name] = 'g/sec'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        try:
                            result = val * data['vol_flow_ASTM'][n]
                        except TypeError:
                            pass #Previous result will be used for data point if there's an invalid entry
                        try:
                            data[name].append(result.n)
                        except:
                            data[name].append(result)

                # carbon burn rate
                name = 'C_ER_ASTM'
                names.append(name)
                units[name] = 'g/sec'
                data[name] = []
                try:
                    for n, val in enumerate(data['CO2v_ER_ASTM']):
                        try:
                            result = val * MW['C'] / MW['CO2v'] + data['CO_ER_ASTM'][n] * MW['C'] / MW['CO']
                        except:
                            result = ''
                        data['C_ER_ASTM'].append(result)
                except:  # still needed something if CO2v doesn't exist
                    for n, val in enumerate(data['CO2_ER_ASTM']):
                        try:
                            result = val * MW['C'] / MW['CO2'] + data['CO_ER_ASTM'][n] * MW['C'] / MW['CO']
                        except:
                            result = ''
                        data['C_ER_ASTM'].append(result)
                # emission rates g/min
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_min_ASTM'
                    names.append(name)
                    units[name] = 'g/min'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        result = val * data['vol_flow_ASTM'][n] * 60
                        try:
                            data[name].append(result.n)
                        except:
                            data[name].append(result)

                # emission rates g/hr
                for species in emissions:
                    concname = species + 'mass'
                    name = species + '_ER_hr_ASTM'
                    names.append(name)
                    units[name] = 'g/hr'
                    data[name] = []
                    for n, val in enumerate(data[concname]):
                        result = val * data['vol_flow_ASTM'][n] * 60 * 60
                        try:
                            data[name].append(result.n)
                        except:
                            data[name].append(result)

                # emission factors (ish)
                for species in emissions:
                    ERname = species + '_ER_hr_ASTM'
                    name = species + '_EF_ASTM'
                    names.append(name)
                    units[name] = 'g/kg_C'  # gram per kilogram carbon
                    data[name] = []
                    for n, val in enumerate(data[ERname]):
                        if data['C_ER_ASTM'][n] == 0:
                            data['C_ER_ASTM'][n] = 0.001  # Avoid division by 0 errors
                        result = val / (data['C_ER_ASTM'][n] * 3600 / 1000)  # g/sec to kg/hr
                        try:
                            data[name].append(result.n)
                        except:
                            data[name].append(result)


            #mass flow of air and pollutants through dilution tunnel
            name='mass_flow'
            names.append(name)
            units[name]='g/sec'
            data[name]=[]
            for n,val in enumerate(data['Flow']):
                try:
                    result=emval['factory_flow_cal'] * emval['flowgrid_cal_factor'] * (val/25.4 * metric['P_duct']/(data['FLUEtemp'][n]+273.15))**0.5   #convert val from in H2O to mm H2O
                except:
                    result = 0#15.3 * flowgrid_cal_factor * (val / 25.4 * metric['P_duct'].n / (data['FLUEtemp'][n] + 273.15)) ** 0.5  # convert val from Pa to inH2O

                try:
                    data[name].append(result.n)
                except:
                    data[name].append(result)

            #volume flow of air and pollutants through dilution tunnel
            name='vol_flow'
            names.append(name)
            units[name]='m^3/sec'
            data[name]=[]
            for n,val in enumerate(data['mass_flow']):
                try:
                    result=val/data['density'][n]
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)
                except:
                    data[name].append(0)

            #mole flow of air and pollutants through dilution tunnel
            name='mole_flow'
            names.append(name)
            units[name]='mol/sec'
            data[name]=[]
            for n,val in enumerate(data['mass_flow']):
                result=val/data['MW_duct'][n]
                try:
                    data[name].append(result.n)
                except:
                    data[name].append(result)


            #cumulative volume through dilution tunnel
            name='totvol'
            names.append(name)
            units[name]='m^3'
            data[name]=[]
            sample_period = data['seconds'][3]-data['seconds'][2]
            for n,val in enumerate(data['vol_flow']):
                if n == 0:
                    result = val
                else:
                    result=data[name][n-1]+val*sample_period
                try:
                    data[name].append(result.n)
                except:
                    data[name].append(result)


            #emission rates g/sec
            for species in emissions:
                concname=species+'mass'
                name=species+'_ER'
                names.append(name)
                units[name]='g/sec'
                data[name]=[]
                for n,val in enumerate(data[concname]):
                    result=val*data['vol_flow'][n]
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #carbon burn rate
            name='C_ER'
            names.append(name)
            units[name]='g/sec'
            data[name]=[]
            try:
                for n, val in enumerate(data['CO2v_ER']):
                    try:
                        result = val * MW['C'] / MW['CO2v'] + data['CO_ER'][n] * MW['C'] / MW['CO']
                    except:
                        result = ''
                    data['C_ER'].append(result)
            except: #still needed something if CO2v doesn't exist
                for n, val in enumerate(data['CO2_ER']):
                    try:
                        result = val * MW['C'] / MW['CO2'] + data['CO_ER'][n] * MW['C'] / MW['CO']
                    except:
                        result = ''
                    data['C_ER'].append(result)
            #emission rates g/min
            for species in emissions:
                concname=species+'mass'
                name=species+'_ER_min'
                names.append(name)
                units[name]='g/min'
                data[name]=[]
                for n,val in enumerate(data[concname]):
                    result=val*data['vol_flow'][n]*60
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #emission rates g/hr
            for species in emissions:
                concname=species+'mass'
                name=species+'_ER_hr'
                names.append(name)
                units[name]='g/hr'
                data[name]=[]
                for n,val in enumerate(data[concname]):
                    result=val*data['vol_flow'][n]*60*60
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #emission factors (ish)
            for species in emissions:
                ERname = species + '_ER_hr'
                name = species + '_EF'
                names.append(name)
                units[name] = 'g/kg_C' #gram per kilogram carbon
                data[name] = []
                for n, val in enumerate(data[ERname]):
                    if data['C_ER'][n] == 0:
                        data['C_ER'][n] = 0.001 #Avoid division by 0 errors
                    result = val / (data['C_ER'][n] * 3600 / 1000) #g/sec to kg/hr
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #firepower
            wood_Cfrac = 0.5  # carbon fraction of fuel (should be an input in energy inputs
            name='firepower_carbon'
            names.append(name)
            units[name]='W'
            data[name]=[]
            for n,val in enumerate(data['C_ER']):
                try:
                    result=val / wood_Cfrac * float(emetrics['fuel_heating_value']) #old spreadsheet
                except:
                    try:
                        result = val / float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_EHV_' + phase]) #new spreadsheet
                    except:
                        result = ''
                try:
                    data[name].append(result.n)
                except:
                    data[name].append(result)

            #cumulative mass
            for species in emissions:
                ername=species+'_ER'
                name=species+'_totmass'
                names.append(name)
                units[name]='g'
                data[name]=[]
                for n,val in enumerate(data[ername]):
                    if n == 0:
                        result = val
                    else:
                        result=data[name][n-1]+val*sample_period
                    try:
                        data[name].append(result.n)
                    except:
                        data[name].append(result)

            #output time series data file
            phaseoutputpath=inputpath[:-4]+'Metrics_'+phase+'.csv'    #name the output file by removing 'Data.csv' and inserting 'Metrics' and the phase name into inputpath
            io.write_timeseries_without_uncertainty(phaseoutputpath,names,units,data)

            line='created phase time series data file with processed emissions:\n'+phaseoutputpath
            print(line)
            logs.append(line)

            #### phase average emission metrics  ####################

            #MCE
            name='MCE'
            pmetricnames.append(name)
            metricunits[name]='mol/mol'
            '''
            if phase == 'full':
                co = 0
                co2 = 0
                for p in phases:
                    if p != 'full':
                        try:
                            mco2 = metric['CO2v_'+p]
                            mco = metric['CO_'+p]
                        except:
                            try:
                                mco2 = metric['CO2_' + p]
                                mco = metric['CO_' + p]
                            except:
                                mco2 = 0
                                mco = 0
                        co = co + mco
                        co2 = co2 + mco2 #sum off all the phases

                pmetric[name] = co2 / ( co2 + co)
            else:
            '''
            try:
                pmetric[name]=metric['CO2v_'+phase]/(metric['CO2v_'+phase]+metric['CO_'+phase])
            except:
                pmetric[name] = metric['CO2_' + phase] / (metric['CO2_' + phase] + metric['CO_' + phase])

            for name in ['MW_duct','density','mass_flow','mole_flow','vol_flow']:
                pmetricnames.append(name)
                metricunits[name]=units[name]
                pmetric[name]=sum(data[name])/len(data[name])

            #cumulative volume
            name='totvol'
            pmetricnames.append(name)
            metricunits[name]='m^3'
            pmetric[name]=data[name][-1]

            for species in emissions:
                #mass concentration
                name=species+'mass'
                pmetricnames.append(name)
                metricunits[name]='gm^-3'
                pmetric[name]=sum(data[name])/len(data[name])

                #total mass
                name=species+'_total_mass'
                pmetricnames.append(name)
                metricunits[name]='g'
                try:
                    pmetric[name]=data[species+'_totmass'][-1]
                except:
                    pmetric[name]=''

                #emission factor dry fuel
                name=species+'_fuel_dry_mass'
                pmetricnames.append(name)
                metricunits[name]='g/kg'
                try:
                #print(species+'_total_mass    '+str(pmetric[species+'_total_mass'])+'    '+str(type(pmetric[species+'_total_mass'])))
                #print('fuel_dry_mass_'+phase+'    '+str(euval['fuel_dry_mass_'+phase])+'    '+str(type(euval['fuel_dry_mass_'+phase])))
                    pmetric[name]=pmetric[species+'_total_mass']/euval['fuel_dry_mass_'+phase]
                except:
                    pmetric[name]=''

                #emission factor energy
                name=species+'_fuel_energy'
                pmetricnames.append(name)
                metricunits[name]='g/MJ'
                try:
                    pmetric[name]=pmetric[species+'_total_mass']/euval['fuel_mass_'+phase]/euval['fuel_heating_value']*1000
                except:
                    pmetric[name]=''

                #emission factor energy with energy credit for char
                name=species+'_fuel_energy_w_char'
                pmetricnames.append(name)
                metricunits[name]='g/MJ'
                try:
                    pmetric[name]=pmetric[species+'_total_mass']/(euval['fuel_mass_'+phase]*euval['fuel_heating_value']-euval['char_mass_'+phase]*euval['char_heating_value'])*1000
                except:
                    pmetric[name]=''

                #emission factor useful energy delivered
                name=species+'_useful_eng_deliver'
                pmetricnames.append(name)
                if species == 'PM':
                    metricunits[name]='mg/MJ'
                    try:
                        pmetric[name]=pmetric[species+'_total_mass']/euval['useful_energy_delivered_'+phase]*1000*1000
                    except:
                        pmetric[name]=''
                else:
                    metricunits[name]='g/MJ'
                    try:
                        pmetric[name]=pmetric[species+'_total_mass']/euval['useful_energy_delivered_'+phase]*1000
                    except:
                        pmetric[name]=''

                #emission rate
                name=species+'_mass_time'
                pmetricnames.append(name)
                if species == 'PM':
                    metricunits[name]='mg/min'
                    try:
                        pmetric[name]=pmetric[species+'_total_mass']/len(data['time'])/sample_period*60*1000
                        name = species + '_heat_mass_time'
                        pmetricnames.append(name)
                        metricunits[name] = 'g/hr'
                        pmetric[name] = pmetric[species + '_total_mass'] / len(data['time'])/sample_period * 60 * 60
                    except:
                        pmetric[name]=''
                else:
                    metricunits[name]='g/min'
                    try:
                        pmetric[name]=pmetric[species+'_total_mass']/len(data['time'])/sample_period*60
                    except:
                        pmetric[name]=''

            #Carbon emission rate
            name = 'C_mass_time'
            pmetricnames.append(name)
            metricunits[name] = 'g/min'
            try:
                pmetric[name] = pmetric['CO2v_mass_time'] * MW['C'] / MW['CO2v'] + pmetric['CO_mass_time'] * MW['C'] / MW['CO']
            except:
                pmetric[name] = pmetric['CO2_mass_time'] * MW['C'] / MW['CO2'] + pmetric['CO_mass_time'] * MW['C'] / MW['CO']

            #Emission factor
            for species in emissions:
                ERname = species + '_mass_time'
                name = species + '_EF'
                pmetricnames.append(name)
                metricunits[name] = 'g/kg_C' #gram per kilogram carbon
                if species == 'PM':
                    pmetric[name] = (pmetric[ERname] / 1000) / (pmetric['C_mass_time'] / 1000) #mg/min to g/min, g/min tp kg/min
                else:
                    pmetric[name] = pmetric[ERname] / (pmetric['C_mass_time'] / 1000) #g/min to kg/min

            name = 'firepower_carbon'
            pmetricnames.append(name)
            metricunits[name] = 'W'
            try:
                pmetric[name] = sum(data['firepower_carbon']) / len(data['firepower_carbon'])
            except:
                pmetric[name] = ''

            #add phase identifier to metric names
            for name in pmetricnames:                          #for each metric calculated for the phase
                metricname=name+'_'+phase        #add the phase identifier to the variable name
                metric[metricname] = pmetric[name]
                metricunits[metricname]=metricunits[name]
                metricnames.append(metricname)              #add the new full variable name to the list of variables that will be output

            ###################################################
            # carbon in

            name = 'carbon_in_' + phase
            metricnames.append(name)
            metricunits[name] = 'g'
            try:
                if emetrics['final_char_mass_' + phase] != '': #if char was entered in old data sheet
                    try:
                        metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_mass_' + phase])
                                        - 0.81 * float(emetrics['char_mass_' + phase])) * 1000
                    except:
                        metric[name] = (0.5 * float(emetrics['fuel_mass_' + phase]) - 0.81 *
                                        float(emetrics['char_mass_' + phase])) * 1000
                        line = 'Used assumed wood carbon fraction of 0.5 g/g for carbon in calculations'
                        print(line)
                        logs.append(line)
                else:
                    try:
                        metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_mass_' + phase])) \
                                       * 1000
                    except:
                        metric[name] = (0.5 * float(emetrics['fuel_mass_' + phase])) * 1000
                        line = 'Used assumed wood carbon fraction of 0.5 g/g for carbon in calculations'
                        print(line)
                        logs.append(line)
            except: #new spreadsheet considers charcoal as a multi-fuel input
                try:
                    metric[name] = (float(emetrics['fuel_Cfrac_' + phase]) * float(emetrics['fuel_mass_' + phase])) * 1000  # kg to g
                except:
                    metric[name] = ''
            # carbon out
            name = 'carbon_out_' + phase
            metricnames.append(name)
            metricunits[name] = 'g'
            try: #this needs an expection for SB with only CO2 sensor
                metric[name] = (metric['CO_total_mass_' + phase] * MW['C'] / MW['CO'] + metric['CO2v_total_mass_' + phase] * MW['C'] / MW['CO2v'] + 0.91 * metric['PM_total_mass_' + phase])
            except:
                try:
                    metric[name] = (metric['CO_total_mass_' + phase] * MW['C'] / MW['CO'] + metric['CO2_total_mass_' + phase] * MW['C'] / MW['CO2'] + 0.91 * metric['PM_total_mass_' + phase])
                except:
                    metric[name] = ''

            #carbon out/in
            name = 'C_Out_In_' + phase
            metricnames.append(name)
            metricunits[name] = 'g/g'
            try:
                metric[name] = metric['carbon_out_' + phase] / metric['carbon_in_' + phase]
            except:
                metric[name] = ''
        # carbon burn rate
        #for phase in phases:
            #name = 'ERC_' + phase
            #units[name] = 'g/hr'
            #metric[name] = (metric['carbon_out_' + phase] - metric['carbon_in_' + phase]) / (
                        #emetric['phase_time_' + phase] / 60)

    ###########################################
    # ISO weighted metrics
    existing_weight_phases = []
    weighted_metrics = ['CO_useful_eng_deliver', 'PM_useful_eng_deliver', 'PM_mass_time', 'PM_heat_mass_time',
                        'CO_mass_time']

    for phase in phases:
        name = 'weight_' + phase
        try:
            if emetrics[name].n != '':
                existing_weight_phases.append(phase)
        except:
            if emetrics[name] != '':
                existing_weight_phases.append(phase)

    for name in weighted_metrics:
        weight_name = name + '_weighted'
        metricnames.append(weight_name)
        try:
            metricunits[weight_name] = metricunits[name + '_hp']
        except:
            try:
                metricunits[weight_name] = metricunits[name + '_mp']
            except:
                try:
                    metricunits[weight_name] = metricunits[name + '_lp']
                except:
                    try:
                        metricunits[weight_name] = metricunits[name + '_L1']
                    except:
                        metricunits[weight_name] = metricunits[name + '_L5']

        metric[weight_name] = ufloat(0, 0)
        for phase in existing_weight_phases:
            phase_name = name + '_' + phase
            try:
                metric[weight_name] = metric[weight_name] + (metric[phase_name] * euval['weight_' + phase]) / \
                                      euval['weight_total']
            except:
                pass

    if metric['CO_useful_eng_deliver_weighted'].n != 0:
        name = 'tier_CO_useful_eng_deliver'
        metricnames.append(name)
        metricunits[name] = ''
        metric[name] = 'nan'
        if metric['CO_useful_eng_deliver_weighted'].n > 18.3:
            metric[name] = 'Tier 0'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 18.3 and metric['CO_useful_eng_deliver_weighted'].n > 11.5:
            metric[name] = 'Tier 1'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 11.5 and metric['CO_useful_eng_deliver_weighted'].n > 7.2:
            metric[name] = 'Tier 2'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 7.2 and metric['CO_useful_eng_deliver_weighted'].n > 4.4:
            metric[name] = 'Tier 3'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 4.4 and metric['CO_useful_eng_deliver_weighted'].n > 3:
            metric[name] = 'Tier 4'
        elif metric['CO_useful_eng_deliver_weighted'].n <= 3:
            metric[name] = 'Tier 5'

    if metric['PM_useful_eng_deliver_weighted'].n != 0:
        name = 'tier_PM_useful_eng_deliver'
        metricnames.append(name)
        metricunits[name] = ''
        metric[name] = 'nan'
        if metric['PM_useful_eng_deliver_weighted'].n > 1030:
            metric[name] = 'Tier 0'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 1030 and metric['PM_useful_eng_deliver_weighted'].n > 481:
            metric[name] = 'Tier 1'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 481 and metric['PM_useful_eng_deliver_weighted'].n > 218:
            metric[name] = 'Tier 2'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 218 and metric['PM_useful_eng_deliver_weighted'].n > 62:
            metric[name] = 'Tier 3'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 62 and metric['PM_useful_eng_deliver_weighted'].n > 5:
            metric[name] = 'Tier 4'
        elif metric['PM_useful_eng_deliver_weighted'].n <= 5:
            metric[name] = 'Tier 5'

    #print phase metrics output file
    io.write_constant_outputs(emisoutputpath,metricnames,metricunits,metricval,metricunc,metric)
    
    line='\ncreated emission metrics output file:\n'+emisoutputpath
    print(line)
    logs.append(line)

    
    #### print all metrics output file (energy, grav, emissions)    ######################
    #add the energy outputs
    for name in enames:
        allnames.append(name)
        allunits[name]=eunits[name]
        allval[name]=emetrics[name]
        allunc[name]=eunc[name]
    
    #add the grav outputs, if they are present
    if pmetric['MSC'] != emval['MSC_default']:
        for name in gravnames[1:]:  #skip first line because it is the header
            allnames.append(name)
            allunits[name]=gravunits[name]
            allval[name]=gravmetrics[name]
            allunc[name]=gravunc[name]
        
    #add emissions outputs
    for name in metricnames[1:]:    #skip first line because it is the header
        allnames.append(name)
        allunits[name]=metricunits[name]
        allval[name]=metricval[name]
        allunc[name]=metricunc[name]
        alluval[name]=metric[name]

    #add lems averages outputs
    for name in metricnamesall[1:]:    #skip first line because it is the header
        allnames.append(name)
        allunits[name]=metricunits[name]
        allval[name]=metricval[name]
        allunc[name]=metricunc[name]
        alluval[name]=metric[name]

    #average other sensors by phase and add to alloutputs
    timenames,timeunits,timeval,timeunc,timeuval = io.load_constant_inputs(timespath)

    sensorpaths = []
    # Read in additional sensor data and add it to dictionary
    if os.path.isfile(fuelpath):
        sensorpaths.append(fuelpath)

    if os.path.isfile(fuelmetricpath):
        sensorpaths.append(fuelmetricpath)

    if os.path.isfile(exactpath):
        sensorpaths.append(exactpath)

    if os.path.isfile(scalepath):
        sensorpaths.append(scalepath)

    if os.path.isfile(nanopath):
        sensorpaths.append(nanopath)

    if os.path.isfile(TEOMpath):
        sensorpaths.append(TEOMpath)

    if os.path.isfile(senserionpath):
        sensorpaths.append(senserionpath)

    if os.path.isfile(OPSpath):
        sensorpaths.append(OPSpath)

    if os.path.isfile(Picopath):
        sensorpaths.append(Picopath)

    #phases.remove('full')

    for path in sensorpaths:
        try:
            [snames, sunits, sdata] = io.load_timeseries(path)

            name = 'dateobjects'
            snames.append(name)
            sunits[name] = 'date'
            sdata[name] = []
            for n, val in enumerate(sdata['time']):
                try:
                    dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
                except:
                    dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
                sdata[name].append(dateobject)

            name = 'datenumbers'
            snames.append(name)
            sunits[name] = 'date'
            sdatenums = matplotlib.dates.date2num(sdata['dateobjects'])
            sdatenums = list(sdatenums)
            sdata[name] = sdatenums

            samplerate = sdata['seconds'][1] - sdata['seconds'][0]  # find sample rate
            date = data['time'][0][0:8]

            for phase in phases:
                start = timeval['start_time_' + phase]
                end = timeval['end_time_' + phase]

                if start != '':
                    if len(start) < 10:
                        start = date + ' ' + start
                        end = date + ' ' + end
                    try:
                        startdateobject = dt.strptime(start, '%Y%m%d %H:%M:%S')
                    except:
                        startdateobject = dt.strptime(start, '%Y-%m-%d %H:%M:%S')
                    try:
                        enddateobject = dt.strptime(end, '%Y%m%d %H:%M:%S')
                    except:
                        enddateobject = dt.strptime(end, '%Y-%m-%d %H:%M:%S')

                    startdatenum = matplotlib.dates.date2num(startdateobject)
                    enddatenum = matplotlib.dates.date2num(enddateobject)

                    phasedata = {}
                    for name in snames:
                        try:
                            phasename = name + '_' + phase

                            #for x, date in enumerate(sdata['datenumbers']):  # cut data to phase time
                                #if startdatenum <= date <= enddatenum:
                                    #phasedata[phasename].append(sdata[name][x])
                            m = 1
                            ind = 0
                            while m <= samplerate + 1 and ind == 0:
                                try:
                                    startindex = sdata['dateobjects'].index(startdateobject)
                                    ind = 1
                                except:
                                    startdateobject = startdateobject + timedelta(seconds=1)
                                    m += 1
                            m = 1
                            ind = 0
                            while m <= samplerate + 1 and ind == 0:
                                try:
                                    endindex = sdata['dateobjects'].index(enddateobject)
                                    ind = 1
                                except:
                                    enddateobject = enddateobject + timedelta(seconds=1)
                                    m += 1

                            phasedata[phasename] = sdata[name][startindex:endindex + 1]

                            if 'seconds' in name:
                                phaseaverage = phasedata[phasename][-1] - phasedata[phasename][0]
                                allnames.append(phasename)
                                allunits[phasename] = sunits[name]
                                allval[phasename] = phaseaverage
                                allunc[phasename] = ''
                                alluval[phasename] = ''
                            elif 'TC' in name:
                                phaseaverage = sum(phasedata[phasename]) / len(phasedata[phasename])
                                allnames.append('S' + phasename)
                                allunits['S' + phasename] = sunits[name]
                                allval['S' + phasename] = phaseaverage
                                allunc['S' + phasename] = ''
                                alluval['S' + phasename] = ''
                            elif 'time' not in name and 'date' not in name:
                                phaseaverage = sum(phasedata[phasename]) / len(phasedata[phasename])
                                allnames.append(phasename)
                                allunits[phasename] = sunits[name]
                                allval[phasename] = phaseaverage
                                allunc[phasename] = ''
                                alluval[phasename] = ''
                        except:
                            phaseaverage = ''
                            allnames.append(phasename)
                            allunits[phasename] = sunits[name]
                            allval[phasename] = phaseaverage
                            allunc[phasename] = ''
                            alluval[phasename] = ''
            line = 'Added sensor data from: ' + path + 'to: ' + alloutputpath
            print(line)
            logs.append(line)
        except UnboundLocalError:
            message = 'Data from: ' + path + ' could not be cut to the same time as sensorbox data.\n'
            print(message)
            logs.append(message)
    
    io.write_constant_outputs(alloutputpath,allnames,allunits,allval,allunc,alluval)
    
    line='\ncreated all metrics output file:\n'+alloutputpath
    print(line)
    logs.append(line)    

    #############################################################
    #create a full timeseries with metrics
    combined_names = []
    combined_units = {}
    combined_data = {}
    #compile full timeseries file
    for phase in phases:
        #read in time series data file
        phaseinputpath=inputpath[:-4]+'Metrics_'+phase+'.csv'

        if os.path.isfile(phaseinputpath): #check that time series path exists
            [names,units,data] = io.load_timeseries(phaseinputpath)

            #combine names, units, and data
            for name in names:
                if name not in combined_names:
                    combined_names.append(name)
                    combined_units[name] = units[name]
                if name in combined_data:
                    combined_data[name] += data[name] # Append to existing data if name already exists
                else:
                    combined_data[name] = data[name]  # Initialize  data if name is new

    # output time series data file
    phaseoutputpath = inputpath[
                      :-4] + 'Metrics_full.csv'  # name the output file by removing 'Data.csv' and inserting 'Metrics' and the phase name into inputpath
    io.write_timeseries_without_uncertainty(phaseoutputpath, combined_names, combined_units, combined_data)

    line = 'created phase time series data file with processed emissions for all phases:\n' + phaseoutputpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)

    #CHANGE HERE 
    #return allnames,allunits,allval,allunc,alluval
    return logs, metricval, metricunits
    
#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath)