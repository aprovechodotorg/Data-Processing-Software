'''
Created on Oct 10, 2010

@author: surya
'''

from PIL.ImageStat import Stat
from IANASteps.Geometry.Point import Point
from IANASteps.Geometry.Rectangle import Rectangle
from IANASettings.Settings import CalibratorConstants


class ColorBar:
    '''
    This class represents a ColorBar on the Stage, and contains functionality to
    Sample the color in the ColorBar.

    NOTE: A ColorBar is represented by two rectangles, leftBox and righBox which
    are small rectangles within the ColorBar on the left and right extremities of the
    ColorBar in the Image.

    NOTE: The information of interest in a ColorBar is the RGB value of the ColorBar
          (derived from leftBox and rightBox)
    '''

    def __init__(self, left, right):
        ''' Constructor

        Keyword Arguments:
        left    --  This is a point on the left part of the ColorBar
        right   --  This is a point on the right part of the ColorBar
        level   --  The logging level
        '''

        # TODO: push this to settings
        self.boxSize = Point(CalibratorConstants.BoxSize, CalibratorConstants.BoxSize)

        # LeftBox - a nxn box on the left side of the ColorBar
        self.leftBox = Rectangle([int(x) for x in left - self.boxSize] + [int(x) for x in left + self.boxSize])

        # RightBox - a nxn box on the right side of the ColorBar
        self.rightBox = Rectangle([int(x) for x in right - self.boxSize] + [int(x) for x in right + self.boxSize])

        # TODO: whats' the exception handling story: currently choose the right point

    #       and throw one unified exception
    # TODO: throw debug messages wherever necessary
    def sample(self, image):
        ''' Samples leftBox and rightBox areas from the given Image

        Keyword Arguments:
        image  -- a PIL.Image instance

        Returns:
        The RGB value of the ColorBar
        '''

        # The color as sample through the leftBox
        l = Point(Stat(image.crop(self.leftBox.coordinates)).mean)
        # The color as sample through the rightBox
        r = Point(Stat(image.crop(self.rightBox.coordinates)).mean)

        # !!TODO: enforce color threshold within calibrating bars
        # allow for some variation in the bar
        # if (l-r).distance() > 35:
        #    raise CalibrationError(('Color bars should be constant! '
        #                                    'found (left, right): ({l}, {r})')
        #

        # save the average color
        return (l + r) / 2

    def draw(self, drawing, color):
        ''' Draws the ColorBar.
        '''
        self.leftBox.draw(drawing, color)
        self.rightBox.draw(drawing, color)