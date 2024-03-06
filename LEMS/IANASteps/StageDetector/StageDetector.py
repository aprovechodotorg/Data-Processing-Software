'''
The StageImageFilter module computes the absolute coordinates of the Stage(and the Calibrator).

NOTE: The calibrator + filter dock = Stage

Created on Oct 8, 2010

@author: surya
'''

import logging

from IANASteps.StageDetector.Stage import Stage
from IANASteps.StageDetector.Calibrator import  Calibrator
# from Logging.Logger import getLog
from IANASettings.Settings import ExitCode, StageDetectorConstants


# log = getLog("StageDetector")
# log.setLevel(logging.ERROR)

def computeBoxFromQR(qr, left, right, top, bottom, parenttags=None):
    ''' Uses the QR coordinates to compute the coordinates of a Box
        subject to left, right, top, bottom params.

    Keyword Arguments:
    left   -- distance from qrTopLeft to left
    right  -- distance from qrTopLeft to right
    top    -- distance from qrTopLeft to top
    bottom -- distance from qrTopLeft to bottom
    parenttags -- tag string of the calling function

    Returns:
    (topLeft, bottomLeft, bottomRight, topRight) coordinates
    '''

    qrTopLeft = qr.topLeft
    qrTopRight = qr.topRight
    qrBottomLeft = qr.bottomLeft
    qrBottomRight = qr.bottomRight

    # The dimensions for each side (in the worst case this is
    # a generic quadrilateral, but in the best case it's a square)
    qrTopL2R = qrTopRight - qrTopLeft
    qrBottomL2R = qrBottomRight - qrBottomLeft
    qrLeftT2B = qrBottomLeft - qrTopLeft
    qrRightT2B = qrBottomRight - qrTopRight
    qrDeltaL2R_T2B = qrRightT2B - qrLeftT2B

    leftT2B = qrLeftT2B + qrDeltaL2R_T2B * left
    topLeft = qrTopLeft + qrTopL2R * left + leftT2B * top
    bottomLeft = qrBottomLeft + qrBottomL2R * left + leftT2B * bottom

    rightT2B = qrLeftT2B + qrDeltaL2R_T2B * right
    topRight = qrTopLeft + qrTopL2R * right + rightT2B * top
    bottomRight = qrBottomLeft + qrBottomL2R * right + rightT2B * bottom

    # log.info("Coordinates: topLeft:{0}, bottomLeft:{1}, bottomRight:{2}, topRight:{3} ".format(topLeft, bottomLeft, bottomRight, topRight), extra=parenttags)
    return topLeft, bottomLeft, bottomRight, topRight


def detectStage(qr, parenttags=None, level=logging.ERROR):
    ''' Returns the coordinates of the Stage

    Keyword Arguments:
    qr         -- a QRFilter_.QR object
    parenttags -- The tag string of the calling method
    level      -- The logging level

    Returns:
    (topLeft, bottomLeft, bottomRight, topRight) coordinates of the Stage
    '''
    # Set the logging level
    # log.setLevel(level)
    tags = parenttags + " STAGE"

    # log.info("Running Stage Detection", extra=tags)
    try:
        topLeft, bottomLeft, bottomRight, topRight = computeBoxFromQR(qr,
                                                                      StageDetectorConstants.sleft,
                                                                      StageDetectorConstants.sright,
                                                                      StageDetectorConstants.stop,
                                                                      StageDetectorConstants.sbottom,
                                                                      tags)
    except Exception as err:
        # log.error('Error %s' % str(err), extra=tags)
        return None, ExitCode.StageDetectionError

        # log.info("Done Running Stage Detection", extra=tags)
    return Stage(topLeft, bottomLeft, bottomRight, topRight), ExitCode.Success


def detectStageEnlarged(qr, parenttags=None, level=logging.ERROR):
    ''' Returns the coordinates of the Stage

    Keyword Arguments:
    qr         -- a QRFilter_.QR object
    parenttags -- The tag string of the calling method
    level      -- The logging level

    Returns:
    (topLeft, bottomLeft, bottomRight, topRight) coordinates of the Stage
    '''
    # Set the logging level
    # log.setLevel(level)
    tags = parenttags + " STAGE"

    # log.info("Running Stage Detection", extra=tags)
    try:
        topLeft, bottomLeft, bottomRight, topRight = computeBoxFromQR(qr,
                                                                      StageDetectorConstants.sleftEnlarged,
                                                                      StageDetectorConstants.srightEnlarged,
                                                                      StageDetectorConstants.stopEnlarged,
                                                                      StageDetectorConstants.sbottomEnlarged,
                                                                      tags)
    except Exception as err:
        # log.error('Error %s' % str(err), extra=tags)
        return None, ExitCode.StageDetectionError

        # log.info("Done Running Stage Detection", extra=tags)
    return Stage(topLeft, bottomLeft, bottomRight, topRight), ExitCode.Success


def detectCalibrator(qr, parenttags=None, level=logging.ERROR):
    ''' Returns the coordinates of the Calibrator

    Keyword Arguments:
    qr         -- a QRFilter_.QR object
    parenttags -- The tag string of the calling method
    level      -- The logging level

    Returns:
    (topLeft, bottomLeft, bottomRight, topRight) coordinates of the calibrator
    '''
    # Set the logging level
    # log.setLevel(level)
    #tags = parenttags + " CALIBRATOR"

    ##log.info("Running Calibrator Detection", extra=tags)
    #try:
    topLeft, bottomLeft, bottomRight, topRight = computeBoxFromQR(qr,
                                                                  StageDetectorConstants.cleft,
                                                                  StageDetectorConstants.cright,
                                                                  StageDetectorConstants.ctop,
                                                                  StageDetectorConstants.cbottom)
    '''
    except Exception as err:
        # log.error('Error %s' % str(err), extra=tags)
        return None, ExitCode.CalibratorDetectionError
    '''

    ##log.info("Done Running Calibrator Detection", extra=tags)
    return Calibrator(topLeft, bottomLeft, bottomRight, topRight), ExitCode.Success
    #return ([topLeft, bottomLeft, topRight, bottomRight]), ExitCode.Success