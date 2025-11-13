# v0.2 Python3

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

# calculates PM mass concentration by gravimetric method
# inputs gravimetric filter weights
# determines which test phases and which flow trains by reading which variable names are present in the grav input file
# inputs phase times input file to calculate phase time length
# outputs filter net mass, flow, duration, and concentration for each phase
# outputs report to terminal and log file

# do:
# add plot of PM scat and grav flows with phase markers as a visual check
# create grav input file to interface with filter log database

import LEMS_DataProcessing_IO as io
import easygui
# import matplotlib.pyplot as plt
# import matplotlib
from datetime import datetime as dt
import traceback
from uncertainties import ufloat
import os

#########      inputs      ##############
# gravimetric filter masses input file:
gravinputpath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_GravInputs.csv'
# phase averages input data file:
aveinputpath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_Averages.csv'
# gravimetric output metrics data file:
gravoutputpath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_GravOutputs.csv'
# input file of start and end times for background and test phase periods
timespath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_PhaseTimes.csv'
logpath = 'C:\Mountain Air\equipment\Ratnoze\DataProcessing\LEMS\LEMS-Data-Processing\Data\CrappieCooker\CrappieCooker_test2\CrappieCooker_test2_log.txt'


##########################################

def LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod):
    ver = '0.5'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_GravCalcs v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    outnames = []  # initialize list of variable names for grav output metrics
    outuval = {}  # initialize dictionary for grav output metrics (type: ufloats)
    outunits = {}  # dict of units for grav output metrics
    outval = {}  # only used for output file header
    outunc = {}  # only used for output file header

    # list of phases for filter inputs
    phases = ['_hp', '_mp', '_lp']
    # define flow sensor channel names
    gravtrain = {}
    gravtrain['A'] = 'GravFlo1'
    gravtrain['B'] = 'GravFlo2'
    gravtrain['SB4007_A'] = 'GravFlo1'
    gravtrain['SB4007_B'] = 'GravFlo2'
    gravtrain['SB4008_A'] = 'GravFlo1'
    gravtrain['SB4008_B'] = 'GravFlo2'
    gravtrain['SB3001_A'] = 'GravFlo1'
    gravtrain['SB3001_B'] = 'GravFlo2'
    gravtrain['SB3002_A'] = 'GravFlo1'
    gravtrain['SB3002_B'] = 'GravFlo2'
    gravtrain['SB3009_A'] = 'GravFlo1'
    gravtrain['SB3009_B'] = 'GravFlo2'
    gravtrain['SB3015/16_A'] = 'GravFlo1'
    gravtrain['SB3015/16_B'] = 'GravFlo2'
    gravtrain['Possum2'] = 'GravFlo1'

    ##################
    # need to create grav input file here
    # potential options:
    #   1. run io function to create from 2d data entry form
    ##################

    # load phase averages data file
    [names, units, ave, aveunc, aveuval] = io.load_constant_inputs(aveinputpath)

    line = 'Loaded phase averages:' + aveinputpath
    print(line)
    logs.append(line)

    # load phase times input file
    [timenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(timespath)

    line = 'Loaded input file of phase start and end times:' + timespath
    print(line)
    logs.append(line)

    ###Check if running IDC test or not
    if 'start_time_L1' in timenames:
        phases.insert(0, '_L1')
    if 'start_time_L5' in timenames:
        phases.append('_L5')

    check = 0
    choice = []
    # check for grav path
    if os.path.isfile(gravinputpath):
        # load grav filter weights input file
        [gravnames, gravunits, gravval, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
        # check if input file is correct current version
        for name in gravnames:
            if 'start_time_A' in name:
                if 'A' not in choice:
                    choice.append('A')
            if 'start_time_B' in name:
                if 'B' not in choice:
                    choice.append('B')
            if 'start_time_SB4007_A' in name:
                if 'SB4007_A' not in choice:
                    choice.append('SB4007_A')
            if 'start_time_SB4007_B' in name:
                if 'SB4007_B' not in choice:
                    choice.append('SB4007_B')
            if 'start_time_SB4008_A' in name:
                if 'SB4008_A' not in choice:
                    choice.append('SB4008_A')
            if 'start_time_SB4008_B' in name:
                if 'SB4008_B' not in choice:
                    choice.append('SB4008_B')
            if 'start_time_SB3001_A' in name:
                if 'SB3001_A' not in choice:
                    choice.append('SB3001_A')
            if 'start_time_SB3001_B' in name:
                if 'SB3001_B' not in choice:
                    choice.append('SB3001_B')
            if 'start_time_SB3002_A' in name:
                if 'SB3002_A' not in choice:
                    choice.append('SB3002_A')
            if 'start_time_SB3002_B' in name:
                if 'SB3002_B' not in choice:
                    choice.append('SB3002_B')
            if 'start_time_SB3009_A' in name:
                if 'SB3009_A' not in choice:
                    choice.append('SB3009_A')
            if 'start_time_SB3009_B' in name:
                if 'SB3009_B' not in choice:
                    choice.append('SB3009_B')
            if 'start_time_SB3015/16_A' in name:
                if 'SB3015/16_A' not in choice:
                    choice.append('SB3015/16_A')
            if 'start_time_SB3015/16_B' in name:
                if 'SB3015/16_B' not in choice:
                    choice.append('SB3015/16_B')
            if 'Possum2' in name:
                if 'Possum2' not in choice:
                    choice.append('Possum2')
        for name in choice:
            line = f"Grav inputfile already exists for channel {name} at: {gravinputpath}"
            print(line)
            logs.append(line)

    if len(choice) == 0:
        check = 1

    if check == 1:  # Create input file if does not exist or correct version does not exist
        msg = f"Select Grav Channels Used. For 3000 series, select the appropriate sensorbox verison.\n" \
              f"Select your sensorbox version with the corresponding channel used. If you do not see your " \
              f"sensorbox version, select A or B"  # check for cannels used in grav filter
        title = 'Gitdone'
        channels = ['A', 'B', 'SB4007_A', 'SB4007_B', 'SB4008_A', 'SB4008_B', 'SB3001_A', 'SB3001_B',
                    'SB3002_A', 'SB3002_B', 'SB3009_A', 'SB3009_B', 'SB3015/16_A', 'SB3015/16_B', 'Possum2']
        choice = easygui.multchoicebox(msg, title, channels)  # Can choose both

        gravnames = ['variable']
        gravunits = {}
        gravval = {}
        gravunc = {}
        gravuval = {}

        # make header
        name = 'variable'
        gravunits[name] = 'units'
        gravval[name] = 'value'
        gravunc[name] = 'uncertainty'

    for c in choice:  # for each channel choice
        tempnames = []
        defaults = []
        for phase in phases:
            name = 'filterID_' + c + phase
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'text'
            if check == 1:
                defaults.append('')
            else:
                defaults.append(gravval[name])

            name = 'taremass_' + c + phase
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'g'
            if check == 1:
                defaults.append('')
            else:
                defaults.append(gravval[name])

            name = 'grossmass_' + c + phase
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'g'
            if check == 1:
                defaults.append('')
            else:
                defaults.append(gravval[name])

            name = 'start_time_' + c + phase
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'yyyymmdd hh:mm:ss'
            start = 'start_time' + phase
            if check == 1:
                defaults.append(timestring[start])
            else:
                defaults.append(gravval[name])

            name = 'end_time_' + c + phase
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'yyyymmdd hh:mm:ss'
            end = 'end_time' + phase
            if check == 1:
                defaults.append(timestring[end])
            else:
                defaults.append(gravval[name])

        if 'SB4007_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB4007_B' == c:  # 3002 has default grav flow value
            name = 'GravFlo2'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo2' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo2'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo2'])
        if 'SB4008_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB4008_B' == c:  # 3002 has default grav flow value
            name = 'GravFlo2'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo2' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo2'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo2'])
        if 'SB3001_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB3001_B' == c:  # 3002 has default grav flow value
            name = 'GravFlo2'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo2' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo2'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo2'])
        if 'SB3002_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB3002_B' == c:  # 3002 has default grav flow value
            name = 'GravFlo2'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo2' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo2'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo2'])
        if 'SB3009_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB3015/16_A' == c:  # 3002 has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])
        if 'SB3015/16_B' == c:  # 3002 has default grav flow value
            name = 'GravFlo2'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo2' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo2'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo2'])
        if 'Possum2' == c:  # possum has default grav flow value
            name = 'GravFlo1'
            gravnames.append(name)
            tempnames.append(name)
            gravunits[name] = 'lpm'
            [enames, eunits, eval, eunc, euval] = io.load_constant_inputs(energypath)  # Load energy metrics
            if check == 1:
                if 'GravFlo1' in enames:  # if data entry sheet has default flow value, grab that
                    defaults.append(euval['GravFlo1'])
                else:  # assign default value (can be changed later during csv creation
                    defaults.append(16.7)
            else:
                defaults.append(gravval['GravFlo1'])

        # GUI box to edit grav inputs
        zeroline = f'Enter grav input data (g)\n' \
                   f'Start and end times are from phase times but may be changed to reflect times the gravimetric pump was running.\n' \
                   f'GravFlo 1 and 2 are used for sensor boxes without digital flow meter in the gravimetric train. ' \
                   f'The default is derived from the critical orifice.'
        secondline = 'Click OK to continue\n'
        thirdline = 'Click Cancel to exit'
        msg = zeroline + secondline + thirdline
        title = 'Gitdone'
        fieldNames = tempnames
        height = len(fieldNames)
        width = max(len(fieldNames) for message in fieldNames)
        # currentvals=['', '', '', data['time'][0], data['time'][-1]]
        newvals = easygui.multenterbox(msg, title, fieldNames, values=defaults)  # , height = height)
        if newvals:
            if newvals != defaults:
                defaults = newvals
                for n, name in enumerate(tempnames):
                    gravval[name] = defaults[n]
        else:
            line = 'Error: Undefined variables'
            print(line)
            logs.append(line)

    io.write_constant_outputs(gravinputpath, gravnames, gravunits, gravval, gravunc, gravuval)
    line = '\nCreated phase times input file: ' + gravinputpath
    print(line)
    logs.append(line)

    ##################################

    # load grav filter weights input file
    [gravnames, gravunits, gravval, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
    gravnames = gravnames[1:]  # remove the first name because it is the header

    line = 'Loaded input file of gravimetric filter weights:' + gravinputpath
    print(line)
    logs.append(line)

    # Load previous background selections if they exist
    prev_bg_filter = gravval.get('bg_filter_choice', None)
    prev_bg_mass = gravval.get('bg_mass_baseline', None)

    # define test phases by reading the variable names in the grav input file
    phases = []  # initialize a list of test phases (low power, med power, high power)
    for name in gravnames:
        if gravval[name] != '':  # if the value is not blank
            try:
                spot = name.rindex('_')  # locate the last underscore
                phase = name[spot + 1:]  # grab the string after the last underscore
                if phase not in phases:  # if it is a new phase
                    phases.append(phase)  # add to the list of phases
            except:
                pass  # for GravFlo1

    # ===== NEW: Background filter selection =====
    bg_filter = None
    bg_mass = None

    if len(choice) == 2:
        # Extract the base channel names for comparison
        ch1, ch2 = choice[0], choice[1]

        # Determine if we have a pair of A and B variants
        is_pair = False
        pair_base = None

        if (ch1.endswith('_A') and ch2.endswith('_B')) or (ch1.endswith('_B') and ch2.endswith('_A')):
            # Get the base (e.g., 'SB4007' from 'SB4007_A')
            base1 = ch1[:-2]
            base2 = ch2[:-2]
            if base1 == base2:
                is_pair = True
                pair_base = base1
        elif (ch1 == 'A' and ch2 == 'B') or (ch1 == 'B' and ch2 == 'A'):
            is_pair = True
            pair_base = ''

        if is_pair:
            # Build option labels based on actual channels
            ch1_label = ch1 if ch1 in ['A', 'B'] else ch1
            ch2_label = ch2 if ch2 in ['A', 'B'] else ch2

            options = ['None', f'Background {ch1_label}', f'Background {ch2_label}', 'Baseline Weight']

            # Determine default option based on previous selection
            default_opt = None
            if prev_bg_filter == ch1:
                default_opt = f'Background {ch1_label}'
            elif prev_bg_filter == ch2:
                default_opt = f'Background {ch2_label}'
            elif prev_bg_mass:
                default_opt = 'Baseline Weight'
            else:
                default_opt = 'None'

            msg = "Would you like to designate a background filter and/or enter a baseline background weight?\n\n" \
                  "Select 'Background ' + channel, 'Baseline Weight', or 'None'."
            title = "Background Filter Options"
            bg_choice = easygui.choicebox(msg, title, options,
                                          preselect=options.index(default_opt) if default_opt in options else 0)

            if bg_choice == f'Background {ch1_label}':
                bg_filter = ch1
                line = f"Filter {ch1} designated as background filter."
                print(line)
                logs.append(line)
            elif bg_choice == f'Background {ch2_label}':
                bg_filter = ch2
                line = f"Filter {ch2} designated as background filter."
                print(line)
                logs.append(line)
            elif bg_choice == 'Baseline Weight':
                msg = "Enter baseline background weight (g):"
                title = "Baseline Background Weight"
                default_weight = str(prev_bg_mass) if prev_bg_mass else ''
                bg_mass_str = easygui.enterbox(msg, title, default=default_weight)
                if bg_mass_str:
                    try:
                        bg_mass = float(bg_mass_str)
                        line = f"Baseline background weight set to {bg_mass} g."
                        print(line)
                        logs.append(line)
                    except ValueError:
                        line = "Warning: Could not convert baseline weight to number. No background correction applied."
                        print(line)
                        logs.append(line)
    else:
        options = ['None', 'Baseline Weight']

        # Determine default option based on previous selection
        default_opt = None
        if prev_bg_filter == ch1:
            default_opt = f'Background {ch1_label}'
        elif prev_bg_filter == ch2:
            default_opt = f'Background {ch2_label}'
        elif prev_bg_mass:
            default_opt = 'Baseline Weight'
        else:
            default_opt = 'None'

        msg = "Would you like to designate a background filter and/or enter a baseline background weight?\n\n" \
              "Select 'Background ' + channel, 'Baseline Weight', or 'None'."
        title = "Background Filter Options"
        bg_choice = easygui.choicebox(msg, title, options,
                                      preselect=options.index(default_opt) if default_opt in options else 0)

        if bg_choice == f'Background {ch1_label}':
            bg_filter = ch1
            line = f"Filter {ch1} designated as background filter."
            print(line)
            logs.append(line)
        elif bg_choice == f'Background {ch2_label}':
            bg_filter = ch2
            line = f"Filter {ch2} designated as background filter."
            print(line)
            logs.append(line)
        elif bg_choice == 'Baseline Weight':
            msg = "Enter baseline background weight (g):"
            title = "Baseline Background Weight"
            default_weight = str(prev_bg_mass) if prev_bg_mass else ''
            bg_mass_str = easygui.enterbox(msg, title, default=default_weight)
            if bg_mass_str:
                try:
                    bg_mass = float(bg_mass_str)
                    line = f"Baseline background weight set to {bg_mass} g."
                    print(line)
                    logs.append(line)
                except ValueError:
                    line = "Warning: Could not convert baseline weight to number. No background correction applied."
                    print(line)
                    logs.append(line)

    # Save background selections to the grav input file for next time
    gravval['bg_filter_choice'] = bg_filter if bg_filter else ''
    gravval['bg_mass_baseline'] = str(bg_mass) if bg_mass else ''

    # Add to gravnames if not already present
    if 'bg_filter_choice' not in gravnames:
        gravnames.append('bg_filter_choice')
        gravunits['bg_filter_choice'] = 'text'
    if 'bg_mass_baseline' not in gravnames:
        gravnames.append('bg_mass_baseline')
        gravunits['bg_mass_baseline'] = 'g'

    io.write_constant_outputs(gravinputpath, gravnames, gravunits, gravval, gravunc, gravuval)
    line = '\nCreated phase times input file: ' + gravinputpath
    print(line)
    logs.append(line)

    line = '\nGravimetric PM mass concentration report:'
    print(line)
    logs.append(line)

    for phase in phases:
        line = '\nPhase:' + phase
        print(line)
        logs.append(line)

        line = 'Grav train'.ljust(12) + 'channel'.ljust(12) + 'net mass (g)'.ljust(20) + 'flow (lpm)'.ljust(
            20) + 'phase time (min)'.ljust(18) + 'PM conc (ug/m^3)'
        print(line)
        logs.append(line)

        line = '..........'.ljust(12) + '.......'.ljust(12) + '............'.ljust(20) + '..........'.ljust(
            20) + '................'.ljust(18) + '................'
        print(line)
        logs.append(line)

        # initialize dictionaries to calculate concentration
        flow = {}
        netmass = {}
        conc = {}
        goodtrains = []

        if 'A' in choice:
            startname = 'start_time_A_' + phase
            endname = 'end_time_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'B' in choice:
            startname = 'start_time_B_' + phase
            endname = 'end_time_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            try:
                duration = timeperiod(starttime, endtime)
            except:
                duration = ''
        elif 'SB4007_A' in choice:
            startname = 'start_time_SB4007_A_' + phase
            endname = 'end_time_SB4007_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB4007_B' in choice:
            startname = 'start_time_SB4007_B_' + phase
            endname = 'end_time_SB4007_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB4008_A' in choice:
            startname = 'start_time_SB4008_A_' + phase
            endname = 'end_time_SB4008_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB4008_B' in choice:
            startname = 'start_time_SB4008_B_' + phase
            endname = 'end_time_SB4008_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3001_A' in choice:
            startname = 'start_time_SB3001_A_' + phase
            endname = 'end_time_SB3001_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3001_B' in choice:
            startname = 'start_time_SB3001_B_' + phase
            endname = 'end_time_SB3001_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3002_A' in choice:
            startname = 'start_time_SB3002_A_' + phase
            endname = 'end_time_SB3002_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3002_B' in choice:
            startname = 'start_time_SB3002_B_' + phase
            endname = 'end_time_SB3002_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3009_A' in choice:
            startname = 'start_time_SB3009_A_' + phase
            endname = 'end_time_SB3009_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3009_B' in choice:
            startname = 'start_time_SB3009_B_' + phase
            endname = 'end_time_SB3009_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3015/16_A' in choice:
            startname = 'start_time_SB3015/16_A_' + phase
            endname = 'end_time_SB3015/16_A_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'SB3015/16_B' in choice:
            startname = 'start_time_SB3015/16_B_' + phase
            endname = 'end_time_SB3015/16_B_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        elif 'Possum2' in choice:
            startname = 'start_time_Possum2_' + phase
            endname = 'end_time_Possum2_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)
        else:
            startname = 'start_time_' + phase
            endname = 'end_time_' + phase
            starttime = gravval[startname]
            endtime = gravval[endname]
            duration = timeperiod(starttime, endtime)

        for train in ['A', 'B', 'SB4007_A', 'SB4007_B', 'SB4008_A', 'SB4008_B', 'SB3001_A', 'SB3001_B',
                      'SB3002_A', 'SB3002_B', 'SB3009_A', 'SB3009_B', 'SB3015/16_A', 'SB3015/16_B', 'Possum2']:
            # for each grav flow train
            line = (train + ':').ljust(12)

            tarename = 'taremass_' + train + '_' + phase
            grossname = 'grossmass_' + train + '_' + phase
            try:
                avename = gravtrain[train] + '_' + phase
            except:
                pass

            try:
                netmass[train] = gravuval[grossname] - gravuval[tarename]  # grams

                # ===== NEW: Apply background correction =====
                if bg_filter == 'A' and train.endswith('B'):
                    bg_net = gravuval['grossmass_' + pair_base + '_A_' + phase] - \
                             gravuval['taremass_' + pair_base + '_A_' + phase]
                    netmass[train] = netmass[train] - bg_net
                elif bg_filter == 'B' and train.endswith('A'):
                    bg_net = gravuval['grossmass_' + pair_base + '_B_' + phase] - \
                             gravuval['taremass_' + pair_base + '_B_' + phase]
                    netmass[train] = netmass[train] - bg_net
                elif bg_mass is not None and train != 'A' and train != 'B':
                    netmass[train] = netmass[train] - bg_mass

                if train == 'SB4007_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB4007_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'SB4008_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB4008_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'SB3001_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB3001_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'SB3002_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB3002_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'SB3009_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB3009_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'SB3015/16_A':
                    flow[train] = gravuval['GravFlo1']
                elif train == 'SB3015/16_B':
                    flow[train] = gravuval['GravFlo2']
                elif train == 'Possum2':
                    flow[train] = gravuval['GravFlo1']
                else:
                    flow[train] = aveuval[avename]
                conc[train] = calcPMconc(netmass[train], flow[train], duration)
                goodtrains.append(train)

                line = line + gravtrain[train].ljust(12)
                line = line + (str(round(netmass[train].n, 6)) + '+/-' + str(round(netmass[train].s, 6))).ljust(20)
                line = line + (str(round(flow[train].n, 3)) + '+/-' + str(round(flow[train].s, 3))).ljust(20)
                line = line + str(round(duration, 2)).ljust(18) + str(round(conc[train].n, 1)) + '+/-' + str(
                    round(conc[train].s, 1))

                name = f'PMsample_mass_{train}_{phase}'
                outnames.append(name)
                outunits[name] = 'g'
                outval[name] = netmass[train].n
                outuval[name] = netmass[train]

                name = f'Qsample_{train}_{phase}'
                outnames.append(name)
                outunits[name] = 'l/min'
                outval[name] = flow[train].n
                outuval[name] = flow[train]

                name = f'PMmass_{train}_{phase}'
                outnames.append(name)
                outunits[name] = 'ug/m^3'
                outval[name] = conc[train].n
                outuval[name] = conc[train]

            except KeyError:
                line = line + '---'.ljust(12) + '---'.ljust(20) + '---'.ljust(20) + '---'.ljust(18) + '---'

            print(line)
            logs.append(line)

        # define which flow trains are used for the total calculation
        if 'A' in goodtrains and 'B' in goodtrains:
            chan = 'both'
        elif 'A' in goodtrains:
            chan = gravtrain['A']
        elif 'B' in goodtrains:
            chan = gravtrain['B']
        elif '4007_A' in goodtrains:
            chan = gravtrain['SB4007_A']
        elif '4007_B' in goodtrains:
            chan = gravtrain['SB4007_B']
        elif '4008_A' in goodtrains:
            chan = gravtrain['SB4008_A']
        elif '4008_B' in goodtrains:
            chan = gravtrain['SB4008_B']
        elif '3001_A' in goodtrains:
            chan = gravtrain['SB3001_A']
        elif '3001_B' in goodtrains:
            chan = gravtrain['SB3001_B']
        elif '3002_A' in goodtrains:
            chan = gravtrain['SB3002_A']
        elif '3002_B' in goodtrains:
            chan = gravtrain['SB3002_B']
        elif '3009_A' in goodtrains:
            chan = gravtrain['SB3009_A']
        elif '3009_B' in goodtrains:
            chan = gravtrain['SB3009_B']
        elif 'SB3015/16_A' in goodtrains:
            chan = gravtrain['SB3015/16_A']
        elif 'SB3015/16_B' in goodtrains:
            chan = gravtrain['SB3015/16_B']
        elif 'Possum2' in goodtrains:
            chan = gravtrain['Possum2']
        else:
            chan = ''

        # calculate total concentration from both flow trains
        if bg_filter == 'A':
            for name in netmass:
                if name.endswith('B'):
                    filterkey = name
            totalnetmass = netmass[filterkey]
        elif bg_filter == 'B':
            for name in netmass:
                if name.endswith('A'):
                    filterkey = name
            totalnetmass = netmass[filterkey]
        else:
            totalnetmass = sum(netmass.values())
        name = 'PMsample_mass_' + phase
        outuval[name] = totalnetmass
        outnames.append(name)
        outunits[name] = 'g'

        totalflow = sum(flow.values())
        name = 'Qsample_' + phase
        outuval[name] = totalflow
        outnames.append(name)
        outunits[name] = 'l/min'

        name = 'phase_time_' + phase
        outuval[name] = duration
        outnames.append(name)
        outunits[name] = 'min'

        name = 'PMmass_' + phase
        outuval[name] = calcPMconc(totalnetmass, totalflow, duration)
        outnames.append(name)
        outunits[name] = 'ug/m^3'

        try:
            line = 'total:'.ljust(12) + chan.ljust(12) + (
                        str(round(totalnetmass.n, 6)) + '+/-' + str(round(totalnetmass.s, 6))).ljust(20)
        except:
            line = 'total:'.ljust(12) + chan.ljust(12) + (str(round(totalnetmass, 6)))
        try:
            line = line + (str(round(totalflow.n, 3)) + '+/-' + str(round(totalflow.s, 3))).ljust(20)
        except:
            line = line + (str(round(totalflow, 3))).ljust(20)
        try:
            line = line + str(round(duration, 2)).ljust(18) + str(round(outuval[name].n, 1)) + '+/-' + str(
                round(outuval[name].s, 1))
        except:
            line = line + str(duration).ljust(18) + str(outuval[name])
        print(line)
        logs.append(line)

    # make header for output file
    name = 'variable_name'
    outnames = [name] + outnames
    outunits[name] = 'units'
    outval[name] = 'value'
    outunc[name] = 'uncertainty'

    # print grav output metrics data file
    io.write_constant_outputs(gravoutputpath, outnames, outunits, outval, outunc, outuval)

    line = '\ncreated gravimetric PM output file:\n' + gravoutputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)

    return logs, gravval, outval, gravunits, outunits


def calcPMconc(Netmass, Flow, Duration):
    # function calculates PM mass concentration
    # inputs: Netmass (g), Flow (l/min), Duration (minutes)
    try:
        PMconc = Netmass / Flow / Duration * 1000000 * 1000  # (ug/m^3), correction factors = 1,000,000 ug/g    and   1,000 liters/m^3
    except:
        try:
            PMconc = Netmass.n / Flow / Duration * 1000000 * 1000
        except:
            PMconc = ''
    return PMconc


def timeperiod(StartTime, EndTime):
    # function calculates time difference in minutes
    # Inputs start and end times as strings and converts to time objects
    try:
        start_object = dt.strptime(StartTime, '%Y%m%d %H:%M:%S')
        end_object = dt.strptime(EndTime, '%Y%m%d %H:%M:%S')
    except:
        start_object = dt.strptime(StartTime, '%H:%M:%S')
        end_object = dt.strptime(EndTime, '%H:%M:%S')
    delta_object = end_object - start_object
    Time = delta_object.total_seconds() / 60
    return Time


#######################################################################
# run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, gravoutputpath, logpath)