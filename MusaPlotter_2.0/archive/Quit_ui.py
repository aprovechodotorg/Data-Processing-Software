# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Quit.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Quit(object):
    def setupUi(self, Quit):
        Quit.setObjectName(_fromUtf8("Quit"))
        Quit.resize(132, 49)
        self.label = QtGui.QLabel(Quit)
        self.label.setGeometry(QtCore.QRect(10, 0, 111, 41))
        self.label.setObjectName(_fromUtf8("label"))

        self.retranslateUi(Quit)
        QtCore.QMetaObject.connectSlotsByName(Quit)

    def retranslateUi(self, Quit):
        Quit.setWindowTitle(_translate("Quit", "X", None))
        self.label.setText(_translate("Quit", "Shutting Down.", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Quit = QtGui.QDialog()
    ui = Ui_Quit()
    ui.setupUi(Quit)
    Quit.show()
    sys.exit(app.exec_())

