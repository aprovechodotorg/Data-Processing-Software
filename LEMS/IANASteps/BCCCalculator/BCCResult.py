'''
Created on Oct 12, 2010

@author: surya
'''


class BCCResult:
    ''' This class holds the reults of a BCC Computation
    '''

    def __init__(self):
        ''' Constructs the BCCResult object that holds various components
            of the BCC computation. namely:

            fitRed, fitGreen, fitBlue, rSquaredRed, rSquaredGreen, rSquaredBlue,
            sample, BCAreaRed, BCAreaGreen, BCAreaBlue, BCVolRed, BCVolGreen, BCVolBlue.

        '''

        self.fitRed = None
        self.fitGreen = None
        self.fitBlue = None
        self.rSquaredRed = None
        self.rSquaredGreen = None
        self.rSquaredBlue = None
        self.sample = None
        self.BCAreaRed = None
        self.BCAreaGreen = None
        self.BCAreaBlue = None
        self.BCVolRed = None
        self.BCVolGreen = None
        self.BCVolBlue = None

    def __str__(self):
        ''' Human readable representation

        Returns:
        str -- the string representation of the BCCResult
        '''

        return 'BCCResult: fitRed:{0}, ' \
               'fitGreen:{1}, ' \
               'fitBlue:{2}, ' \
               'rSquaredRed:{3}, ' \
               'rSquaredGreen:{4}, ' \
               'rSquaredBlue:{5}, ' \
               'sample:{6}, ' \
               'BCAreaRed:{7}, ' \
               'BCAreaGreen:{8}, ' \
               'BCAreaBlue:{9}, ' \
               'BCVolRed:{10}, ' \
               'BCVolGreen:{11}, ' \
               'BCVolBlue:{12}'.format(self.fitRed,
                                       self.fitGreen,
                                       self.fitBlue,
                                       self.rSquaredRed,
                                       self.rSquaredGreen,
                                       self.rSquaredBlue,
                                       self.sample,
                                       self.BCAreaRed,
                                       self.BCAreaGreen,
                                       self.BCAreaBlue,
                                       self.BCVolRed,
                                       self.BCVolGreen,
                                       self.BCVolBlue)