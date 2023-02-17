


from matplotlib import pyplot as plt
import easygui
import numpy as np

def field_plot_data(data, units, plots, y_label):
    plt.clf() #Clear any plots already existing
    plt.ion()  # Turn on interactive plot

    scale = [1] * len(plots) #Create a scale of 1 for each data set

    n = 0
    large = []
    for name in plots: #Plot each dataset vs. seconds and scale it by set scalar
        scalar = scale[n]
        data[name] = [x * scalar for x in data[name]]
        plt.plot(data['seconds'], data[name])
        large.append(max(data[name])) #Add max value from each data set
        n += 1

    large = max(large)
    plt.ylim(0, large) #Make y limit the largest data point in all data sets

    plt.xlabel("Times (s)")
    plt.ylabel(y_label + ' (' + units[plots[0]] + ')') #Looks at what's plotted and add units
    plt.title(y_label + ' of ' + str(plots) + ' over time')
    plt.legend(plots) #Add legend
    plt.show()

    ######## Create a pop up to edit the scale of the data to see it better
    running = 'fun'

    while (running == 'fun'):

        zero = 'Edit scales\n'
        first = 'Click OK to update plot\n'
        second = 'Click Cancel to exit\n'
        msg = zero + first + second
        title = 'Gitrdone'
        #Create a pop up where user can enter desired scales
        newscale = easygui.multenterbox(msg, title, plots, scale)

        if newscale: #If the user does anything but click cancel
            x = 0
            for name in plots: #Go through each plots and revert it back to original data
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            scale = []
            for item in newscale: #Create a new scale from numbers entered by user
                scale.append(int(item))
            print(scale)
        else: #If the cancel button is hit revert data back to origional values and close plot and prompt box
            x = 0
            for name in plots:
                scalar = scale[x]
                data[name] = [x / scalar for x in data[name]]
                x += 1
            running = 'not fun'

        plt.clf() #clear plot

        n = 0
        for name in plots: #Scale plot according to input
            scalar = scale[n]
            data[name] = [x * scalar for x in data[name]]
            plt.plot(data['seconds'], data[name])
            n += 1
        plt.ylim(0, large)  # Make y limit the largest data point in all data sets

        plt.xlabel("Times (s)")
        plt.ylabel(y_label + ' (' + units[plots[0]] + ')')  # Looks at what's plotted and add units
        plt.title(y_label + ' of ' + str(plots) + ' over time')
        plt.legend(plots)  # Add legend
        plt.show()

def subtract_background (names, data, potentialBkgNames):
    bkgnames = []  # initialize list of actual channel names that will get background subtraction

    # define which channels will get background subtraction
    # could add easygui multi-choice box here instead so user can pick the channels
    # Currently just does CO and CO2

    # If one of the background measurements is in the measurements, record which it is
    for name in names:
        if name in potentialBkgNames:
            bkgnames.append(name)

    # For each background name, look for the realtime background data and subtract it from the value
    for name in bkgnames:
        bkg = name + 'bkg'
        #CO and CO2 have different values for undiluted measurments. Look to these values for background subtraction
        if name == 'CO' or name == 'CO2':
            name = name + 'hi'
        data[name] = (np.subtract(data[name], data[bkg]))

    return names, data
