'''
This Module contains all the constants for the SuryaImageAnalyzer

Created on Oct 8, 2010

@author: surya
'''
# TODO : Must be able to configure the constants through an admin interface
import IANASteps.Geometry


########################################################################
#              Linear card constants have "lin_" in front              #
########################################################################

########################################################################
#                      BCCCalculator  Constants                        #
########################################################################
class BCCCalculatorConstants:
    ##
    # Fitting parameters for leastSquaresFit
    FittingParameters = (-0.5, 200, -0.01)

    ##
    # Stopping limit for leastSquaresFit
    StoppingLimit = 0.00005

    ##
    # PI
    Pi = 3.1415926535897931

    @classmethod
    def str(cls):
        ''' Returns a String Representation of this class

        Returns:
        str - String representation of BCCCalculatorConstants
        '''
        return 'BCCCalculatorConstants: FittingParameters:{0}, StoppingLimit:{1}, Pi:{2}'.format(cls.FittingParameters,
                                                                                                 cls.StoppingLimit,
                                                                                                 cls.Pi)


########################################################################
#                        Image Resize Constants                        #
########################################################################
class ResizeImageConstants:
    ##
    # Resize the largest side to this new resolution
    LargestSide = [1024, 800]

    ##
    # Rotation constant
    RotateDegrees = 45


########################################################################
#                          BCFilter Constants                          #
########################################################################
class BCFilterConstants:
    ##
    # Resolution of the accumulator
    dp = 2

    ##
    # Minimum Radius of circles to detect
    minimumRadius = 0

    ##
    # Maximum Radius of circles to detect
    maximumRadius = 0

    ##
    # Minimum Distance between circles
    minimumDistance = 200

    ##
    # Accumulator Threshold to detect a circle
    accumulatorThreshold = 100

    ##
    # The edge detection threshold(the low threshold is half the high threshold by default)
    highThreshold = 100

    ##
    # The cvSmooth Mask Size
    masksize = 3

    @classmethod
    def str(cls):
        ''' Returns a String Representation of this class

        Returns:
        str - String representation of BCFilterConstants
        '''
        return 'BCFilterConstants dp:{0}, ' \
               'minimum distance:{1}, ' \
               'high threshold:{2}, ' \
               'accumulator threshold:{3}, ' \
               'minimum radius:{4}, ' \
               'maximum radius:{5}, ' \
               'masksize:{6}'.format(cls.dp,
                                     cls.minimumDistance,
                                     cls.highThreshold,
                                     cls.accumulatorThreshold,
                                     cls.minimumRadius,
                                     cls.maximumRadius,
                                     cls.masksize)


########################################################################
#                    BCFilterFixed Constants                           #
########################################################################
class BCFilterFixedConstants:
    # Linear version
    # Offset from QR to the linear
    down = 2.26
    left = -0.825

    # Offset from QR to the radial version
    rad_down = 0.8
    rad_left = -0.8

    ##
    # Radius scaling
    rscale = 0.25
    rad_rscale = 0.31

    @classmethod
    def str(cls):
        ''' Returns a String Representation of this class

        Returns:
        str - String representation of CalibratorConstants
        '''

        return 'StageDetectorConstants: left:{0}, ' \
               'down:{1}, ' \
               'rscale{2}'.format(cls.left,
                                  cls.down,
                                  cls.rscale)


