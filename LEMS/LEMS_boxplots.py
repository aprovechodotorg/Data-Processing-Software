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
    load_plot_selection_csv,
    get_y_axis_label,
    convert_value,
)

def LEMS_boxplots(inputpath, savefigpath, logpath, labels=None, pair_groups=None, parameterspath=None, templatepath=None, lp_inputpath=None):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_boxplots v' + ver + '   ' + timestampstring  # Add to log
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

        # Merge LP cut data if present
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

        # Merge LP cut data if present
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
    folder_path = os.path.dirname(parameterspath) if parameterspath else os.path.dirname(savefigpath)
    if templatepath is None:
        templatepath = find_template_file(folder_path)
    pairs_csv_path = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')
    if templatepath:
        resolve_template_variables(templatepath, inputpath, test, data_values, names, units, pairs_csv_path=pairs_csv_path, logs=logs)

    # Load display names and units from PlotSelection.csv if available
    display_names = {}
    target_units = {}
    params_file = parameterspath if (parameterspath and os.path.isfile(parameterspath)) else os.path.join(folder_path, 'PlotSelection.csv')
    if os.path.isfile(params_file):
        try:
            _, display_names, target_units = load_plot_selection_csv(params_file)
        except Exception:
            pass

    selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    if not selected_variable:
        return None, None

    fig, ax = plt.subplots()

    src_unit = data_values[selected_variable]['units']
    tgt_unit = target_units.get(selected_variable, '') if target_units else ''
    raw_selected = data_values[selected_variable]["values"]
    selected_data = []
    for grp in raw_selected:
        items = list(grp) if isinstance(grp, (list, tuple)) else [grp]
        clean_grp = []
        for val in items:
            if val is not None and str(val).strip().lower() not in ('nan', '', 'none', 'null'):
                try:
                    cval = convert_value(val, src_unit, tgt_unit)
                    vf = float(cval)
                    clean_grp.append(vf)
                except:
                    pass
        selected_data.append(clean_grp)

    for i, num_list in enumerate(selected_data):
        x_values = [i + 1] * len(num_list)
        ax.scatter(x_values, num_list, color='blue', s=12)

    ax.boxplot(selected_data, widths=0.8, showmeans=True,
               meanprops={"marker": 'x', "markeredgecolor": 'black', "markersize": 8})

    if display_names and selected_variable in display_names:
        y_label = get_y_axis_label(selected_variable, src_unit, display_names, target_units)
    else:
        unit_str = tgt_unit if tgt_unit else src_unit
        y_label = f"{selected_variable} ({unit_str})" if unit_str else selected_variable

    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlabel('Test Names', fontsize=10)

    if pair_groups:
        display_labels = format_plot_labels(test, max_width=18)
        ax.set_xticks(range(1, len(test) + 1))
        ax.set_xticklabels(display_labels, fontsize=8, rotation=45, ha='right')
        apply_pair_shading(ax, pair_groups, x_offset=1, num_tests=len(test))
        plt.subplots_adjust(top=0.90, bottom=0.25)
    else:
        ax.set_xticks(range(1, len(test) + 1))
        ax.set_xticklabels(test, fontsize=8, rotation=90)
        fig.tight_layout()
    ax.tick_params(axis='both', which='major', labelsize=8)

    safe_var_name = selected_variable.replace('/', '_').replace(' ', '_').replace(',', '')
    savefigpath = savefigpath + '_' + safe_var_name + '.png'
    plt.savefig(savefigpath, bbox_inches='tight')
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    #print to log file
    io.write_logfile(logpath, logs)

    return savefigpath, selected_variable
