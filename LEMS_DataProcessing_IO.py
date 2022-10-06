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

from uncertainties import ufloat
import csv
from openpyxl import load_workbook
import xlrd

#####################################################################
def load_inputs_from_spreadsheet(Inputpath):
    #do: add case for opening xls files using xlrd
    
    #function reads in spreadsheet (data entry form) and stores variable names, units, and values in dictionaries
    #Input: Inputpath: spreadsheet file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_TE_DataEntryForm.xlsx
    
    names = [] #list of variable names
    units={}    #dictionary keys are variable names, values are units
    val={}      #dictionary keys are variable names, values are variable values
    nom={}  #dictionary keys are variable names, values are variable nominal values 
    unc={}  #dictionary keys are variable names, values are variable uncertainty values
    
    #make header line and store in dictionary
    name='variable_name'
    names.append(name)
    units[name] = 'units'
    val[name]= 'value'
    unc[name]='uncertainty'
    
    wb = load_workbook(filename = Inputpath, data_only=True)    #load spreadsheet
    sheet=wb.active #grab first sheet
    
    #iterate through all cells in the sheet. Find 'label' as reference point to read in cells
    grabvals = 0    #flag to read in cells after 'label' is found
    colnum=0    #initialize column number
    for col in sheet.iter_cols():   #for each column in the sheet
        colnum=colnum+1
        rownum=0    #initialize row number
        for cell in col:    #for each cell in the column
            rownum = rownum+1
            if grabvals == 1:   #if the cell should be read in
                if cell.value is None:  #if cell is blank then stop reading in cell values
                    grabvals = 0
                else:   #if cell is not blank then read it in
                    name=cell.value
                    names.append(name)
                    units[name] = sheet.cell(row=rownum, column=units_colnum).value 
                    val[name] = sheet.cell(row=rownum, column=colnum-1).value    #variable value is one cell to the left of the label
                    #nom[name] = sheet.cell(row=rownum, column=colnum-2).value    #if spreadsheet includes uncertainty cells, nominal value is 2 cells left of label
                    #unc[name] = sheet.cell(row=rownum, column=colnum-1).value     #if spreadsheet includes uncertainty cells, uncertainty value is 1 cell left of label            
            if cell.value == 'label':
                grabvals = 1 #start reading in cells
                #find the units column (the location varies)
                for n in range(colnum,0,-1):    #for each column to the left of label
                    nextcell=sheet.cell(row=rownum, column=n).value #read the cell
                    if nextcell in ['Units','units']:   #if it is the units column
                        units_colnum= n                 #record the column number
                        break
                        
    return names,units,nom,unc,val                #type: list, dict, dict, dict, dict
#####################################################################
def load_constant_inputs(Inputpath):
    #function loads in variables from csv input file and stores variable names, units, and values in dictionaries
    #Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_EnergyInputs.csv
    
    names = [] #list of variable names
    units={}    #dictionary keys are variable names, values are units
    val={}      #dictionary keys are variable names, values are variable values
    nom={}  #dictionary keys are variable names, values are variable nominal values 
    unc={}  #dictionary keys are variable names, values are variable uncertainty values
    
    #load input file
    stuff=[]
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)
        
    #put inputs in a dictionary    
    for row in stuff:
        name=row[0]
        units[name]=row[1]
        nom[name]=row[2]
        unc[name]=row[3]
        try:
            val[name]=ufloat(row[2],row[3])
        except:
            val[name]=row[2]
        names.append(name)
            
    return names,units,nom,unc,val
#######################################################################
def write_constant_outputs(Outputpath,Names,Units,Nom,Unc,Val):
    #function writes output variables from dictionaries to to csv output file
    #Inputs:
        #Outputpath: output csv file that will be created. example:  C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_EnergyOutputs.csv
        #Names: list of variable names
        #units: dictionary keys are variable names, values are units
        #val: dictionary keys are variable names, values are variable values
        #nom: dictionary keys are variable names, values are variable nominal values 
        #unc: dictionary keys are variable names, values are variable uncertainty values
    
    #store data as a list of lists to print by row
    for name in Names:
        try:                                                    #see if a nominal value exists
            Nom[name]
        except:                                             #if not then 
            try:                                                #try getting the nominal value from the ufloat
                Nom[name]=Val[name].n
            except:                                        #and if that doesn't work then define the nominal value as the single value
                Nom[name]=Val[name]
        try:                                                   #see if uncertainty value exists
            Unc[name]
        except:                                             #if not then
            try:                                                #try getting the uncertainty value from the ufloat
                Unc[name]=Val[name].s
            except:
                Unc[name]=''                            #and if that doesn't work then define the uncertainty value as blank
    
    output=[]                                               #initialize list of lines
    for name in Names:                           #for each variable
        row=[]                                               #initialize row
        row.append(name)
        row.append(Units[name])
        row.append(Nom[name])
        row.append(Unc[name])
        output.append(row)                          #add the row to output list

    #print to the output file
    with open(Outputpath,'w',newline='') as csvfile: 
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)
########################################################################
def write_logfile(Logpath,Logs):
    #writes to logfile.txt to document data manipulations
    #Inputs: 
    #Logpath: logfile.txt path. example:  C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_log.txt
    #Logs: list of lines that will get logged to the file
    with open(Logpath, 'a') as logfile: 
        for log in Logs:
            logfile.write('\n'+log)
#######################################################################
