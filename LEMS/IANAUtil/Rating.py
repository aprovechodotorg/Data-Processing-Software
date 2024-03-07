'''
Created on Nov 11, 2010

@author: surya
'''

import matplotlib
matplotlib.use('Agg')
import pylab
import numpy

class Rating:
    @staticmethod
    def rsquared(fitfunc, param, x, y):
        ''' The R^2 value
        '''
        yhat = fitfunc(param, x)
        ymean = pylab.mean(y)
        ssreg = pylab.sum((yhat - ymean)**2)
        sstot = pylab.sum((y - ymean)**2)

        return (ssreg / sstot)**2

    @staticmethod
    def expmod_og(params, point):
        ''' This is the y = (a + b * e ^ (c * x)) function
        '''
        offset = params[0]
        scale = params[1]
        powerscale = params[2]
        return offset + scale * pylab.exp(powerscale * point)

    @staticmethod
    def expmod(params, point, output):
        ''' This is the y = (a + b * e ^ (c * x)) function
        '''
        offset, scale, powerscale = params
        power = powerscale * point
        return output - (offset + scale * numpy.exp(power))
