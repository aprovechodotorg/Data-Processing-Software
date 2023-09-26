
inputpath = ["C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2.csv",
             "C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2_averages.csv"]

outputpath = 'C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL3.csv'
import csv
import os
import math
#import LEMS_IO_Test_L3 as io
import LEMS_DataProcessing_IO as io
import statistics
from scipy import stats

def LEMS_FormatData_L3(inputpath, outputpath):

    header = ['units']
    data_values = {}
    test = []
    units = {}
    names = []

    x = 0
    for path in inputpath:

        #Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        #load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        for n, name in enumerate(new_names):
            if name not in names:
                names.insert(n, name)
                units[name] = new_units[name]

    for path in inputpath:
        #load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        #metric = {'average': {}, 'N': {}, 'stdev': {}, 'confidence': {}, 'high_tier': {}, 'low_tier': {}, 'COV': {}, 'CI': {}}

        if (x == 0): #If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    #print(data["average"][name])
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"]],
                                         "High Tier": [data["High Tier"][name]], "Low Tier": [data["Low Tier"][name]],
                                         "COV": [data["COV"][name]], "CI": [data["CI"][name]]}
                except:
                    data_values[name] = {"units": '', "values": [''], "average": [''], "confidence": [''], "N": [''],
                                         "stdev": [''], "High Tier": [''], "Low Tier": [''], "COV": [''], "CI": ['']}
        else:
            for name in names: #append values to dictionary
                try:
                    data_values[name]["values"].append(values[name])
                    data_values[name]["average"].append(data["average"][name])
                    data_values[name]["confidence"].append(data["Interval"][name])
                    data_values[name]["N"].append(data["N"][name])
                    data_values[name]["stdev"].append(data["stdev"][name])
                    data_values[name]["High Tier"].append(data["High Tier"][name])
                    data_values[name]["Low Tier"].append(data["Low Tier"][name])
                    data_values[name]["COV"].append(data["COV"][name])
                    data_values[name]["CI"].append(data["CI"][name])
                except:
                    data_values[name]["values"].append('')
                    data_values[name]["average"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
                    data_values[name]["High Tier"].append('')
                    data_values[name]["Low Tier"].append('')
                    data_values[name]["COV"].append('')
                    data_values[name]["CI"].append('')
        x += 1

    average = {}
    N = {}
    stadev = {}
    interval = {}
    high_tier = {}
    low_tier = {}
    COV = {}
    CI = {}

    # Add headers for additional columns of comparative data
    header.append("average")
    header.append("N")
    header.append("stadev")
    header.append("Interval")
    header.append("High Tier Estimate")
    header.append("Low Tier Estimate")
    header.append("COV")
    header.append("CI")

    statistic_names = ['average', 'confidence'] #list of statistics we're interested in printing out

    for variable in data_values: #For each of the variables being measured
        #num_list = [] #Create a place holder list to store values

        for statsn in statistic_names:
            num_list = []
            for value in data_values[variable][statsn]: #For each data point for each varible average for each stove
                if value == '': #skip over blank celss
                    pass
                elif value == 'nan':
                    pass
                else:
                    try: #Test if the value is a number. Only add it if it's a number
                        num_list.append(float(value))
                    except:
                        pass
            if variable == 'Basic Operation' or variable == 'Total Emissions':
                average[variable] = 'average'

            else:
                try:
                    average[variable] = round(sum(num_list) / len(num_list), 3)
                except:
                    average[variable] = math.nan

            statname = 'average' + statsn
            data_values[variable].update({statname: average[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                N[variable] = 'N'
            else:
                N[variable] = len(num_list)
            statname = 'N' + statsn
            data_values[variable].update({statname: N[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                stadev[variable] = 'stadev'
            else:
                try:
                    stadev[variable] = round(statistics.stdev(num_list), 3)
                except:
                    stadev[variable] = math.nan
            statname = 'stadev' + statsn
            data_values[variable].update({statname: stadev[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                interval[variable] = 'Interval'
            else:
                try:
                    interval[variable] = ((stats.t.ppf(1 - 0.05, (N[variable] - 1))))
                    interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
                except:
                    interval[variable] = math.nan

            statname = 'interval' + statsn
            data_values[variable].update({statname : interval[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                high_tier[variable] = 'High Tier Estimate'
                low_tier[variable] = 'Low Tier Estimate'
            else:
                high_tier[variable] = round((average[variable] + interval[variable]), 3)
                low_tier[variable] = round((average[variable] - interval[variable]), 3)
            statname = 'high_tier' + statsn
            data_values[variable].update({statname: high_tier[variable]})
            statname = 'low_tier' + statsn
            data_values[variable].update({statname: low_tier[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                COV[variable] = 'COV'
            else:
                try:
                    COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)
                except:
                    COV[variable] = math.nan
            statname = 'COV' + statsn
            data_values[variable].update({statname: COV[variable]})

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                CI[variable] = 'CI'
            else:
                CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
            statname = 'CI' + statsn
            data_values[variable].update({statname: CI[variable]})


    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Reprint header to specify section (really you just need the section title but having the other column callouts
        # repeated makes it easier to read
        for statsn in statistic_names:
            header.insert(0, statsn)
            writer.writerow(header)
            header.remove(statsn)

            aname = 'average' + statsn
            Nname = 'N' + statsn
            sname = 'stadev' + statsn
            iname = 'interval' + statsn
            hname = 'high_tier' + statsn
            lname = 'low_tier' + statsn
            COVname = 'COV' + statsn
            CIname = 'CI' + statsn
            # Write units, values, and comparative data for all varaibles in all tests
            for variable in data_values:
                writer.writerow([variable, data_values[variable]["units"]]
                                + data_values[variable][statsn]
                                + [data_values[variable][aname]]
                                + [data_values[variable][Nname]]
                                + [data_values[variable][sname]]
                                + [data_values[variable][iname]]
                                + [data_values[variable][hname]]
                                + [data_values[variable][lname]]
                                + [data_values[variable][COVname]]
                                + [data_values[variable][CIname]])
        #for dictionary in full:
            #for variable in full[dictionary]:
                #print(full[dictionary][variable]["units"])
                #writer.writerow([variable, full[dictionary][variable]["units"]]
                                #+ [full[dictionary][variable]["average"]])
        csvfile.close()
        '''
        t = 0
        #print(path)
        while t < 2:
            if t == 0:
                print('test')
                path = path + calcs[t]
            else:
                print(path)
                path = path.replace(calcs[t-1], calcs[t])

            directory, filename = os.path.split(path)
            datadirectory, testname = os.path.split(directory)
            header.append(testname)

            with open(path) as f:
                data_values = json.load(f)
            # data_values = ast.literal_eval(data_values)

            if (x == 0):
                for each in data_values:
                    print(each)
                    L3[each] = {"units": units[each], "values": [values[each]], "average": []}
            else:
                for name in copied_values:
                    data_values[name]["values"].append(values[name])
            x += 1

            if t == 0:
                with open(outputpath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Add the header to the outputfile
                    writer.writerow(header)
                    # Write units, values, and comparative data for all varaibles in all tests
                    for variable in data_values:
                        # print(data_values[variable]["average"])
                        writer.writerow([variable, data_values[variable]["units"]]
                                        + [data_values[variable]["average"]])
            else:
                with open(outputpath, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Add the header to the outputfile
                    writer.writerow(header)
                    # Write units, values, and comparative data for all varaibles in all tests
                    for variable in data_values:
                        # print(data_values[variable]["average"])
                        writer.writerow([variable, data_values[variable]["units"]]
                                        + [data_values[variable]["average"]])

            t += 1
            '''


###################################################################### the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_FormatData_L3(inputpath, outputpath)