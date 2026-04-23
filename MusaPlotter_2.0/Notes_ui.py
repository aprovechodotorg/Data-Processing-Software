# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Notes.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Notes(object):
    def setupUi(self, Notes):
        Notes.setObjectName("Notes")
        Notes.resize(571, 188)
        self.buttonBox = QtWidgets.QDialogButtonBox(Notes)
        self.buttonBox.setGeometry(QtCore.QRect(110, 130, 131, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.textBrowser = QtWidgets.QTextBrowser(Notes)
        self.textBrowser.setGeometry(QtCore.QRect(20, 10, 541, 91))
        self.textBrowser.setObjectName("textBrowser")

        self.retranslateUi(Notes)
        self.buttonBox.accepted.connect(Notes.accept)
        self.buttonBox.rejected.connect(Notes.reject)
        QtCore.QMetaObject.connectSlotsByName(Notes)

    def retranslateUi(self, Notes):
        _translate = QtCore.QCoreApplication.translate
        Notes.setWindowTitle(_translate("Notes", "Set Values"))
        self.buttonBox.setToolTip(_translate("Notes", "connect to port"))
        self.textBrowser.setHtml(_translate("Notes", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">If header ID comes from machine as -1, Software will loop forever.</p></body></html>"))
import pics_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Notes = QtWidgets.QDialog()
    ui = Ui_Notes()
    ui.setupUi(Notes)
    Notes.show()
    sys.exit(app.exec_())
