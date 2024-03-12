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

import logging
import cv2
import numpy as np

from IANASteps.Geometry.Point import Point
from IANASteps.QRDetector.QR import QR_Radial, QR_Linear

def is_color_close_to_black(region):
    #checks if a given color is close to black and not any other colors

    # Calculate the average color in the region
    avg_color = region

    # Define a threshold for darkness (adjust as needed)
    red_threshold = 60
    blue_threshold = 60
    green_threshold = 85

    #if the average rgb is less than each threshhold (closer to 0 is black) then it is close to black
    if avg_color[0] < red_threshold and avg_color[1] < green_threshold and avg_color[2] < blue_threshold:
        return True
    else:
        return False

def detectQR(file_, parenttags=None, level=logging.ERROR):
    '''Using geometry detection, find the black boxes and return their coordinates

    Keyword arguments:
    file_      -- The full file name toward the image file to be processed.
    parenttags -- The tag string of the calling method.
    level      -- The logging level.

    Returns:
    QR       -- an object of QRDetector.QR type.
    exitcode -- exit code returning from FindQRCode.jar.
    '''

    # Read the image
    image = cv2.imread(file_)

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

            # Define a range for acceptable aspect ratios for QR codes (qr codes are squares so they should be close to a 1:1 aspect ratio
            aspect_ratio_range = (0.5, 1.5)

            # Check if the aspect ratio falls within the acceptable range and width is larger enough
            if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                if w > 15 and w < 155:
                    try:
                        # Calculate the center of the QR code
                        M = cv2.moments(approx)
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])

                        # Check the average color in a 2x2 pixel square around the center
                        center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                        mean_color = np.mean(center_region, axis=(0, 1))
                        #check if the center of the square is black
                        if is_color_close_to_black(mean_color) == True:
                            # Draw a rectangle around the QR code
                            cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
                            #append the coordiantes
                            qr_centers.append((cX, cY))
                    except:
                        pass

    if len(qr_centers) != 4:
        # Read the image
        image = cv2.imread(file_)

        # Apply a Gaussian blur to the image to reduce noise and improve detection
        blurred = cv2.GaussianBlur(image, (7, 7), 0)

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

                # Define a range for acceptable aspect ratios for QR codes (qr codes are squares so they should be close to a 1:1 aspect ratio
                aspect_ratio_range = (0.5, 1.5)

                # Check if the aspect ratio falls within the acceptable range and width is larger enough
                if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                    if w > 15 and w < 155:
                        try:
                            # Calculate the center of the QR code
                            M = cv2.moments(approx)
                            cX = int(M["m10"] / M["m00"])
                            cY = int(M["m01"] / M["m00"])

                            # Check the average color in a 2x2 pixel square around the center
                            center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                            mean_color = np.mean(center_region, axis=(0, 1))
                            # check if the center of the square is black
                            if is_color_close_to_black(mean_color) == True:
                                # Draw a rectangle around the QR code
                                cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
                                # append the coordiantes
                                qr_centers.append((cX, cY))
                        except:
                            pass

    if len(qr_centers) != 4:
        # Read the image
        image = cv2.imread(file_)

        # Apply a Gaussian blur to the image to reduce noise and improve detection
        blurred = cv2.GaussianBlur(image, (3, 3), 0)

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

                # Define a range for acceptable aspect ratios for QR codes (qr codes are squares so they should be close to a 1:1 aspect ratio
                aspect_ratio_range = (0.5, 1.5)

                # Check if the aspect ratio falls within the acceptable range and width is larger enough
                if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                    if w > 15 and w < 155:
                        try:
                            # Calculate the center of the QR code
                            M = cv2.moments(approx)
                            cX = int(M["m10"] / M["m00"])
                            cY = int(M["m01"] / M["m00"])

                            # Check the average color in a 2x2 pixel square around the center
                            center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                            mean_color = np.mean(center_region, axis=(0, 1))
                            # check if the center of the square is black
                            if is_color_close_to_black(mean_color) == True:
                                # Draw a rectangle around the QR code
                                cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
                                # append the coordiantes
                                qr_centers.append((cX, cY))
                        except:
                            pass

    # Show the image with QR codes highlighted
    #imS = cv2.resize(image, (960, 540))
    #cv2.imshow("QR Codes", imS)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    # Sort the QR centers based on coordinates (top left, top right, bottom left, bottom right)

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

    #reformat the list of coordinates
    qr_centers = [top_left, top_right, bottom_left, bottom_right]

    #make the coordinates into points
    points = []
    for value in qr_centers:
        points.append(Point((float(value[0]), float(value[1]))))

    #specify that the newer radial card is being used
    aux = 'radial'
    if aux[0:6] == 'radial':
        #go into function, return more information from coordinates
        return QR_Radial(aux, points)
    else:
        return QR_Linear(aux, points)
