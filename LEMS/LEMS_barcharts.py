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

from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import os
import matplotlib.pyplot as plt
import easygui
from easygui import choicebox
from LEMS_PairsPlotHelper import (
    format_plot_labels,
    apply_pair_shading,
    merge_lp_cut_data_for_group,
    find_template_file,
    resolve_template_variables,
    convert_value,
    get_y_axis_label,
    load_plot_selection_csv,
)

def LEMS_barcharts(inputpath, savefigpath, logpath, labels=None, pair_groups=None, lp_inputpath=None, parameterspath=None, templatepath=None):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_barcharts v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names

    x = 0
    for i, path in enumerate(inputpath):

        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
        if labels is not None and i < len(labels) and str(labels[i]).strip():
            testname = str(labels[i]).strip()
        header.append(testname)
        test.append(testname)

        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        # Merge LP cut data from Step 21 if present
        merge_lp_cut_data_for_group(path, new_names, new_units, values, data, lp_inputpath=lp_inputpath, logs=None)

        # Make a complete list of all variable names from all tests
        for n, name in enumerate(new_names):
            if name not in names:  # If this is a new name, insert it into the ist of names
                names.insert(n, name)
                units[name] = new_units[name]

    for path in inputpath:
        # load in inputs from each energyoutput file
        [new_names, new_units, values, data] = io.load_L2_constant_inputs(path)

        line = 'loaded: ' + path
        print(line)
        logs.append(line)

        # Merge LP cut data from Step 21 if present
        merge_lp_cut_data_for_group(path, new_names, new_units, values, data, lp_inputpath=lp_inputpath, logs=logs)

        if (x == 0):  # If this is the first time through the loop, establish dictionary paths
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
            for name in names:  # append values to dictionary
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

    # Resolve custom template variables (e.g. combustion temperatures mapped across varying thermocouples)
    folder_path = os.path.dirname(savefigpath)
    if templatepath is None:
        templatepath = find_template_file(folder_path)
    pairs_csv_path = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')
    if templatepath:
        resolve_template_variables(templatepath, inputpath, test, data_values, names, units, pairs_csv_path=pairs_csv_path, logs=logs)

    # Load display names and units from PlotSelection.csv if available
    display_names = {}
    target_units = {}
    if parameterspath and os.path.isfile(parameterspath):
        _, display_names, target_units = load_plot_selection_csv(parameterspath)
    else:
        plot_sel_cand = os.path.join(folder_path, 'PlotSelection.csv')
        if os.path.isfile(plot_sel_cand):
            _, display_names, target_units = load_plot_selection_csv(plot_sel_cand)

    selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    if selected_variable is None:
        line = 'Variable selection cancelled by user.'
        print(line)
        logs.append(line)
        io.write_logfile(logpath, logs)
        return

    src_unit = data_values[selected_variable].get('units', '')
    tgt_unit = target_units.get(selected_variable, '')
    unit_str = tgt_unit if tgt_unit else src_unit
    y_label = get_y_axis_label(selected_variable, src_unit, display_names, target_units)

    raw_data = data_values[selected_variable]["average"]
    raw_conf = data_values[selected_variable]["confidence"]
    selected_data = []
    confidence = []
    for odx in range(len(raw_data)):
        try:
            cval = convert_value(raw_data[odx], src_unit, tgt_unit)
            selected_data.append(float(cval))
        except:
            selected_data.append(0.0)

    for odx in range(len(raw_conf)):
        try:
            cconf = convert_value(raw_conf[odx], src_unit, tgt_unit)
            confidence.append(float(cconf))
        except:
            confidence.append(0.0)

    try:
        plt.bar(test, selected_data, yerr=confidence, color='blue', width=0.4, capsize=5)
    except:
        plt.bar(test, selected_data, color="blue")

    plt.ylabel(y_label)
    plt.xlabel('Test Names')
    ax = plt.gca()
    if pair_groups:
        display_labels = format_plot_labels(test, max_width=18)
        plt.xticks(range(len(test)), display_labels, rotation=45, ha='right')
        apply_pair_shading(ax, pair_groups, x_offset=0, num_tests=len(test))
        plt.subplots_adjust(top=0.90, bottom=0.25)
    else:
        plt.xticks(range(len(test)), test, rotation=45, ha='right')
        plt.tight_layout()

    var_clean = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in selected_variable)
    savefigpath = savefigpath + '_' + var_clean + '.png'
    plt.savefig(savefigpath, bbox_inches='tight')
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath, logs)

    return savefigpath, selected_variable
