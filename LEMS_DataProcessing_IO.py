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

#####################################################################
def load_inputs_from_spreadsheet(Inputpath):
    
    names = []
    units={}
    val={}
    nom={}
    unc={}
    #make header line and store in dictionary
    name='variable_name'
    names.append(name)
    units[name] = 'units'
    val[name]= 'value'
    unc[name]='uncertainty'
    
    wb = load_workbook(filename = Inputpath, data_only=True)
    sheet=wb.active
    
    grabvals = 0
    colnum=0
    for col in sheet.iter_cols():
        colnum=colnum+1
        rownum=0
        for cell in col:
            rownum = rownum+1
            if grabvals == 1:
                if cell.value is None:
                    grabvals = 0
                else:
                    name=cell.value
                    names.append(name)
                    units[name] = sheet.cell(row=rownum, column=units_colnum).value
                    val[name] = sheet.cell(row=rownum, column=colnum-1).value    
                    #nom[name] = sheet.cell(row=rownum, column=colnum-2).value    
                    #unc[name] = sheet.cell(row=rownum, column=colnum-1).value                      
            if cell.value == 'label':
                grabvals = 1
                for n in range(colnum,0,-1):
                    nextcell=sheet.cell(row=rownum, column=n).value
                    if nextcell in ['Units','units']:
                        units_colnum= n
                        break
                        
    return names,units,nom,unc,val                
#####################################################################
def load_constant_inputs(Inputpath):

    names = []
    units={}
    val={}
    nom={}
    unc={}
    
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
 #store data as a list of lists to print by row
    
    for name in Names:
        try:
            Nom[name]
        except:
            try:
                Nom[name]=Val[name].n
            except:
                Nom[name]=Val[name]
        try: 
            Unc[name]
        except:
            try:
                Unc[name]=Val[name].s
            except:
                Unc[name]=''
    
    output=[]
    for name in Names:
        row=[]  
        row.append(name)
        row.append(Units[name])
        row.append(Nom[name])
        row.append(Unc[name])
        output.append(row)  

    #print to the output file
    with open(Outputpath,'w',newline='') as csvfile: 
        writer = csv.writer(csvfile)
        for row in output:
            writer.writerow(row)
########################################################################
def write_logfile(Logpath,Logs):
    with open(Logpath, 'a') as logfile: 
        for log in Logs:
            logfile.write('\n'+log)
#######################################################################
