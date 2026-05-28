# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CandD.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CandD(object):
    def setupUi(self, CandD):
        CandD.setObjectName("CandD")
        CandD.resize(490, 390)
        self.verticalLayoutWidget = QtWidgets.QWidget(CandD)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 10, 481, 371))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.verticalLayoutWidget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CandD)
        self.buttonBox.accepted.connect(CandD.accept)
        self.buttonBox.rejected.connect(CandD.reject)
        QtCore.QMetaObject.connectSlotsByName(CandD)

    def retranslateUi(self, CandD):
        _translate = QtCore.QCoreApplication.translate
        CandD.setWindowTitle(_translate("CandD", "Set Values"))
import pics_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CandD = QtWidgets.QDialog()
    ui = Ui_CandD()
    ui.setupUi(CandD)
    CandD.show()
    sys.exit(app.exec_())
