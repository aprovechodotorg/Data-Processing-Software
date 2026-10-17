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
from matplotlib.patches import Patch
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
    get_sorted_group_indices,
    merge_lp_cut_data_for_group,
)


def _get_converted_bar_data(raw_data, raw_conf, src_unit, tgt_unit):
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
    return selected_data, confidence


def _render_and_save_single_barchart(plot_data, plot_conf, plot_tests, y_label, pair_groups, plot_filepath, logs):
    fig, ax = plt.subplots()
    num_tests = len(plot_tests)
    try:
        ax.bar(range(num_tests), plot_data, yerr=plot_conf, color='#1f77b4', width=0.4, capsize=5)
    except:
        ax.bar(range(num_tests), plot_data, color='#1f77b4', width=0.4)

    ax.set_ylabel(y_label)
    ax.set_xlabel('Test Names')
    if pair_groups:
        display_labels = format_plot_labels(plot_tests, max_width=18)
        ax.set_xticks(range(num_tests))
        ax.set_xticklabels(display_labels, rotation=45, ha='right')
        apply_pair_shading(ax, pair_groups, x_offset=0, num_tests=num_tests)
        plt.subplots_adjust(top=0.90, bottom=0.25)
    else:
        ax.set_xticks(range(num_tests))
        ax.set_xticklabels(plot_tests, rotation=45, ha='right')
        plt.tight_layout()
    plt.savefig(plot_filepath, bbox_inches='tight')
    plt.show()

    line = 'Saved plot at: ' + plot_filepath
    print(line)
    logs.append(line)
    plt.close()


def _render_and_save_dual_barchart(plot_data_l, plot_conf_l, plot_data_r, plot_conf_r, plot_tests,
                                    y_label_l, y_label_r, name_left, name_right,
                                    pair_groups, plot_filepath, logs):
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    num_tests = len(plot_tests)
    indices = range(num_tests)
    pos_left = [i - 0.18 for i in indices]
    pos_right = [i + 0.18 for i in indices]

    try:
        ax1.bar(pos_left, plot_data_l, yerr=plot_conf_l, width=0.35, color='#1f77b4', capsize=4)
    except:
        ax1.bar(pos_left, plot_data_l, width=0.35, color='#1f77b4')

    try:
        ax2.bar(pos_right, plot_data_r, yerr=plot_conf_r, width=0.35, color='#ff7f0e', capsize=4)
    except:
        ax2.bar(pos_right, plot_data_r, width=0.35, color='#ff7f0e')

    ax1.set_ylabel(y_label_l, color='#1f77b4', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax2.set_ylabel(y_label_r, color='#ff7f0e', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#ff7f0e')
    ax1.set_xlabel('Test Names')

    ax1.set_xlim(-0.6, num_tests - 0.4)
    ax2.set_xlim(-0.6, num_tests - 0.4)

    if pair_groups:
        display_labels = format_plot_labels(plot_tests, max_width=18)
        ax1.set_xticks(range(num_tests))
        ax1.set_xticklabels(display_labels, rotation=45, ha='right')
        apply_pair_shading(ax1, pair_groups, x_offset=0, num_tests=num_tests)
        plt.subplots_adjust(top=0.88, bottom=0.25, left=0.1, right=0.90)
    else:
        ax1.set_xticks(range(num_tests))
        ax1.set_xticklabels(plot_tests, rotation=45, ha='right')
        plt.subplots_adjust(top=0.88, bottom=0.4, left=0.1, right=0.90)

    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.grid(False)

    legend_elements = [
        Patch(facecolor='#1f77b4', label=f"{name_left} (Left)"),
        Patch(facecolor='#ff7f0e', label=f"{name_right} (Right)")
    ]
    ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.0, 1.15), ncol=2, framealpha=0.8, fontsize=8)

    plt.savefig(plot_filepath, bbox_inches='tight')
    plt.show()

    line = 'Saved dual-axis plot at: ' + plot_filepath
    print(line)
    logs.append(line)
    plt.close()


