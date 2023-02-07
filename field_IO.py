
def load_timeseries_with_header(Inputpath):
    # function loads in raw time series data csv input file from sensor box with header and startup diagnostics. Stores variable names, units, header parameters, and time series data in dictionaries
    # Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData.csv

    names = []  # list of variable names
    units ={}  # dictionary keys are variable names, values are units A={}  # dictionary keys are variable names, values are A parameters (span)
    B={} # dictionary keys are variable names, values are B parameters (offset)
    C={}  #   dictionary keys are variable names, values are C parameters (constant variable names)
    D={}  #   dictionary keys are variable names, values are D parameters (constant variable values)
    const = {}  # dic  ionary keys are constant variable names(C parameters), values are constant variable values (D parameters)
    data = {}  # dic  ionary keys are variable names, values are time series as a list

    # load input file
    stuff=[]
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # find the row indices for the header and the data
    for n,row in enumerate(stuff[:100]):  # ite  ate through first 101 rows to look for the header
        if row[0] == '#A:':
            Arow = n
        if row[0] == '#B:':
            Brow = n
        if row[0] == '#C:':
            Crow = n
        if row[0] == '#D:':
            Drow = n
        if row[0] == '#units:':
            unitsrow = n
        if row[0] == 'time':
            namesrow = n

    datarow = namesrow + 1

    names=stuff [ namesrow]
    for n, name in enumerate(names):
        units[name]=stuff [ unitsrow][n]
        data[name]=[x[n] for x in stuff[datarow:]]
        for m,val in enumerate(data[name]):
            try:
                data[name][m]=float(data[name][m])
            except:
                pass
        try:
            A[name]=float(stuff[Arow][n])
        except:
            A[name]=stuff[Arow][n]
        try:
            B[name]=float(stuff[Brow][n])
        except:
            B[name]=stuff[Brow][n]
        try:
            C[name]=float(stuff[Crow][n])
        except:
            C[name]=stuff[Crow][n]
        try:
            D[name]=float(stuff[Drow][n])
        except:
            D[name]=stuff[Drow][n]

        # define the constant parameters (names are C parameters, values are D parameters)
        if type(C[name]) is str:
            const[C[name]] = D[name]

    return names,units,data,A,B ,C,D, const

# #####


###############################################################

def load_header(Inputpath):
    # function loads in header from raw time series data csv input file or header input file. Stores variable names, units, header parameters in dictionaries
    # same as load_timeseries_with_header() but without data series
    # Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData.csv

    names = []  # list   f variable names
    units={}  #   di  nary keys are variable names, values are units
    A={} # dictio  eys are variable names, values are A parameters (span)
    B={}  # diction a ry keys are variable names, values are B parameters (offset)
    C={}  # diction a ry keys are variable names, values are C parameters (constant variable names)
    D={}  # diction a ry keys are variable names, values are D parameters (constant variable values)
    const = {}  # dictionary   eys are constant variable names(C parameters), values are constant variable values (D parameters)

    # load input file
    stuff=[]
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    # find the row indices for the header and the data
    for n,row in enumerate(stuff[:100]):  # iterate thr  ugh first 101 rows to look for the header
        if row[0] == '#A:':
            Arow = n
        if row[0] == '#B:':
            Brow = n
        if row[0] == '#C:':
            Crow = n
        if row[0] == '#D:':
            Drow = n
        if row[0] == '#units:':
            unitsrow = n
        if row[0] == 'time':
            namesrow = n

    names=stuff[namesrow]
    for n,name in enumerate(names):
        units[name]=stuff[unitsrow][n]
        try:
            A[name]=float(stuff[Arow][n])
        except:
            A[name]=stuff[Arow][n]
        try:
            B[name]=float(stuff[Brow][n])
        except:
            B[name]=stuff[Brow][n ]
        try:
            C[name]=float(stuff[Crow][n])
        except:
            C[name]=stuff[Crow][n ]
        try:
            D[name]=float(stuff[Drow][n])
        except:
            D[name]=stuff[Drow][n ]

        # define the constant parameters (names are C parameters, values are D parameters)
        if type(C[name]) is str:
            const[C[name]] = D[name]

    return names,units,A,B,C,D, const

# ## ## ## #####


############################################################################

def load_timeseries(Inputpath):
    # function loads in time series data from csv input file and stores variable names, units, and time series in dictionaries
    # Input: Inputpath: csv file to load. example: C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_RawData.csv

    names = []  # list of var  able names
    units={}  # dicti o na  eys are variable names, values are units
    data = {}  # dictionary   eys are variable names, values are time series as a list

    # load input file
    stuff=[]
    with open(Inputpath) as f:
        reader = csv.reader(f)
        for row in reader:
            stuff.append(row)

    names=stuff[0]  #   first ro   channel names
    for n, name in enumerate(names):
        units[name]=stuff[1][n]  #   second row   s units
        data[name]=[x[n] for x in stuff[2:]]  # data series
        for m,val in enumerate(data[name]):
            try:
                data[name][m]=float(data[name][m])
            except:
                pass

    return names,units,data
### ###### ##############################################################
