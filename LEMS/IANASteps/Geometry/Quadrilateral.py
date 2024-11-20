'''
Created on Oct 21, 2010

@author: surya
'''


class Quadrilateral:
    '''
    This class implements the base functionality for all image components
    that are quadrilaterals.

    Using this class as the base class the inheritors will by default be able
    to crop/draw.
    '''

    def __init__(self, topLeft, bottomLeft, bottomRight, topRight):
        ''' Constructor

        Sets the logging level and the topLeft, bottomLeft, bottomRight, topRight
        fields of this class

        Keyword Arguments:
        topLeft     -- topLeft coordinate of the Stage(the absolute topLeft)
        bottomLeft  -- bottomLeft coordinate of the Stage(the absolute bottomLeft)
        bottomRight -- bottomRight coordinate of the Stage(the absolute bottomRight)
        topRight    -- topRight coordinate of the Stage(the absolute topRight)
        '''

        self.topLeft = topLeft
        self.bottomLeft = bottomLeft
        self.topRight = topRight
        self.bottomRight = bottomRight

    def __str__(self):
        ''' Human readable representation

        Returns:
        str -- all the information regarding the Quadrilateral
        '''

        return '{{topLeft:{0}, bottomLeft:{1}, topRight:{2}, bottomRight:{3}}}'.format(self.topLeft,
                                                                                       self.bottomLeft,
                                                                                       self.topRight,
                                                                                       self.bottomRight)

    def draw(self, drawing, color):
        """ Draws the draw of the Stage on the specified drawing

        Keyword arguments:
        drawing -- Image.Draw instance
        color   -- Color to draw the draw in
        """

        # TOP: RED
        drawing.line(tuple(self.topLeft) + tuple(self.topRight), fill='red')
        # RIGHT: YELLOW
        drawing.line(tuple(self.topRight) + tuple(self.bottomRight), fill='yellow')
        # BOTTOM: CYAN
        drawing.line(tuple(self.bottomRight) + tuple(self.bottomLeft), fill='cyan')
        # LEFT: MAGENTA
        drawing.line(tuple(self.bottomLeft) + tuple(self.topLeft), fill='magenta')

    def crop(self, image):
        """ Creates a cropped copy of the image using the bounds of the filter

        Keyword arguments:
        image -- Image instance

        Returns:
        Cropped Image
        """
        return image.crop((int(self.topLeft[0]), int(self.topLeft[1])),
                          (int(self.bottomRight[0]), int(self.bottomRight[1])))