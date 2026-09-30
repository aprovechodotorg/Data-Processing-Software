# v0.0 Python3

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

import matplotlib
import os.path
import logging
import pylab
import cv2
from PIL import Image
import numpy as np
import easygui
from datetime import datetime as dt
import traceback
from IANASettings.Settings import MainConstants
from IANASteps.QRDetector.QRDetector import detectQR, QR_Radial
from IANASteps.Calibrator.Calibrator import getGrayBarsRadial
from IANASteps.BCFilterDetector.BCFilterFixedDetector import detectBCFilterFixed
from IANASteps.BCCCalculator.BCCCalculator import rateFilter, computeBCC
from IANASettings.Settings import ResizeImageConstants, BCFilterFixedConstants
import LEMS_DataProcessing_IO as io

matplotlib.use('TkAgg')

# Inputs to run script directly ##################################################
bcpicpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\image0.jpeg"
debugpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\image0_Debug.jpeg"
bcinputpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\BC test pics_BCInputs.csv"
bcoutputpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\BC test pics_BCOutputs.csv"
gravinputpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\BC test pics_GravInputs.csv"
gravoutputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\" \
                 "IDCTests data\\5.31\\5.31_GravOutputs.csv"
logpath = "C:\\Users\\Jaden\\Documents\\BC test pics\\log.txt"
directory = "C:\\Users\\Jaden\\Documents\\BC test pics\\"
testname = "image0"
inputmethod = '1'
#####################################################################################


