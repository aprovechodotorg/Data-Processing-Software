'''
Created on Nov 2, 2010

@author: surya
'''

import os
import os.path
import StringIO
import logging
# import psyco
import traceback
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont

from Logging.Logger import getLog
from IANASteps.Geometry.Point import Point
from IANASteps.QRDetector.QRDetector import detectQR
from IANASteps.Calibrator.Calibrator import getGrayBars
from IANASteps.StageDetector.StageDetector import detectStage, detectCalibrator
from IANASteps.ImageTransformer.ImageTransformer import transform
from IANASettings.Settings import ExitCode, MainConstants, CalibratorConstants, \
    BCFilterConstants, BCFilterFixedConstants, LimitConstants
from IANASteps.BCFilterDetector.BCFilterDetector import splitToBands, detectBCFilter, select
from IANASteps.BCFilterDetector.BCFilterFixedDetector import detectBCFilterFixed

log = getLog("FeatureExtractor")
log.setLevel(logging.ERROR)


def saveDebugImage(debugImage, debugImagefile, tags):
    ''' Saves the PIL.Image debugImage to the debugImagefile

        Keyword Arguments:
        debugImage     -- a PIL.Image object
        debugImagefile -- a file or string
        tags           -- tag string of the caliing function for logging
    '''
    if isinstance(debugImagefile, str):
        debugImage.save(debugImagefile)
    else:
        try:
            debugImage.save(debugImagefile, 'png')
            debugImagefile.close()
            log.info('saved debug image', extra=tags)
        except Exception as err:
            log.error('Error %s' % str(err), extra=tags)


