'''
The CalibratorFilter Module contains functionality to process the
calibrator area in the image and extracts the:

 Color values from the ColorBar in the calibrator,
 Grayscale values from the GrayBar in the calibrator,
 Black value from the BlackBar in the calibrator.


Created on Oct 10, 2010

@author: surya
'''

import logging

from IANASteps.Calibrator.GrayBar import *
from IANASteps.Calibrator.ColorBar import ColorBar
from IANASteps.Calibrator.BlackWhite import BlackWhite
# from Logging.Logger import getLog
from IANASettings.Settings import ExitCode, CalibratorConstants


# log = getLog("Calibrator")
# log.setLevel(logging.ERROR)

def getGrayBarsRadial(qr, image, parenttags=None, level=logging.ERROR):
    ''' Extracts the GrayBars from the Image and represents them
        as GrayBar objects.

    Keyword Arguments:
    qr    -- QRDetector.QR object
    image -- a PIL.Image object
    parenttags -- tag string of the calling function
    level -- the logging level

    Returns
    A list of Calibrator.GrayBar objects.
    '''

    # Set the logging level
    # log.setLevel(level)
    #tags = parenttags + " GRAYBAR"

    ##log.info('Running GrayBar Detection', extra=tags)

    # #new calibrator
    leftT = (qr.topRight - qr.topLeft)
    leftH = (qr.bottomLeft - qr.topLeft)

    grayBars = []

    adjustX = leftT[0] / 50.0
    adjustY = leftH[1] / 50.0
    # print "leftT:", leftT
    # print "leftH:", leftH
    # print "adjustX:", adjustX
    # print "adjustY:", adjustY
    qr.topLeft = qr.topLeft + (adjustX, adjustY)
    # print "qrtopleft:", qr.topLeft

    # first set of boxes
    c0 = GrayBarRadial(.24864 * leftT + .13451 * leftH + qr.topLeft, qr.width)  # lightest, not white
    c1 = GrayBarRadial(.36277 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    c2 = GrayBarRadial(.47690 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    c3 = GrayBarRadial(.59103 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    c4 = GrayBarRadial(.70516 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    c5 = GrayBarRadial(.24864 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    c6 = GrayBarRadial(.36277 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    c7 = GrayBarRadial(.47690 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    c8 = GrayBarRadial(.59103 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    c9 = GrayBarRadial(.70516 * leftT + leftH * .24864 + qr.topLeft, qr.width)

    grayBars.append(c0)
    grayBars.append(c1)
    grayBars.append(c2)
    grayBars.append(c3)
    grayBars.append(c4)
    grayBars.append(c5)
    grayBars.append(c6)
    grayBars.append(c7)
    grayBars.append(c8)
    grayBars.append(c9)

    # second set, boxes are on opposite sides of first set
    c0 = GrayBarRadial(.70516 * leftT + .81929 * leftH + qr.topLeft, qr.width)  # lightest, not white
    c1 = GrayBarRadial(.59103 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    c2 = GrayBarRadial(.47690 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    c3 = GrayBarRadial(.36277 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    c4 = GrayBarRadial(.24864 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    c5 = GrayBarRadial(.70516 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    c6 = GrayBarRadial(.59103 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    c7 = GrayBarRadial(.47690 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    c8 = GrayBarRadial(.36277 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    c9 = GrayBarRadial(.24864 * leftT + leftH * .70516 + qr.topLeft, qr.width)

    grayBars.append(c0)
    grayBars.append(c1)
    grayBars.append(c2)
    grayBars.append(c3)
    grayBars.append(c4)
    grayBars.append(c5)
    grayBars.append(c6)
    grayBars.append(c7)
    grayBars.append(c8)
    grayBars.append(c9)

    # third set, boxes are orthogonal to the first and second sets
    c0 = GrayBarRadial(.13451 * leftT + .24864 * leftH + qr.topLeft, qr.width)  # lightest, not white
    c1 = GrayBarRadial(.13451 * leftT + .36277 * leftH + qr.topLeft, qr.width)
    c2 = GrayBarRadial(.13451 * leftT + .47690 * leftH + qr.topLeft, qr.width)
    c3 = GrayBarRadial(.13451 * leftT + .59103 * leftH + qr.topLeft, qr.width)
    c4 = GrayBarRadial(.13451 * leftT + .70516 * leftH + qr.topLeft, qr.width)
    c5 = GrayBarRadial(.24864 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    c6 = GrayBarRadial(.24864 * leftT + leftH * .36277 + qr.topLeft, qr.width)
    c7 = GrayBarRadial(.24864 * leftT + leftH * .47690 + qr.topLeft, qr.width)
    c8 = GrayBarRadial(.24864 * leftT + leftH * .59103 + qr.topLeft, qr.width)
    c9 = GrayBarRadial(.24864 * leftT + leftH * .70516 + qr.topLeft, qr.width)

    grayBars.append(c0)
    grayBars.append(c1)
    grayBars.append(c2)
    grayBars.append(c3)
    grayBars.append(c4)
    grayBars.append(c5)
    grayBars.append(c6)
    grayBars.append(c7)
    grayBars.append(c8)
    grayBars.append(c9)

    # fourth set, boxes are on opposite side third set
    c0 = GrayBarRadial(.81929 * leftT + .70516 * leftH + qr.topLeft, qr.width)  # lightest, not white
    c1 = GrayBarRadial(.81929 * leftT + .59103 * leftH + qr.topLeft, qr.width)
    c2 = GrayBarRadial(.81929 * leftT + .47690 * leftH + qr.topLeft, qr.width)
    c3 = GrayBarRadial(.81929 * leftT + .36277 * leftH + qr.topLeft, qr.width)
    c4 = GrayBarRadial(.81929 * leftT + .24864 * leftH + qr.topLeft, qr.width)
    c5 = GrayBarRadial(.70516 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    c6 = GrayBarRadial(.70516 * leftT + leftH * .59103 + qr.topLeft, qr.width)
    c7 = GrayBarRadial(.70516 * leftT + leftH * .47690 + qr.topLeft, qr.width)
    c8 = GrayBarRadial(.70516 * leftT + leftH * .36277 + qr.topLeft, qr.width)
    c9 = GrayBarRadial(.70516 * leftT + leftH * .24864 + qr.topLeft, qr.width)

    grayBars.append(c0)
    grayBars.append(c1)
    grayBars.append(c2)
    grayBars.append(c3)
    grayBars.append(c4)
    grayBars.append(c5)
    grayBars.append(c6)
    grayBars.append(c7)
    grayBars.append(c8)
    grayBars.append(c9)

    # for grayBar in grayBars:
    # #log.info(grayBar.__str__(), extra=tags)

    # grayBars.reverse()
    ##log.info('Done Running GrayBar Detection', extra=tags)
    return grayBars, ExitCode.Success


def getBlackWhiteRadial(qr, image, parenttags=None, level=logging.ERROR):
    ''' Extracts the GrayBars from the Image and represents them
        as GrayBar objects.

    Keyword Arguments:
    qr    -- QRDetector.QR object
    image -- a PIL.Image object
    parenttags -- tag string of the calling function
    level -- the logging level

    Returns
    A list of Calibrator.GrayBar objects.
    '''

    # Set the logging level
    # log.setLevel(level)
    tags = parenttags + " GRAYBAR"

    ##log.info('Running GrayBar Detection', extra=tags)

    # #new calibrator
    leftT = (qr.topRight - qr.topLeft)
    leftH = (qr.bottomLeft - qr.topLeft)

    grayBars = []

    adjustX = leftT[0] / 50.0
    adjustY = leftH[1] / 50.0
    # print "leftT:", leftT
    # print "leftH:", leftH
    # print "adjustX:", adjustX
    # print "adjustY:", adjustY
    qr.topLeft = qr.topLeft + (adjustX, adjustY)
    # print "qrtopleft:", qr.topLeft

    # first set of boxes
    c10 = GrayBarRadialSmall(.24864 * leftT + 0.0 * leftH + qr.topLeft, qr.width)  # finding white
    c11 = GrayBarRadialSmall(0.0 * leftT + 0.0 * leftH + qr.topLeft, qr.width)  # finding black

    grayBars.append(c10)
    grayBars.append(c11)

    # second set, boxes are on opposite sides of first set
    c10 = GrayBarRadialSmall(.70516 * leftT + 1.0 * leftH + qr.topLeft, qr.width)  # finding white
    c11 = GrayBarRadialSmall(1.0 * leftT + 0.0 * leftH + qr.topLeft, qr.width)  # finding black

    grayBars.append(c10)
    grayBars.append(c11)

    # third set, boxes are orthogonal to the first and second sets
    c10 = GrayBarRadialSmall(0.0 * leftT + .24864 * leftH + qr.topLeft, qr.width)  # finding white
    c11 = GrayBarRadialSmall(0.0 * leftT + 1.0 * leftH + qr.topLeft, qr.width)  # finding black

    grayBars.append(c10)
    grayBars.append(c11)

    # fourth set, boxes are on opposite side third set
    c10 = GrayBarRadialSmall(1.0 * leftT + .70516 * leftH + qr.topLeft, qr.width)  # finding white
    c11 = GrayBarRadialSmall(0.0 * leftT + 0.0 * leftH + qr.topLeft,
                             qr.width)  # finding black, repeated first one because small QR is not big enough

    grayBars.append(c10)
    grayBars.append(c11)

    # for grayBar in grayBars:
    # #log.info(grayBar.__str__(), extra=tags)

    # grayBars.reverse()
    ##log.info('Done Running GrayBar Detection', extra=tags)
    return grayBars, ExitCode.Success


def getGrayBarsLinear(qr, image, parenttags=None, level=logging.ERROR):
    ''' Extracts the GrayBars from the Image and represents them
        as GrayBar objects.

    Keyword Arguments:
    qr    -- QRDetector.QR object
    image -- a PIL.Image object
    parenttags -- tag string of the calling function
    level -- the logging level

    Returns
    A list of Calibrator.GrayBar objects.
    '''

    # Set the logging level
    # log.setLevel(level)
    tags = parenttags + " GRAYBAR"

    ##log.info('Running GrayBar Detection', extra=tags)

    leftT = qr.topLeft - qr.topRight
    leftB = qr.bottomLeft - qr.bottomRight

    grayBars = []
    # For each coloumn of the GrayBars (there are two GrayBar columns to the left of the QR Code)
    for grayBarColumnOffset in CalibratorConstants.GrayBarColumnOffsets[:2]:
        top = grayBarColumnOffset * leftT + qr.topLeft
        bottom = grayBarColumnOffset * leftB + qr.bottomLeft
        down = (bottom - top) * CalibratorConstants.LastGrayBarOffset
        bottom = top + down

        blockOffset = (bottom - top) / 5
        block = top

        # For each GrayBar in the given GrayBarColumn
        for i in range(6):

            try:
                grayBars.append(GrayBar(block, qr.width))
            except Exception as err:
                # log.error('Error %s' % str(err), extra=tags)
                return None, ExitCode.GrayBarDetectionError

            block += blockOffset

    # for grayBar in grayBars:
    ##log.info("Each gray bar:" + grayBar.__str__(), extra=tags)

    grayBars.reverse()
    ##log.info('Done Running GrayBar Detection', extra=tags)
    return grayBars, ExitCode.Success

