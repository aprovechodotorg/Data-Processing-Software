'''
Created on Nov 2, 2010

@author: surya
'''

import logging

from Logging.Logger import getLog
from IANASteps.BCCCalculator.BCCCalculator import rateFilter
from IANAUtil.Chart import plotChart


log = getLog('BCCResultComputation')


def bccResultComputation(sampledRGB, filterRadius, exposedTime, airFlowRate, bcGradient, gradient, chartFile):
    ''' This method gets invoked externally with the specified params and computes the BCVol,
        it also plots the chart.

    Keyword Arguments:
    sampledRGB   -- The sampled RGB values of the BCFilter
    filterRadius -- The radius of the filter in the image
    exposedTime  -- The time duration for which the filter was exposed.
    airFlowRate  -- The flowrate of the pump
    bcGradient   -- The gradient values to be used in the interpolation to ind the BCVol
    gradient     -- The gradient/grayscale list that is used in the interpolation
    chartFile    -- The name of the chartFile in which to store the plotted results
    parenttags   -- The tag string of the calling function
    level        -- The logging level

    Returns:
    BCCResult object containing the results of the Image Analysis.

    '''

    # Compute BCC
    bccResult = rateFilter(sampledRGB, bcGradient, gradient)

    plotChart(filterRadius, exposedTime, airFlowRate, bcGradient, gradient, bccResult, sampledRGB, chartFile)

    return bccResult