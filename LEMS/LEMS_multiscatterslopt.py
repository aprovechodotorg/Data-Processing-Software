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
plt.rcParams.update({'font.size': 10}) #set font size
import easygui
import csv
from easygui import choicebox
from LEMS_PairsPlotHelper import (
    format_plot_labels,
    apply_pair_shading,
    ensure_plot_selection_csv,
    load_plot_selection_csv,
    get_y_axis_label,
    convert_value,
    extract_individual_test_names,
    attach_hover_labels,
    merge_lp_cut_data_for_group,
)

def _find_equivalent_metric_pairs(plotnames):
    """
    Identifies pairs of equivalent metrics in plotnames:
      - Lambda & O2_1 (with matching phase suffix, e.g. '', '_hp', '_lp', '_mp', '_L1', etc.)
      - SenO2Percent & O2_1_per (with matching phase suffix)
    Returns list of tuples: (var_primary, var_secondary, family, suffix)
    """
    pairs = []
    name_map = {name.strip().lower(): name for name in plotnames}

    # Family 1: Lambda & O2_1
    for name in plotnames:
        lower_name = name.strip().lower()
        if lower_name.startswith('lambda'):
            suffix = lower_name[6:]  # part after 'lambda'
            target_key = f"o2_1{suffix}"
            if target_key in name_map:
                o2_name = name_map[target_key]
                pairs.append((name, o2_name, 'lambda', suffix))

    # Family 2: SenO2Percent & O2_1_per
    for name in plotnames:
        lower_name = name.strip().lower()
        if lower_name.startswith('seno2percent'):
            suffix = lower_name[12:]  # part after 'seno2percent'
            target_key = f"o2_1_per{suffix}"
            if target_key in name_map:
                o2_name = name_map[target_key]
                pairs.append((name, o2_name, 'o2_percent', suffix))

    return pairs


def _get_converted_values(raw_data, src_unit, tgt_unit):
    """
    Converts a 2D list of numeric values from src_unit to tgt_unit
    without mutating the input structure.
    """
    converted = []
    for odx in range(len(raw_data)):
        row = []
        for idx in range(len(raw_data[odx])):
            try:
                cval = convert_value(raw_data[odx][idx], src_unit, tgt_unit)
                row.append(float(cval))
            except:
                row.append(0.0)
        converted.append(row)
    return converted


def _render_and_save_scatter(points_per_group, test_labels, unit_str, y_label, pair_groups, plot_filepath, logs):
    """
    Renders and saves a scatter plot figure with points, averages, shading, and hover labels.
    """
    fig, ax = plt.subplots()
    hover_items = []

    for i, (num_list, point_labels) in enumerate(points_per_group):
        x_values = [i + 1] * len(num_list)
        y_values = num_list

        if num_list:
            sc = ax.scatter(x_values, y_values, color='blue')
            hover_items.append((sc, point_labels, unit_str))
            avg_y = sum(y_values) / len(y_values)
            sc_avg = ax.scatter(i + 1, avg_y, color='red', marker='_', s=1000)
            group_name = test_labels[i] if i < len(test_labels) else f"Group {i + 1}"
            hover_items.append((sc_avg, [(f"{group_name} Average", avg_y)], unit_str))

    ax.set_ylabel(y_label)
    ax.set_xlabel('Test Names')

    if pair_groups:
        display_labels = format_plot_labels(test_labels, max_width=18)
        ax.set_xticks(range(1, len(test_labels) + 1))
        ax.set_xticklabels(display_labels, rotation=45, ha='right')
        apply_pair_shading(ax, pair_groups, x_offset=1, num_tests=len(test_labels))
        plt.subplots_adjust(bottom=0.25, top=0.90, left=0.1, right=0.95)
    else:
        ax.set_xticks(range(1, len(test_labels) + 1))
        ax.set_xticklabels(test_labels, rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.4, top=1, left=0.03, right=1)
    plt.grid(axis='y', alpha=0.5)

    attach_hover_labels(fig, hover_items)

    plt.savefig(plot_filepath, format="png", bbox_inches="tight")
    plt.show()

    line = 'Saved plot at: ' + plot_filepath
    print(line)
    logs.append(line)
    plt.close()


