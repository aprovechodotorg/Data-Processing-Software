'''
The QRFilter Module contains functionality to extract data from a
QR code(aux_id), and the co-ordinates of the QR code itself.

It essentially takes a filename (absolute path to the input image),
uses Popen to spawn a new sub-process to execute:

     java -jar pathToFindQRCode/FindQRCode.jar [options] filename

And parses out a the aux_id and a set of QR coordinates from the output pipe.


Created on Oct 8, 2010

@author: surya
'''

import os
import logging
import cv2
from pyzbar.pyzbar import decode
import numpy as np
#import StringIO
from io import StringIO

from subprocess import PIPE, Popen
#from Logging.Logger import getLog
from IANASteps.Geometry.Point import Point
from IANASteps.QRDetector.QR import QR_Radial, QR_Linear
from IANASettings.Settings import ExitCode


#log = getLog("QRFilter")
#log.setLevel(logging.ERROR)
def is_color_close_to_black(region):
    # Calculate the average color in the region
    avg_color = region

    # Define a threshold for darkness (adjust as needed)
    red_threshold = 100
    blue_threshold = 100
    green_threshold = 100

    if avg_color[0] < red_threshold and avg_color[1] < green_threshold and avg_color[2] < blue_threshold:
        return True
    else:
        return False

    # Check if the average color is close to black
    #return all(value < threshold for value in avg_color)

