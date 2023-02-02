import statistics

inputpath = ['Data/FormattedDataL2.csv',
             'Data/yatzo alcohol/yatzo_L2_FormattedData.csv '
             ]
outputpath = 'Data/L3_data.csv'

import json
import csv
import os
import LEMS_IO_Test_L3 as io

def LEMS_FormatData_L3(inputpath, outputpath):

    #calcs = ['_EnergyCalcs.json', '_BasicOps.json']

    # Populate header
    header = ['ISO Performance Metrics (Weighted Mean)', 'units']

    data_values = {}
    #full = {}
    test = []

    x = 0
    for path in inputpath:


        #Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        #load in inputs from each energyoutput file
        [names, units, values, average] = io.LEMS_IO_test_L3(path)
        average_t = {}
        N = {}
        stadev = {}
        interval = {}
        high_tier = {}
        low_tier = {}
        COV = {}
        CI = {}

        if (x == 0):
            for name in names:
                data_values[name] = {"units": units[name], "values": [values[name]], "test average": [average[name]]}
        else:
            for name in names:
                data_values[name]["values"].append(values[name])
                data_values[name]["test average"].append(average[name])
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

    for variable in data_values:
        num_list = []

        for value in data_values[variable]["values"]:
            if value == '':
                error = 1
            else:
                num_list.append(float(value))

        try:
            average[variable] = round(sum(num_list)/len(num_list), 3)
        except:
            average[variable] = math.nan

        data_values[variable].update({"average": average[variable]})

        N[variable] = len(num_list)
        data_values[variable].update({"N" : N[variable]})

        try:
            stadev[variable] = round(statistics.stdev(num_list), 3)
        except:
            stadev[variable] = math.nan

        data_values[variable].update({"stdev" : stadev[variable]})

        try:
            interval[variable] = ((stats.t.ppf(1-0.05, (N[variable] -1 ))))
            interval[variable] = round(interval[variable] * stadev[variable] / pow(N[variable], 0.5), 3)
        except:
            interval[variable] = math.nan

        data_values[variable].update({"interval" : interval[variable]})

        high_tier[variable] = round((average[variable] + interval[variable]), 3)
        low_tier[variable] = round((average[variable] - interval[variable]), 3)

        data_values[variable].update({"high_tier": high_tier[variable]})
        data_values[variable].update({"low_tier": low_tier[variable]})

        COV[variable] = round(((stadev[variable] / average[variable]) * 100), 3)

        data_values[variable].update({"COV": COV[variable]})

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
                            + [data_values[variable]["test average"]])
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