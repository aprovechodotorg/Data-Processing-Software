import csv


inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\LEMS-Data-Processing\\PEMS\\Data\\Partial\\GP0021.2.24.23.csv'
inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\LEMS-Data-Processing\\PEMS\\Data\\Partial\\GP0021.2.24.23_Processed.csv'
def partPEMS_Process_File(inputpath, outputpath):
    # load input file
    stuff = []
    with open(inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # find the row indices for the header and the data
    for n, row in enumerate(stuff[:100]):  # iterate through first 101 rows to look for the header
        if row[0] == '#0':
            multirow = n
        if row[0] == 'seconds':
            namesrow = n

    datarow = namesrow+1

    names = stuff[namesrow]