def detectQR(file_, parenttags=None, level=logging.ERROR):
    '''Call FindQRCode.jar to see whether QR code is correct.

    Keyword arguments:
    file_      -- The full file name toward the image file to be processed.
    parenttags -- The tag string of the calling method.
    level      -- The logging level.

    Returns:
    QR       -- an object of QRDetector.QR type.
    exitcode -- exit code returning from FindQRCode.jar.

    '''
    '''
    #try:
    # Set the logging level
    #log.setLevel(level)
    #tags = parenttags + " QR"

    #print "Running QR Detection"
    if isinstance(file_, str):
        qrCommand = ['java', '-jar', os.path.join(os.path.dirname(__file__), 'FindQRCode.jar'),
                         'http://www.projectsurya.org/', file_]

        QRFinder = Popen(qrCommand, stdout=PIPE, close_fds=True)
        QRFinder_out = QRFinder.stdout
    else:
        qrCommand = ['java', '-jar', os.path.join(os.path.dirname(__file__), 'FindQRCode.jar'),
                         'http://www.projectsurya.org/']
        QRFinder = Popen(qrCommand, stdout=PIPE, stdin=PIPE, close_fds=True)
        s = StringIO(file_)
        file_.save(s,'png')
        s.seek(0)
        #QRFinder_out = QRFinder.communicate(input=file_.tostring())[0].splitlines()
        QRFinder_out = QRFinder.communicate(input=s.read())[0].splitlines()
    exitcode = QRFinder.wait()

    '''
    #'''
    # Read the image
    image = cv2.imread(file_)

    # Convert the image to grayscale
    #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a Gaussian blur to the image to reduce noise and improve detection
    blurred = cv2.GaussianBlur(image, (5, 5), 0)

    # Use the Canny edge detector to find edges in the image
    edges = cv2.Canny(blurred, 50, 150)

    # Find contours in the image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    qr_centers = []

    # Loop over the contours
    for contour in contours:
        # Approximate the contour to a polygon
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # If the polygon has 4 vertices and has a reasonable aspect ratio, it might be a QR code
        if len(approx) == 4:
            # Calculate the aspect ratio of the bounding box
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h

            # Define a range for acceptable aspect ratios for QR codes
            aspect_ratio_range = (0.6, 1.4)

            # Check if the aspect ratio falls within the acceptable range and width is larger enough
            if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1] and w > 20 and w < 155:
                # Calculate the center of the QR code
                M = cv2.moments(approx)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                # Check the average color in a 1x1 pixel square around the center
                center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                mean_color = np.mean(center_region, axis=(0, 1))
                if is_color_close_to_black(mean_color) == True:
                    # Draw a rectangle around the QR code
                    cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)

                    qr_centers.append((cX, cY))

    # Show the image with QR codes highlighted
    #imS = cv2.resize(image, (960, 540))
    #cv2.imshow("QR Codes", imS)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    # Sort the QR centers based on coordinates (top left, top right, bottom left, bottom right)
    #qr_centers.sort(key=lambda point: (point[1], point[0]))
    # Sort coordinates based on x values
    sorted_coordinates = sorted(qr_centers, key=lambda x: x[0])
    max_x = sorted_coordinates[3][0]
    # Sort coordinates based on y values
    sorted_coordinates = sorted(qr_centers, key=lambda x: x[1])
    max_y = sorted_coordinates[3][1]

    target_x = max_x / 2
    target_y = max_y / 2

    for coor in qr_centers:
        if coor[0] < target_x and coor[1] < target_y:
            top_left = coor
        elif coor[0] < target_x and coor[1] > target_y:
            bottom_left = coor
        elif coor[0] > target_x and coor[1] < target_y:
            top_right = coor
        elif coor[0] > target_x and coor[1] > target_y:
            bottom_right = coor
    # Sort coordinates based on x values
    #sorted_coordinates = sorted(qr_centers, key=lambda x: x[0])

    # Top left: low x, low y
    #top_left = sorted_coordinates[0]

    # Top right: high x, low y
    #top_right = sorted_coordinates[3]

    # Sort coordinates based on y values
    #sorted_coordinates = sorted(qr_centers, key=lambda x: x[1])

    # Bottom left: low x, high y
    #bottom_left = sorted_coordinates[2]

    # Bottom right: high x, high y
    #bottom_right = sorted_coordinates[3]

    qr_centers = [top_left, top_right, bottom_left, bottom_right]

    points = []
    for value in qr_centers:
        points.append(Point((float(value[0]), float(value[1]))))

    #'''
    '''
    #Extracting QR code
    points = []

    qrLine = None
    for line in QRFinder_out:
        if qrLine is None:
            qrLine = line[:-1]
            #log.info("Finding QRCode: " + str(qrLine), extra=tags)
            #print "Finding QRCode: " + str(qrLine)
            continue
        try:
            x, y = line[:-1].split(',')
        except:
            test = line[:-2].decode("utf-8")
            x, y = test.split(',')
        points.append(Point((float(x), float(y))))
        #log.info("test: {0}, {1}".format(Point((float(x), float(y)))[0],Point((float(x), float(y)))[1]))
        #log.info("QR point (x, y): {0:s}, {1:s}".format(x, y), extra=tags)
        #log.info("QR fpoint (x, y): {0}, {1}".format(float(x), float(y)), extra=tags)
        # eg. Points: [(653.0, 412.0), (653.5, 282.5), (782.5, 283.5), (763.5, 395.5)]

    QRFinder.stdout.close()

    if not points:
        #log.error("Cannot extract QR info, check FindQRCode.jar, " + "exitcode of FindQRCode.jar is " + str(exitcode), extra=tags)
        print("Cannot extract QR info, check FindQRCode.jar, " + "exitcode of FindQRCode.jar is " + str(exitcode))
        return None, ExitCode.QRDetectionError
    
    aux = ""
    if qrLine:
        aux = str(qrLine)
        try:
            aux = aux[aux.rindex("v=")+2:]
        except Exception as err:
            print('Error %s' % str(err))
            #log.error('Error %s' % str(err), extra=tags)

    #log.info("QR Aux info. (aux_id): " + aux, extra=tags)

    #log.info("Done Running QR Detection", extra=tags)
    
    print("aux[0:6]:", aux[0:6])
    '''
    aux = 'radial'
    if aux[0:6] == 'radial':
        return QR_Radial(aux, points)
    else:
        return QR_Linear(aux, points)
    '''
    except Exception as err:
        #log.error("QR Detection Failed %s", str(err), extra=tags)
        return None, ExitCode.QRDetectionError
    '''