def LEMS_multibarcharts(inputpath, parameterspath, savefigpath, logpath, labels=None, pair_groups=None, lp_inputpath=None):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_multibarcharts v' + ver + '   ' + timestampstring  # Add to log
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

    # Check / create parameters csv
    created = ensure_plot_selection_csv(parameterspath, names, units)
    if created:
        line = 'Parameter file created: ' + parameterspath
    else:
        line = 'Parameters file already exists: ' + parameterspath
    print(line)
    logs.append(line)

    # Load plot selection, display names, target units, structured plot configs, and sort orders
    plotnames, display_names, target_units, plot_configs, sort_orders = load_plot_selection_csv(
        parameterspath, return_plot_configs=True, return_sort=True
    )

    base_savefigpath = savefigpath

    for cfg in plot_configs:
        if cfg['type'] == 'single':
            selected_variable = cfg['variable']
            if selected_variable not in data_values:
                line = f"Notice: Variable '{selected_variable}' selected in PlotSelection.csv not found in data; skipping."
                print(line)
                logs.append(line)
                continue

            src_unit = data_values[selected_variable]['units']
            tgt_unit = target_units.get(selected_variable, '')

            plot_data, plot_conf = _get_converted_bar_data(
                data_values[selected_variable]["average"],
                data_values[selected_variable]["confidence"],
                src_unit, tgt_unit
            )
            y_label = get_y_axis_label(selected_variable, src_unit, display_names, target_units)

            if cfg.get('plot_num'):
                plot_filepath = f"{base_savefigpath}_Plot{cfg['plot_num']}_{selected_variable}.png"
            else:
                plot_filepath = f"{base_savefigpath}_{selected_variable}.png"

            plot_tests = list(test)

            var_sort = cfg.get('sort', '') or sort_orders.get(selected_variable, '')
            is_smallest = var_sort.strip().lower() in ('smallest', 'small', 'asc', 'ascending')

            if pair_groups and is_smallest:
                line = f"Notice: Sorting is not available in pairs mode for '{selected_variable}'; preserving pair group order."
                print(line)
                logs.append(line)
            elif not pair_groups and is_smallest:
                sorted_indices = get_sorted_group_indices(plot_data, sort_order=var_sort, pair_groups=pair_groups)
                plot_tests = [plot_tests[i] for i in sorted_indices]
                plot_data = [plot_data[i] for i in sorted_indices]
                plot_conf = [plot_conf[i] for i in sorted_indices]
                line = f"Sorted test groups for '{selected_variable}' from smallest to largest (left to right)."
                print(line)
                logs.append(line)

            _render_and_save_single_barchart(plot_data, plot_conf, plot_tests, y_label, pair_groups, plot_filepath, logs)

        elif cfg['type'] == 'dual':
            var_left = cfg['left']
            var_right = cfg['right']
            if var_left not in data_values or var_right not in data_values:
                missing = [v for v in (var_left, var_right) if v not in data_values]
                line = f"Notice: Dual plot {cfg.get('plot_num', '')} metric(s) {missing} not found in data; skipping."
                print(line)
                logs.append(line)
                continue

            src_unit_l = data_values[var_left]['units']
            tgt_unit_l = target_units.get(var_left, '')
            plot_data_l, plot_conf_l = _get_converted_bar_data(
                data_values[var_left]["average"],
                data_values[var_left]["confidence"],
                src_unit_l, tgt_unit_l
            )
            y_label_l = get_y_axis_label(var_left, src_unit_l, display_names, target_units)

            src_unit_r = data_values[var_right]['units']
            tgt_unit_r = target_units.get(var_right, '')
            plot_data_r, plot_conf_r = _get_converted_bar_data(
                data_values[var_right]["average"],
                data_values[var_right]["confidence"],
                src_unit_r, tgt_unit_r
            )
            y_label_r = get_y_axis_label(var_right, src_unit_r, display_names, target_units)

            name_left = display_names.get(var_left) or var_left
            name_right = display_names.get(var_right) or var_right

            plot_num_str = f"_Plot{cfg['plot_num']}" if cfg.get('plot_num') else "_Dual"
            plot_filepath = f"{base_savefigpath}{plot_num_str}_{var_left}_vs_{var_right}.png"

            plot_tests = list(test)

            var_sort = cfg.get('sort', '')
            sort_metric = cfg.get('sort_var', '')
            is_smallest = var_sort.strip().lower() in ('smallest', 'small', 'asc', 'ascending')

            if pair_groups and is_smallest:
                line = f"Notice: Sorting is not available in pairs mode for Plot {cfg.get('plot_num', '')}; preserving pair group order."
                print(line)
                logs.append(line)
            elif not pair_groups and is_smallest:
                target_data = plot_data_r if sort_metric == var_right else plot_data_l
                sorted_indices = get_sorted_group_indices(target_data, sort_order=var_sort, pair_groups=pair_groups)
                plot_tests = [plot_tests[i] for i in sorted_indices]
                plot_data_l = [plot_data_l[i] for i in sorted_indices]
                plot_conf_l = [plot_conf_l[i] for i in sorted_indices]
                plot_data_r = [plot_data_r[i] for i in sorted_indices]
                plot_conf_r = [plot_conf_r[i] for i in sorted_indices]
                line = f"Sorted test groups for Plot {cfg.get('plot_num', '')} by '{sort_metric}' from smallest to largest (left to right)."
                print(line)
                logs.append(line)

            notice = f"Generating dual Y-axis bar chart (Plot {cfg.get('plot_num', '')}): '{var_left}' (Left) vs '{var_right}' (Right)..."
            print(notice)
            logs.append(notice)

            _render_and_save_dual_barchart(
                plot_data_l, plot_conf_l, plot_data_r, plot_conf_r, plot_tests,
                y_label_l, y_label_r, name_left, name_right, pair_groups, plot_filepath, logs
            )

    #print to log file
    io.write_logfile(logpath,logs)