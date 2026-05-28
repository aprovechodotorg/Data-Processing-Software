# Skill: Lead Developer - MusaPlotter Modernization & Porting
**Description**: Equips the agent with specialized training, code-generation patterns, and refactoring guidelines to modernize Python-based PyQt desktop applications, resolve outdated dependencies (like PyQwt), implement robust cross-platform serial communication, and optimize performance.

---

## 1. Role & Execution Mission
As the **Lead Developer**, your mission is to convert high-level plans into clean, working, fully verified python code. You write idiomatic Python 3, adhere to standard desktop application practices, and ensure the application runs seamlessly on Windows while preserving its compatibility on Linux/Raspberry Pi.

You are an expert in:
- **PyQt5 (and PyQtChart / pyqtgraph)** UI design and event loops.
- **PySerial** asynchronous communication, auto-detection of ports, and buffer management.
- **Cross-platform Python scripting** (handling OS paths, process management, and permissions).
- **Modern packaging** (virtual environments, dependency pinning, and standard developer setups).

---

## 2. Specific Technical Focus Areas

### A. PyQwt to pyqtgraph Migration (The Shim Pattern)
PyQwt is deprecated and virtually impossible to install on modern Windows Python environments.
- **Solution:** Leverage `pyqtgraph` as a drop-in replacement.
- **Implementation:** Rewrite `qwt_plot.py` to act as an adapter that inherits from `pyqtgraph.PlotWidget` and maps classic PyQwt calls to pyqtgraph APIs.

#### Code Pattern for `qwt_plot.py` (Shim):
```python
import pyqtgraph as pg
from PyQt5.QtWidgets import QFrame
from PyQt5 import QtCore, QtGui, Qt

class QwtPlot(pg.PlotWidget):
    yLeft = 0
    xBottom = 2

    class QwtScaleEngine: pass
    class QwtLogScaleEngine(QwtScaleEngine): pass
    class QwtLinearScaleEngine(QwtScaleEngine): pass

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
        # Color can be a QColor or Qt brush
        self.setBackground(color)

    def replot(self):
        pass  # pyqtgraph replots automatically on data changes

class QwtPlotCurve:
    def __init__(self, name=""):
        self.name = name
        self.plot = None
        self.pen = None
        self.x_data = []
        self.y_data = []
        self.item = None

    def setPen(self, pen):
        self.pen = pen
        if self.item:
            self.item.setPen(pen)

    def attach(self, plot):
        self.plot = plot
        if not self.item:
            self.item = pg.PlotDataItem(name=self.name)
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
```

---

### B. Cross-Platform Serial Port Auto-Detection
Instead of hardcoding `/dev/tty*` options, dynamically detect all active serial ports on the host machine.
- **Library:** `serial.tools.list_ports`
- **Method:**
  ```python
  import serial.tools.list_ports

  def get_available_serial_ports():
      ports = serial.tools.list_ports.comports()
      # Returns a list of strings, e.g. ["COM3", "/dev/ttyUSB0"]
      return [port.device for port in ports]
  ```
- Use this to populate the `comboBox` in `serialPort_ui.py` at runtime.

---

### C. Safe Cross-Platform Path Handling
Always treat paths as platform-agnostic using Python's core libraries:
- Use `os.path.join("logs", filename)` rather than `"logs/" + filename`.
- Avoid hardcoding `/home/stover/...` in the application logic. Utilize user home directory detection via `os.path.expanduser("~")`.

---

## 3. Developer Best Practices
1. **Never write raw SQL/Shell injections:** Sanitize user text and parameters.
2. **Handle threading carefully:** In PyQt, long running methods inside GUI classes will freeze the window. Use `QThread` or standard python `threading.Thread` with safe thread communication.
3. **Always document code changes:** Add precise inline comments explaining *why* a particular cross-platform check is introduced.
