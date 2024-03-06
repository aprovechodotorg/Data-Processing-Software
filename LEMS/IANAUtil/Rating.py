'''
Created on Nov 11, 2010

@author: surya
'''

import matplotlib
matplotlib.use('Agg')
import pylab

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
    def expmod(offset, scale, powerscale, point):
        ''' This is the y = (a + b * e ^ (c * x)) function
        '''
        return offset + scale * pylab.exp(powerscale * point)