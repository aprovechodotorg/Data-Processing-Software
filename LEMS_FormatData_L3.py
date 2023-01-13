

inputpath = ["Data/yatzo alcohol/L2_dict"]
outputpath = 'Data/L3_data.csv'

import json
import csv
import os

def LEMS_FormatData_L3(inputpath, outputpath):

    calcs = ['_EnergyCalcs.json', '_BasicOps.json']

    # Populate header
    header = ['Basic Operation', 'units']

    for path in inputpath:
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


###################################################################### the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_FormatData_L3(inputpath, outputpath)