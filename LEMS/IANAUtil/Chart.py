'''
Created on Oct 12, 2010

@author: surya
'''

import matplotlib
# matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import scipy
#import StringIO

# matplotlib.rc('text', usetex=True)

from IANAUtil.Rating import Rating


def plotChart(bcgradient, gradient, bccResult, sampledRGB, chartName):
    # plotChart(filterRadius, exposedTime, flowRate, bcgradient, gradient, bccResult, sampledRGB, chartName):
    ''' Plot the results onto a Chart
    '''

    BCGradient = scipy.array(bcgradient)

    # gradientRed, gradientGreen, gradientBlue = zip(*gradient[1:-1])
    gradientRed, gradientGreen, gradientBlue = zip(*gradient)
    redSample, greenSample, blueSample = sampledRGB

    fig = Figure()  # Figure(figsize=(6.4, 4.8), dpi=100) # should be
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    # plot the RGB vals of the test strip
    ax.plot(gradientRed, BCGradient, 'rx',
            gradientGreen, BCGradient, 'gx',
            gradientBlue, BCGradient, 'bx')

    plotrange = scipy.array(range(50, 252))

    # plot the lines fit to the RGB vals of the test strip
    ax.plot(plotrange, Rating.expmod(bccResult.fitRed, plotrange), 'r-',
            plotrange, Rating.expmod(bccResult.fitGreen, plotrange), 'g-',
            plotrange, Rating.expmod(bccResult.fitBlue, plotrange), 'b-')

    # plot the sample point
    red, green, blue = sampledRGB
    ax.plot(red, -1, 'rs', green, -1, 'gs', blue, -1, 'bs')

    ax.plot(redSample, bccResult.BCAreaRed, 'ks', greenSample, bccResult.BCAreaGreen, 'ks',
            blueSample, bccResult.BCAreaBlue, 'ks')

    # legend with the r^2 values
    rsqr = "$r^2$" + (' = %0.3f (R),') % bccResult.rSquaredRed + (' %0.3f (G),') % bccResult.rSquaredGreen + (
        ' %0.3f (B)') % bccResult.rSquaredBlue
    ax.set_xlabel('R,G,B pixel value (0-255)')
    ax.set_xlim([0, 255])
    ax.set_ylim([-2, 28])
    ax.set_ylabel('$\mathrm{\mu g/cm^2}$')

    bcstrip_float = [float(s.strip()) for s in
                     str(BCGradient).strip()[1:-1].split()]  # the str(BCBCGradient) is "[ x.xx ... ]"
    bcstrip_short = ""
    for f in bcstrip_float:
        bcstrip_short += "{val:0.2f} ".format(val=f)

    ax.set_title('BCStrip: ' + str(bcstrip_short) + '\n' + str(rsqr))

    message = '$y = y_0 + a*e^{bR}$ \n$y_0$ = %0.4f \n$a$ = %0.4f \n$b$ = %0.4f' % (
    bccResult.fitRed[0], bccResult.fitRed[1], bccResult.fitRed[2])
    ax.text(200, 21, message)

    newChart = StringIO.StringIO()
    canvas.print_png(newChart)
    newChart.seek(0)
    return newChart
    # Note make sure file represented by 'chartName' is closed later