'''
Created on Oct 10, 2010

@author: surya
'''

from PIL.ImageStat import Stat
from PIL import Image
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from IANASteps.Geometry.Point import Point
from IANASteps.Geometry.Rectangle import Rectangle
from IANASettings.Settings import CalibratorConstants


class GrayBar:
    '''
    This class represents a GrayBar on the Stage, and includes functionality to get
    a gradient involving gray-scale values on the GrayBar.
    '''

    def __init__(self, point, qrwidth):
        ''' Constructor

        Sets the logging level, and represents the GrayBar in terms
        of a small Rectangle relative the point param.

        Keyword Arguments:
        point  -- A point in the GrayBar
        qrwidth -- the width of the QR.
        '''

        tempBoxSize = int(round(qrwidth * CalibratorConstants.BoxScale[0] + CalibratorConstants.BoxScale[1]))

        # TODO: push this to settings
        # self.boxSize = Point(CalibratorConstants.BoxSize,CalibratorConstants.BoxSize)
        self.boxSize = Point(tempBoxSize, tempBoxSize)

        # LeftBox - a nxn box on the left side of the ColorBar
        self.box = Rectangle([int(x) for x in point - self.boxSize] + [int(x) for x in point + self.boxSize])

    def __str__(self):
        ''' Returns a Human-Readable representation of the class
        '''
        test = 1
        return 'GrayBar: [ ' + self.box.__str__() + ' - ' + self.boxSize.__str__() + ' ]'

    def sample(self, image):
        ''' Samples the GrayBar

        Keyword Arguments:
        image -- a PIL.Image object

        Returns:
        The RGB value of the GrayBar
        '''
        image = image.convert("RGB")
        image.load()
        color = Stat(image.crop(self.box.coordinates)).mean
        return color

    def draw(self, drawing, color):
        '''
        '''

        self.box.draw(drawing, color)


class GrayBarRadial:
    '''
    This class represents a GrayBar on the Stage, and includes functionality to get
    a gradient involving gray-scale values on the GrayBar.
    '''

    def __init__(self, point, qrwidth):
        ''' Constructor

        Sets the logging level, and represents the GrayBar in terms
        of a small Rectangle relative the point param.

        Keyword Arguments:
        point  -- A point in the GrayBar
        qrwidth -- the width of the QR.
        '''

        tempBoxSize = int(round(qrwidth * CalibratorConstants.rad_BoxScale[0] + CalibratorConstants.rad_BoxScale[1]))

        # TODO: push this to settings
        # self.boxSize = Point(CalibratorConstants.BoxSize,CalibratorConstants.BoxSize)
        self.boxSize = Point(tempBoxSize, tempBoxSize)

        # LeftBox - a nxn box on the left side of the ColorBar
        self.box = Rectangle([int(x) for x in point - self.boxSize] + [int(x) for x in point + self.boxSize])

    def __str__(self):
        ''' Returns a Human-Readable representation of the class
        '''
        test = 1
        return 'GrayBar: [ ' + self.box.__str__() + ' - ' + self.boxSize.__str__() + ' ]'

    def sample(self, image):
        ''' Samples the GrayBar

        Keyword Arguments:
        image -- a PIL.Image object

        Returns:
        The RGB value of the GrayBar
        '''
        image = image.convert("RGB")
        image.load()
        color = Stat(image.crop(self.box.coordinates)).mean
        return color

    def draw(self, drawing, color):
        '''
        '''
        test = 1
        self.box.draw(drawing, color)


class GrayBarRadialSmall:
    '''
    This class represents a GrayBar on the Stage, and includes functionality to get
    a gradient involving gray-scale values on the GrayBar.
    '''

    def __init__(self, point, qrwidth):
        ''' Constructor

        Sets the logging level, and represents the GrayBar in terms
        of a small Rectangle relative the point param.

        Keyword Arguments:
        point  -- A point in the GrayBar
        qrwidth -- the width of the QR.
        '''

        tempBoxSize = int(
            round(qrwidth * CalibratorConstants.rad_BoxScaleSmall[0] + CalibratorConstants.rad_BoxScaleSmall[1] - 4))

        # TODO: push this to settings
        # self.boxSize = Point(CalibratorConstants.BoxSize,CalibratorConstants.BoxSize)
        self.boxSize = Point(tempBoxSize, tempBoxSize)

        # LeftBox - a nxn box on the left side of the ColorBar
        self.box = Rectangle([int(x) for x in point - self.boxSize] + [int(x) for x in point + self.boxSize])

    def __str__(self):
        ''' Returns a Human-Readable representation of the class
        '''
        return 'GrayBar: [ ' + self.box.__str__() + ' - ' + self.boxSize.__str__() + ' ]'

    def sample(self, image):
        ''' Samples the GrayBar

        Keyword Arguments:
        image -- a PIL.Image object

        Returns:
        The RGB value of the GrayBar
        '''
        image = image.convert("RGB")
        image.load()
        color = Stat(image.crop(self.box.coordinates)).mean
        return color

    def draw(self, drawing, color):
        '''
        '''

        self.box.draw(drawing, color)