# TODO: This method returns an image make it return the samples value
def featureExtractor(imagefile, imageLogLevel, debugImagefile, preProcessingConfiguration, computationConfiguration,
                     parenttags=None, level=logging.ERROR, ):
    ''' This method analyzes the imageFile, and extracts the grayscale gradient, samples
        the filter in the image and returns the aux_id contained in the QR Code

        Keyword Arguments:
        imagefile      -- The image file on which to perform the black carbon concentration analysis
        imageLogLevel  -- 0, no logging, 1 log image, 2 log and show image
        debugImagefile -- The image file in which to store the image processing debug info.
        preProcessingConfiguration -- The (bcfilter, sampling)configuration under which to preprocess this image.
                                        NOTE: MUST HAVE (dp, minimumRadius, maximumRadius, highThreshold, accumulatorThreshold, minimumDistance) fields
        computationConfiguration -- Used for bcDetectorType ... used to determine which BC Detector to use
        parenttags     -- tag string of the calling function
        level          -- The logging level

        Returns:
        image, aux_id, gradient, bcfilter, exitcode
    '''
    ##
    # Set the logging level
    log.setLevel(level)
    tags = parenttags + " FEATUREEXTRACTION"

    try:
        ###
        # Open the image file using PIL.Image
        ###
        if isinstance(imagefile, str):
            if not os.path.isfile(imagefile):
                log.error('imagefile ' + imagefile + ' does not exist', extra=tags)
                return None, ExitCode.FileNotExists
            image = Image.open(imagefile)
        else:
            image = Image.open(StringIO.StringIO(imagefile.read()))
            imagefile.get().seek(0)  # reset to make sure at beggining

        ###
        # If the ImageLogLevel > 1, copy the original image for image logging
        ###
        if imageLogLevel:
            debugImage = image.copy()
            drawing = ImageDraw.Draw(debugImage)
            # For all the text that goes into the debug image
            font = ImageFont.truetype(MainConstants.fontfile, 45)

        ###
        # QR Detection Step
        ###
        qr, exitcode = detectQR(imagefile, tags, logging.DEBUG)

        if exitcode is not ExitCode.Success:
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)
            log.error('Could not process imagefile for QR: ' + ExitCode.toString[exitcode], extra=tags)
            return None, exitcode

        if imageLogLevel:
            qr.draw(drawing, 'red')

        ###
        # Stage detection Step
        ###
        stage, exitcode = detectStage(qr, tags, logging.DEBUG)

        if exitcode is not ExitCode.Success:
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)
            log.error('Could not process imagefile for Stage: ' + ExitCode.toString[exitcode], extra=tags)
            return None, exitcode

        # Calibrator detection Step
        calibrator, exitcode = detectCalibrator(qr, tags, logging.DEBUG)

        if exitcode is not ExitCode.Success:
            log.error('Could not process for Calibrator: ' + exitcode, extra=tags)
            return None, exitcode

        ###
        # Extract Data from the Calibrator, i.e. Gradient
        ###
        grayBars, exitcode = getGrayBars(qr, image, tags, logging.DEBUG)

        if exitcode is not ExitCode.Success:
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)
            log.error('Could not get grayBars from imagefile Calibrator ' + ExitCode.toString[exitcode], extra=tags)
            return None, exitcode

        gradient = []
        for grayBar in grayBars:
            gradient.append(grayBar.sample(image))

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

        sampledRGB = None
        log.debug("######## compconfig is: " + computationConfiguration.bcDetectorType)
        if computationConfiguration.bcDetectorType == "fixed":
            log.debug("!!!!!!!!! Running fixed filter finder !!!!!!!!!!!!11")
            bands = splitToBands(image)
            log.info("Split the image into bands", extra=tags)
            if bands is None:
                log.error('Could not find the bcfilter in the image', extra=tags)
                return None, ExitCode.UnknownError

            bcFiltersPerBand = []

            if imageLogLevel:
                bandIndex = 0

            for band in bands:
                bcFilters, exitcode = detectBCFilterFixed(qr, BCFilterFixedConstants, tags, logging.DEBUG)

                if exitcode is not ExitCode.Success:
                    if imageLogLevel:
                        saveDebugImage(debugImage, debugImagefile, tags)
                    log.error('Could not detect filters in the Image ' + ExitCode.toString[exitcode], extra=tags)
                    return None, exitcode

                if imageLogLevel:
                    index = 1
                    for bcFilter in bcFilters:
                        drawing.text(bcFilter.center, str(index), MainConstants.bandnames[bandIndex], font)
                        if preProcessingConfiguration.samplingFactorFixed is None or preProcessingConfiguration.samplingFactorFixed is 0:
                            bcFilter.draw(drawing, MainConstants.bandnames[bandIndex],
                                          MainConstants.samplingfactorfixed)
                        else:
                            bcFilter.draw(drawing, MainConstants.bandnames[bandIndex],
                                          preProcessingConfiguration.samplingFactorFixed)
                        index += 1
                    bandIndex += 1

                bcFiltersPerBand.append(bcFilters)

            bestBand = select(bcFiltersPerBand)

            if not bestBand:
                if imageLogLevel:
                    saveDebugImage(debugImage, debugImagefile, tags)
                log.error('Could not detect any filters in the image: ' + ExitCode.toString[exitcode], extra=tags)
                return None, ExitCode.UnknownError

            bestBcFilter = bestBand[0]

            ###
            # Save the debug image
            ###
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)

            if imageLogLevel > 1:
                if isinstance(debugImagefile, str):
                    debugImage.show()

            if preProcessingConfiguration.samplingFactorFixed is None or preProcessingConfiguration.samplingFactorFixed is 0:
                sampledRGB = bestBcFilter.sample(image, bestBcFilter.radius / MainConstants.samplingfactorfixed)
            else:
                sampledRGB = bestBcFilter.sample(image,
                                                 bestBcFilter.radius / preProcessingConfiguration.samplingFactorFixed)

        # Patch
        draw = ImageDraw.Draw(image)
        draw.polygon((calibrator.topLeft, calibrator.bottomLeft, calibrator.bottomRight, calibrator.topRight),
                     fill='black')
        del draw

        ###
        # Image Transformation Step
        ###
        image, exitcode = transform(image, stage, tags, logging.DEBUG)

        if exitcode is not ExitCode.Success:
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)
            log.error('Could not transform imagefile using Stage Coordinates: ' + ExitCode.toString[exitcode],
                      extra=tags)
            return None, exitcode

        if imageLogLevel:
            # Image Transformation Step
            debugImage, exitcode = transform(debugImage, stage, tags, logging.DEBUG)

            if exitcode is not ExitCode.Success:
                if imageLogLevel:
                    saveDebugImage(debugImage, debugImagefile, tags)
                log.error('Could not transform debugImage using Stage Coordinates: ' + ExitCode.toString[exitcode],
                          extra=tags)
                return None, exitcode

            drawing = ImageDraw.Draw(debugImage)

        ###
        # Detect bcFilters
        ###
        if computationConfiguration.bcDetectorType == "hough":
            log.debug("!!!!!!!!! Running hough filter finder !!!!!!!!!!!!11")
            bands = splitToBands(image)
            log.info("Split the image into bands", extra=tags)
            if bands is None:
                log.error('Could not find the bcfilter in the image', extra=tags)
                return None, ExitCode.UnknownError

            bcFiltersPerBand = []

            if imageLogLevel:
                bandIndex = 0

            for band in bands:
                bcFilters, exitcode = detectBCFilter(band, preProcessingConfiguration, tags, logging.DEBUG)
                ##### Eric added:
                bcFilters = bcFilters[0:10]  ## take only first 10 circles
                width, height = image.size
                newbcFiltersPerBand = []  ## new list for restricting to those close to the filter region, see below
                ##### end
                if exitcode is not ExitCode.Success:
                    if imageLogLevel:
                        saveDebugImage(debugImage, debugImagefile, tags)
                    log.error('Could not detect filters in the Image ' + ExitCode.toString[exitcode], extra=tags)
                    return None, exitcode

                ##### Eric added/modified: Limit the circles that get included to those close to the filter region
                for bcFilter in bcFilters:
                    if (bcFilter.center[0] / width > LimitConstants.xloc[0] and bcFilter.center[0] / width <
                        LimitConstants.xloc[1]) and (bcFilter.center[1] / height > LimitConstants.yloc[0] and
                                                     bcFilter.center[1] / height < LimitConstants.yloc[1]):
                        # if (bcFilter.center[0]/width > 0.2746 and bcFilter.center[0]/width < 0.7193) and (bcFilter.center[1]/height > 0.569 and bcFilter.center[1]/height < 0.9):
                        newbcFiltersPerBand.append(
                            bcFilter)  ## append the filters in the correct location to a new list

                bcFiltersPerBand.append(
                    newbcFiltersPerBand)  ## append subset of circles within correct location to list
                # bcFiltersPerBand.append(bcFilters)
                ##### end

                if imageLogLevel:
                    index = 1
                    for bcFilter in newbcFiltersPerBand:  ## also Eric added here, only draw the circles within the limits (was: "for bcFilter in bcFilters:")
                        drawing.text(bcFilter.center, str(index), MainConstants.bandnames[bandIndex], font)
                        if preProcessingConfiguration.samplingFactor is None or preProcessingConfiguration.samplingFactor is 0:
                            bcFilter.draw(drawing, MainConstants.bandnames[bandIndex], MainConstants.samplingfactor)
                        else:
                            bcFilter.draw(drawing, MainConstants.bandnames[bandIndex],
                                          preProcessingConfiguration.samplingFactor)
                        index += 1
                        # if index > 5:
                        #    break
                    bandIndex += 1

            bestBand = select(bcFiltersPerBand)

            if not bestBand:
                if imageLogLevel:
                    saveDebugImage(debugImage, debugImagefile, tags)
                log.error('Could not detect any filters in the image: ' + ExitCode.toString[exitcode], extra=tags)
                return None, ExitCode.UnknownError

            bestBcFilter = bestBand[0]

            ###
            # Save the debug image
            ###
            if imageLogLevel:
                saveDebugImage(debugImage, debugImagefile, tags)

            if imageLogLevel > 1:
                if isinstance(debugImagefile, str):
                    debugImage.show()

            if preProcessingConfiguration.samplingFactor is None or preProcessingConfiguration.samplingFactor is 0:
                sampledRGB = bestBcFilter.sample(image, bestBcFilter.radius / MainConstants.samplingfactor)
            else:
                sampledRGB = bestBcFilter.sample(image, bestBcFilter.radius / preProcessingConfiguration.samplingFactor)

        return (sampledRGB, qr.aux, gradient), exitcode

    except Exception as err:
        log.error('Error %s' % traceback.format_exc(), extra=tags)
        if imageLogLevel:
            saveDebugImage(debugImage, debugImagefile, tags)
        return None, ExitCode.UnknownError
