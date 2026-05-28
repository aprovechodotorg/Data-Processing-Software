# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'serialPort.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SerialPortDialog(object):
    def setupUi(self, SerialPortDialog):
        SerialPortDialog.setObjectName("SerialPortDialog")
        SerialPortDialog.resize(400, 202)
        self.buttonBox = QtWidgets.QDialogButtonBox(SerialPortDialog)
        self.buttonBox.setGeometry(QtCore.QRect(190, 150, 181, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.comboBox = QtWidgets.QComboBox(SerialPortDialog)
        self.comboBox.setGeometry(QtCore.QRect(60, 80, 201, 27))
        self.comboBox.setEditable(True)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.label = QtWidgets.QLabel(SerialPortDialog)
        self.label.setGeometry(QtCore.QRect(70, 26, 241, 41))
        self.label.setObjectName("label")

        self.retranslateUi(SerialPortDialog)
        self.buttonBox.accepted.connect(SerialPortDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(SerialPortDialog)

    def retranslateUi(self, SerialPortDialog):
        _translate = QtCore.QCoreApplication.translate
        SerialPortDialog.setWindowTitle(_translate("SerialPortDialog", "Dialog"))
        self.buttonBox.setToolTip(_translate("SerialPortDialog", "connect to port"))
        self.comboBox.setToolTip(_translate("SerialPortDialog", "port name, select or enter"))
        
        self.comboBox.clear()
        try:
            import serial.tools.list_ports
            active_ports = [p.device for p in serial.tools.list_ports.comports()]
            if not active_ports:
                self.comboBox.addItem("/dev/ttyUSB0")
                self.comboBox.addItem("COM1")
            else:
                for port in active_ports:
                    self.comboBox.addItem(port)
        except Exception:
            self.comboBox.addItem("/dev/ttyUSB0")
            self.comboBox.addItem("COM1")
            
        self.label.setText(_translate("SerialPortDialog", "Choose serial port:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SerialPortDialog = QtWidgets.QDialog()
    ui = Ui_SerialPortDialog()
    ui.setupUi(SerialPortDialog)
    SerialPortDialog.show()
    sys.exit(app.exec_())