########################################################################
#                      Calibrator Constants                            #
########################################################################
class CalibratorConstants:
    ##
    # Offset from QR to color calibrating stripes
    ColorOffset = .46

    ##
    # Separation between color calibrating stripes
    ColorSeparation = .21

    ##
    # Offset of each colorbar from the bottom of the QR code
    OffSum = ColorOffset + ColorSeparation
    ColorBarOffsets = []
    for i in range(3):
        ColorBarOffsets.append(OffSum * i)

    ##
    # Offset from qr to gray calibrating stripes
    # GrayOffset = .3 # MLL: changed to .32 on 2010-11-27 so it is centered a little better
    # GrayOffset = .32 # MLL: changed to .35 on 2012-05-16 so it is centered better
    GrayOffset = .37

    ##
    # Separation between gray calibrating stripes
    GraySeparation = .31

    ##
    # Offset of each column of GrayBars from the left of the QR Codes
    GrayBarColumnOffsets = []
    for i in range(3):
       GrayBarColumnOffsets.append(GrayOffset + GraySeparation * i)

    ##
    # Last Gray Bar offset
    # LastGrayBarOffset = 5.0/3.0 # MLL: changed to 21.0/12.0 so sample boxes are more in centers
    LastGrayBarOffset = 21.0 / 12.0

    ##
    # BoxSize representing GrayBars and ColorBars
    # BoxSize = 4 # MLL: changed to 6 on 2010-11-27 so we sample more points
    BoxSize = 6

    ##
    # BoxScale is how to choose the BoxSize based on the QR.width. Computed based on m = (8-4.)/(257.130317155 - 128.565158577)
    # (m,b) where BoxSize = m*QR.width + b
    BoxScale = (0.04111, 0.0)
    rad_BoxScale = (0.03, 0.0)
    rad_BoxScaleSmall = (0.015, 0.0)

    @classmethod
    def str(cls):
        ''' Returns a String Representation of this class

        Returns:
        str - String representation of CalibratorConstants
        '''

        return 'CalibratorConstants  ColorOffset:{0}, ' \
               'ColorSeparation:{1}, ' \
               'ColorBarOffsets:{2}, ' \
               'GrayOffset:{3}, ' \
               'GraySeparation:{4}, ' \
               'GrayBarColumnOffsets:{5}, ' \
               'LastGrayBarOffset:{6}, ' \
               'BoxSize:{7} '.format(cls.ColorOffset,
                                     cls.ColorSeparation,
                                     cls.ColorBarOffsets,
                                     cls.GrayOffset,
                                     cls.GraySeparation,
                                     cls.GrayBarColumnOffsets,
                                     cls.LastGrayBarOffset,
                                     cls.BoxSize)


########################################################################
#                   StageDetector Constants                            #
########################################################################
class StageDetectorConstants:
    # Stage Offset in terms of QR  (-1.5, 1.8, -0.15, 3.5)
    sleft = -1.5
    sright = 1.8
    stop = -0.15
    sbottom = 3.5

    # Enlarged
    sleftEnlarged = -1.6
    srightEnlarged = 1.9
    stopEnlarged = -0.25
    sbottomEnlarged = 3.6

    # Calibrator Offset in terms of QR (-1.5, 1.8, -0.15, 1.1)
    cleft = -1.5
    cright = 1.8
    ctop = -0.15
    cbottom = 1.1

    @classmethod
    def str(cls):
        ''' Returns a String Representation of this class

        Returns:
        str - String representation of CalibratorConstants
        '''

        return 'StageDetectorConstants: sleft:{0}, ' \
               'sright:{1}. ' \
               'stop:{2}. ' \
               'sbottom:{3}. ' \
               'cleft:{4}. ' \
               'cright:{5}. ' \
               'ctop:{6}. ' \
               'cbottom:{7}. '.format(cls.sleft,
                                      cls.sright,
                                      cls.ctop,
                                      cls.sbottom,
                                      cls.cleft,
                                      cls.cright,
                                      cls.ctop,
                                      cls.cbottom)


########################################################################
#                              EXITCODES                               #
########################################################################
class ExitCode:
    Success = 0
    UnknownError = 1
    FileNotExists = 2
    BCCComputationError = 3
    FilterDetectionError = 4
    GrayBarDetectionError = 5
    BlackBarDetectionError = 6
    ColorBarDetectionError = 7
    ImageTransformationError = 8
    QRDetectionError = 9
    StageDetectionError = 10
    CalibratorDetectionError = 11

    toString = {0: 'Success',
                1: 'UnknownError',
                2: 'FileNotExists',
                3: 'BCCComputationError',
                4: 'FilterDetectionError',
                5: 'GrayBarDetectionError',
                6: 'BlackBarDetectionError',
                7: 'ColorBarDetectionError',
                8: 'ImageTransformationError',
                9: 'QRDetectionError',
                10: 'StageDetectionError',
                11: 'CalibratorDetectionError'}


########################################################################
#                         MAIN CONSTANTS                               #
########################################################################
import os


class MainConstants:
    fontfile = IANASteps.Geometry.__path__[0] + '/arial.ttf'
    bandnames = ['red', 'green', 'blue']
    # samplingfactor = 10 # MLL: changed to 5 on 2010-11-27 so we have a larger sample area
    # samplingfactor = 5 # MLL: changed to 10 on 2011-01-17 so we have a smaller area to deal with EPA filters
    samplingfactor = 3.0
    # for the fixed BC detector
    samplingfactorfixed = 1.75
    radial_samplingfactorfixed = 3.0


#######################################################################################
#                         LIMIT CIRCLE REGION CONSTANTS                               #
#######################################################################################
# for image 823 wide and 1160 tall, left top boundary (x,y) = (226, 660) and right bottom boundary = (592, 1044), which is xlims = 27.46%, 71.93%, ylims = 56.90%, 90.00%
class LimitConstants:
    xloc = [0.2746, 0.7193]
    yloc = [0.569, 0.9]
