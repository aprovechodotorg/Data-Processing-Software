# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Notes.ui'
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

class Ui_Notes(object):
    def setupUi(self, Notes):
        Notes.setObjectName(_fromUtf8("Notes"))
        Notes.resize(571, 188)
        self.buttonBox = QtGui.QDialogButtonBox(Notes)
        self.buttonBox.setGeometry(QtCore.QRect(110, 130, 131, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.textBrowser = QtGui.QTextBrowser(Notes)
        self.textBrowser.setGeometry(QtCore.QRect(20, 10, 541, 91))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))

        self.retranslateUi(Notes)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Notes.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Notes.reject)
        QtCore.QMetaObject.connectSlotsByName(Notes)

    def retranslateUi(self, Notes):
        Notes.setWindowTitle(_translate("Notes", "Set Values", None))
        self.buttonBox.setToolTip(_translate("Notes", "connect to port", None))
        self.textBrowser.setHtml(_translate("Notes", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">If header ID comes from machine as -1, Software will loop forever.</p></body></html>", None))

import pics_rc

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Notes = QtGui.QDialog()
    ui = Ui_Notes()
    ui.setupUi(Notes)
    Notes.show()
    sys.exit(app.exec_())

