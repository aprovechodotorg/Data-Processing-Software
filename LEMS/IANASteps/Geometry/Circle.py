'''
Created on Oct 12, 2010

@author: surya
'''

from IANASteps.Geometry.Point import Point


class Circle:
    """
    This class implements the base functionality for all image components
    that are circular.

    Using this class as the base class the inheritors will by default be able
    to crop/draw.
    """

    def __init__(self, x, y, radius):
        """ Constructor

        Sets the logging level and the center and radius fields of this class

        Keyword arguments:
        x     -- Circle x coordinate
        y     -- Circle y coordinate
        radius-- Circle radius
        """

        self.center = Point(x, y)
        self.radius = radius

    def __str__(self):
        """ Human readable representation

        Returns:
        str -- the center and radius of the circle
        """
        return '{{center:{0}, radius:{1}}}'.format(self.center, self.radius)

    def draw(self, drawing, color, samplingfactor=20):
        """ Draws the outline of the circle on the specified drawing

        Keyword arguments:
        drawing -- Image.Draw instance
        color   -- Color to draw the outline in
        samplingfactor -- An indicator to the size of the center of the circle that needs to be drawn
        """
        offset = self.radius, self.radius

        drawing.ellipse((self.center - offset, self.center + offset),
                        outline=color)
        spotRadius = self.radius / samplingfactor
        offset = spotRadius, spotRadius

        topLeft = self.center - offset
        bottomRight = self.center + offset
        drawing.rectangle((topLeft, bottomRight), outline=color)

    def crop(self, image):
        """ Creates a cropped copy of the image using the bounds of the filter

        Keyword arguments:
        image -- Image instance

        Returns:
        Cropped Image
        """
        offset = self.radius, self.radius

        topLeft = self.center - offset
        bottomRight = self.center + offset

        return image.crop((int(topLeft[0]), int(topLeft[1]),
                           int(bottomRight[0]), int(bottomRight[1])))