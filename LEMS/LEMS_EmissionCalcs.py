#v0.0 Python3

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
import os

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



def LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath):
    
    ver = '0.0'
    
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
    
    emissions=['CO','CO2', 'CO2v','PM']     #emission species that will get metric calculations
    
    phases=['hp','mp','lp', 'full']
    
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
    MW['HxCy']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['CH4']=float(16.04) # molecular weight of methane (g/mol)
    MW['air']=float(29) #molecular weight of air (g/mol)
    R=float(8.314)     #universal gas constant (m^3Pa/mol/K)
    
    #load phase averages data file
    [metricnamesall,metricunits,metricval,metricunc,metric]=io.load_constant_inputs(aveinputpath)  #these are not used but copied to the output

    #############Check for IDC test
    if 'ID_L1' in metricnamesall:
        phases.insert(0, 'L1')
    if 'ID_L5' in metricnamesall:
        phases.append('L5')
    if 'CO2v_prebkg' in metricnamesall: #check if CO2v is present
        emissions.remove('CO2') #only run CO2v if present
    else:
        emissions.remove('CO2v')
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
    emetrics['eff_w_char_hp']
    line = 'Loaded energy metrics:'+energypath
    print(line)
    logs.append(line)
    
    #load grav metrics data file
    name = 'MSC'
    pmetricnames.append(name)
    metricunits[name] = 'm^2/g'
    try:
        [gravnames,gravunits,gravmetrics,gravunc,gravuval]=io.load_constant_inputs(gravinputpath)
        line = 'Loaded gravimetric PM metrics:'+gravinputpath
        print(line)
        logs.append(line)
        pmetric[name] = 0
    except:
        line = 'No gravimetric data, using default MSC'
        print(line)
        logs.append(line)
        pmetric[name] = 3
    
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
        if phase == 'full':
            phaseinputpath = inputpath #full path is all of timeseries data
        else:
            phaseinputpath=inputpath[:-4]+'_'+phase+'.csv'

        if os.path.isfile(phaseinputpath): #check that time series path exists
            [names,units,data] = io.load_timeseries(phaseinputpath)
        
            line = 'Loaded phase time series data:'+phaseinputpath
            print(line)
            logs.append(line)


            #MSC mass scattering cross-section (constant)
    
            name='MSC'
            #pmetricnames.append(name)
            #metricunits[name]='m^2/g'
            scat=sum(data['PM'])/len(data['PM'])    #average scattering value Mm^-1
            if pmetric[name] != 3:
                if phase == 'full':
                    conc = 0
                    for p in phases:
                        if p != 'full':
                            try:
                                gra = gravuval['PMmass_'+p]   #average PM mass concentration ug/m^3
                                conc = conc + gra #sum of all PM mass concentrations from all phases
                            except:
                                pass
                else:
                    conc=gravuval['PMmass_'+phase]   #average PM mass concentration ug/m^3

            if pmetric[name] == 0:
                try:
                    pmetric[name]=scat/conc
                except:
                    pmetric[name]=ufloat(np.nan,np.nan)

            #calculate mass concentration data series
            for species in emissions:   #for each emission species that will get metrics
                name=species+'mass'
                names.append(name)
                units[name]='gm^-3'
                data[name]=[]
                for n,val in enumerate(data[species]):
                    try:
                        if species == 'PM':
                            result=val/pmetric['MSC']/1000000
                        else:   #from ppm and ideal gas law
                            result=val*MW[species]*metric['P_duct']/(data['FLUEtemp'][n]+273.15)/1000000/R
                    except:
                        result=''
                    data[name].append(result)

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

            #mass flow of air and pollutants through dilution tunnel
            name='mass_flow'
            names.append(name)
            units[name]='g/sec'
            data[name]=[]
            for n,val in enumerate(data['Flow']):
                try:
                    result=15.3*flowgrid_cal_factor*(val/25.4*metric['P_duct']/(data['FLUEtemp'][n]+273.15))**0.5   #convert val from Pa to inH2O
                except:
                    result = 0#15.3 * flowgrid_cal_factor * (val / 25.4 * metric['P_duct'].n / (data['FLUEtemp'][n] + 273.15)) ** 0.5  # convert val from Pa to inH2O

                try:
                    data[name].append(result.n)
                except:
                    data[name].append(result)

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
            io.write_timeseries(phaseoutputpath,names,units,data)

            line='created phase time series data file with processed emissions:\n'+phaseoutputpath
            print(line)
            logs.append(line)

            #### phase average emission metrics  ####################

            #MCE
            name='MCE'
            pmetricnames.append(name)
            metricunits[name]='mol/mol'
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

            #phases.remove('full')
            if 'L1' in phases or 'L5' in phases:  # if IDC test
                name = 'carbon_in_' + phase
                metricnames.append(name)
                metricunits[name] = 'g'
                try:
                    delta_char = float(emetrics['final_pot1_mass_' + phase]) - float(emetrics['pot1_dry_mass'])
                except:
                    delta_char = 0
                try:
                    if eunits['final_pot1_mass_' + phase] == 'lb':
                        delta_char = delta_char / 2.205  # lb to kg
                except:
                    pass
                try:
                    metric[name] = ((wood_Cfrac * float(emetrics['fuel_dry_mass_' + phase])) - (
                            0.81 * delta_char)) * 1000  # kg to g
                except:
                    metric[name] = ''
            else:
                name = 'carbon_in_' + phase
                metricnames.append(name)
                metricunits[name] = 'g'
                try:
                    metric[name] = (wood_Cfrac * emetrics['fuel_dry_mass_' + phase] - 0.81 * emetrics[
                        'char_mass_' + phase]) * 1000
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
    if pmetric['MSC'] != 3:
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
    
    io.write_constant_outputs(alloutputpath,allnames,allunits,allval,allunc,alluval)
    
    line='\ncreated all metrics output file:\n'+alloutputpath
    print(line)
    logs.append(line)    
    
    #print to log file
    io.write_logfile(logpath,logs)

    #CHANGE HERE 
    return allnames,allunits,allval,allunc,alluval
    
#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    LEMS_EmissionCalcs(inputpath,energypath,gravinputpath,aveinputpath,emisoutputpath,alloutputpath,logpath)