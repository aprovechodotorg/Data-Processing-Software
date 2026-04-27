# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Nozzle.ui'
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

class Ui_Nozzle(object):
    def setupUi(self, Nozzle):
        Nozzle.setObjectName(_fromUtf8("Nozzle"))
        Nozzle.resize(457, 188)
        self.label = QtGui.QLabel(Nozzle)
        self.label.setGeometry(QtCore.QRect(10, 0, 131, 41))
        self.label.setObjectName(_fromUtf8("label"))
        self.doubleSpinBox = QtGui.QDoubleSpinBox(Nozzle)
        self.doubleSpinBox.setGeometry(QtCore.QRect(30, 50, 101, 27))
        self.doubleSpinBox.setObjectName(_fromUtf8("doubleSpinBox"))
        self.buttonBox = QtGui.QDialogButtonBox(Nozzle)
        self.buttonBox.setGeometry(QtCore.QRect(160, 130, 131, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.textBrowser = QtGui.QTextBrowser(Nozzle)
        self.textBrowser.setGeometry(QtCore.QRect(210, 10, 211, 81))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))

        self.retranslateUi(Nozzle)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Nozzle.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Nozzle.reject)
        QtCore.QMetaObject.connectSlotsByName(Nozzle)

    def retranslateUi(self, Nozzle):
        Nozzle.setWindowTitle(_translate("Nozzle", "Set Values", None))
        self.label.setText(_translate("Nozzle", "Enter Nozzle Size:", None))
        self.buttonBox.setToolTip(_translate("Nozzle", "connect to port", None))
        self.textBrowser.setHtml(_translate("Nozzle", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><img src=\":/images(1).jpg\" /></p></body></html>", None))

import pics_rc

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Nozzle = QtGui.QDialog()
    ui = Ui_Nozzle()
    ui.setupUi(Nozzle)
    Nozzle.show()
    sys.exit(app.exec_())

