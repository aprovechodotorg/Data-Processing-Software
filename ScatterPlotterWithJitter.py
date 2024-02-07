#python 3

import csv
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from uncertainties import ufloat
import LEMS_DataProcessing_IO as io

#this function makes 1 D scatter plot (like a box plot)
#it plots the individual averages for each event within each group, and total averages, and arithmetic averages

data = {}
jitter = 0.05
#x= [,1,2,3,1+jitter,2+jitter,3+jitter]

testnames = ['pile1','pile2','pile3','pile4','pile5','pile6','pile7','pile8','pile9']
for testname in testnames:
    metricpath = 'C:\Mountain Air\Projects\\biochar\cornstalks\data\\'+testname+'\\'+testname+'_EmissionOutputs.csv'
    print(metricpath)
    [names,units,val,unc,uval] = io.load_constant_inputs(metricpath)
    data[testname] = uval
    
rep1 = ['pile2','pile1','pile3']    #group of test replicates
rep2 = ['pile5','pile4','pile6']    #group of test replicates
rep3 = ['pile7','pile8','pile9']    #group of test replicates
    
#metricnames = ['EFmass_dry_PM_fed','EFmass_dry_CO_fed','EFmass_dry_CH4_fed']
metric = 'EFmass_dry_PM_fed'
#ylabelstring =  'EF OC '+'('+units[metric]+')'
ylabelstring =  'EF PM (g/kg)'
#f1, (ax1, ax2, ax3) = plt.subplots(3) 
f1, (ax1) = plt.subplots(1) 

if metric == 'EFmass_dry_OC_fed' or metric == 'EFmass_dry_TC_fed' or metric == 'EFmass_dry_PM_fed':
    for testname in testnames:
        data[testname][metric] = data[testname][metric]/1000    #convert from mg/kg to g/kg

rep1_x = [1-jitter,2-jitter,3-jitter]
rep1_y=[]
rep1_yerrbars = []
for testname in rep1:
    rep1_y.append(data[testname][metric].n)
    rep1_yerrbars.append(data[testname][metric].s)
ax1.errorbar(rep1_x, rep1_y, yerr=rep1_yerrbars, fmt="o", markersize=10,markeredgewidth=1, capsize = 10, color = 'black', label = 'corn stalks')

rep2_x = [1,2,3]
rep2_y=[]
rep2_yerrbars = []
for testname in rep2:
    rep2_y.append(data[testname][metric].n)
    rep2_yerrbars.append(data[testname][metric].s)
ax1.errorbar(rep2_x, rep2_y, yerr=rep2_yerrbars, fmt="o", markersize=10,markeredgewidth=1, color = 'black', capsize = 10)

rep3_x = [1+jitter,2+jitter,3+jitter]  #use this line for all other metrics
#rep3_x = [2+jitter,3+jitter]    #use this line for AAE (skip test 7)
rep3_y=[]
rep3_yerrbars = []
for testname in rep3:  #use this line for all other metrics
#for testname in rep3[1:]:   #use this line for AAE (skip test 7)
    rep3_y.append(data[testname][metric].n)
    rep3_yerrbars.append(data[testname][metric].s)
ax1.errorbar(rep3_x, rep3_y, yerr=rep3_yerrbars, fmt="o", markersize=10,markeredgewidth=1, capsize = 10, color = 'brown', label = 'broomcorn stalks')

ax1.set_ylabel(ylabelstring, fontsize = 20)
#ax.set_title(name)
ax1.set_xticks([1,2,3],['side lit','top lit','top lit and\nquenched'], fontsize = 20)
plt.yticks(fontsize = 15)
box = ax1.get_position()
#ax1.set_position([box.x0, box.y0, box.width * 0.9, box.height * 0.9])    #squeeze it down to make room for the legend
plt.subplots_adjust(left=0.2,bottom=0.2) #squeeze it vertically to make room for the long x axis data labels
ax1.legend(fontsize = 20)
plt.show()