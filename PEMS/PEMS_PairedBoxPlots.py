from datetime import datetime as dt
import LEMS_DataProcessing_IO as io
import os
import matplotlib.pyplot as plt
import easygui
from easygui import choicebox
def PEMS_PairedBoxPlots(inputpath, savefigpath, logpath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_craigboxplots v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    header = ['units'] #establish header
    data_values = {} #nested dictionary. Keys are variable names
    test = [] #list of test names
    units = {}
    names = [] #list of variable names


    x = 0
    for path in inputpath:

        # Pull each test name/number. Add to header
        directory, filename = os.path.split(path)
        datadirectory, testname = os.path.split(directory)
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
    selected_variable = easygui.choicebox("Select a variable to compare", choices=list(data_values.keys()))

    fig, axes = plt.subplots(ncols=len(inputpath)//2, nrows=1, sharey=True, figsize=(10, 6))

    fig.suptitle(selected_variable + ' (' + data_values[selected_variable]['units'] + ')')

    figure_titles = ['Measured Period', 'Fire Period', 'Cold Start', 'Reload Period', 'Active Period', 'Burnout Period']
    #figure_titles = ['Measured Period', 'Fire Period', 'Active Period', 'Burnout Period']
    #figure_titles = ['Cold Start', 'Reload Period']
    figure_xticks =['NSPS Step 1 and 2', 'EPA Phase I and II']
    box_colors = ['red', 'blue']

    #for i, ax in enumerate(axes):
    data = data_values[selected_variable]["values"]
    for odx in range(len(data)):
        for idx in range(len(data[odx])):
            try:
                data[odx][idx] = float(data[odx][idx])
            except:
                data[odx][idx] = 0

    for n, testlist in enumerate(data):
        if n % 2 == 0 and n != 0: #if number is even
            axes[int(n / 2)].boxplot([testlist, data[n + 1]], widths=0.8, showmeans=True,
               meanprops={"marker": 'x', "markeredgecolor": 'black', "markersize":"8"})

            # Customize box colors
            #for box, color in zip(boxes['boxes'], box_colors):
                #box.set_facecolor(color)

            axes[int(n/2)].set_xticks(ticks=[1,2], fontsize=16, rotation=90)
            axes[int(n/2)].tick_params(axis='both', which='major', labelsize=16)
            axes[int(n / 2)].set_xticklabels(figure_xticks)
            axes[int(n/2)].title.set_text(figure_titles[int(n/2)])
            axes[int(n / 2)].title.set_size(20)

            x_values = [1] * len(testlist)
            axes[int(n/2)].scatter(x_values, testlist, color='blue', s=12)

            x_values = [2] * len(data[n + 1])
            axes[int(n / 2)].scatter(x_values, data[n + 1], color='blue', s=12)
        elif n == 0:
            axes[n].boxplot([testlist, data[n + 1]], widths=0.8, showmeans=True,
               meanprops={"marker": 'x', "markeredgecolor": 'black', "markersize":"8"})

            # Customize box colors
            #for box, color in zip(boxes['boxes'], box_colors):
                #box.set_facecolor(color)

            axes[n].set_xticks(ticks=[1, 2], fontsize=16, rotation=90)
            axes[n].tick_params(axis='both', which='major', labelsize=16)
            axes[n].set_xticklabels(figure_xticks)
            axes[n].title.set_text(figure_titles[n])
            axes[n].title.set_size(20)

            x_values = [1] * len(testlist)
            axes[n].scatter(x_values, testlist, color='blue', s=12)

            x_values = [2] * len(data[n + 1])
            axes[n].scatter(x_values, data[n + 1], color='blue', s=12)
        #elif n == 1:
            #axes[0].boxplot(testlist, 2)
        #else: # if number is odd
            #axes[int((n-1)/2)].boxplot(testlist, 2)

    axes[0].set_ylabel(selected_variable + ' (' + data_values[selected_variable]['units'] + ')', fontsize=20)

    #plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust the layout for the title
    plt.subplots_adjust(wspace=0)
    savefigpath = savefigpath + '_' + selected_variable + '.png'
    plt.savefig(savefigpath)
    plt.show()

    line = 'Saved plot at: ' + savefigpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    selected_data = data_values[selected_variable]["values"]
    for odx in range(len(selected_data)):
        try:
            for idx in range(len(selected_data[odx])):
                head, tail = selected_data[odx][idx].split('+')
                selected_data[odx][idx] = float(head)
        except:
            try:
                for idx in range(len(selected_data[odx])):
                    selected_data[odx][idx] = float(selected_data[odx][idx])
            except:
                selected_data[odx][idx] = 0

    plt.boxplot(selected_data)
    y_label = selected_variable + ' (' + data_values[selected_variable]['units'] + ')'
    plt.ylabel(y_label)
    plt.xlabel('Test Names')
    #plt.legend(test)
    plt.xticks(range(1, len(test) + 1), test)
    savefigpath = savefigpath + '_' + selected_variable +'.png'
    plt.savefig(savefigpath)
    plt.show()