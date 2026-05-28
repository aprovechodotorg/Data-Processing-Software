import pyqtgraph as pg
from PyQt5.QtWidgets import QFrame
from PyQt5 import QtCore, QtGui, Qt

pg.setConfigOptions(antialias=True)

class QwtScaleEngine: pass
class QwtLogScaleEngine(QwtScaleEngine): pass
class QwtLinearScaleEngine(QwtScaleEngine): pass

class QwtPlot(pg.PlotWidget):
    yLeft = 0
    xBottom = 2
    RightLegend = 1  # Mock legend position if used

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setBackground('w')  # Match white canvas background
        self.getPlotItem().showGrid(x=True, y=True, alpha=0.15)
        # Custom styles for clean, modern look

    def setAxisScaleEngine(self, axisId, scaleEngine):
        is_log = isinstance(scaleEngine, QwtLogScaleEngine)
        if axisId == self.yLeft:
            self.getPlotItem().setLogMode(y=is_log)

    def setAxisScale(self, axisId, min_val, max_val):
        if axisId == self.xBottom:
            self.setXRange(min_val, max_val, padding=0)
        elif axisId == self.yLeft:
            self.setYRange(min_val, max_val, padding=0)

    def setAxisAutoScale(self, axisId):
        if axisId == self.yLeft:
            self.enableAutoRange(axis=pg.ViewBox.YAxis)
        elif axisId == self.xBottom:
            self.enableAutoRange(axis=pg.ViewBox.XAxis)

    def insertLegend(self, legend=None, position=None):
        self.addLegend()

    def setAxisTitle(self, axisId, title):
        if axisId == self.xBottom:
            self.setLabel('bottom', title)
        elif axisId == self.yLeft:
            self.setLabel('left', title)

    def setCanvasBackground(self, color):
        # Color can be a QColor, Qt brush, or Qt GlobalColor Enum
        if isinstance(color, QtCore.Qt.GlobalColor) or isinstance(color, int):
            self.setBackground(QtGui.QColor(color))
        else:
            self.setBackground(color)

    def replot(self):
        pass  # pyqtgraph replots automatically on data changes

class QwtLegend:
    pass

class QwtPlotCurve:
    def __init__(self, name=""):
        self.name = name
        self.plot = None
        self.pen = None
        self.x_data = []
        self.y_data = []
        self.item = None

    def setPen(self, pen):
        if isinstance(pen, QtGui.QPen):
            # Thick lines in pyqtgraph become wavy "ribbons" if not rounded and cosmetic
            pen.setCosmetic(True)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            pen.setCapStyle(QtCore.Qt.RoundCap)
        self.pen = pen
        if self.item:
            self.item.setPen(pen)

    def attach(self, plot):
        self.plot = plot
        if not self.item:
            # autoDownsample prevents massive path-stroking artifacts when zooming out on dense data
            self.item = pg.PlotDataItem(name=self.name, autoDownsample=True, downsampleMethod='subsample')
            if self.pen:
                self.item.setPen(self.pen)
        if self.item not in self.plot.listDataItems():
            self.plot.addItem(self.item)
        if len(self.x_data) > 0:
            self.item.setData(self.x_data, self.y_data)

    def setSamples(self, x, y):
        self.x_data = x
        self.y_data = y
        if self.item:
            self.item.setData(x, y)

    def detach(self):
        if self.plot and self.item:
            self.plot.removeItem(self.item)
