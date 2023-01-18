

inputpath = ['Data/yatzo alcohol/yatzo_L2_FormattedData.csv']
outputpath = 'Data/L3_data.csv'

import json
import csv
import os
import LEMS_IO_Test_L3 as io

def LEMS_FormatData_L3(inputpath, outputpath):

    calcs = ['_EnergyCalcs.json', '_BasicOps.json']

    # Populate header
    header = ['ISO Performance Metrics (Weighted Mean)', 'units']

    data_values = {}
    full = {}
    test = []

    for path in inputpath:

        x = 0


        #Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        #load in inputs from each energyoutput file
        [names, units, values, average] = io.LEMS_IO_test_L3(path)


        if (x == 0):
            for name in names:
                data_values[name] = {"units": units[name], "values": [values[name]], "average": [average[name]]}
        else:
            for name in names:
                data_values[name]["values"].append(values[name])
        x += 1

        print(data_values)
        full[testname] = data_values
        print(full)

        #full[testname].append(data_values)
    #for variable in data_values:

    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Reprint header to specify section (really you just need the section title but having the other column callouts
        # repeated makes it easier to read
        writer.writerow(header)
        # Write units, values, and comparative data for all varaibles in all tests
        for name in test:
            print(name)
            for variable in full[testname]:
                print(full[name][variable]["units"])
                writer.writerow([variable, data_values[name][variable]["units"]]
                                + [data_values[name][variable]["average"]])
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