'''
The CircleFilter Module uses the Hough Transform to detect circles in a given image

Created on Oct 5, 2010

@author: surya
'''

# import opencv
# import cv
import cv2 as cv
import numpy
import logging

from IANASteps.BCFilterDetector.BCFilter import BCFilter
# from Logging.Logger import getLog
from IANASettings.Settings import BCFilterConstants
from IANASettings.Settings import ExitCode


# log = getLog("BCFilterDetector")
# log.setLevel(logging.ERROR)

def splitToBands(image):
    ''' Split the given image into separate bands

    Keyword Arguments:
    image -- a PIL.Image object

    Returns:
    if the Image is RGB bands corresponding to R,G,B bands of the image
    if the Image is GrayScale then a single band containing the iage itself
    '''

    if image.mode == 'L':
        bands = (image,)
    else:
        if image.mode != 'RGB':
            image = image.convert('RGB')

        bands = image.split()

    return bands


def fixcirclesize(image, circles, tags):
    width, height = image.size
    for circ in circles:
        ##log.info("width: %d, radius: %f, mult: %f" % (width, circ.radius, width * 0.0625), extra=tags)
        if circ.radius < width * 0.0625:  # (0.75 / 2 ) / 6
            ##log.info("!!! Expanding from: %f to: radius: %f" % (circ.radius, width * 0.10416), extra=tags)
            circ.radius = width * 0.10416  # (1.25 / 2 ) / 6


def detectBCFilter(image, bcFilterConstants, parenttags=None, level=logging.ERROR):
    ''' Detects circles in an image

    Keyword Arguments:
    image -- Image instance
    bcFilterConstants -- The configuration under which to run bcFilter detection
    parenttags -- tag string of the calling function
    level -- The logging level

    Returns:
    list of CirclesFilter_.BCFilter objects
    '''

    # Sets the logging level
    # log.setLevel(level)
    tags = " BCFILTER"

   # try:
    # log.info('Running BCFilter Detection', extra=tags)
    circles = houghTransform(image, bcFilterConstants, tags)

    width, height = image.size

    # if more than about half the filter spot would
    # be cut off reject the match
    bcFilters = [BCFilter(*cir) for cir in circles
                 if 0 <= cir[0] <= width and 0 <= cir[1] <= height]

    fixcirclesize(image, bcFilters, tags)

    ##log.info('Done Running BCFilter Detection', extra=tags)
    return bcFilters, ExitCode.Success

    #except Exception as err:
        # log.error('Error %s' % str(err), exc_info=True)
        #return None, ExitCode.FilterDetectionError


def houghTransform(image, bcFilterConstants, parenttags=None):
    """ Runs the hough circle detection against the image

    Keyword Arguments:
    image -- Image instance
    bcFilterConstants -- The configuration under which to run bcFilter detection
    parenttags -- tag string of the calling function

    Returns:
    a list of CirclesFilter_.Circle objects
    """

    if bcFilterConstants is None:
        constants = BCFilterConstants
    else:
        constants = bcFilterConstants

    # cvImage = opencv.PIL2Ipl(image)
    # cvImage = cv.CreateImageHeader(image.size, cv.IPL_DEPTH_8U, 1)
    # cv.SetData(cvImage, image.tostring())

    # smoothen the Image
    # opencv.cvSmooth( cvImage, cvImage, opencv.CV_GAUSSIAN, BCFilterConstants.masksize, BCFilterConstants.masksize);
    # cv.Smooth( cvImage, cvImage, opencv.CV_GAUSSIAN, BCFilterConstants.masksize, BCFilterConstants.masksize);

    # storage = opencv.cvCreateMemStorage(0)
    # storage = cv.CreateMemStorage(0)
    # storage = cv.CreateMat(cvImage.width, 1, cv.CV_32FC3)

    # print the settings that were used to detect circles
    ##log.info('BCFilterConstants dp:{0}, 'minimum distance:{1}, 'high threshold:{2}, 'accumulator threshold:{3}, 'minimum radius:{4}, 'maximum radius:{5}'.format(constants.dp,constants.minimumDistance,constants.highThreshold,constants.accumulatorThreshold,constants.minimumRadius,constants.maximumRadius), extra=parenttags)

    # circles = opencv.cvHoughCircles(cvImage,
    circles = cv.HoughCircles(numpy.array(image),
                              cv.HOUGH_GRADIENT,
                              constants.dp,
                              constants.minimumDistance,
                              param1=constants.highThreshold,
                              param2=constants.accumulatorThreshold,
                              minRadius=constants.minimumRadius,
                              maxRadius=constants.maximumRadius)

    # unpack the circle into a generic tuple
    # !!something wrong with circle.__getitem__ (don't use "tuple(circle)")
    result = []

    ##log.info('Found circles: %d', storage.rows, extra=parenttags)

    if constants.maximumRadius != 0:
        # neither minimumRadius nor maximumRadius seem to be an absolue
        # circles = [(float(circle[0]), float(circle[1]), float(circle[2]))
        #                for circle in circles
        #                if constants.minimumRadius <= circle[2] <= constants.maximumRadius]
        for i in range(len(circles[0])):
            if constants.minimumRadius <= storage[0, i][2] <= constants.maximumRadius:
                result.append(storage[0, i])
    else:
        # circles = [(float(circle[0]), float(circle[1]), float(circle[2]))
        #                for circle in circles]
        for i in range(len(circles[0])):
            result.append(storage[0, i])

    ##log.debug('Using circles: %s', circles, extra=parenttags)

    return result


def select(bands):
    """ Select the best circles based on the color bands

    Keyword Arguments:
    bands  -- Circle detections from bands: [red, green, blue]

    Returns:
    the selected CirclesFilter_.Circle object
    """

    # Check the circles detected in the red band.
    if len(bands[2]) > 0:
        return bands[2]
    elif len(bands[1]) > 0:
        return bands[1]
    elif len(bands[0]) > 0:
        return bands[0]
    else:
        return None

# ##
# # Initializes Psyco
# def PsycoInit(psyco):
# # !!Will cause segfault without this
# #psyco.cannotcompile(houghTransform)
# #psyco.cannotcompile(opencv.cvHoughCircles)
# pass
