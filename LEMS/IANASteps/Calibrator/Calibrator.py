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
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

    drawing = np.array(image)
    color = (255, 255, 255)
    thickness = 2

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

    start_point = (c0.box.coordinates[0], c0.box.coordinates[1])
    end_point = (c0.box.coordinates[2], c0.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c0', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c1 = GrayBarRadial(.36277 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    start_point = (c1.box.coordinates[0], c1.box.coordinates[1])
    end_point = (c1.box.coordinates[2], c1.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c1', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c2 = GrayBarRadial(.47690 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    start_point = (c2.box.coordinates[0], c2.box.coordinates[1])
    end_point = (c2.box.coordinates[2], c2.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c3 = GrayBarRadial(.59103 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    start_point = (c3.box.coordinates[0], c3.box.coordinates[1])
    end_point = (c3.box.coordinates[2], c3.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c4 = GrayBarRadial(.70516 * leftT + .13451 * leftH + qr.topLeft, qr.width)
    start_point = (c4.box.coordinates[0], c4.box.coordinates[1])
    end_point = (c4.box.coordinates[2], c4.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c5 = GrayBarRadial(.24864 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c5.box.coordinates[0], c5.box.coordinates[1])
    end_point = (c5.box.coordinates[2], c5.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c5', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c6 = GrayBarRadial(.36277 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c6.box.coordinates[0], c6.box.coordinates[1])
    end_point = (c6.box.coordinates[2], c6.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c6', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c7 = GrayBarRadial(.47690 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c7.box.coordinates[0], c7.box.coordinates[1])
    end_point = (c7.box.coordinates[2], c7.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c7', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c8 = GrayBarRadial(.59103 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c8.box.coordinates[0], c8.box.coordinates[1])
    end_point = (c8.box.coordinates[2], c8.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c8', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c9 = GrayBarRadial(.70516 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c9.box.coordinates[0], c9.box.coordinates[1])
    end_point = (c9.box.coordinates[2], c9.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c9', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

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
    start_point = (c0.box.coordinates[0], c0.box.coordinates[1])
    end_point = (c0.box.coordinates[2], c0.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c0_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c1 = GrayBarRadial(.59103 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    start_point = (c1.box.coordinates[0], c1.box.coordinates[1])
    end_point = (c1.box.coordinates[2], c1.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c1_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c2 = GrayBarRadial(.47690 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    start_point = (c2.box.coordinates[0], c2.box.coordinates[1])
    end_point = (c2.box.coordinates[2], c2.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c2_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c3 = GrayBarRadial(.36277 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    start_point = (c3.box.coordinates[0], c3.box.coordinates[1])
    end_point = (c3.box.coordinates[2], c3.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c3_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c4 = GrayBarRadial(.24864 * leftT + .81929 * leftH + qr.topLeft, qr.width)
    start_point = (c4.box.coordinates[0], c4.box.coordinates[1])
    end_point = (c4.box.coordinates[2], c4.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c4_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c5 = GrayBarRadial(.70516 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c5.box.coordinates[0], c5.box.coordinates[1])
    end_point = (c5.box.coordinates[2], c5.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c5_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c6 = GrayBarRadial(.59103 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c6.box.coordinates[0], c6.box.coordinates[1])
    end_point = (c6.box.coordinates[2], c6.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c6_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c7 = GrayBarRadial(.47690 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c7.box.coordinates[0], c7.box.coordinates[1])
    end_point = (c7.box.coordinates[2], c7.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c7_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c8 = GrayBarRadial(.36277 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c8.box.coordinates[0], c8.box.coordinates[1])
    end_point = (c8.box.coordinates[2], c8.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c8_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c9 = GrayBarRadial(.24864 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c9.box.coordinates[0], c9.box.coordinates[1])
    end_point = (c9.box.coordinates[2], c9.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c9_2', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

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
    start_point = (c0.box.coordinates[0], c0.box.coordinates[1])
    end_point = (c0.box.coordinates[2], c0.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c0_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c1 = GrayBarRadial(.13451 * leftT + .36277 * leftH + qr.topLeft, qr.width)
    start_point = (c1.box.coordinates[0], c1.box.coordinates[1])
    end_point = (c1.box.coordinates[2], c1.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c1_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1, lineType=cv2.LINE_AA)

    c2 = GrayBarRadial(.13451 * leftT + .47690 * leftH + qr.topLeft, qr.width)
    start_point = (c2.box.coordinates[0], c2.box.coordinates[1])
    end_point = (c2.box.coordinates[2], c2.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c2_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c3 = GrayBarRadial(.13451 * leftT + .59103 * leftH + qr.topLeft, qr.width)
    start_point = (c3.box.coordinates[0], c3.box.coordinates[1])
    end_point = (c3.box.coordinates[2], c3.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c3_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c4 = GrayBarRadial(.13451 * leftT + .70516 * leftH + qr.topLeft, qr.width)
    start_point = (c4.box.coordinates[0], c4.box.coordinates[1])
    end_point = (c4.box.coordinates[2], c4.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c4_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c5 = GrayBarRadial(.24864 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c5.box.coordinates[0], c5.box.coordinates[1])
    end_point = (c5.box.coordinates[2], c5.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c5_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c6 = GrayBarRadial(.24864 * leftT + leftH * .36277 + qr.topLeft, qr.width)
    start_point = (c6.box.coordinates[0], c6.box.coordinates[1])
    end_point = (c6.box.coordinates[2], c6.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c6_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c7 = GrayBarRadial(.24864 * leftT + leftH * .47690 + qr.topLeft, qr.width)
    start_point = (c7.box.coordinates[0], c7.box.coordinates[1])
    end_point = (c7.box.coordinates[2], c7.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c7_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c8 = GrayBarRadial(.24864 * leftT + leftH * .59103 + qr.topLeft, qr.width)
    start_point = (c8.box.coordinates[0], c8.box.coordinates[1])
    end_point = (c8.box.coordinates[2], c8.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c8_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c9 = GrayBarRadial(.24864 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c9.box.coordinates[0], c9.box.coordinates[1])
    end_point = (c9.box.coordinates[2], c9.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c9_3', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

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
    start_point = (c0.box.coordinates[0], c0.box.coordinates[1])
    end_point = (c0.box.coordinates[2], c0.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c0_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c1 = GrayBarRadial(.81929 * leftT + .59103 * leftH + qr.topLeft, qr.width)
    start_point = (c1.box.coordinates[0], c1.box.coordinates[1])
    end_point = (c1.box.coordinates[2], c1.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c1_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c2 = GrayBarRadial(.81929 * leftT + .47690 * leftH + qr.topLeft, qr.width)
    start_point = (c2.box.coordinates[0], c2.box.coordinates[1])
    end_point = (c2.box.coordinates[2], c2.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c2_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c3 = GrayBarRadial(.81929 * leftT + .36277 * leftH + qr.topLeft, qr.width)
    start_point = (c3.box.coordinates[0], c3.box.coordinates[1])
    end_point = (c3.box.coordinates[2], c3.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c3_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c4 = GrayBarRadial(.81929 * leftT + .24864 * leftH + qr.topLeft, qr.width)
    start_point = (c4.box.coordinates[0], c4.box.coordinates[1])
    end_point = (c4.box.coordinates[2], c4.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c4_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c5 = GrayBarRadial(.70516 * leftT + leftH * .70516 + qr.topLeft, qr.width)
    start_point = (c5.box.coordinates[0], c5.box.coordinates[1])
    end_point = (c5.box.coordinates[2], c5.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c5_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c6 = GrayBarRadial(.70516 * leftT + leftH * .59103 + qr.topLeft, qr.width)
    start_point = (c6.box.coordinates[0], c6.box.coordinates[1])
    end_point = (c6.box.coordinates[2], c6.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c6_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c7 = GrayBarRadial(.70516 * leftT + leftH * .47690 + qr.topLeft, qr.width)
    start_point = (c7.box.coordinates[0], c7.box.coordinates[1])
    end_point = (c7.box.coordinates[2], c7.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c7_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c8 = GrayBarRadial(.70516 * leftT + leftH * .36277 + qr.topLeft, qr.width)
    start_point = (c8.box.coordinates[0], c8.box.coordinates[1])
    end_point = (c8.box.coordinates[2], c8.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c8_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

    c9 = GrayBarRadial(.70516 * leftT + leftH * .24864 + qr.topLeft, qr.width)
    start_point = (c9.box.coordinates[0], c9.box.coordinates[1])
    end_point = (c9.box.coordinates[2], c9.box.coordinates[3])
    cv2.rectangle(drawing, start_point, end_point, color, thickness)
    label_position = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
    cv2.putText(drawing, 'c9_4', label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=1,
                lineType=cv2.LINE_AA)

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

    drawing = Image.fromarray(drawing)

    # for grayBar in grayBars:
    # #log.info(grayBar.__str__(), extra=tags)

    # grayBars.reverse()
    ##log.info('Done Running GrayBar Detection', extra=tags)
    return grayBars, drawing, ExitCode.Success


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

