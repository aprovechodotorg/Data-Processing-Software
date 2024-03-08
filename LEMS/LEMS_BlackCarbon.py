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
# import psyco
#import StringIO
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import PIL.ImageTransform as ImageTransform
from optparse import OptionParser
import cv2
from PIL import Image
from io import StringIO
import numpy as np
import math
from wand.image import Image as IMG
from wand.display import display


#from Logging.Logger import getLog
from IANASteps.Geometry.Point import Point
from IANASettings.Settings import ExitCode, MainConstants, CalibratorConstants
from IANASteps.QRDetector.QRDetector import detectQR, QR_Radial
from IANASteps.StageDetector.StageDetector import detectStage, detectCalibrator
from IANASteps.ImageTransformer.ImageTransformer import transformRadial, transformLinear
from IANASteps.Calibrator.Calibrator import getGrayBarsRadial, getBlackWhiteRadial, getGrayBarsLinear
from IANASteps.BCFilterDetector.BCFilterDetector import splitToBands, detectBCFilter, select#, PsycoInit
from IANASteps.BCFilterDetector.BCFilterFixedDetector import detectBCFilterFixed
from IANASteps.BCCCalculator.BCCCalculator import rateFilter, computeBCC
from IANASteps.ColorCorrect.BlackWhiteScale import nonlinGrayBarScale
from IANASettings.Settings import ResizeImageConstants, BCFilterConstants, BCFilterFixedConstants
from IANASettings.Settings import ExitCode
from IANAUtil.Chart import plotChart
from IANASteps.ImageTransformer.ImageTransformer import transformRadial
#from ImageUtils import ImageResize
from optparse import OptionParser

import LEMS_DataProcessing_IO as io
import easygui
from datetime import datetime as dt

bcpicpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_2043_Filter.JPG"
debugpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_2043_DebugFilter.png"
bcinputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCInputs.csv"
bcoutputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCOutputs.csv"
gravpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_GravOutputs.csv"
logpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_log.txt"

