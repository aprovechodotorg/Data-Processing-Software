
import logging
import cv2
import numpy as np
from PIL import Image

from IANASteps.BCFilterDetector.BCFilter import BCFilter
# from Logging.Logger import getLog
from IANASettings.Settings import BCFilterFixedConstants
from IANASettings.Settings import ExitCode


# log = getLog("BCFilterDetector")
# log.setLevel(logging.ERROR)


def computeCircleFromRadialQR(drawing, qr, down, left, rscale, parenttags=None):
    """ Uses the QR coodinates to compute the coordinates
        of a circle where the filter _should_ be

    Keyword Arguments:
    qr    -- The QR object
    down  -- How far down
    left  -- How far to the left

    Returns:
    (x, y) coordinates
    """

    qrTopLeft = qr.topLeft
    qrTopRight = qr.topRight
    qrBottomLeft = qr.bottomLeft
    qrBottomRight = qr.bottomRight

    x = [qrTopLeft[0], qrTopRight[0], qrBottomLeft[0], qrBottomRight[0]]
    y = [qrTopLeft[1], qrTopRight[1], qrBottomLeft[1], qrBottomRight[1]]

    middle = sum(x) / len(x), sum(y) / len(y)
    d0 = (qr.topLeft - middle)
    d1 = (qr.bottomLeft - qr.bottomRight)
    d2 = (qr.topRight - qr.bottomRight)
    d3 = (qr.topRight - qr.topLeft)
    d4 = (qr.topLeft - qr.bottomLeft)
    adjust = .1 / 1472.0 * max(abs(d1[0]), abs(d1[1]), abs(d2[0]), abs(d2[1]), abs(d3[0]), abs(d3[1]), abs(d4[0]),
                               abs(d4[1]))

    if d0[0] < 0:
        adjustX = -adjust
    else:
        adjustX = adjust
    if d0[1] < 0:
        adjustY = -adjust
    else:
        adjustY = adjust

    point = middle + (adjustX, adjustY)
    point2 = (qr.topLeft - qr.topRight)
    radius = abs(point2[0]) * .075
    drawing = np.array(drawing)
    cv2.circle(drawing, (int(point[0]), int(point[1])), int(radius), (0, 255, 0), 2)
    drawing = Image.fromarray(drawing)

    return point[0], point[1], radius, drawing


def computeCircleFromLinearQR(qr, down, left, rscale, parenttags=None):
    """ Uses the QR coodinates to compute the coordinates
        of a circle where the filter _should_ be

    Keyword Arguments:
    qr    -- The QR object
    down  -- How far down
    left  -- How far to the left

    Returns:
    (x, y) coordinates
    """

    qrTopLeft = qr.topLeft
    qrTopRight = qr.topRight
    qrBottomLeft = qr.bottomLeft
    qrBottomRight = qr.bottomRight

    # The dimensions for each side (in the worst case this is
    # a generic quadrilateral, but in the best case it's a square)
    qrTopL2R = qrTopRight - qrTopLeft  # x-distance at top
    qrBottomL2R = qrBottomRight - qrBottomLeft  # x-distance at bottom
    qrLeftT2B = qrBottomLeft - qrTopLeft  # y-distance at left
    qrRightT2B = qrBottomRight - qrTopRight  # y-distance at right
    qrDeltaL2R_T2B = qrRightT2B - qrLeftT2B  #

    # leftT2B = qrLeftT2B + qrDeltaL2R_T2B * left
    # topLeft = qrTopLeft + qrTopL2R * left + leftT2B * top
    # bottomLeft = qrBottomLeft + qrBottomL2R * left + leftT2B * bottom

    # rightT2B = qrLeftT2B + qrDeltaL2R_T2B * right
    # topRight = qrTopLeft + qrTopL2R * right + rightT2B * top
    # bottomRight = qrBottomLeft + qrBottomL2R * right + rightT2B * bottom

    point = (qrBottomRight + qrRightT2B * down) + qrBottomL2R * left
    radius = qrBottomLeft.distance(qrBottomRight) * rscale

    ##log.info("Put filter at: " + str(point) + " r: " + str(radius), extra=parenttags)

    return point[0], point[1], radius


def detectBCFilterFixed(qr, bcFilterFixedConstants, drawing, cardType, parenttags=None):
    ''' Detects circles in an image

    Keyword Arguments:
    image -- Image instance
    bcFilterConstantsFixed -- The configuration under which to run bcFilter detection
    parenttags -- tag string of the calling function
    level -- The logging level

    Returns:
    list of CirclesFilter_.BCFilter objects
    '''
    bcFilters = []

    if cardType == 'radial':
        p0, p1, radius, drawing = computeCircleFromRadialQR(drawing, qr, bcFilterFixedConstants.rad_down,
                                                            bcFilterFixedConstants.rad_left,
                                           bcFilterFixedConstants.rad_rscale)
        circle = (p0, p1, radius)
    else:
        circle = computeCircleFromLinearQR(qr, bcFilterFixedConstants.down, bcFilterFixedConstants.left,
                                           bcFilterFixedConstants.rscale)

    bcFilters.append(BCFilter(*circle))

    return bcFilters, drawing
