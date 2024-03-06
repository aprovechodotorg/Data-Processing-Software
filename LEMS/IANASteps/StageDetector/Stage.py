'''
Created on Oct 10, 2010

@author: surya
'''

from IANASteps.Geometry.Quadrilateral import Quadrilateral


class Stage(Quadrilateral):
    """
    Represents the Stage. This class contains all the information
    and functionality regarding the Stage.
    """

    # TODO: need a unit testing run where i can test all the components

    def __init__(self, topLeft, bottomLeft, bottomRight, topRight):
        """ Constructor

        Sets the logging level and the topLeft, bottomLeft, bottomRight, topRight
        fields of this class

        Keyword Arguments:
        topLeft     -- topLeft coordinate of the Stage(the absolute topLeft)
        bottomLeft  -- bottomLeft coordinate of the Stage(the absolute bottomLeft)
        bottomRight -- bottomRight coordinate of the Stage(the absolute bottomRight)
        topRight    -- topRight coordinate of the Stage(the absolute topRight)
        """

        Quadrilateral.__init__(self, topLeft, bottomLeft, bottomRight, topRight)

    def __str__(self):
        """ Human readable representation

        Returns:
        str -- all the information regarding the Stage
        """

        return 'Stage: {0}'.format(Quadrilateral.__str__(self))
