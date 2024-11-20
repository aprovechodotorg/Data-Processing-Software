'''
Created on Oct 8, 2010

@author: surya
'''

import math

from IANASteps.Geometry.Quadrilateral import Quadrilateral


class QR_Radial(Quadrilateral):
    '''
    Represents a QR code in the image, this class contains
    all the information on and from the QR code :
    aux_id, co-ordinates, height, width, rotation, and the corrected
    topLeft, topRight, bottomLeft, bottomRight coordinates
    '''

    def __init__(self, aux, points):
        # Called by QRDetector
        ''' Constructor

        Sets the logging level, and the aux and points fields

        This method also computes all QR properties namely:
        height, width, rotation, and the corrected
        topLeft, topRight, bottomLeft, bottomRight coordinates

        Keyword arguments:
        aux    -- aux_id used to get calibration data refer:DB Schema
        points -- a tuple of 4 Geometry.Point objects representing the co-ordinates for the QR code
        '''

        self.aux = aux
        # The raw QR points
        self.points = points

        # top right to bottom right
        v23 = points[3] - points[1]
        # top left to top right
        v21 = points[0] - points[1]

        self.width = v23.distance()
        self.height = v21.distance()
        p2 = v23[0] / self.width
        p3 = v23[1] / self.width

        # find angle between points
        rotation = math.degrees(math.atan2(p3, p2))

        # bound rotation to 0 to 360
        if rotation < 0 or rotation > 360:
            rotation -= math.floor(rotation / 360.0) * 360

        self.rotation = rotation

        # topLeft, bottomLeft, bottomRight, topRight
        Quadrilateral.__init__(self, points[0], points[2], points[3], points[1])  # no adjustment


    def __str__(self):
        """ Human readable representation

        Returns:
        str -- all the information regarding the QR code
        """

        return 'QR: aux:{0}, points:{1}, width:{2}, height:{3}, rotation:{4}, {5}'.format(self.aux,
                                                                                            self.points,
                                                                                            self.width,
                                                                                            self.height,
                                                                                            self.rotation,
                                                                                            Quadrilateral.__str__(self))


class QR_Linear(Quadrilateral):
    '''
    Represents a QR code in the image, this class contains
    all the information on and from the QR code :
    aux_id, co-ordinates, height, width, rotation, and the corrected
    topLeft, topRight, bottomLeft, bottomRight coordinates
    '''

    def __init__(self, aux, points):
        ''' Constructor

        Sets the logging level, and the aux and points fields

        This method also computes all QR properties namely:
        height, width, rotation, and the corrected
        topLeft, topRight, bottomLeft, bottomRight coordinates

        Keyword arguments:
        aux    -- aux_id used to get calibration data refer:DB Schema
        points -- a tuple of 4 Geometry.Point objects representing the co-ordinates for the QR code
        '''

        self.aux = aux
        # The raw QR points
        self.points = points

        v23 = points[2] - points[1]
        v21 = points[0] - points[1]

        self.width = v23.distance()
        self.height = v21.distance()

        rotation = math.degrees(math.atan2(*reversed(v23 / self.width)))

        # bound rotation to 0 to 360
        if rotation < 0 or rotation > 360:
            rotation -= math.floor(rotation / 360.0) * 360

        self.rotation = rotation


        # This is not technically the corners, but instead
        # adjusted for the alignment point (which is offset
        # from the other points)
        #!! this will change if you change the QR code (at least it just did)
        Quadrilateral.__init__(self, points[1], (points[0] - v21 / 7.4), points[3], (points[2] - v23 / 7.0))

    def __str__(self):
        """ Human readable representation

        Returns:
        str -- all the information regarding the QR code
        """

        return 'QR: aux:{0}, points:{1}, width:{2}, height:{3}, rotation:{4}, {5}'.format(self.aux,
                                                                                            self.points,
                                                                                            self.width,
                                                                                            self.height,
                                                                                            self.rotation,
                                                                                            Quadrilateral.__str__(self))