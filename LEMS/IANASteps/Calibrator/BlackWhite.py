'''
Created on Jan 13, 2011

@author: Martin
'''

from PIL.ImageStat import Stat
from IANASteps.Geometry.Point import Point
from IANASteps.Geometry.Rectangle import Rectangle
from IANASettings.Settings import CalibratorConstants


class BlackWhite:
    '''
    This class represents the darkets and lightest parts of the entire calibrator.
    It includes the histogram for debugging purposes
    '''

    def __init__(self, blackcoords, whitecoords, hist=None):
        ''' Constructor

        Sets the logging level, and represents the darket
        of a small Rectangle relative the point param.

        Keyword Arguments:
        white -- the coords of lightest part of the image
        black -- the coords of darkest part of the image
        hist -- the histogram for a single channel... an array of length 256
        '''
        self.whitecoords = Point(whitecoords)
        self.blackcoords = Point(blackcoords)
        # Caution: Hardcoded to return red value
        # self.black, self.white = image.getpixel(self.blackcoords)[0], image.getpixel(self.whitecoords)[0]
        if hist is not None:
            self.hist = Point(hist)
        else:
            self.hist = None
        # boxSize for drawing where the sample is
        self.boxSize = Point(CalibratorConstants.BoxSize, CalibratorConstants.BoxSize)
        self.wbox = Rectangle(
            [int(x) for x in whitecoords - self.boxSize] + [int(x) for x in whitecoords + self.boxSize])
        self.bbox = Rectangle(
            [int(x) for x in blackcoords - self.boxSize] + [int(x) for x in blackcoords + self.boxSize])

    def __str__(self):
        ''' Returns a Human-Readable representation of the class
        '''
        return 'Black: [ ' + self.white + ', ' + self.blackcoords.__str__() + ' ] White: [ ' + self.white + ', ' + self.whitecoords.__str__() + ' ]'

    def sample(self, image):
        ''' Sample the darkest and lightest parts of the image

        Keyword Arguments:
        image -- a PIL.Image object

        Returns:
        The darkest and lightest values of the image
        '''
        # Caution: Hardcoded to return red value
        return image.getpixel(self.blackcoords)[0], image.getpixel(self.whitecoords)[0]
        # return black, white

    def hist(self, image):
        '''Return the histogram

        Keyword Arguments:
        image -- a PIL.Image object

        Returns:
        The histogram for the entire image as a Point object
        '''
        return self.hist

    def draw(self, drawing, color):
        '''
        '''
        self.wbox.draw(drawing, color)
        self.bbox.draw(drawing, color)

    def histout(self, filename):
        '''Output the histogram for plotting
        '''
        if self.hist is None:
            return
        fd = open(filename, 'w')
        for i in self.hist:
            fd.write("%d\n" % (i))
        fd.close()