def LEMS_BlackCarbon(bcpicpath, debugpath, bcinputpath, bcoutputpath, gravpath, logpath):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_BlackCarbon v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    tags =" IANAMAIN"

    if os.path.isfile(bcpicpath):
        image = Image.open(bcpicpath)
    else:
        line = f'file path {bcpicpath} does not exist. Nothing was processed.'
        print(line)
        logs.append(line)
        exit()

    origimage = image.copy()

    debugImage = image.copy()
    drawing = ImageDraw.Draw(debugImage)
    # For all the text that goes into the debug image
    font = ImageFont.truetype(MainConstants.fontfile, 45)

    #resize image
    for resizeSize in ResizeImageConstants.LargestSide:
        image = image.resize((resizeSize, resizeSize))
        image.save(debugpath)
        qr = detectQR(debugpath, tags, logging.DEBUG)

    # transform image
    image = np.array(image)

    og_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[1][0], qr.points[1][1]],
                            [qr.points[3][0], qr.points[3][1]]])

    new_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[0][0] + 470, qr.points[1][1]],
                             [qr.points[3][0], qr.points[1][1] + 600]])
    M = cv2.getAffineTransform(og_points, new_points)
    image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    # Convert the NumPy array back to an image
    image = Image.fromarray(image)
    image.save(debugpath)
    qr = detectQR(debugpath, tags, logging.DEBUG)

    '''
    #transform image
    image = np.array(image)

    og_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[1][0], qr.points[1][1]],
                             [qr.points[3][0], qr.points[3][1]]])

    new_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[1][0], qr.points[0][1]],
                             [qr.points[1][0], qr.points[3][1]]])
    M = cv2.getAffineTransform(og_points, new_points)
    image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    # Convert the NumPy array back to an image
    image = Image.fromarray(image)
    image.save(debugpath)
    qr = detectQR(debugpath, tags, logging.DEBUG)

    #transform image
    image = np.array(image)

    og_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[3][0], qr.points[3][1]],
                             [qr.points[2][0], qr.points[2][1]]])

    new_points = np.float32([[qr.points[0][0], qr.points[0][1]], [qr.points[3][0], qr.points[3][1]],
                             [qr.points[2][0], qr.points[3][1] - 45]])
    M = cv2.getAffineTransform(og_points, new_points)
    image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))

    # Convert the NumPy array back to an image
    image = Image.fromarray(image)
    image.save(debugpath)
    qr = detectQR(debugpath, tags, logging.DEBUG)
    '''
    top_left = [qr.points[0][0], qr.points[0][1]]
    top_right = [qr.points[1][0], qr.points[1][1]]
    bottom_left = [qr.points[2][0], qr.points[2][1]]
    bottom_right = [qr.points[3][0], qr.points[3][1]]



    og_points = np.float32([top_left, top_right, bottom_left, bottom_right])

    new_top_left = [qr.points[0][0], qr.points[0][1]]
    new_top_right = [qr.points[1][0], qr.points[0][1]]
    new_bottom_left = [qr.points[2][0], qr.points[3][1] - 40]
    new_bottom_right = [qr.points[1][0], qr.points[3][1]]

    new_points = np.float32([new_top_left, new_top_right, new_bottom_left, new_bottom_right])
    points = (top_left[0], top_left[1], top_right[0], top_right[1], bottom_left[0], bottom_left[1], bottom_right[0], bottom_right[1],
              new_top_left[0], new_top_left[1], new_top_right[0], new_top_right[1], new_bottom_left[0], new_bottom_left[1], new_bottom_right[0], new_bottom_right[1])

    #with IMG(filename=debugpath) as img:
        #img.virtual_pixel = 'white'
        #img.distort('perspective', points, best_fit=True)
        #img.save(filename=debugpath)
        #display(img)
    #image = cv2.imread(debugpath)
    # transform image
    image = np.array(image)
    # Execute getAffineTransform to generate our transformation matrix
    M = cv2.getPerspectiveTransform(og_points, new_points)
    # Feed into warpAffrine function to perform our skew
    image = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))

    #m = cv2.getPerspectiveTransform(og_points, new_points)
    #image = cv2.warpAffine(image, m, (resizeSize, resizeSize), cv2.INTER_LINEAR,  borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    # Convert the NumPy array back to an image
    #image = Image.fromarray(image)
    #image.save(debugpath)
    #image.show()
    image = Image.fromarray(image)
    #image.show()
    image.save(debugpath)
    qr = detectQR(debugpath, tags, logging.DEBUG)


    print(f'QR code: {qr}')

    #rimage = StringIO()

    #qr = detectQR(debugpath, tags, logging.DEBUG)

    drawing = np.array(image)
    for loc in qr.points:
        top_left = (int(loc[0] - 15), int(loc[1] - 15))
        bottom_right = (int(loc[0] + 15), int(loc[1] + 15))

        # Draw the blue square on the image
        cv2.rectangle(drawing, top_left, bottom_right, (255, 0, 0), 2)
    drawing = Image.fromarray(drawing)

    drawing.save(debugpath)
    #drawing.show()
    # Stage detection Step
    stage, exitcode = detectStage(qr, tags, logging.DEBUG)

        # Calibrator detection Step
    calibrator, exitcode = detectCalibrator(qr, tags, logging.DEBUG)

    # Extract Data from the Calibrator
    grayBars, drawing, exitcode = getGrayBarsRadial(qr, debugpath, tags, logging.DEBUG)
    #drawing.show()
    print(f'grey bars: {grayBars}')

    # store the gray bar RGB averages in an array called "gradient"
    gradient = []
    for i in range(0, 10):
        R_avg = 0
        G_avg = 0
        B_avg = 0
        for grayBar in grayBars[i::10]:
            #if imageLogLevel:
                #grayBar.draw(drawing, 'magenta')
            R, G, B = grayBar.sample(image)
            R_avg = R_avg + R
            G_avg = G_avg + G
            B_avg = B_avg + B
        gradient.append([R_avg / 4.0, G_avg / 4.0, B_avg / 4.0])
        #log.info("greyBar.sample averages [R,G,B]: [%d, %d, %d]" % (R_avg / 4.0, G_avg / 4.0, B_avg / 4.0), extra=tags)
    sampledRGB = None

    tags = 'radial'
    bcFilter, drawing, exitcode = detectBCFilterFixed(qr, BCFilterFixedConstants, drawing, tags, logging.DEBUG)
    drawing.show()
    print(f'BC Filter: {bcFilter}')

    drawing.save(debugpath)

    # Gives the RGB
    sampledRGB = bcFilter[0].sample(image, bcFilter[0].radius / MainConstants.samplingfactorfixed)
    print(f'sampled RGB: {sampledRGB}')

    #check for BCpath
    if os.path.isfile(bcinputpath):
        # load bc input file
        [bcnames, bcbunits, bcval, bcunc, bcuval] = io.load_constant_inputs(bcinputpath)
    else:
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

    exposedTime = gravval['phase_time_L1'] #temporary phase set
    airFlowRate = gravval['Qsample_L1']
    # BC Loading trained from selecton of LA and SD data
    #BC_TOT used for gradient values
    bcGradient =pylab.array([1.237, 1.523, 1.898, 2.387, 3.027, 3.864, 4.958, 6.389, 8.259, 10.704])
                    # BC Loading trained from India outdoor data
    # Compute BCC
    #bccResult, exitcode = rateFilter(sampledRGB, filterRadius, exposedTime, airFlowRate, bcGradient, gradient, tags,
                                     #logging.DEBUG)
    bccResult, exitcode = rateFilter(sampledRGB, bcGradient,gradient, tags, logging.DEBUG)

    print(f'Results: {bccResult}')

    bcLoading = bccResult.BCAreaRed
    bccCalcs = computeBCC(filterRadius, bcLoading, exposedTime, airFlowRate)
    print(f'Results: {bccCalcs}')
########################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_BlackCarbon(bcpicpath, debugpath, bcinputpath, bcoutputpath, gravpath, logpath)
