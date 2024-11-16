'''
Created on Oct 8, 2010

@author: surya
'''

import PIL.ImageStat as ImageStat

from IANASteps.Geometry.Circle import Circle


class BCFilter(Circle):
    """
    This class contains all functionality related to the Black Carbon Filter,
    namely sampling the filter. This class derives from the circle class and
    hence can be drawn using an Image.Draw instance and can be cropped.
    """

    def __init__(self, x, y, radius):
        """ Constructor

        Sets the logging level and the center and radius fields of this class

        Keyword arguments:
        x     -- Circle x coordinate
        y     -- Circle y coordinate
        radius-- Circle radius
        """

        Circle.__init__(self, x, y, radius)

    def __str__(self):
        """ Human readable representation

        Returns:
        str -- the center and radius of the circle
        """
        return 'BCFilter: {0}'.format(Circle.__str__(self))

    # TODO: all default values for params to be documented
    def sample(self, image, radius):
        """ Returns a sampling of the Circle

        Keyword arguments:
        image  -- Image instance
        radius -- Radius of the Area in which to sample

        Returns:
        mean value of pixels in the circle
        """
        offset = radius + 0.5 * radius, radius + 0.5 * radius

        topLeft = self.center - offset
        bottomRight = self.center + offset
        image = image.convert("RGB")
        image.load()
        filterSpot = image.crop((int(topLeft[0]), int(topLeft[1]), int(bottomRight[0]), int(bottomRight[1])))
        imageStats = ImageStat.Stat(filterSpot)

        return imageStats.mean
