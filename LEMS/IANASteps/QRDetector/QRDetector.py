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

def is_color_close_to_black(region, black):
    #checks if a given color is close to black and not any other colors

    # Calculate the average color in the region
    avg_color = region

    # Define a threshold for darkness (adjust as needed)
    red_threshold = black[0]
    blue_threshold = black[1]
    green_threshold = black[2]

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

    blur = [(5, 5), (7, 7), (3, 3)]
    black = [150, 150, 150]
    qr_centers = []
    loops = 0
    found_valid_centers = False

    while (len(qr_centers) != 4) and (loops <= len(blur)) and not found_valid_centers:
        for blurry in blur:
            # Read the image
            image = cv2.imread(file_)

            # Apply a Gaussian blur to the image to reduce noise and improve detection
            blurred = cv2.GaussianBlur(image, blurry, 0)

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
                    aspect_ratio_range = (0.5, 1.5)

                    # Check if the aspect ratio falls within the acceptable range and width is large enough
                    if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                        if w > 20 and w < 155:
                            try:
                                # Calculate the center of the QR code
                                M = cv2.moments(approx)
                                cX = int(M["m10"] / M["m00"])
                                cY = int(M["m01"] / M["m00"])

                                # Check the average color in a 2x2 pixel square around the center
                                center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                                mean_color = np.mean(center_region, axis=(0, 1))
                                # Check if the center of the square is black
                                if is_color_close_to_black(mean_color, black):
                                    # Append the coordinates
                                    qr_centers.append((cX, cY))
                            except:
                                pass
            if len(qr_centers) == 4:
                found_valid_centers = True
                break

            # If we have more than 4 QR centers, we need to remove the ones that are not black enough
            if len(qr_centers) > 4:
                while (len(qr_centers) > 4) and (black[0] >= 0):
                    for idx, val in enumerate(black):
                        black[idx] = val - 5

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
                            aspect_ratio_range = (0.5, 1.5)

                            # Check if the aspect ratio falls within the acceptable range and width is large enough
                            if aspect_ratio_range[0] < aspect_ratio < aspect_ratio_range[1]:
                                if w > 20 and w < 155:
                                    try:
                                        # Calculate the center of the QR code
                                        M = cv2.moments(approx)
                                        cX = int(M["m10"] / M["m00"])
                                        cY = int(M["m01"] / M["m00"])

                                        # Check the average color in a 2x2 pixel square around the center
                                        center_region = image[cY - 1:cY + 1, cX - 1:cX + 1]
                                        mean_color = np.mean(center_region, axis=(0, 1))

                                        # If the center of the square is not black, remove it from qr_centers
                                        if not is_color_close_to_black(mean_color, black):
                                            if (cX, cY) in qr_centers:
                                                qr_centers.remove((cX, cY))
                                    except:
                                        pass

                    # If we've reduced qr_centers to exactly 4, exit both loops
                    if len(qr_centers) == 4:
                        found_valid_centers = True
                        break

            if found_valid_centers:
                break

        loops += 1
    # After the loop, draw rectangles for the final qr_centers
    for (cX, cY) in qr_centers:
        # Find the bounding box of the QR code associated with each center
        for contour in contours:
            # Approximate the contour to a polygon
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                M = cv2.moments(approx)
                # Check if M["m00"] is zero to avoid division by zero
                if M["m00"] != 0:
                    centerX = int(M["m10"] / M["m00"])
                    centerY = int(M["m01"] / M["m00"])
                else:
                    # Handle the case where the area is zero
                    centerX, centerY = 0, 0  # or some other default value or skip this contour
                    continue  # Skip further processing for this contour

                if (centerX, centerY) == (cX, cY):
                    # Draw a rectangle around the QR code
                    cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)

    # Resize the image for display
    #imS = cv2.resize(image, (960, 540))

    # Show the final image with the rectangles drawn
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
