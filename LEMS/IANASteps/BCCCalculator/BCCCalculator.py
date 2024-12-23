'''
Created on Oct 12, 2010

@author: surya
'''

import matplotlib
import numpy

matplotlib.use('Agg')
import pylab
import logging


from IANASteps.BCCCalculator.BCCResult import BCCResult
# from Logging.Logger import getLog
from IANAUtil.Rating import Rating
#from Scientific.Functions.LeastSquares import leastSquaresFit
import scipy.optimize as optimization
from IANASettings.Settings import ExitCode, BCCCalculatorConstants
import numpy


# log = getLog("BCCCalculator")
# log.setLevel(logging.ERROR)


def computeBCC(bcFilterRadius, bcLoading, exposedTime, flowRate):
    ''' Computes the black carbon concentration(ug/cm^3) according to the formula

        BCC(ug/L) = (bcFilterArea(cm^2) * bcLoading(ug/cm^2)) / (exposedTime(min) * flowRate(L/min))

        NOTE : since cm^3 = L/1000

        BCC(ug/cm^3) = BCC(ug/L) * 1000

        Keyword arguments:
        bcFilterArea  -- The Radius of the filter in cm
        bcLoading     -- The black carbin loading value in ug/cm^2
        exposedTime   -- The exposure time of the bcfilter in mins
        flowRate      -- The flowrate of the pump in L/min

        Returns:
        Black Carbon Concentration(ug/cm^3)
    '''
    flowRate = float(flowRate)
    flowRateNEW = flowRate
    # We want the flowrate in L/m... so we know our pumps run at at least 200 cc/m... so
    # if we are a small number than the number is already in L/m
    if flowRate > 20:
        flowRateNEW = flowRate / 1000.

    area = BCCCalculatorConstants.Pi * (float(bcFilterRadius) / 10) ** 2  # cm^2

    bccalcs = {}
    bccalcs['concentration'] = (area * bcLoading * 1000) / (float(exposedTime) * flowRateNEW)

    bccalcs['weight'] = area * bcLoading  # cm^2 * ug/cm^2 = ug

    bccalcs['emissionrate'] = (area * bcLoading) / float(exposedTime)  # ug/min

    return bccalcs


def rateFilter(sampledRGB, bcgradient, gradient):
    ''' Computes the BCArea and BCVolume subject to the params

    Keyword arguments:
    sampledRGB  -- The sampled RGB values of the BCFilter
    exposedTime -- The duration for which the filter was exposed to air from the pump
    flowRate    -- The flow rate of the pump
    bcgradient  -- The calibration value obtained from the database
    gradient    -- The values corresponding to the color values from GrayBar objects
    parenttags  -- The tag string of the calling function
    level       -- The logging level

    Returns:
    BCCResult object
    '''
    fitParam = BCCCalculatorConstants.FittingParameters
    stop = BCCCalculatorConstants.StoppingLimit
    expmod = Rating.expmod
    expmod_og = Rating.expmod_og
    rsquared = Rating.rsquared

    # The results of this computation
    bccResult = BCCResult()

    # separate by color leaving off the black and white
    # gradientRed, gradientGreen, gradientBlue = zip(*gradient[1:-1])
    # separate by color, no black and white collected
    gradientRed, gradientGreen, gradientBlue = zip(*gradient)
    gradientRed = numpy.asarray(gradientRed)
    gradientRed = numpy.round(gradientRed)
    gradientRed = numpy.sort(gradientRed)
    gradientRed = gradientRed[::-1]
    print(gradientRed)
    # fit the gradient
    result_full = optimization.least_squares(expmod, fitParam, args=(gradientRed, bcgradient))
    bccResult.fitRed = result_full['x']
    #bccResult.fitGreen, chi = leastSquaresFit(expmod, fitParam, zip(gradientGreen, bcgradient), stopping_limit=stop)
    #bccResult.fitBlue, chi = leastSquaresFit(expmod, fitParam, zip(gradientBlue, bcgradient), stopping_limit=stop)

    # compute the rsquared value
    #eventually will want
    #bccResult.rSquaredRed = rsquared(expmod, bccResult.fitRed, pylab.array(gradientRed), bcgradient)
    #bccResult.rSquaredGreen = rsquared(expmod, bccResult.fitGreen, pylab.array(gradientGreen), bcgradient)
   #bccResult.rSquaredBlue = rsquared(expmod, bccResult.fitBlue, pylab.array(gradientBlue), bcgradient)

    red, green, blue = sampledRGB
    print(red)

    bccResult.BCAreaRed = expmod_og(bccResult.fitRed, red)
    #bccResult.BCAreaGreen = expmod(bccResult.fitGreen, green)
    #bccResult.BCAreaBlue = expmod(bccResult.fitBlue, blue)

    # log.info('Computing Black Carbon Concentration: ', extra=tags)
    # bccResult.BCVolRed   = computeBCC(filterRadius, bccResult.BCAreaRed, exposedTime ,flowRate)
    # bccResult.BCVolGreen = computeBCC(filterRadius, bccResult.BCAreaGreen, exposedTime, flowRate)
    # bccResult.BCVolBlue = computeBCC(filterRadius, bccResult.BCAreaBlue, exposedTime, flowRate)
    bccResult.BCVolRed = None
    #bccResult.BCVolGreen = None
    #bccResult.BCVolBlue = None

    return bccResult
