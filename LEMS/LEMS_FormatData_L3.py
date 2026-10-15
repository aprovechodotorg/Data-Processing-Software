#v0.2 Python3

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

inputpath = ["C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2.csv",
             "C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL2_averages.csv"]

outputpath = 'C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\FormattedDataL3.csv'
logpath = 'C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\log.txt'

import csv
import os
import math
#import LEMS_IO_Test_L3 as io
import LEMS_DataProcessing_IO as io
import statistics
from scipy import stats
from datetime import datetime as dt
from scipy.stats import t


def _normalize_path(p):
    """Normalize file path for robust cross-platform comparison."""
    if not p:
        return ''
    return os.path.normcase(os.path.normpath(p.replace('\\', '/').strip()))


def load_pairs_test_codes(pairs_path):
    """
    Parses PairsUnformattedDataL2FilePaths.csv and returns a list of dictionaries
    representing test entries:
      [{'path': str, 'norm_path': str, 'group_dir_name': str, 'test_code': str, 'name': str, 'group': str}, ...]
    """
    if not pairs_path or not os.path.exists(pairs_path):
        return []

    entries = []
    with open(pairs_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            p = row_norm.get('path', '')
            t_code = row_norm.get('test_code', '')
            d_key = row_norm.get('data_key', '')
            name = row_norm.get('name', '')
            group = row_norm.get('group', '')

            # Resolve code: prefer test_code, fallback to data_key (if not a diff formula)
            code = t_code if t_code else (d_key if d_key and not ('/' in d_key or d_key.startswith('d')) else '')

            if p or code:
                norm_p = _normalize_path(p) if p else ''
                group_dir_name = ''
                if p:
                    parent_dir = os.path.dirname(norm_p)
                    group_dir_name = os.path.basename(parent_dir).strip().lower()

                entries.append({
                    'path': p,
                    'norm_path': norm_p,
                    'group_dir_name': group_dir_name,
                    'test_code': code,
                    'name': name.strip().lower(),
                    'group': group.strip().lower()
                })
    return entries


def find_test_code(test_path, test_idx, pairs_entries):
    """
    Finds the test_code for a given test path by matching:
    1. Exact normalized path
    2. Parent directory (group folder name, handles LP files like UnFormattedDataL2_lp.csv)
    3. Test folder name against name or group column
    4. Positional fallback
    """
    if not pairs_entries:
        return ''

    norm_t = _normalize_path(test_path)
    parent_dir_name = os.path.basename(os.path.dirname(norm_t)).strip().lower()

    # 1. Exact normalized path
    for entry in pairs_entries:
        if entry['norm_path'] and entry['norm_path'] == norm_t and entry['test_code']:
            return entry['test_code']

    # 2. Parent directory match (handles UnFormattedDataL2_lp.csv matching UnFormattedDataL2.csv)
    for entry in pairs_entries:
        if entry['group_dir_name'] and entry['group_dir_name'] == parent_dir_name and entry['test_code']:
            return entry['test_code']

    # 3. Match test folder name against name or group column
    for entry in pairs_entries:
        if parent_dir_name and (entry['name'] == parent_dir_name or entry['group'] == parent_dir_name) and entry['test_code']:
            return entry['test_code']

    # 4. Positional fallback (if test index corresponds to an entry with a test_code)
    code_entries = [e for e in pairs_entries if e['test_code']]
    if 0 <= test_idx < len(code_entries):
        return code_entries[test_idx]['test_code']

    return ''


def LEMS_FormatData_L3(inputpath, outputpath, logpath, pairs_path=None):

    #Function intakes list of inputpaths and creates comparison between values in list.
    ver = '1.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_FormatData_L3 v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    # Resolve pairs configuration file if present
    if pairs_path is None or not os.path.exists(pairs_path):
        candidate = os.path.join(os.path.dirname(outputpath), 'PairsUnformattedDataL2FilePaths.csv')
        if os.path.exists(candidate):
            pairs_path = candidate

    pairs_entries = load_pairs_test_codes(pairs_path) if pairs_path and os.path.exists(pairs_path) else []
    if pairs_entries:
        line = f"Loaded test code mapping from: {pairs_path}"
        print(line)
        logs.append(line)

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    test_codes = [] #list of short test codes
    units = {}
    names = [] #list of variable names

    x = 0
    loaded_data = []
    for idx, path in enumerate(inputpath):

        #Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        header.append(testname)
        test.append(testname)

        if pairs_entries:
            code = find_test_code(path, idx, pairs_entries)
            test_codes.append(code)

        #load in inputs from each unformattedL2 data file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)
        loaded_data.append((path, values, data))

        #Make a complete list of all variable names from all tests
        for n, name in enumerate(new_names):
            if name not in names: #If this is a new name, insert it into the ist of names
                print(f"Adding new variable: {name}")
                names.append(name)  # Changed from .insert(n, name)
                units[name] = new_units[name]

    for path, values, data in loaded_data:
        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        if (x == 0): #If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"][name]],
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

    #create dictionaries for global statistics
    average = {}
    percent = {}
    high = {}
    low = {}
    N = {}

    # Add headers for additional columns of comparative data
    header.append("average")
    header.append("Percent Change")
    header.append("Percent Change High")
    header.append("Percent Change Low")

    statistic_names = ['average', 'confidence', 'N'] #list of statistics we're interested in printing out
    #statistic_names = ['average']

    for variable in data_values: #For each of the variables being measured

        for statsn in statistic_names:
            num_list = [] #List of actual numbers (excluding blanks and strs)
            for value in data_values[variable][statsn]: #For each data point for each variable average for each stove
                if value == '': #skip over blank cells
                    pass
                elif value == 'nan': #Skip over nan cells
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
            data_values[variable].update({statname: average[variable]}) #Update with new nested dictionary

            if variable == 'Basic Operation' or variable == 'Total Emissions':
                N[variable] = 'N'
            else:
                N[variable] = len(num_list)

            if N[variable] == 2:  # For comparison of two
                try:
                    # calculate percent change
                    # %chg = (avg_final - avg_initial / avg_initial) * 100
                    #print(variable)
                    percent[variable] = round(((float(data_values[variable]["average"][1]) -
                                          float(data_values[variable]["average"][0])) /
                                         float(data_values[variable]["average"][0]))*100, 3)
                except (TypeError, ZeroDivisionError, ValueError):
                    percent[variable] = math.nan
                try:
                    # degrees of freedom
                    # N_initial + N_final - 2
                    deg_free = float(data_values[variable]["N"][0]) + float(data_values[variable]["N"][1]) - 2
                    # Critical T value at 95% confidence
                    t_crit = t.ppf(0.95, deg_free)
                except (TypeError, ValueError):
                    t_crit = math.nan
                try:
                    # standard error
                    # SE_x = standard deviation / square root (N)
                    se1 = float(data_values[variable]["stdev"][0]) / math.sqrt(float(data_values[variable]["N"][0]))
                    se2 = float(data_values[variable]["stdev"][1]) / math.sqrt(float(data_values[variable]["N"][1]))
                    # SE = absolute(avg_final/avg_initial) * square root((SE_final^2/avg_final^2) + (SE_initial^2/avg_initial^2))*100
                    se = (abs((float(data_values[variable]["average"][1])) /
                             (float(data_values[variable]["average"][0]))) *
                    math.sqrt(((se2 ** 2)/(float(data_values[variable]["average"][1]) ** 2)) +
                              ((se1 ** 2) / (float(data_values[variable]["average"][0]) ** 2)))) * 100
                except (TypeError, ZeroDivisionError, ValueError):
                    se = math.nan
                try:
                    # High and low estimates
                    low_est = percent[variable] - (t_crit * se)
                    high_est = percent[variable] + (t_crit * se)
                    high[variable] = round(high_est, 3)
                    low[variable] = round(low_est, 3)
                except TypeError:
                    high[variable] = math.nan
                    low[variable] = math.nan
            else:
                percent[variable] = math.nan
                high[variable] = math.nan
                low[variable] = math.nan
            data_values[variable][f"percent{statsn}"] = percent[variable]
            data_values[variable][f"percent{statsn}_high"] = high[variable]
            data_values[variable][f"percent{statsn}_low"] = low[variable]

    test_code_row = None
    if test_codes and any(test_codes):
        # Format: ['test_code', ''] + test_codes + 4 blank entries for summary columns (average, % change, high, low)
        test_code_row = ['test_code', ''] + test_codes + [''] * 4
        line = f"Adding test_code row: {test_codes}"
        print(line)
        logs.append(line)

    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Reprint header to specify section (really you just need the section title but having the other column callouts
        # repeated makes it easier to read
        for statsn in statistic_names:
            header.insert(0, statsn)
            writer.writerow(header)
            header.remove(statsn)

            # Insert test_code row beneath the primary header row (Row 2 in CSV)
            if statsn == statistic_names[0] and test_code_row:
                writer.writerow(test_code_row)

            aname = 'average' + statsn
            pname = f'percent{statsn}'
            pname_high = f'percent{statsn}_high'
            pname_low = f'percent{statsn}_low'
            # Write units, values, and comparative data for all varaibles in all tests
            for variable in data_values:
                writer.writerow([variable, data_values[variable]["units"]]
                                + data_values[variable][statsn]
                                + [data_values[variable][aname]]
                                + [data_values[variable][pname]]
                                + [data_values[variable][pname_high]]
                                + [data_values[variable][pname_low]])
    csvfile.close()

    line = 'Created: ' + outputpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath,logs)

    return data_values, units, logs


###################################################################### the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    LEMS_FormatData_L3(inputpath, outputpath, logpath)