'''
The BlackWhiteScale Module contains functionality to adjust the color
of the image to try and compensate for glare and other problems.

 Color values from the ColorBar in the calibrator,
 Grayscale values from the GrayBar in the calibrator,
 Black value from the BlackBar in the calibrator,
 Black and White values from the BlackWhite objects created from the images.

Created on Jan 17, 2011

@author: Martin
'''

import logging

#from Logging.Logger import getLog
from IANASettings.Settings import ExitCode, CalibratorConstants
from IANASteps.Calibrator.Calibrator import GrayBar, ColorBar, BlackWhite

#log = getLog("BlackWhiteScale")

#log.setLevel(logging.ERROR)


def nonlinGrayBarScale(image, gradient, mostBlack, mostWhite, parenttags=None, level=logging.ERROR):
    ''' Uses the ratio method to scale the

    Keyword Arguments:
    image -- a PIL.Image object
    graduent -- a list of tuples (RGB) represending the grayBars
    mostBlack -- the darkest value in the stage
    mostWhite -- the lighest value in the stage
    parenttags -- tag string of the parent function
    level -- the logging level

    Returns
    A list of tuples to be used in place of the input gradient object
    '''

    # TODO: Make this work with any color. For now, hard code to red

    # Set the logging level
    log.setLevel(level)
    tags = parenttags + " GREYBARSCALE"

    log.info('Running nonlinGrayBarScale-ing', extra=tags)

    # Get the Black and White according to the grayBar
    origBlack = gradient[-1][0]
    origWhite = gradient[0][0]

    if origBlack == 0:
        origBlack = 1
    if origWhite == 0:
        origWhite = 1

    # Compute the ratio
    ratioB = (mostBlack + 0.0) / origBlack
    ratioW = (mostWhite + 0.0) / origWhite

    # Compute the line for origColor as X and ratio as Y
    slope = (ratioB - ratioW) / (origBlack - origWhite)
    intercept = ratioB - slope * origBlack

    log.info('oB: %f oW: %f nB: %f nW: %f m: %f b: %f' % (origBlack, origWhite, mostBlack, mostWhite, slope, intercept),
             extra=tags)

    newgrad = []
    for g in gradient:
        r, g, b = (g[0] * slope + intercept) * g[0], g[1], g[2]
        newgrad.append((r, g, b))

    # log.info('%s' % (newgrad), extra=tags)

    return newgrad



