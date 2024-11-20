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

matplotlib.use('Agg')

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


def LEMS_BlackCarbon(directory, testname, bcinputpath, bcoutputpath, gravinputpath, gravoutputpath, logpath,
                     inputmethod):
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

    bcnames = []  # List of metric names
    bcunits = {}  # Dictionary of units, key is names
    bcval = {}  # Dictionary of values, key is names
    bcuval = {}  # Dictionary of uncertainties, key is names
    bcunc = {}  # Dictionary of values and uncertainties as ufloats, key is name

    defaults = []  # List of default values for user prompt

    # make header
    name = 'variable'
    bcnames.append(name)
    bcunits[name] = 'units'
    bcval[name] = 'value'
    bcunc[name] = 'uncertainty'

    # Find filter pictures
    filters = []
    phases = {}
    [gravnames, gravunits, gravvals, gravunc, gravuval] = io.load_constant_inputs(gravinputpath)
    line = 'Loaded ' + gravinputpath
    print(line)
    logs.append(line)

    for name in gravnames:
        if 'filterID' in name:  # Find filter numbers
            if gravvals[name] != '':
                filter = gravvals[name]
                filters.append(filter)
                phase = name[len(name) - 2:]
                phases[filter] = phase

                name = 'filterRadius_' + filter
                bcnames.append(name)
                bcunits[name] = 'mm'
                defaults.append(1.95)

    # check for BCpath
    if os.path.isfile(bcinputpath):
        # load bc input file
        [bcnames, bcunits, bcval, bcunc, bcuval] = io.load_constant_inputs(bcinputpath)
        line = f'loaded: {bcinputpath}'
        print(line)
        logs.append(line)
        defaults = []
        for name in bcnames[1:]:
            defaults.append(bcval[name])

    if inputmethod == '1':  # If in interactive mode
        message = 'Enter filter inputs needed for calculation.\n Click OK to continue.\n Click Cancel to exit.'
        title = 'Filter Inputs'
        newvals = easygui.multenterbox(message, title, bcnames[1:], values=defaults)
        if newvals:
            for i, name in enumerate(bcnames[1:]):
                bcval[name] = newvals[i]

        io.write_constant_outputs(bcinputpath, bcnames, bcunits, bcval, bcunc, bcuval)
        line = 'Created bc input file: ' + bcinputpath
        print(line)
        logs.append(line)

    # Load gravimetric metrics
    [gravonames, gravounits, gravovals, gravounc, gravouval] = io.load_constant_inputs(gravoutputpath)
    line = 'Loaded ' + gravoutputpath
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

    for filter in filters:  # For each filter
        fail = 0
        filterRadius = bcval['filterRadius_' + filter]

        bcpicpath = os.path.join(directory, testname + '_' + filter + '.jpeg')  # Path to filter picture
        # (foldername_filter number)
        debugpath = os.path.join(directory, testname + '_' + filter + '_Debug.jpg')  # Path to filter with detection
        # (foldername_filter number_Debug)

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
                    print(f'QR code: {qr}')
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
                print(f'grey bars: {grayBars}')

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

                if inputmethod == '1':
                    # show and save the debug image
                    drawing.show()
                drawing.save(debugpath)
                line = f'Please check the image: {debugpath} and verify that everything was detected correctly. ' \
                       f'If not, retake image.'
                print(line)
                logs.append(line)

                print(f'BC Filter: {bcFilter}')

                # Gives the RGB in the filter
                sampledRGB = bcFilter[0].sample(image, bcFilter[0].radius / MainConstants.samplingfactorfixed)
                print(f'sampled RGB: {sampledRGB}')

                exposedTime = gravovals['phase_time_' + phases[filter]]
                airFlowRate = gravovals['Qsample_' + phases[filter]]

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

                print(f'Results: {bccResult}')

                # calculate BC
                bcLoading = bccResult.BCAreaRed
                name = 'BCloading_' + filter + '_' + phases[filter]
                names.append(name)
                units[name] = 'ug/cm^2'
                data[name] = bcLoading

                bccCalcs = computeBCC(filterRadius, bcLoading, exposedTime, airFlowRate)
                print(f'Results: {bccCalcs}')

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
########################################################################
# run function as executable if not called by another function


if __name__ == "__main__":
    LEMS_BlackCarbon(directory, testname, bcinputpath, bcoutputpath, gravinputpath, gravoutputpath, logpath, inputmethod)
