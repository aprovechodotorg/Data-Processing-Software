#v0.0 Python3

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

matplotlib.use('Agg')
import os.path
import logging
import pylab
import cv2
from PIL import Image
import numpy as np
import easygui
from datetime import datetime as dt
import traceback

from IANASettings.Settings import ExitCode, MainConstants, CalibratorConstants
from IANASteps.QRDetector.QRDetector import detectQR, QR_Radial
from IANASteps.Calibrator.Calibrator import getGrayBarsRadial, getBlackWhiteRadial, getGrayBarsLinear
from IANASteps.BCFilterDetector.BCFilterDetector import splitToBands, detectBCFilter, select#, PsycoInit
from IANASteps.BCFilterDetector.BCFilterFixedDetector import detectBCFilterFixed
from IANASteps.BCCCalculator.BCCCalculator import rateFilter, computeBCC
from IANASettings.Settings import ResizeImageConstants, BCFilterConstants, BCFilterFixedConstants

import LEMS_DataProcessing_IO as io

bcpicpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_2041_Filter.JPG"
debugpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_2041_DebugFilter.png"
bcinputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCInputs.csv"
bcoutputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCOutputs.csv"
gravpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_GravOutputs.csv"
logpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_log.txt"

def LEMS_BlackCarbon(bcpicpath, debugpath, bcinputpath, bcoutputpath, gravpath, logpath):
    '''Main script for black carbon function, takes in image of filter with the newer nextleaf sheet.
    Takes in outputs from the gravametric filter to calculate BC. Saves image showing dectected areas.'''
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_BlackCarbon v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    tags =" IANAMAIN"

    if os.path.isfile(bcpicpath): #check if the given image file exists
        image = Image.open(bcpicpath)
        line = f'opened: {bcpicpath}'
        print(line)
        logs.append(line)
    else:
        bcpicpath = bcpicpath[:-3] + 'JPG' #try JPG instead of PNG
        if os.path.isfile(bcpicpath):
            image = Image.open(bcpicpath)
            line = f'opened: {bcpicpath}'
            print(line)
            logs.append(line)
        else: #there's no file, exit from program
            line = f'file path {bcpicpath} does not exist. Nothing was processed.'
            print(line)
            logs.append(line)
            exit()

    #resize image so all images input are the same size
    for resizeSize in ResizeImageConstants.LargestSide:
        image = image.resize((resizeSize, resizeSize)) #resize to a square
        image.save(debugpath)
        try:
            qr = detectQR(debugpath, tags, logging.DEBUG) #Find the 4 QR codes and return their coordinates
        except:
            line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:\n' \
                   f'   Reduce glare (especially on black squares)\n' \
                   f'   Avoid shadows\n' \
                   f'   Make paper as square as possible'
            print(line)
            logs.append(line)

    # transform image so the height and width between QR codes is consistent
    #convert image to numpy array
    image = np.array(image)
    #define origional points as qr coordinates
    og_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[1][0], qr.points[1][1]],
                            [qr.points[3][0], qr.points[3][1]]])
    #new points shift the bottom right point down from the top right by 600 and over from top left by 470
    new_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[0][0] + 470, qr.points[1][1]],
                             [qr.points[3][0], qr.points[1][1] + 600]])
    #create a matrix
    M = cv2.getAffineTransform(og_points, new_points)
    #warp image according to matrix
    image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    # Convert the NumPy array back to an image
    image = Image.fromarray(image)
    #save image
    image.save(debugpath)
    #get QR coordinates again
    try:
        qr = detectQR(debugpath, tags, logging.DEBUG)
    except:
        line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:\n' \
               f'   Reduce glare (especially on black squares)\n' \
               f'   Avoid shadows\n' \
               f'   Make paper as square as possible'
        print(line)
        logs.append(line)

    #transform image given 4 points to fix image skew

    #convery image to nupy array
    image = np.array(image)

    #define origional points from qr coordinates
    top_left = [qr.points[0][0], qr.points[0][1]]
    top_right = [qr.points[1][0], qr.points[1][1]]
    bottom_left = [qr.points[2][0], qr.points[2][1]]
    bottom_right = [qr.points[3][0], qr.points[3][1]]

    og_points = np.float32([top_left, top_right, bottom_left, bottom_right])

    #define new values based on how QR codes are supposed to line up
    new_top_left = [qr.points[0][0], qr.points[0][1]]
    new_top_right = [qr.points[1][0], qr.points[0][1]]
    new_bottom_left = [qr.points[0][0] + 30, qr.points[3][1] - 40]
    new_bottom_right = [qr.points[1][0], qr.points[3][1]]

    new_points = np.float32([new_top_left, new_top_right, new_bottom_left, new_bottom_right])

    # Execute getAffineTransform to generate transformation matrix
    M = cv2.getPerspectiveTransform(og_points, new_points)
    # Feed into warpAffrine function to perform skew
    image = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))

    #convert image from array
    image = Image.fromarray(image)
    #save image
    image.save(debugpath)
    #get qr coordinates again
    try:
        qr = detectQR(debugpath, tags, logging.DEBUG)
        print(f'QR code: {qr}')
    except Exception as e:
        line = f'Picture: {bcpicpath} cannot be orriented correctly. Please retake picture make sure to:\n' \
               f'   Reduce glare (especially on black squares)\n' \
               f'   Avoid shadows\n' \
               f'   Make paper as square as possible'
        print(line)
        logs.append(line)
        traceback.print_exception(type(e), e, e.__traceback__)  # Print error message with line number)
        exit()

    #draw blue squares around where each qr code was detected for verification
    drawing = np.array(image)
    for loc in qr.points:
        top_left = (int(loc[0] - 15), int(loc[1] - 15))
        bottom_right = (int(loc[0] + 15), int(loc[1] + 15))

        # Draw the blue square on the image
        cv2.rectangle(drawing, top_left, bottom_right, (255, 0, 0), 2)
    drawing = Image.fromarray(drawing)

    #save to debug image
    drawing.save(debugpath)

    # Extract Data from the Calibrator - return debug image with squares around each graybar
    grayBars, drawing, exitcode = getGrayBarsRadial(qr, debugpath, tags, logging.DEBUG)
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

    #specify that we're using the radial identification card
    tags = 'radial'
    #find the filter using the qr coordianates and traveling a fixed distance from them - circle what is being sampled for rgb values
    bcFilter, drawing, exitcode = detectBCFilterFixed(qr, BCFilterFixedConstants, drawing, tags, logging.DEBUG)

    #show and savethe debug image
    drawing.show()
    drawing.save(debugpath)
    line = f'Please check the image: {debugpath} and verify that everything was detected correctly. If not, retake image.'
    print(line)
    logs.append(line)

    print(f'BC Filter: {bcFilter}')

    # Gives the RGB in the filter
    sampledRGB = bcFilter[0].sample(image, bcFilter[0].radius / MainConstants.samplingfactorfixed)
    print(f'sampled RGB: {sampledRGB}')

    #check for BCpath
    if os.path.isfile(bcinputpath):
        # load bc input file
        [bcnames, bcbunits, bcval, bcunc, bcuval] = io.load_constant_inputs(bcinputpath)
        line = f'loaded: {bcinputpath}'
        print(line)
        logs.append(line)
    else: #create input file and ask user for needed inputs
        bcnames = []
        entrynames = []
        bcunits = {}
        bcval = {}
        bcuval = {}
        bcunc = {}

        #make header
        name = 'variable'
        bcnames.append(name)
        bcunits[name] = 'units'
        bcval[name] = 'value'
        bcunc[name] = 'uncertainty'

        name = 'filterNumber'
        entrynames.append(name)
        bcnames.append(name)
        bcunits[name] = ''

        name = 'filterRadius'
        entrynames.append(name)
        bcnames.append(name)
        bcunits[name] = 'mm'

        message = 'Enter filter inputs needed for calculation.\n Click OK to continue.\n Click Cancel to exit.'
        title = 'Gitdone'
        newvals = easygui.multenterbox(message, title, entrynames)
        if newvals:
            for i, name in enumerate(entrynames):
                bcval[name] = newvals[i]

        io.write_constant_outputs(bcinputpath, bcnames, bcunits, bcval, bcunc, bcuval)
        line = '\nCreated bc input file: ' + bcinputpath
        print(line)
        logs.append(line)

    filterRadius = bcval['filterRadius']

    # load grav output file
    [gravnames, gravbunits, gravval, gravunc, gravuval] = io.load_constant_inputs(gravpath)
    line = f'loaded: {gravpath}'
    print(line)
    logs.append(line)

    exposedTime = gravval['phase_time_L1'] #temporary phase set
    airFlowRate = gravval['Qsample_L1']

    #BC_TOT used for gradient values
    bcGradient =pylab.array([1.237, 1.523, 1.898, 2.387, 3.027, 3.864, 4.958, 6.389, 8.259, 10.704])
    line = 'BC_TOT used as calibration method'
    print(line)
    logs.append(line)

    # Compute BCC
    bccResult, exitcode = rateFilter(sampledRGB, bcGradient,gradient, tags, logging.DEBUG)

    print(f'Results: {bccResult}')

    #calculate BC
    bcLoading = bccResult.BCAreaRed
    bccCalcs = computeBCC(filterRadius, bcLoading, exposedTime, airFlowRate)
    print(f'Results: {bccCalcs}')

    #write to logs
    io.write_logfile(logpath, logs)
########################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_BlackCarbon(bcpicpath, debugpath, bcinputpath, bcoutputpath, gravpath, logpath)
