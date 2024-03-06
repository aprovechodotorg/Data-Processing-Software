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
from optparse import OptionParser

#from Logging.Logger import getLog
from IANASteps.Geometry.Point import Point
from IANASettings.Settings import ExitCode, MainConstants, CalibratorConstants
from IANASteps.QRDetector.QRDetector import detectQR
from IANASteps.StageDetector.StageDetector import detectStage, detectCalibrator
from IANASteps.ImageTransformer.ImageTransformer import transformRadial, transformLinear
from IANASteps.Calibrator.Calibrator import getGrayBarsRadial, getBlackWhiteRadial, getGrayBarsLinear
from IANASteps.BCFilterDetector.BCFilterDetector import splitToBands, detectBCFilter, select#, PsycoInit
from IANASteps.BCFilterDetector.BCFilterFixedDetector import detectBCFilterFixed
from IANASteps.BCCCalculator.BCCCalculator import rateFilter
from IANASteps.ColorCorrect.BlackWhiteScale import nonlinGrayBarScale
from IANASettings.Settings import ResizeImageConstants, BCFilterConstants, BCFilterFixedConstants
from IANASettings.Settings import ExitCode
from IANAUtil.Chart import plotChart
#from ImageUtils import ImageResize
from optparse import OptionParser

import LEMS_DataProcessing_IO as io
import easygui
from datetime import datetime as dt

bcpicpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_Filter.png"
bcinputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCInputs.csv"
bcoutputpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_BCOutputs.csv"
gravpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_GravOutputs.csv"
logpath = "C:\\Users\\Jaden\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\IDCTests data\\5.31\\5.31_log.txt"

def LEMS_BlackCarbon(bcpicpath, bcinputpath, bcoutputpath, gravpath, logpath):
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
    #font = ImageFont.truetype(MainConstants.fontfile, 45)

    qr, exitcode = detectQR(bcpicpath, tags, logging.DEBUG)

    '''
    for resizeSize in ResizeImageConstants.LargestSide:
        if exitcode is not ExitCode.Success:
            # log.error('Could not process for QR: ' + str(exitcode), extra=tags)
            # return None, exitcode
            log.info("Resizing image to %d first" % (resizeSize), extra=tags)
            image = ImageResize.imageResize(origimage, resizeSize)
            # image = ImageResize.imageResize(image, 600)
            replimg = StringIO.StringIO()
            image.save(replimg, format="JPEG")
            replimg.seek(0)
            log.info("Resizing image %d" % (replimg.len), extra=tags)
            qr, exitcode = detectQR(replimg, tags, logging.DEBUG)

            if exitcode is not ExitCode.Success:
                image = ImageResize.imageRotate(image, 45)
                replimg = StringIO.StringIO()
                log.info("Rotating image", extra=tags)
                image.save(replimg, format="JPEG")
                replimg.seek(0)
                qr, exitcode = detectQR(replimg, tags, logging.DEBUG)
    '''
    # Stage detection Step
    stage, exitcode = detectStage(qr, tags, logging.DEBUG)

    #if exitcode is not ExitCode.Success:
        #log.error('Could not process for Stage: ' + str(exitcode), extra=tags)
        #return None, exitcode

        # Calibrator detection Step
    calibrator, exitcode = detectCalibrator(qr, tags, logging.DEBUG)

    # Extract Data from the Calibrator
    grayBars, exitcode = getGrayBarsRadial(qr, image, tags, logging.DEBUG)

    '''
    gradient = []
    for grayBar in grayBars:
        gradient.append(grayBar.sample(image))

    '''
    '''
    if imageLogLevel:
        # draw boxes on each graybar
        for grayBar in grayBars:
            grayBar.draw(drawing, 'magenta')

        # lines across the graybars columns
        boxsize = Point(CalibratorConstants.BoxSize, CalibratorConstants.BoxSize)
        for i in range(0, 2):
            top = Point(grayBars[0 + i * 6].box.coordinates[0:2])
            bottom = Point(grayBars[5 + i * 6].box.coordinates[0:2])

            drawing.line(tuple(top + boxsize) + tuple(bottom + boxsize), 'yellow')
            '''
    '''

    sampledRGB = None

    tempimage, exitcode = transformRadial(image, stage, tags, logging.DEBUG)
    imgBlackWhite = getBlackWhiteRadial(qr, tempimage, tags, logging.DEBUG)#, bcpicpath[:-4] + "-hist.csv")
    #CHANGE HERE
    mostBlack = min(imgBlackWhite.flatten())
    mostWhite = max(imgBlackWhite.flatten())
    #mostBlack, mostWhite = imgBlackWhite.sample(tempimage)

    gradientScaled = nonlinGrayBarScale(tempimage, gradient, mostBlack, mostWhite, tags, logging.DEBUG)

    # Patch - black out the calibrator so circle detection will not be distracted by it
    draw = ImageDraw.Draw(image)
    draw.polygon((calibrator.topLeft, calibrator.bottomLeft, calibrator.bottomRight, calibrator.topRight), fill='black')
    del draw

    # Image Transformation Step - crop and unskew
    image, exitcode = transformRadial(image, stage, tags, logging.DEBUG)

    bands = splitToBands(image)
    bcFiltersPerBand = []

    BCFconst = BCFilterConstants
    BCFconst.minimumRadius = minRadius
    BCFconst.maximumRadisu = maxRadius
    for band in bands:
        bcFilters, exitcode = detectBCFilter(band, BCFconst, tags, logging.DEBUG)
        # bcFilters, exitcode = detectBCFilter(band, None, tags, logging.DEBUG)
        bcFiltersPerBand.append(bcFilters)
    '''
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

    bcFilter, exitcode = detectBCFilterFixed(qr, BCFilterFixedConstants, tags, logging.DEBUG)
    #if exitcode is not ExitCode.Success:
        #log.error('Could not detect filters in the Image ' + str(exitcode), extra=tags)
        #return None, exitcode

    #if imageLogLevel:
        #drawing.text(bcFilter[0].center, str(1), MainConstants.bandnames[0], font)
        #bcFilter[0].draw(drawing, MainConstants.bandnames[0], MainConstants.samplingfactorfixed)

    # Gives the RGB
    sampledRGB = bcFilter[0].sample(image, bcFilter[0].radius / MainConstants.samplingfactorfixed)
    #log.info("sampled filter [R,G,B]: [%d, %d, %d]" % (sampledRGB[0], sampledRGB[1], sampledRGB[2]), extra=tags)

    debugImage = debugImage.crop(
        (int(qr.topLeft[0]), int(qr.topLeft[1]), int(qr.bottomRight[0]), int(qr.bottomRight[1])))

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
    bcGradient =pylab.array([0.53805296,   0.77764056,   1.10252548,   1.54307503, 2.14046781,   2.9505427 ,
                             4.04901822,   5.53856995, 7.55842775,  10.29738974])
                    # BC Loading trained from India outdoor data
    # Compute BCC
    #bccResult, exitcode = rateFilter(sampledRGB, filterRadius, exposedTime, airFlowRate, bcGradient, gradient, tags,
                                     #logging.DEBUG)
    bccResult, exitcode = rateFilter(sampledRGB, bcGradient,gradient, tags, logging.DEBUG)

    print(bccResult)
########################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_BlackCarbon(bcpicpath, bcinputpath, bcoutputpath, gravpath, logpath)
