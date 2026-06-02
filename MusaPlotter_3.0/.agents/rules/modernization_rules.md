# Rule: Modernization Standards
**Activation Mode**: Always On
**Scope**: Workspace-wide

---

## Coding Standards & Code Quality
- **Python Version:** All code must be compatible with Python 3.8+ (including Python 3.10 and 3.11). Avoid Python 2 constructs entirely.
- **Library Modernization:** 
  - Do not use `PyQt4` or older versions of PySide.
  - Standardize on `PyQt5`.
  - Replace PyQwt (`PyQt5.Qwt`) using the `pyqtgraph`-based shim in `qwt_plot.py`. Do not try to compile or install PyQwt binaries on modern systems.
- **Type Conversions:** Ensure explicit type casting when reading inputs (e.g. casting GUI numeric spinboxes/lineEdits to floats or ints).
- **String Formatting:** Prefer f-strings (`f"Value: {val}"`) or standard `.format()` over legacy `%` formatting.

## GUI Development Rules
- **Thread Separation:** The GUI thread must never execute blocking operations (e.g. `serial.readline()`, `time.sleep()`, heavy system commands). All such work must reside in worker threads.
- **Signal-Slot Connections:** Use modern PyQt5 signal connection syntax (e.g. `button.clicked.connect(self.handler)`) instead of legacy style (`QtCore.QObject.connect(button, QtCore.SIGNAL('clicked()'), handler)`).
- **Dynamic Port Population:** The serial port selection dialog must query available serial ports on startup via `serial.tools.list_ports.comports()` rather than showing a hardcoded static list.
