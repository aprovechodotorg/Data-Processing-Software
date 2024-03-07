'''
Created on Oct 13, 2010

@author: surya
'''

import logging

from PIL.Image import QUAD, BICUBIC, Image, PERSPECTIVE
from PIL import Image
# from Logging.Logger import getLog
from IANASettings.Settings import ExitCode
import numpy


# log = getLog("ImageTransformer")
# log.setLevel(logging.ERROR)

# where pb is the four vertices in the current plane, and pa contains four vertices in the resulting plane
def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

    A = numpy.matrix(matrix, dtype=float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


def transformRadial(image, qr, parenttags=None, level=logging.ERROR):
    ''' Performs the skew correction in the image.

    Keyword Arguments:
    image -- PIL.Image instance
    stage -- Absolute coordinates of the stage
    parentttags -- tag string of the calling function

    Returns:
    PIL.Image, The cropped image containing the stage.
    '''

    # Set the logging level
    # log.setLevel(level)
    #tags = parenttags + " TRANSFORM"
    # log.info('Running Image Transformation - Skew Correction', extra=tags)

    height = (qr.topLeft - qr.bottomLeft).distance()
    width = (qr.topRight - qr.topLeft).distance()

    if height > width:
        width = height
    else:
        height = width

    oWidth, oHeight = image.size

    # dimensions and geometery of ideal QR code
    paddingX = (oWidth - width) / 2
    paddingY = (oHeight - height) / 2
    fTL = (paddingX, paddingY)
    fTR = (paddingX + width, paddingY)
    fBL = (paddingX, height + paddingY)
    fBR = (width * 0.934783 + paddingX, height * 0.934783 + paddingY)

    coeffs = find_coeffs((fTR, fTL, fBL, fBR), (qr.topRight, qr.topLeft, qr.bottomLeft, qr.bottomRight))

    try:
        img = image.transform((oWidth, oHeight), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    except Exception as err:
        # log.error('Error %s' % str(err), extra=tags)
        return None, ExitCode.ImageTransformationError

    return img, ExitCode.Success


def transformLinear(image, stage, parenttags=None, level=logging.ERROR):
    ''' Performs the skew correction in the image.

    Keyword Arguments:
    image -- PIL.Image instance
    stage -- Absolute coordinates of the stage
    parentttags -- tag string of the calling function

    Returns:
    PIL.Image, The cropped image containing the stage.
    '''

    # Set the logging level
    # log.setLevel(level)
    tags = parenttags + " TRANSFORM"

    height = ((stage.topRight - stage.bottomRight).distance()
              + (stage.topLeft - stage.bottomLeft).distance()) / 2
    width = ((stage.topRight - stage.topLeft).distance()
             + (stage.bottomRight - stage.bottomLeft).distance()) / 2

    ##log.info('Running Image Transformation - Skew Correction', extra=tags)

    try:
        img = image.transform((int(width), int(height)), QUAD,
                              (stage.topLeft[0], stage.topLeft[1], stage.bottomLeft[0], stage.bottomLeft[1],
                               stage.bottomRight[0], stage.bottomRight[1], stage.topRight[0], stage.topRight[1]),
                              BICUBIC)

    except Exception as err:
        # log.error('Error %s' % str(err), extra=tags)
        return None, ExitCode.ImageTransformationError

    return img, ExitCode.Success