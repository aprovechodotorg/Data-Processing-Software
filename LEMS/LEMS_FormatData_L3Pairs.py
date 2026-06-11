# v1.0 Python3 - Parameters Driven Output

#    Copyright (C) 2022 Aprovecho Research Center
#    Contact: sam@aprovecho.org

import csv
import math
import LEMS_DataProcessing_IO as io
from datetime import datetime as dt
from scipy.stats import t

# Set the input path to point to your new CSV workflow file
inputpath = 'PairsUnformattedDataL2FilePaths.csv'

# Output configurations
outputpath = 'C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\PairsFormattedDataL3.csv'
logpath = 'C:\\Users\\Jaden\\Documents\\DOE-stak\\HH_full\\GP027_full\\log.txt'


def LEMS_FormatData_L3Pairs(inputpath_csv, outputpath, logpath):
    ver = '1.0'
    timestampstring = dt.now().strftime("%Y%m%d %H:%M:%S")
    line = 'LEMS_FormatData_L3 v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    # --- 1. Parse the workflow and paths from the new CSV ---
    workflow_keys = []  # The exact order of columns to print
    file_paths = []  # The Unformatted files to load
    code_to_idx = {}  # Maps a data_key (e.g. '1B') to its index in memory

    with open(inputpath_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        idx = 0
        for row in reader:
            d_key = row.get('data_key', '').strip()
            path_val = row.get('path', '').strip()

            if not d_key:
                continue

            workflow_keys.append(d_key)

            # If there's a path, it's a data load instruction
            if path_val:
                file_paths.append(path_val)
                code_to_idx[d_key] = idx
                idx += 1

    # --- 2. Load the Unformatted Data ---
    data_values = {}
    units = {}
    names = []

    # Pass 1: Grab all possible variable names
    for path in file_paths:
        try:
            [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)
            for name in new_names:
                if name not in names:
                    names.append(name)
                    units[name] = new_units[name]
        except Exception as e:
            logs.append(f"Failed to scan {path}: {e}")

    # Pass 2: Populate the dictionary (Maintaining original try/except structure for unequal lists)
    x = 0
    for path in file_paths:
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)
        log_line = 'loaded: ' + path
        print(log_line)
        logs.append(log_line)

        if x == 0:
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"][name]]}
                except:
                    data_values[name] = {"units": '', "values": [''], "average": [''], "confidence": [''], "N": [''],
                                         "stdev": ['']}
        else:
            for name in names:
                try:
                    data_values[name]["values"].append(values[name])
                    data_values[name]["average"].append(data["average"][name])
                    data_values[name]["confidence"].append(data["Interval"][name])
                    data_values[name]["N"].append(data["N"][name])
                    data_values[name]["stdev"].append(data["stdev"][name])
                except:
                    data_values[name]["values"].append('')
                    data_values[name]["average"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
        x += 1

    # --- 3. Generate Output Driven by Data Key ---
    statistic_names = ['average', 'confidence', 'N']

    # Build the dynamic header
    base_header = ['variable_name', 'units']
    for d_key in workflow_keys:
        if '/' in d_key or d_key.startswith('d'):
            # Expansion for difference calculations
            base_header.extend([f"{d_key} % Change", f"{d_key} High", f"{d_key} Low"])
        else:
            base_header.append(d_key)

    with open(outputpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        for statsn in statistic_names:
            # Recreate header style: first cell indicates the section (e.g. 'average')
            current_header = [statsn] + base_header[1:]
            writer.writerow(current_header)

            for variable in names:
                if variable not in data_values: continue

                row_out = [variable, data_values[variable]["units"]]

                for d_key in workflow_keys:

                    # CASE A: Percent Difference Calculation (Triggered by a '/' in the data_key)
                    if '/' in d_key or d_key.startswith('d'):
                        # Only compute math if we are processing the 'average' section
                        if statsn == 'average':
                            # Parse out the two test codes (e.g., 'd1B/1R1' -> '1B' and '1R1')
                            clean_key = d_key.lstrip('d')
                            parts = clean_key.split('/')

                            if len(parts) == 2:
                                idx_init = code_to_idx.get(parts[0])
                                idx_final = code_to_idx.get(parts[1])

                                if idx_init is not None and idx_final is not None:
                                    try:
                                        avg_init = float(data_values[variable]["average"][idx_init])
                                        avg_final = float(data_values[variable]["average"][idx_final])
                                        N_init = float(data_values[variable]["N"][idx_init])
                                        N_final = float(data_values[variable]["N"][idx_final])
                                        stdev_init = float(data_values[variable]["stdev"][idx_init])
                                        stdev_final = float(data_values[variable]["stdev"][idx_final])

                                        # Core Calculations
                                        pct = ((avg_final - avg_init) / avg_init) * 100
                                        deg_free = N_init + N_final - 2
                                        t_crit = t.ppf(0.95, deg_free)

                                        se1 = stdev_init / math.sqrt(N_init)
                                        se2 = stdev_final / math.sqrt(N_final)
                                        se = (abs(avg_final / avg_init) * math.sqrt(
                                            (se2 ** 2 / avg_final ** 2) + (se1 ** 2 / avg_init ** 2))) * 100

                                        high = pct + (t_crit * se)
                                        low = pct - (t_crit * se)

                                        row_out.extend([round(pct, 3), round(high, 3), round(low, 3)])
                                    except (TypeError, ValueError, ZeroDivisionError):
                                        row_out.extend([math.nan, math.nan, math.nan])
                                else:
                                    row_out.extend(['', '', ''])  # Files were not matched
                            else:
                                row_out.extend(['', '', ''])  # Malformed key (e.g., missing '/')
                        else:
                            # For 'N' and 'confidence' sections, leave calculation columns blank
                            row_out.extend(['', '', ''])

                            # CASE B: Standard Data Look-up
                    else:
                        if d_key in code_to_idx:
                            idx = code_to_idx[d_key]
                            try:
                                val = data_values[variable][statsn][idx]
                                row_out.append(val)
                            except (KeyError, IndexError):
                                row_out.append('')
                        else:
                            row_out.append('')

                writer.writerow(row_out)
            writer.writerow([])  # Optional empty line between sections

    line = 'Created: ' + outputpath
    print(line)
    logs.append(line)
    io.write_logfile(logpath, logs)

    return data_values, units, logs


if __name__ == "__main__":
    LEMS_FormatData_L3Pairs(inputpath, outputpath, logpath)