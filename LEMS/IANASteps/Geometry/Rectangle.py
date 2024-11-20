'''
Created on Oct 12, 2010

@author: surya
'''


class Rectangle:
    '''
    This class implements the base functionality for all image components
    that are rectangular.

    Using this class as the base class the inheritors will by default be able
    to crop/draw.
    '''

    def __init__(self, coordinates):
        ''' Constructor

        Initialized the rectangles coordinates

        Keyword Arguments:
        coordinates -- [topleftx, topLefty,
                        bottomRightx, bottomRighty] coordinate of a rectangle (list)
        '''

        self.coordinates = coordinates

    def __str__(self):
        ''' Returns a String representation for this class
        '''

        return 'Rectangle: {0},{1},{2},{3}'.format(self.coordinates[0],
                                                   self.coordinates[1],
                                                   self.coordinates[2],
                                                   self.coordinates[3])

    def draw(self, drawing, color):
        ''' Draws a rectangle on the given drawing

        Keyword Arguments:
        drawing -- An Image.Draw instance
        color   -- The color of the outline of the rectangle
        '''

        drawing.rectangle(self.coordinates, outline=color)