def LEMS_BlackCarbon(bcinputpath, bcoutputpath, gravinputpath, gravoutputpath, logpath, inputmethod):
    # Function Purpose: Find photos of filters in the data folder, process photos to find the r value of the filter
    # and correct using the gradient around the photo. Fit the value to the loading curve to find the loading value
    # of black carbon. Intake other filter metrics to determine black carbon total and emission rate

    # Inputs:
    # directory: the folder path
    # testname: folder name
    # bc inputpath: inputs of black crabon filter (radius of each filter) (read if it exists)
    # gravinputpath: inputs for gravimetric sample (filter numbers)
    # gravoutputs: metrics for gravimetric sample (phase time, flow rate)
    # inputmethod: 1 interactive mode or 2 non-interactive mode

    # Outputs:
    # bc inputpath: inputs of black crabon filter (radius of each filter)
    # bcoutputs: Metrics of black carbon
    # logpath: logs of noteable events

    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_BlackCarbon v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    directory, filename = os.path.split(bcinputpath)
    datadirectory, testname = os.path.split(directory)

    # Step 1: Load GravInputs (always, for fallback)
    gravnames = []
    gravunits = {}
    gravvals = {}
    gravunc = {}
    gravuval = {}
    if os.path.isfile(gravinputpath):
        [gravnames, gravunits, gravvals, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
        line = 'Loaded ' + gravinputpath
        print(line)
        logs.append(line)
    else:
        line = 'Warning: GravInputs file not found: ' + gravinputpath
        print(line)
        logs.append(line)

    # Step 2: Load GravOutputs early (always, for fallback)
    gravonames = []
    gravounits = {}
    gravovals = {}
    gravounc = {}
    gravouval = {}
    if os.path.isfile(gravoutputpath):
        [gravonames, gravounits, gravovals, gravounc, gravouval] = io.load_constant_inputs(gravoutputpath)
        line = 'Loaded ' + gravoutputpath
        print(line)
        logs.append(line)
    else:
        line = 'Warning: GravOutputs file not found: ' + gravoutputpath
        print(line)
        logs.append(line)

    # Step 5 (check early): Check if BCInputs already exists and load it
    existing_bcnames = []
    existing_bcunits = {}
    existing_bcval = {}
    existing_bcunc = {}
    existing_bcuval = {}
    if os.path.isfile(bcinputpath):
        [existing_bcnames, existing_bcunits, existing_bcval, existing_bcunc, existing_bcuval] = io.load_constant_inputs(bcinputpath)
        line = f'loaded: {bcinputpath}'
        print(line)
        logs.append(line)

    # Step 3: Discover phases from gravnames (filterID_* keys) or existing BCInputs
    phases_discovered = []
    grav_phase_filters = {}
    for name in gravnames:
        if 'filterID' in name:
            phase = name[name.rindex('_') + 1:] if '_' in name else name[len(name) - 2:]
            val = str(gravvals.get(name, '')).strip()
            if val != '':
                grav_phase_filters[phase] = val
                if phase not in phases_discovered:
                    phases_discovered.append(phase)

    # Also discover phases present in existing BCInputs if any
    for name in existing_bcnames:
        if name.startswith('filterID_'):
            phase = name[len('filterID_'):]
            val = str(existing_bcval.get(name, '')).strip()
            if val != '' and phase not in phases_discovered:
                phases_discovered.append(phase)

    # Step 4: Build bcnames / bcval / bcunits / bcunc / bcuval with fallback logic
    bcnames = ['variable']
    bcunits = {'variable': 'units'}
    bcval = {'variable': 'value'}
    bcunc = {'variable': 'uncertainty'}
    bcuval = {}

    popup_names = []
    active_filters = []

    for phase in phases_discovered:
        # Determine filterID for this phase: try existing_bcval first, else gravvals fallback
        fid_key = 'filterID_' + phase
        if fid_key in existing_bcval and str(existing_bcval[fid_key]).strip() != '':
            filter_val = str(existing_bcval[fid_key]).strip()
        else:
            filter_val = grav_phase_filters.get(phase, '')

        # Edge case: filterID_<phase> is blank (no filter used in that phase) -> skip phase
        if filter_val == '':
            continue

        if filter_val not in active_filters:
            active_filters.append(filter_val)

        # 1. filterID_<phase>
        bcnames.append(fid_key)
        popup_names.append(fid_key)
        bcunits[fid_key] = 'text'
        bcval[fid_key] = filter_val
        bcunc[fid_key] = existing_bcunc.get(fid_key, '')

        # 2. phase_time_<phase>
        pt_key = 'phase_time_' + phase
        bcnames.append(pt_key)
        popup_names.append(pt_key)
        bcunits[pt_key] = 'min'
        if pt_key in existing_bcval and str(existing_bcval[pt_key]).strip() != '':
            bcval[pt_key] = existing_bcval[pt_key]
        elif pt_key in gravovals and str(gravovals[pt_key]).strip() != '':
            bcval[pt_key] = gravovals[pt_key]
        else:
            bcval[pt_key] = ''
            line = f'Warning: {pt_key} missing in GravOutputs'
            print(line)
            logs.append(line)
        bcunc[pt_key] = existing_bcunc.get(pt_key, '')

        # 3. Qsample_<phase>
        qs_key = 'Qsample_' + phase
        bcnames.append(qs_key)
        popup_names.append(qs_key)
        bcunits[qs_key] = 'l/min'
        if qs_key in existing_bcval and str(existing_bcval[qs_key]).strip() != '':
            bcval[qs_key] = existing_bcval[qs_key]
        elif qs_key in gravovals and str(gravovals[qs_key]).strip() != '':
            bcval[qs_key] = gravovals[qs_key]
        else:
            bcval[qs_key] = ''
            line = f'Warning: {qs_key} missing in GravOutputs'
            print(line)
            logs.append(line)
        bcunc[qs_key] = existing_bcunc.get(qs_key, '')

    # Filter radius for each active filter
    for f in active_filters:
        rad_key = 'filterRadius_' + f
        bcnames.append(rad_key)
        popup_names.append(rad_key)
        bcunits[rad_key] = 'mm'
        if rad_key in existing_bcval and str(existing_bcval[rad_key]).strip() != '':
            bcval[rad_key] = existing_bcval[rad_key]
        else:
            bcval[rad_key] = 1.95
        bcunc[rad_key] = existing_bcunc.get(rad_key, '')

    # Preserve any other keys from existing BCInputs (e.g. inactive filterRadius) in bcval/bcnames (not in popup)
    for key in existing_bcnames:
        if key not in bcnames:
            bcnames.append(key)
            bcval[key] = existing_bcval[key]
            bcunits[key] = existing_bcunits.get(key, '')
            bcunc[key] = existing_bcunc.get(key, '')
            if key in existing_bcuval:
                bcuval[key] = existing_bcuval[key]

    # Step 6: If inputmethod == '1', show popup (grouped by phase, then filterRadius)
    defaults = [bcval[name] for name in popup_names]
    if inputmethod == '1':
        message = 'Enter filter inputs needed for calculation.\n Click OK to continue.\n Click Cancel to exit.'
        title = 'Filter Inputs'
        newvals = easygui.multenterbox(message, title, popup_names, values=defaults)
        # Step 7: Apply popup edits -> bcval
        if newvals:
            for i, name in enumerate(popup_names):
                bcval[name] = newvals[i]

    # Step 9: Re-derive filters and phases dicts from bcval['filterID_<phase>'] values
    filters = []
    phases = {}
    for phase in phases_discovered:
        fid_key = 'filterID_' + phase
        if fid_key in bcval:
            f_id = str(bcval[fid_key]).strip()
            if f_id != '':
                if f_id not in filters:
                    filters.append(f_id)
                phases[f_id] = phase
                rad_key = 'filterRadius_' + f_id
                if rad_key not in bcval:
                    bcval[rad_key] = 1.95
                    bcunits[rad_key] = 'mm'
                    bcunc[rad_key] = ''
                if rad_key not in bcnames:
                    bcnames.append(rad_key)

    for name in list(bcval.keys()):
        if name.startswith('filterID_'):
            phase = name[len('filterID_'):]
            f_id = str(bcval[name]).strip()
            if f_id != '' and f_id not in filters:
                filters.append(f_id)
                phases[f_id] = phase
                rad_key = 'filterRadius_' + f_id
                if rad_key not in bcval:
                    bcval[rad_key] = 1.95
                    bcunits[rad_key] = 'mm'
                    bcunc[rad_key] = ''
                if rad_key not in bcnames:
                    bcnames.append(rad_key)

    # Step 8: Write entire bcval -> BCInputs (bcinputpath)
    io.write_constant_outputs(bcinputpath, bcnames, bcunits, bcval, bcunc, bcuval)
    line = 'Created bc input file: ' + bcinputpath
    print(line)
    logs.append(line)

    names = []  # List of variable names
    data = {}  # Dictionary of values, key is names
    units = {}  # Dictionary of units, key is names
    unc = {}  # Dicionary of uncertainty values, key is names
    uval = {}  # Dictionary of values and uncertainties as ufloats, key is names

    name = 'variable'
    names.append(name)
    units[name] = 'unit'
    data[name] = 'value'

    pic_list = []

    for filter in filters:  # For each filter
        fail = 0
        filterRadius = bcval['filterRadius_' + filter]

        bcpicpath = os.path.join(directory, testname + '_' + filter + '.jpeg')  # Path to filter picture
        # (foldername_filter number)
        debugpath = os.path.join(directory, testname + '_' + filter + '_Debug.jpg')  # Path to filter with detection
        # (foldername_filter number_Debug)

        pic_list.append(debugpath)

        if os.path.isfile(bcpicpath):  # check if the given image file exists
            image = Image.open(bcpicpath)
            imageoldest = image
            line = f'opened: {bcpicpath}'
            print(line)
            logs.append(line)
            skip = 0
        else:
            bcpicpath = bcpicpath[:-4] + 'jpg'  # try JPG instead of jpeg
            if os.path.isfile(bcpicpath):
                image = Image.open(bcpicpath)
                imageoldest = image
                line = f'opened: {bcpicpath}'
                print(line)
                logs.append(line)
                skip = 0
            else:
                bcpicpath = bcpicpath[:-3] + 'png'  # try png instead of jpeg
                if os.path.isfile(bcpicpath):
                    image = Image.open(bcpicpath)
                    imageoldest = image
                    line = f'opened: {bcpicpath}'
                    print(line)
                    logs.append(line)
                    skip = 0
                else:
                    # there's no file, exit from program
                    line = f'file path {bcpicpath} does not exist. Nothing was processed.'
                    print(line)
                    logs.append(line)
                    skip = 1

        if skip == 0:  # if image was found
            # resize image so all images input are the same size
            width = ResizeImageConstants.LargestSide[0]
            length = ResizeImageConstants.LargestSide[1]
            image = image.resize((width, length))  # resize to a square
            imageolder = image
            image.save(debugpath)
            try:
                qrnew = detectQR(debugpath)  # Find the 4 QR codes and return their coordinates
                qr = qrnew
            except IndexError:
                image = imageoldest
                image.save(debugpath)
                line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:' \
                       f'\n' \
                       f'   Reduce glare (especially on black squares)\n' \
                       f'   Avoid shadows\n' \
                       f'   Make paper as square as possible'
                print(line)
                logs.append(line)
                fail = 1
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

            while fail == 0:
                # transform image so the height and width between QR codes is consistent
                # convert image to numpy array
                image = np.array(image)
                # define origional points as qr coordinates
                og_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[1][0], qr.points[1][1]],
                                        [qr.points[3][0], qr.points[3][1]]])
                # new points shift the bottom right point down from the top right by 600 and over from top left by 470
                new_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[0][0] + 500, qr.points[1][1]],
                                         [qr.points[3][0], qr.points[1][1] + 600]])
                # create a matrix
                M = cv2.getAffineTransform(og_points, new_points)
                # warp image according to matrix
                image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

                # Convert the NumPy array back to an image
                image = Image.fromarray(image)
                imageold = image
                # save image
                image.save(debugpath)
                # get QR coordinates again
                try:
                    qrnew = detectQR(debugpath)
                    qr = qrnew
                except IndexError:
                    image = imageolder
                    image.save(debugpath)
                    line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:\n' \
                           f'   Reduce glare (especially on black squares)\n' \
                           f'   Avoid shadows\n' \
                           f'   Make paper as square as possible'
                    print(line)
                    logs.append(line)
                    fail = 1
                except Exception as e:
                    traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

                # transform image given 4 points to fix image skew

                # convert image to nupy array
                image = np.array(image)

                # define origional points from qr coordinates
                top_left = [qr.points[0][0], qr.points[0][1]]
                top_right = [qr.points[1][0], qr.points[1][1]]
                bottom_left = [qr.points[2][0], qr.points[2][1]]
                bottom_right = [qr.points[3][0], qr.points[3][1]]

                og_points = np.float32([top_left, top_right, bottom_left, bottom_right])

                # define new values based on how QR codes are supposed to line up
                new_top_left = [qr.points[0][0], qr.points[0][1]]
                new_top_right = [qr.points[1][0], qr.points[0][1]]
                new_bottom_left = [qr.points[0][0] + 30, qr.points[3][1] - 40]
                new_bottom_right = [qr.points[1][0], qr.points[3][1]]

                new_points = np.float32([new_top_left, new_top_right, new_bottom_left, new_bottom_right])

                # Execute getAffineTransform to generate transformation matrix
                M = cv2.getPerspectiveTransform(og_points, new_points)
                # Feed into warpAffrine function to perform skew
                image = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))

                # convert image from array
                image = Image.fromarray(image)
                # save image
                image.save(debugpath)
                # get qr coordinates again
                try:
                    qrnew = detectQR(debugpath)
                    #print(f'QR code: {qr}')
                    qr = qrnew
                except IndexError:
                    image = imageold
                    image.save(debugpath)
                    line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:\n' \
                           f'   Reduce glare (especially on black squares)\n' \
                           f'   Avoid shadows\n' \
                           f'   Make paper as square as possible'
                    print(line)
                    logs.append(line)
                    fail = 1
                except Exception as e:
                    traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)

                # draw blue squares around where each qr code was detected for verification
                drawing = np.array(image)
                for loc in qr.points:
                    top_left = (int(loc[0] - 15), int(loc[1] - 15))
                    bottom_right = (int(loc[0] + 15), int(loc[1] + 15))

                    # Draw the blue square on the image
                    cv2.rectangle(drawing, top_left, bottom_right, (255, 0, 0), 2)
                drawing = Image.fromarray(drawing)

                # save to debug image
                drawing.save(debugpath)

                # Extract Data from the Calibrator - return debug image with squares around each graybar
                grayBars, drawing = getGrayBarsRadial(qr, debugpath)
                #print(f'grey bars: {grayBars}')

                # store the gray bar RGB averages in an array called "gradient"
                gradient = []

                for i in range(0, 10):
                    R_avg = 0
                    G_avg = 0
                    B_avg = 0
                    for grayBar in grayBars[i::10]:
                        R, G, B = grayBar.sample(image)
                        R_avg = R_avg + R
                        G_avg = G_avg + G
                        B_avg = B_avg + B
                    gradient.append([R_avg / 4.0, G_avg / 4.0, B_avg / 4.0])

                sampledRGB = None

                # specify that we're using the radial identification card
                tags = 'radial'
                # find the filter using the qr coordianates and traveling a fixed distance from them -
                # circle what is being sampled for rgb values
                bcFilter, drawing = detectBCFilterFixed(qr, BCFilterFixedConstants, drawing, tags)

                #if inputmethod == '1':
                    # show and save the debug image
                    #drawing.show()
                drawing.save(debugpath)
                line = f'Please check the image: {debugpath} and verify that everything was detected correctly. ' \
                       f'If not, retake image.'
                print(line)
                logs.append(line)

                #print(f'BC Filter: {bcFilter}')

                # Gives the RGB in the filter
                sampledRGB = bcFilter[0].sample(image, bcFilter[0].radius / MainConstants.samplingfactorfixed)
                #print(f'sampled RGB: {sampledRGB}')

                exposedTime = bcval['phase_time_' + phases[filter]]
                airFlowRate = bcval['Qsample_' + phases[filter]]

                # BC_TOT used for gradient values
                # BC tot
                bcGradient =pylab.array([1.237, 1.523, 1.898, 2.387, 3.027, 3.864, 4.958, 6.389, 8.259, 10.704])

                # Alternative gradients
                # bcGradient = pylab.array([0.538, 0.778, 1.103, 1.543, 2.140, 2.951, 4.049, 5.539, 7.558, 10.297])
                # bcGradient = pylab.array([0.352, 0.367, 0.629, 1.037, 1.816, 2.500, 3.513, 4.837, 7.216, 10.139])
                line = 'BC_TOT used as calibration method'
                print(line)
                logs.append(line)

                # Compute BCC
                bccResult = rateFilter(sampledRGB, bcGradient, gradient)

                #print(f'Results: {bccResult}')

                # calculate BC
                bcLoading = bccResult.BCAreaRed
                name = 'BCloading_' + filter + '_' + phases[filter]
                names.append(name)
                units[name] = 'ug/cm^2'
                data[name] = bcLoading

                bccCalcs = computeBCC(filterRadius, bcLoading, exposedTime, airFlowRate)
                #print(f'Results: {bccCalcs}')

                name = 'BCconcentration_' + filter + '_' + phases[filter]
                names.append(name)
                units[name] = 'cm^3/ug'
                data[name] = bccCalcs['concentration']

                name = 'BCmass_' + filter + '_' + phases[filter]
                names.append(name)
                units[name] = 'ug'
                data[name] = bccCalcs['weight']

                name = 'BCemissionrate_' + filter + '_' + phases[filter]
                names.append(name)
                units[name] = 'ug/min'
                data[name] = bccCalcs['emissionrate']

                for name in bcnames:
                    if filter in name:
                        names.append(name)
                        units[name] = bcunits[name]
                        data[name] = bcval[name]
                fail = 1

    io.write_constant_outputs(bcoutputpath, names, units, data, unc, uval)
    line = 'Created BC results: ' + bcoutputpath
    print(line)
    logs.append(line)

    # write to logs
    io.write_logfile(logpath, logs)

    return logs, data, units, pic_list
########################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_BlackCarbon(directory, testname, bcinputpath, bcoutputpath, gravinputpath, gravoutputpath, logpath, inputmethod)
