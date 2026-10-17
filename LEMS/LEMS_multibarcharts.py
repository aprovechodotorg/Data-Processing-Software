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
)
def LEMS_multibarcharts(inputpath, parameterspath, savefigpath, logpath, labels=None, pair_groups=None):
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

        if (x == 0):  # If this is the first time through the loop, establish dictionary paths
            for name in names:
                try:
                    data_values[name] = {"units": units[name], "values": [values[name]],
                                         "average": [data["average"][name]], "confidence": [data["Interval"][name]],
                                         "N": [data["N"][name]], "stdev": [data["stdev"]],
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

    # Check / create parameters csv
    created = ensure_plot_selection_csv(parameterspath, names, units)
    if created:
        line = 'Parameter file created: ' + parameterspath
    else:
        line = 'Parameters file already exists: ' + parameterspath
    print(line)
    logs.append(line)

    # Load plot selection, display names, target units, and sort orders
    plotnames, display_names, target_units, sort_orders = load_plot_selection_csv(parameterspath, return_sort=True)

    #selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))
    r = 0
    for selected_variable in plotnames:
        src_unit = data_values[selected_variable]['units']
        tgt_unit = target_units.get(selected_variable, '')

        raw_data = list(data_values[selected_variable]["average"])
        raw_conf = list(data_values[selected_variable]['confidence'])
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

        plot_tests = list(test)
        plot_data = selected_data
        plot_conf = confidence

        var_sort = sort_orders.get(selected_variable, '').strip()
        is_smallest = var_sort.lower() in ('smallest', 'small', 'asc', 'ascending')

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

        fig, ax = plt.subplots()
        try:
            ax.bar(range(len(plot_tests)), plot_data, yerr=plot_conf, color='blue', width=0.4, capsize=5)
        except:
            ax.bar(range(len(plot_tests)), plot_data, color='blue', width=0.4)

        y_label = get_y_axis_label(selected_variable, src_unit, display_names, target_units)
        ax.set_ylabel(y_label)
        ax.set_xlabel('Test Names')
        if pair_groups:
            display_labels = format_plot_labels(plot_tests, max_width=18)
            ax.set_xticks(range(len(plot_tests)))
            ax.set_xticklabels(display_labels, rotation=45, ha='right')
            apply_pair_shading(ax, pair_groups, x_offset=0, num_tests=len(plot_tests))
            plt.subplots_adjust(top=0.90, bottom=0.25)
        else:
            ax.set_xticks(range(len(plot_tests)))
            ax.set_xticklabels(plot_tests, rotation=45, ha='right')
            plt.tight_layout()
        if r == 0:
            savefigpath = savefigpath + '_' + selected_variable + '.png'
            r+=1
        else:
            base, trash = savefigpath.split('Chart', 1) #split at last underscore
            savefigpath = base + 'Chart_' + selected_variable + '.png'
        plt.savefig(savefigpath, bbox_inches='tight')
        plt.show()

        line = 'Saved plot at: ' + savefigpath
        print(line)
        logs.append(line)
        plt.close()

    #print to log file
    io.write_logfile(logpath,logs)