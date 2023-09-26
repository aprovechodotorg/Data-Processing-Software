import statistics
inputpath = ["C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2.csv",
             "C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2_averages.csv"]

outputpath = 'C:\\Users\\Jaden\\Documents\\HH_full\\FormattedDataL2.csv'
import csv
import os
import math
#import LEMS_IO_Test_L3 as io
import LEMS_DataProcessing_IO as io

def LEMS_FormatData_L3(inputpath, outputpath):

    # Populate header
    header = ['ISO Performance Metrics (Weighted Mean)', 'units']

    data_values = {}
    #full = {}
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

        sumaverage = {}
        sumN = {}
        sumstadev = {}
        suminterval = {}
        sumhigh_tier = {}
        sumlow_tier = {}
        sumCOV = {}
        sumCI = {}

        if (x == 0): #If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]], "data": [data[name]]}
                except:
                    data_values[name] = {"units": '', "values": '', "data": ''}
        else:
            for name in names: #append values to dictionary
                try:
                    data_values[name]["values"].append(values[name])
                    data_values[name]["data"].append(data[name])
                except:
                    data_values[name]["values"].append('')
                    data_values[name]["data"].append('')
        x += 1

    # Add headers for additional columns of comparative data
    header.append("average")
    header.append("N")
    header.append("stdev")
    header.append("Interval")
    header.append("High Tier Estimate")
    header.append("Low Tier Estimate")
    header.append("COV")
    header.append("CI")

    for variable in data_values: #For each of the variables being measured
        num_list = [] #Create a place holder list to store values

        for value in data_values[variable]["test average"]: #For each data point for each varible average for each stove
            if value == '': #skip over blank celss
                pass
            else:
                try: #Test if the value is a number. Only add it if it's a number
                    num_list.append(float(value))
                except:
                    pass
                if variable == 'Basic Operation' or variable == 'Total Emissions':
                    average_t[variable] = 'average'

                else:
                    try:
                        average_t[variable] = round(sum(num_list) / len(num_list), 3)
                        # print(average[variable])
                    except:
                        average_t[variable] = math.nan

        data_values[variable].update({"average": average_t[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            N[variable] = 'N'
        else:
            N[variable] = len(num_list)
        data_values[variable].update({"N" : N[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            stadev[variable] = 'stdev'
        else:
            try:
                stadev[variable] = round(statistics.stdev(num_list), 3)
            except:
                stadev[variable] = math.nan

        data_values[variable].update({"stdev" : stadev[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            interval[variable] = 'Interval'
        else:
            try:
                interval[variable] = ((stats.t.ppf(1 - 0.05, (N[variable] - 1))))
                interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
            except:
                interval[variable] = math.nan

        data_values[variable].update({"interval" : interval[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            high_tier[variable] = 'High Tier Estimate'
            low_tier[variable] = 'Low Tier Estimate'
        else:
            high_tier[variable] = round((average_t[variable] + interval[variable]), 3)
            low_tier[variable] = round((average_t[variable] - interval[variable]), 3)

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            COV[variable] = 'COV'
        else:
            try:
                COV[variable] = round(((stadev[variable] / _t[variable]) * 100), 3)
            except:
                COV[variable] = math.nan
        data_values[variable].update({"COV": COV[variable]})

        if variable == 'Basic Operation' or variable == 'Total Emissions':
            CI[variable] = 'CI'
        else:
            CI[variable] = str(high_tier[variable]) + '-' + str(low_tier[variable])
        data_values[variable].update({"CI": CI[variable]})



        #print(data_values)
        #full[testname] = data_values
        #print(full)

        #full[testname].append(data_values)
    #for variable in data_values:

    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Reprint header to specify section (really you just need the section title but having the other column callouts
        # repeated makes it easier to read
        writer.writerow(header)
        # Write units, values, and comparative data for all varaibles in all tests
        for variable in data_values:
            writer.writerow([variable, data_values[variable]["units"]]
                            + data_values[variable]["test average"]
                            + [data_values[variable]["average"]]
                            + [data_values[variable]["N"]]
                            + [data_values[variable]["stdev"]]
                            + [data_values[variable]["interval"]]
                            + [data_values[variable]["high_tier"]]
                            + [data_values[variable]["low_tier"]]
                            + [data_values[variable]["COV"]]
                            + [data_values[variable]["CI"]])
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