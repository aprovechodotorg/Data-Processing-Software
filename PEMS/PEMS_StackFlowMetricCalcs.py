#v0.2 Python3

#    Copyright (C) 2022 Mountain Air Engineering 
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



import LEMS_DataProcessing_IO as io
import numpy as np
from uncertainties import ufloat
from datetime import datetime as dt

#########      inputs      ##############
#
logpath='C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'
##########################################

def PEMS_StackFlowMetricCalcs(inputpath,energypath,carbalpath,metricpath,logpath):
    
    ver = '0.2'     #for Apro
        #vo.2: handles inputs with and without unc
    timestampobject=dt.now()    #get timestamp from operating system for log file
    timestampstring=timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_StackFlowMetricCalcs v'+ver+'   '+timestampstring
    print(line)
    logs=[line]
    
    metricnames=[]
    val={}
    unc={}
    metric={}

    possible_emissions=['CO','COhi','CO2','CO2hi','NO','NO2','HC','VOC','CH4','PM','C']     #possible emission species that will get metric calculations
    emissions = [] #emission species that will get metric calculations, defined after channel names are read from time series data file
    
    Tstd=float(293)     #define standard temperature in Kelvin
    Pstd=float(101325)   #define standard pressure in Pascals
    R=float(8.314)     #universal gas constant (m^3Pa/mol/K)
    
    MW={}
    MW['C']=float(12.01)    # molecular weight of carbon (g/mol)
    MW['CO']=float(28.01)   # molecular weight of carbon monoxide (g/mol)
    MW['COhi']=float(28.01)   # molecular weight of carbon monoxide (g/mol)
    MW['CO2']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['CO2hi']=float(44.01)   # molecular weight of carbon dioxide (g/mol)
    MW['SO2']=float(64.07)   # molecular weight of sulfur dioxide (g/mol)
    MW['NO']=float(30.01)   # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2']=float(46.01)   # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S']=float(34.1)   # molecular weight of hydrogen sulfide (g/mol)
    MW['HxCy']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['HC']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['VOC']=float(56.11)   # molecular weight of isobutylene (g/mol)
    MW['CH4']=float(16.04) # molecular weight of methane (g/mol)
    MW['air']=float(29) #molecular weight of air (g/mol)

    timestep = 1  #time step for emission rate integration, add code to read dt from time series
    
    #load stack flow time series data file (test period)
    [names,units,data]=io.load_timeseries_with_uncertainty(inputpath)
    #[names,units,data]=io.load_timeseries(inputpath)   #use this if time series input file does not have uncertainty
    

    line = 'Loaded time series data:'+inputpath
    print(line)
    logs.append(line)
    
    #load energy metrics data file
    [enames,eunits,eval,eunc,emetric]=io.load_constant_inputs(energypath)
    
    line = 'Loaded energy metrics:'+energypath
    print(line)
    logs.append(line)
           
    #load carbon balance emission metrics
    [cbnames,cbunits,cbval,cbunc,cbmetric]=io.load_constant_inputs(carbalpath)
    
    line = 'Loaded carbon balance emission metrics:'+carbalpath
    print(line)
    logs.append(line)
    
    ################################################
    #define emission species that will get metric calculations
    for name in possible_emissions:
        ername = 'ER'+name+'stak'
        if ername in names:
            emissions.append(name)
    
    #################################################
    #calculate metrics
    
    #total emissions
    for em in emissions:
        name= 'Mass_'+em
        metricnames.append(name)
        ername = 'ER'+em + 'stak'
        units[name] = 'g'
        
        #integrate the emission rate series
        summ = float(0) #initialize cumulative sum 
        unclist=[]  #initializer series of uncertainty values
        for n,er in enumerate(data[ername]):
            summ = summ + er/3600*timestep
            try:    #if ufloat
                unclist.append(er.s)
            except: #if not ufloat
                pass
        if len(unclist) == 0:   #if no uncertainty
            uncle = float(0)    
        else:
            uncle = sum(unclist)/len(unclist)   #unc assuming perfect correlation between time series values
            
        if em == 'PM' or em == 'OC' or em == 'EC' or em == 'TC':
            metric[name]=ufloat(summ,uncle)/1000    #convert mg to g
        else:
            metric[name]=ufloat(summ,uncle)
        
        print(name)
        print(metric[name])
        
    try:
        metric['Mass_OC'] = metric['Mass_PM']*cbmetric['OC/PM']
        metric['Mass_EC'] = metric['Mass_PM']*cbmetric['EC/PM']
        metric['Mass_TC'] = metric['Mass_PM']*cbmetric['TC/PM']
    except:
        pass
        
    #average emission rates
    for em in emissions:
        name= 'ER_'+em + '_stak'
        units[name] = 'g/hr'
        metricnames.append(name)
        massname = 'Mass_'+em
        try:
            metric[name]=metric[massname]*3600/len(data['time'])
        except:
            metric[name] = ''
            
    #Emission factor, fuel mass based
    for em in emissions:
        name = 'EFmass_'+em+'_stak'
        metricnames.append(name)
        units[name] = 'g/kg'
        massname = 'Mass_'+em
        try:
            metric[name] = metric[massname]/emetric['fuel_mass']
        except:
            metric[name] = ''
        
    #Emission factor, dry fuel mass based
    for em in emissions:
        name = 'EFmass_dry_'+em+'_stak'
        metricnames.append(name)
        units[name] = 'g/kg'
        massname = 'Mass_'+em
        try:
            metric[name] = metric[massname]/emetric['fuel_dry_mass']
        except:
            metric[name] = ''
  
    #Emission factor, fuel energy based
    for em in emissions:
        name = 'EFenergy_'+em+'_stak'
        metricnames.append(name)
        units[name] = 'g/MJ'
        massname = 'Mass_'+em
        try:
            metric[name] = metric[massname]/emetric['fuel_energy']
        except:
            metric[name] = ''

    name = 'Firepower'
    metricnames.append(name)
    units[name] = 'W'
    metric[name] = sum(data[name]) / len(data[name])

    name = 'UsefulPower'
    metricnames.append(name)
    units[name] = 'W'
    metric[name] = sum(data[name]) / len(data[name])

    name = 'ThermalEfficiency'
    metricnames.append(name)
    units[name] = '%'
    metric[name] = (metric['UsefulPower'] / metric['Firepower']) * 100

    #make header for output file:
    name = 'variable_name'
    metricnames = [name]+metricnames
    units[name]='units'
    val[name] = 'value'
    unc[name]='unc'
    
    #print metrics output file
    io.write_constant_outputs(metricpath,metricnames,units,val,unc,metric)
    
    line='\ncreated emission metrics output file:\n'+metricpath
    print(line)
    logs.append(line)    
    
    #print to log file
    io.write_logfile(logpath,logs)

#######################################################################
#run function as executable if not called by another function    
if __name__ == "__main__":
    PEMS_StackFlowMetricCalcs(inputpath,energypath,carbalpath,metricpath,logpath)