def LEMS_multiscaterplots(inputpath, parameterspath, savefigpath, logpath, labels=None, pair_groups=None, lp_inputpath=None):
    ver = '0.0'
    directory, filename = os.path.split(logpath)
    plt.rcParams['savefig.directory'] = directory

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_multiscatterplots v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names


    x = 0
    individual_test_names = []
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
        individual_test_names.append(extract_individual_test_names(new_names, values))

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
                    data_values[name] = {"units": units.get(name, ''), "values": [['']], "average": [''], "confidence": [''], "N": [''],
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
                    data_values[name]["values"].append([''])
                    data_values[name]["average"].append('')
                    data_values[name]["confidence"].append('')
                    data_values[name]["N"].append('')
                    data_values[name]["stdev"].append('')
                    data_values[name]["High Tier"].append('')
                    data_values[name]["Low Tier"].append('')
                    data_values[name]["COV"].append('')
                    data_values[name]["CI"].append('')
        x += 1

    # Check / create parameters csv
    created = ensure_plot_selection_csv(parameterspath, names, units)
    if created:
        line = 'Parameter file created/updated: ' + parameterspath
    else:
        line = 'Parameters file already exists: ' + parameterspath
    print(line)
    logs.append(line)

    # Load plot selection, display names, and target units for conversion
    plotnames, display_names, target_units = load_plot_selection_csv(parameterspath)

    base_savefigpath = savefigpath

    # 1. Generate individual scatter plots for all selected variables
    for selected_variable in plotnames:
        if selected_variable not in data_values:
            continue

        src_unit = data_values[selected_variable]['units']
        tgt_unit = target_units.get(selected_variable, '')
        unit_str = tgt_unit if tgt_unit else src_unit

        converted_data = _get_converted_values(data_values[selected_variable]["values"], src_unit, tgt_unit)

        points_per_group = []
        for i, data_list in enumerate(converted_data):
            num_list = []
            point_labels = []
            g_names = individual_test_names[i] if i < len(individual_test_names) else []
            for j, data in enumerate(data_list):
                try:
                    if data != 0 and str(data).strip().lower() not in ('nan', ''):
                        val_float = float(data)
                        num_list.append(val_float)
                        t_name = g_names[j] if j < len(g_names) else f"Test {j + 1}"
                        point_labels.append((t_name, val_float))
                except:
                    pass
            points_per_group.append((num_list, point_labels))

        y_label = get_y_axis_label(selected_variable, src_unit, display_names, target_units)
        plot_filepath = f"{base_savefigpath}_{selected_variable}.png"
        _render_and_save_scatter(points_per_group, test, unit_str, y_label, pair_groups, plot_filepath, logs)

    # 2. Check for equivalent metric pairs (Lambda & O2_1, or SenO2Percent & O2_1_per)
    equivalent_pairs = _find_equivalent_metric_pairs(plotnames)
    for var_a, var_b, family, suffix in equivalent_pairs:
        if var_a not in data_values or var_b not in data_values:
            continue

        if family == 'lambda':
            src_unit = data_values[var_a].get('units') or data_values[var_b].get('units') or 'lambda'
            tgt_unit = target_units.get(var_a) or target_units.get(var_b) or ''
            unit_str = tgt_unit if tgt_unit else src_unit
            clean_sfx = suffix.lstrip('_')
            phase_suffix_label = f" ({clean_sfx})" if clean_sfx else ""
            default_display = f"Lambda / O2_1{phase_suffix_label}"
            custom_name = display_names.get(var_a) or display_names.get(var_b)
            label_name = custom_name.strip() if custom_name and custom_name.strip() else default_display
            effective_unit = unit_str if unit_str else 'lambda'
            y_label = f"{label_name} ({effective_unit})"
            plot_identifier = f"Lambda_O2_1{suffix}_combined"

        else:  # 'o2_percent'
            src_unit = data_values[var_a].get('units') or data_values[var_b].get('units') or '%'
            tgt_unit = target_units.get(var_a) or target_units.get(var_b) or ''
            unit_str = tgt_unit if tgt_unit else src_unit
            clean_sfx = suffix.lstrip('_')
            phase_suffix_label = f" ({clean_sfx})" if clean_sfx else ""
            default_display = f"Oxygen Content, O2{phase_suffix_label}"
            custom_name = display_names.get(var_a) or display_names.get(var_b)
            label_name = custom_name.strip() if custom_name and custom_name.strip() else default_display
            effective_unit = unit_str if unit_str else '%'
            y_label = f"{label_name} ({effective_unit})"
            plot_identifier = f"O2Percent{suffix}_combined"

        converted_a = _get_converted_values(data_values[var_a]["values"], src_unit, tgt_unit)
        converted_b = _get_converted_values(data_values[var_b]["values"], src_unit, tgt_unit)

        points_per_group = []
        num_groups = max(len(converted_a), len(converted_b))
        for i in range(num_groups):
            num_list = []
            point_labels = []
            g_names = individual_test_names[i] if i < len(individual_test_names) else []

            data_list_a = converted_a[i] if i < len(converted_a) else []
            data_list_b = converted_b[i] if i < len(converted_b) else []
            max_tests = max(len(data_list_a), len(data_list_b))

            for j in range(max_tests):
                t_name = g_names[j] if j < len(g_names) else f"Test {j + 1}"
                val_a = None
                val_b = None
                if j < len(data_list_a):
                    va = data_list_a[j]
                    if va != 0 and str(va).strip().lower() not in ('nan', ''):
                        try:
                            val_a = float(va)
                        except:
                            pass
                if j < len(data_list_b):
                    vb = data_list_b[j]
                    if vb != 0 and str(vb).strip().lower() not in ('nan', ''):
                        try:
                            val_b = float(vb)
                        except:
                            pass

                # If both sensors are present for this test, default to Lambda (var_a)
                if val_a is not None:
                    num_list.append(val_a)
                    point_labels.append((t_name, val_a))
                elif val_b is not None:
                    num_list.append(val_b)
                    point_labels.append((t_name, val_b))

            points_per_group.append((num_list, point_labels))

        notice = f"Generating combined plot for equivalent metrics '{var_a}' and '{var_b}'..."
        print(notice)
        logs.append(notice)

        out_file = f"{base_savefigpath}_{plot_identifier}.png"
        _render_and_save_scatter(points_per_group, test, unit_str, y_label, pair_groups, out_file, logs)


    #print to log file
    io.write_logfile(logpath,logs)
