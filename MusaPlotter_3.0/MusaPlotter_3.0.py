#!/usr/bin/env python3
#    MusaPlotter_2.1: Linux serial port software for musa sensor platform
#    Displays, plots, and logs serial data stream. Push button calibration, Time set function
#    v2.1 change: User-selectable color palette per channel. A small colored square button
#                 next to each channel row opens a QColorDialog. The chosen color is applied
#                 immediately to the live plot curve and the built-in Qwt right-side legend.
#                 Colors persist across plot resets (e.g. when the DAQ header is re-read).
#
#    Copyright (C) 2022  Mountain Air Engineering 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#    
#    Contact: ryan@mtnaireng.com

import queue
import threading 
import time
import sys
import serial
import serial.tools.list_ports
import os
import re
import subprocess
from tempfile import mkstemp
from shutil import move
from os import remove, close
from collections import defaultdict

from PyQt5 import QtGui, QtCore,uic,QtWidgets
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QDialog, QActionGroup, QColorDialog
from PyQt5.QtCore import QSettings
from PyQt5 import Qt
import qwt_plot as Qwt

#for plot reduction :
#from rdp import rdp


# ═════════════════════════════════════════════════════════════════════════════
#  DERIVED CHANNELS
#  Calculated values that are computed from live sensor data and displayed
#  as extra channels alongside the real ones.  They appear in the channel
#  panel with their own reading box, show/hide checkbox, scale spinbox, and
#  colour button, exactly like a hardware channel.  They are intentionally
#  excluded from calibration and are NOT written to the raw CSV log (the raw
#  log stays unmodified so existing post-processing tools keep working).
#
#  HOW TO ADD A CHANNEL
#  ────────────────────
#  Append a tuple to the list below:
#
#      ("DisplayName", formula_function)
#
#  The formula function receives one argument – a dict called `ch` – that
#  maps every *real* channel name (as it appears in headerlist.txt) to its
#  current float value, e.g. ch["CO"], ch["GasFlow"], ch["PM"].
#
#  The function must return:
#    • a float  – the value shown and plotted
#    • None     – leaves the reading box blank for that sample (use this
#                 when a required input is missing or out of range)
#
#  Tips
#  ────
#  • Use ch.get("ChannelName", 0.0) instead of ch["ChannelName"] so the
#    formula degrades gracefully when a channel is absent in a given sensor
#    box configuration rather than raising a KeyError.
#  • Guard denominators:  "if ch.get("Flow",0) > 0 else None"
#  • Channel names must match exactly what is in headerlist.txt (case-sensitive).
#  • Add as many entries as you like; order determines the panel row order.

# ═════════════════════════════════════════════════════════════════════════════

# K_TUNNEL converts the square root of your differential pressure (mmH2O)
# into Standard Volumetric Flow (Liters per second).
# You will need to calculate this based on your tunnel diameter and pitot calibration.
K_TUNNEL = 100.0  # <--- REPLACE THIS with your actual flow calibration factor

DERIVED_CHANNELS = [
    ("Firepower_kW",
     lambda ch: (
         # 1. Convert mmH2O to Liters per sec (using abs() for negative dP readings)
             (K_TUNNEL * (abs(ch.get("Flow", 0)) ** 0.5))

             # 2. Multiply by total carbon concentration (CO2 + CO in ppm converted to fraction)
             # max(0, ...) is used because your CO drifts slightly negative (e.g. -5.72)
             * ((max(0, ch.get("CO2", 0)) + max(0, ch.get("CO", 0))) / 1e6)

             # 3. ISO 19867 standard conversion factor (L/s of C to kW)
             * 19.825

     ) if abs(ch.get("Flow", 0)) > 0 else 0
     ),
]


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

#import dialogs:
from MainWindow_ui import Ui_MainWindow
from serialPort_ui import Ui_SerialPortDialog
from Notes_ui import Ui_Notes
from CandD_ui import Ui_CandD

#for making different color text in terminal
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''



    
        
class SubDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self) 
        self.CandD_ui = Ui_CandD()
        self.CandD_ui.setupUi(self)
        
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        header1 = QtWidgets.QLabel()
        header1.setText("Name")
        header1.setFont(font)
        self.CandD_ui.gridLayout_2.addWidget(header1,0,0,1, 1, QtCore.Qt.AlignLeft )
        header2 = QtWidgets.QLabel()
        header2.setText("Value")
        header2.setFont(font)
        self.CandD_ui.gridLayout_2.addWidget(header2,0,1,1, 1, QtCore.Qt.AlignLeft )
        header3 = QtWidgets.QLabel()
        header3.setText("New Value")
        header3.setFont(font)
        self.CandD_ui.gridLayout_2.addWidget(header3,0,2,1, 1, QtCore.Qt.AlignLeft )
        header4 = QtWidgets.QLabel()
        header4.setText("Update")
        header4.setFont(font)
        self.CandD_ui.gridLayout_2.addWidget(header4,0,3,1, 1, QtCore.Qt.AlignLeft )
        

        #header1.setGeometry(QtCore.QRect(20, 0, 66, 21))

        
    def addRows(self, paralist):
        self.paraName = {} #label
        self.paraVal = {} #label
        self.paraNewVal = {} # spinbox
        self.paraUpdate = {} #checkbox
        print("len paralist", len(paralist))
        for i in range(len(paralist)):
            self.paraName[i] = QtWidgets.QLabel()
            self.paraName[i].setText(paralist[i][0])
            self.paraName[i].setObjectName(_fromUtf8("name"+str(i)))
            self.CandD_ui.gridLayout_2.addWidget(self.paraName[i],i+1,0,1, 1, QtCore.Qt.AlignLeft )

            self.paraVal[i] = QtWidgets.QLabel()
            self.paraVal[i].setText(paralist[i][1])
            self.paraVal[i].setObjectName(_fromUtf8("val"+str(i)))
            self.CandD_ui.gridLayout_2.addWidget(self.paraVal[i],i+1,1,1, 1, QtCore.Qt.AlignLeft )
            
            self.paraNewVal[i] = QtWidgets.QDoubleSpinBox(self)
            self.paraNewVal[i].setObjectName(_fromUtf8("newVal"+str(i)))
            self.paraNewVal[i].setValue(1.000)
            self.paraNewVal[i].setRange(0.00001, 1000000)
            self.paraNewVal[i].setMinimum(0.001)
            self.paraNewVal[i].setDecimals(3)
            self.paraNewVal[i].setSingleStep(.1)
            self.CandD_ui.gridLayout_2.addWidget(self.paraNewVal[i],i+1,2,1, 1, QtCore.Qt.AlignLeft )
            
            self.paraUpdate[i] = QtWidgets.QCheckBox(self)
            self.paraUpdate[i].setObjectName(_fromUtf8("checkBox"+str(i)))
            self.paraUpdate[i].setChecked(False) 
            self.paraUpdate[i].setMinimumHeight(25)
            self.CandD_ui.gridLayout_2.addWidget(self.paraUpdate[i],i+1,3,1, 1, QtCore.Qt.AlignCenter)

        self.spacer = QtWidgets.QSpacerItem( 20, 40 , QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.CandD_ui.gridLayout_2.addItem(self.spacer,1000,1)
        return  self.paraName,self.paraVal,self.paraNewVal,self.paraUpdate,
        


#class to run main window:
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, nameList, serialComClient):
        QDialog.__init__(self)# Constructs a dialog with parent parent. self being 
        
        self.nameList = nameList
        self.serialComClient = serialComClient
        
        self.plotRunning = False
        self.trimmed = False#flag for trimmed first plot numbers
        # QSettings for cross-restart persistence (Windows registry / INI on Linux)
        self.settings = QSettings("MtnAirEng", "MusaPlotter")
        # channelColors stores user-chosen QColor per channel index.
        # Load any previously saved colors so they survive restarts.
        self.channelColors = {}
        for key in self.settings.allKeys():
            if key.startswith("color_"):
                try:
                    idx = int(key[6:])
                    self.channelColors[idx] = Qt.QColor(self.settings.value(key))
                except Exception:
                    pass
        # Set up the UI from Designer:
        self.ui = Ui_MainWindow()
        #uic.loadUi('MainWindow.ui', self)#gets all the UI stuff created by qtdesigner
        self.ui.setupUi(self)
        #add channels:
        self.addChanBoxes(nameList)
        #connect signals:
        ###QtCore.QObject.connect(self.ui.pushButton_cal, QtCore.SIGNAL('clicked()'), lambda: self.Calibrate(serialComClient))
        self.ui.pushButton_cal.clicked.connect(lambda dummy: self.Calibrate(serialComClient))
        self.ui.actionNon_Cal_Mode.triggered.connect(self.hideCal)
        self.ui.actionCal_Mode.triggered.connect(self.showCal)
        
        self.ui.checkBox_logY.toggled.connect(self.change_Y_axis_loglin)
        self.ui.checkBox.toggled.connect(self.setPlotRanges)
        self.ui.checkBox_2.toggled.connect(self.setPlotRanges)
        self.ui.checkBox_3.toggled.connect(self.setPlotRanges)
        
        #QtCore.QObject.connect(self.ui.actionSet_time, QtCore.SIGNAL('triggered()'), lambda: self.setTime(serialComClient))
        self.ui.actionSet_time.triggered.connect(lambda dummy: self.setTime(serialComClient))
        #QtCore.QObject.connect(self.ui.actionNotes, QtCore.SIGNAL('triggered()'), lambda: self.Notes())
        self.ui.actionNotes.triggered.connect(lambda: self.Notes())
        #QtCore.QObject.connect(self.ui.actionSet_Other_Parameters, QtCore.SIGNAL('triggered()'), lambda: self.CandD(serialComClient))
        self.ui.actionSet_Other_Parameters.triggered.connect(lambda dummy: self.CandD(serialComClient))
        viewGroup = QActionGroup(self.ui.menuView) #is named in _ui.py
        viewGroup.addAction(self.ui.actionCal_Mode)
        viewGroup.addAction(self.ui.actionNon_Cal_Mode)
        
        self.ui.actionTerminal_Mode.triggered.connect(self.terminalToggle)
        self.hideCal() #non cal mode to start
        self.terminalToggle() #needs to be here to set one way or other
        self.ui.plainTextEdit.installEventFilter(self) #install event filter for terminal entry box
        self.cursor = QTextCursor(self.ui.plainTextEdit.document())
    
    def closeEvent(self, event):
        self.serialComClient.queueSend.put("**CLOSE**")
        print("shuting down")
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
        self.ui.textBrowser.setPalette(palette)
        self.ui.textBrowser_2.setPalette(palette)
        font = QtGui.QFont("Times", 15, QtGui.QFont.Bold)
        self.ui.textBrowser.setFont(font)
        self.ui.textBrowser_2.setFont(font)
        self.ui.textBrowser.setText("Shutting Down...")
        self.ui.textBrowser_2.setText("Shutting Down...")

        self.serialComClient.endApplication()
        QApplication.processEvents()
        time.sleep(1.5)
        event.accept()

        
    
    
    def eventFilter(self, source, event): #for terminal manual entry box
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Return:
                self.cursor.select(QTextCursor.LineUnderCursor) # selectscurrent line
                text = self.cursor.selectedText()
                print(text)
                #text = str(text).strip("     =>sent")
                #cursor.movePosition(QTextCursor.End)
                self.cursor.insertText(text+"     =>sent")
                if self.ui.radioButton_2.isChecked():
                    text = "**SEND**"+text+"\r"
                elif self.ui.radioButton_3.isChecked():
                    text = "**SEND**"+text+"\r\n"
                else:
                    text = "**SEND**"+text+"\n"
                      
                self.serialComClient.queueSend.put(str(text))
                
                ##% check checkboxes/radio buttons for /r/n or /n here
                #self.serialComClient.queueSend.put(text+"\r\n")
                """
                if msg[:8] ==  "**SEND**" and self.ser_portOpened == True:
                        self.ser.write(msg[8:]) 
                """              
                
            if key == QtCore.Qt.Key_Up: #prevents up arrowing
                self.cursor.movePosition(QTextCursor.End)
                print("no up")

        else:
            pass # do other stuff

        return QtWidgets.QMainWindow.eventFilter(self, source, event)
            

    def change_Y_axis_loglin(self):
        if  self.ui.checkBox_logY.isChecked() :
            #self.ui.qwtPlot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())
            self.ui.qwtPlot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLogScaleEngine())
            ##% qwtlog->autoScale(<maxNumSteps>, 0, 20000, <stepSize>)
        else:
            #self.ui.qwtPlot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.scale_engine.QwtLinearScaleEngine())
            self.ui.qwtPlot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLinearScaleEngine())
           
        self.ui.qwtPlot.replot()
    
    
    def setTime(self,serialComClient):
        self.ui.actionTerminal_Mode.setChecked(True) #terminal
        self.terminalToggle()
        self.ui.textBrowser.setText("Setting Time...")
        self.ui.textBrowser_2.setText("Setting Time...")        
        print ("starting time set")
        utctime = time.time()
        delay = 5 #time required for firmware to update time
        utctime = utctime+delay #add delay
        timestamp = str(time.strftime("%Y%m%d %H:%M:%S",time.localtime(utctime)))

        #send message here with **TIME**:YYYYMMDD HH:MM:SS

        dateMsg = "**TIME**:"+ timestamp

        serialComClient.queueSend.put(dateMsg)
        serialComClient.calHappening = True
        # send command to thread to set time
        
    def toggleCheck(self,boxName,boxNameOther, num):
        if boxNameOther[num].isChecked():
            boxNameOther[num].blockSignals(True) 
            boxNameOther[num].setChecked(False)
            print("unchecking") 
            boxNameOther[num].blockSignals(False)
   
    def terminalToggle(self):
        if self.ui.actionTerminal_Mode.isChecked(): #terminal
            self.ui.qwtPlot.hide()
            self.ui.textBrowser.hide()
            self.ui.textBrowser_2.show()
            self.ui.plainTextEdit.show()
            self.ui.radioButton.show()
            self.ui.radioButton_2.show()
            self.ui.radioButton_3.show()
            
            self.ui.checkBox_2.hide()
            self.ui.checkBox_3.hide()
            self.ui.checkBox_logY.hide()
            self.ui.checkBox.hide()
            self.ui.spinBox.hide()
            self.ui.spinBox_2.hide()
            self.ui.spinBox_3.hide()
            self.ui.spinBox_4.hide()
            self.ui.spinBox_5.hide()
            
            sbar = self.ui.textBrowser_2.verticalScrollBar()
            sbar.setValue(sbar.maximum())
            
        else:
            self.ui.textBrowser_2.hide()#plot
            self.ui.qwtPlot.show()
            self.ui.plainTextEdit.hide()
            self.ui.textBrowser.show()
            self.ui.radioButton.hide()
            self.ui.radioButton_2.hide()
            self.ui.radioButton_3.hide()
            
            self.ui.checkBox_2.show()
            self.ui.checkBox_3.show()
            self.ui.checkBox_logY.show()
            self.ui.checkBox.show()
            self.ui.spinBox.show()
            self.ui.spinBox_2.show()
            self.ui.spinBox_3.show()
            self.ui.spinBox_4.show()
            self.ui.spinBox_5.show()
        
    def hideCal(self):
        self.ui.label_5.hide()
        self.ui.label_6.hide()
        self.ui.label_7.hide()
        #print "hidecal, number of channels in grid:", self.ui.gridLayout_2.count()
        if (self.ui.gridLayout_2.count() <2):  return
        for i in (list(range(self.ui.gridLayout_2.count()))):
        #for i in range(len(self.nameList)):
            try:
                self.spanBoxes[i].hide()
                self.zeroBoxes[i].hide()
                self.refBoxes[i].hide()
            except: pass
        QtWidgets.QApplication.processEvents()
        req_width = self.ui.gridLayoutWidget_2.minimumSizeHint().width()
        # Fallback in case of weird Qt states
        if req_width < 250: req_width = 250
        
        old_min_width = self.ui.scrollArea.minimumWidth()
        new_min_width = req_width + 30
        
        self.ui.gridLayoutWidget_2.setGeometry(QtCore.QRect(0, 0, req_width, 1975))
        self.ui.scrollAreaWidgetContents.setMinimumSize(QtCore.QSize(req_width, 1975))
        self.ui.scrollArea.setMinimumWidth(new_min_width)
        self.ui.pushButton_cal.hide()
        QtCore.QTimer.singleShot(50, self.alignHeaders)
        
        diff = old_min_width - new_min_width
        if diff > 0:
            self.resize(self.width() - diff, self.height())
        
    def showCal(self):
        self.ui.label_5.show()
        self.ui.label_6.show()
        self.ui.label_7.show()
        #print "showcal, number of channels in grid:", self.ui.gridLayout_2.count()
        if (self.ui.gridLayout_2.count() <2):  return
        for i in (list(range(self.ui.gridLayout_2.count()))):
        #for i in range(len(self.nameList)):
            try:
                self.spanBoxes[i].show()
                self.zeroBoxes[i].show()
                self.refBoxes[i].show()
            except: pass
        QtWidgets.QApplication.processEvents()
        req_width = self.ui.gridLayoutWidget_2.minimumSizeHint().width()
        if req_width < 370: req_width = 370
        
        old_min_width = self.ui.scrollArea.minimumWidth()
        new_min_width = req_width + 30
        
        self.ui.gridLayoutWidget_2.setGeometry(QtCore.QRect(0, 0, req_width, 1975))
        self.ui.scrollAreaWidgetContents.setMinimumSize(QtCore.QSize(req_width, 1975))
        self.ui.scrollArea.setMinimumWidth(new_min_width)
        self.ui.pushButton_cal.show()   
        QtCore.QTimer.singleShot(50, self.alignHeaders)   
        
        diff = new_min_width - old_min_width
        if diff > 0:
            self.resize(self.width() + diff, self.height())
        #self.ui.centralwidget.adjustSize()
    
    def Notes(self):
        notesDialog = QtGui.QDialog()
        Notes_ui = Ui_Notes()
        Notes_ui.setupUi(notesDialog)
        notesDialog.exec_()
        

    
    def CandD(self,serialComClient):
        print("C and D")
        self.ui.actionTerminal_Mode.setChecked(True) #terminal
        self.terminalToggle()
        serialComClient.queueSend.put("**SET_VALS**")
        self.ui.textBrowser_2.setText("getting list of parameters")
        serialComClient.calHappening = True
        

        
    def Calibrate(self,serialComClient):
        self.ui.actionTerminal_Mode.setChecked(True) #terminal
        self.terminalToggle()
        self.ui.textBrowser.setText("uploading calibrations")
        print ("calibration")
        #self.ui.pushButton_cal.setText("working")
        self.calInfoList = ["**CAL**"]
        #loop through names if not CO2 do the following
        for i in range (3,serialComClient.numberOfInputs+3):
            if self.zeroBoxes[i-3].isChecked():#send: **CAL**:zeroOrSpan:ref:zero:chanNum:CO2
                print("zero cal ch:", i-3)
                calMsg = "zero:"
                boxVal = self.refBoxes[i-3].value()
                calMsg +=str(boxVal)#ref
                calMsg += ":"
                boxtext = self.readingBoxes[i-3].text()
                calMsg += str(boxtext)#zero
                calMsg += ":"
                calMsg += str(i-3)#channel number
                calMsg += ":"
                calMsg += str(0)# if 1 => co2 channel, 0 => normal channel
                self.calInfoList.append(calMsg)
                ##%serialComClient.calHappening = True
            if self.spanBoxes[i-3].isChecked():
                print("span cal ch", i-3)
                calMsg = "span:"
                boxVal = self.refBoxes[i-3].value()
                calMsg +=str(boxVal)#ref
                calMsg += ":"
                boxtext = self.readingBoxes[i-3].text()
                calMsg += str(boxtext)#zero
                calMsg += ":"
                calMsg += str(i-3)#channel number
                calMsg += ":"
                calMsg += str(0)# if 1 => co2 channel, 0 => normal channel
                self.calInfoList.append(calMsg)
                #serialComClient.queueSend.put(calMsg)
                ##%serialComClient.calHappening = True
        if len(self.calInfoList) >1:
            serialComClient.queueSend.put(self.calInfoList)
            serialComClient.calHappening = True
        
        
    def plot_update(self,lineOfdata,nameList,calHappening):#puts a new point on the plot
        if self.plotRunning == True:

            if len(lineOfdata) > 2 and len(lineOfdata) == (len(nameList) +3) and "time" not in lineOfdata[0] and calHappening == False: ##% make sure there are some data, not other lines
                #print "lineofdata", lineOfdata
                
                datanoise = False
                lenBefore = len(self.yVals[1])
                ##%for i in range (len(nameList)): 
                for pltNum in range (len(nameList)):
                    #put new y values in array:
                    try:
                        self.yVals[pltNum].append(float(lineOfdata[pltNum+3])) #3 skips over date, time elapsed headid
                    except:
                        print("failed Y append:", end=' ')
                        print("     input: ",pltNum, end=' ')
                        print("     name:", nameList[i])
                        datanoise = True
                        break
                    else:
                        self.y[pltNum] = []
                        if self.showSeriesBoxes[pltNum].isChecked() : #check if attached 
                            for  i in range (len(self.yVals[pltNum])):
                                self.y[pltNum].append(self.yVals[pltNum][i] * self.scaleBoxes[pltNum].value()   )
                
                if datanoise == False:#only add X if Y's are all OK
                    try:
                        self.xVals.append(float(lineOfdata[1])) #elapsed seconds is  [1]
                    except:
                        print("trying to plot before data arrived")
                    self.x = []
                    for  i in range (len(self.xVals)):
                        self.x.append(self.xVals[i] )
                    
                    
                    #data point reduction:
                    if  not self.ui.checkBox.isChecked() and not self.ui.checkBox_2.isChecked():
                        maxPoints =60000            
                        """
                        
                        if len(self.x)>maxPoints: ##% keep dataset from getting too long
                            for i in range (maxPoints):
                                newpoint = i+(len(self.x)//maxPoints)
                                if newpoint<len(self.x):
                                    self.x[i] =self.x[i+(len(self.x)//maxPoints)]
                            self.x = self.x[:maxPoints]
                            for i in range (len(nameList)):
                                for j in range (maxPoints):
                                    newpoint = j+(len(self.y[i])//maxPoints)
                                    if newpoint<len(self.y[i]):
                                        self.y[i][j] =  self.y[i][j+(len(self.y[i])//maxPoints)]
                                self.y[i] = self.y[i][:maxPoints]
                            print "data legnth: ", len(self.x)
                        """
                        
                        plotLegnth = len(self.x)
                        if plotLegnth>maxPoints: ##% keep dataset from getting too long, cut off older data
                            del self.x[:(plotLegnth-maxPoints)]
                            for i in range (len(nameList)):
                                del self.y[i][:(plotLegnth-maxPoints)]
                            ##%print len(self.x)
                        
                        """
                        if plotLegnth>maxPoints: ##% keep dataset from getting too long Ramer-Douglas-Peucker
                            #could use  Ramer-Douglas-Peucker, but would have to assemble x,y into pairs, then take apart
                            newArray = rdp([[1, 1], [2, 2], [3, 3], [4, 4]])   
                        """
                    
                    
                    self.updatePlotLineScale2()
                    ##% set trim here:
                    if self.x[0] == 3 and self.trimmed == False:#remove first sets
                        for i in range(2):
                            del self.x[i]
                            del self.y[i]
                            del self.yVals[i]
                        print ("removed first sets")
                        self.trimmed = True

                    if len(self.x) >3:
                        self.setPlotRanges()
                else:
                    #clean up other points that did not append:
                    print("cleaning up  ", end=' ') 
                    print("legnth before: ", lenBefore)
                    for i in range (len(nameList)):
                        if len( self.y[i]) >lenBefore:
                            print("shortening ", i)
                            self.y[i].pop()
                
                    
    def updatePlotLineScale2(self):
        
        #note: self.yVals[i][j] => [input][point]
         
        for i in range(len(self.y)):
            #visible or not:
            if  self.showSeriesBoxes[i].isChecked() :
                self.cWt[i].attach(self.ui.qwtPlot)
            else:
                self.cWt[i].detach()
            for j in range(len(self.y[i])-1):
                currentYval = self.yVals[i][j] #[input][point]   
                currentScaleboxval = self.scaleBoxes[i].value()
                self.y[i][j] = currentYval * currentScaleboxval
            #set data to plot
            self.cWt[i].setSamples(self.x, self.y[i])

        ##>>%self.ui.qwtPlot.replot() ##>>% DONE ELSEWHERE
    
                    
    def setPlotRanges(self):
        if  self.ui.checkBox.isChecked() and not self.ui.checkBox_2.isChecked():#range overrides
            tailLegnth = self.ui.spinBox_5.value()
            self.ui.qwtPlot.setAxisScale(Qwt.QwtPlot.xBottom, self.x[-1]-tailLegnth,self.x[-1])#show tail data
            
        elif  self.ui.checkBox_2.isChecked():
            #read spin boxes:
            Xmin = self.ui.spinBox.value()
            Xmax = self.ui.spinBox_2.value()
            self.ui.qwtPlot.setAxisScale(Qwt.QwtPlot.xBottom, Xmin,Xmax)#show range data    
        
        else:
            self.ui.qwtPlot.setAxisScale(Qwt.QwtPlot.xBottom, self.x[0]+2,self.x[-1])#show all data
            
        if self.ui.checkBox_3.isChecked():
            Ymin = self.ui.spinBox_4.value()
            Ymax = self.ui.spinBox_3.value()
            self.ui.qwtPlot.setAxisScale(Qwt.QwtPlot.yLeft, Ymin,Ymax)#show range data
        else:
            self.ui.qwtPlot.setAxisAutoScale (Qwt.QwtPlot.yLeft)
        self.ui.qwtPlot.replot()
       
    # Curated default palette – distinct, readable colors used when the user
    # has not yet picked a custom color for a channel.
    DEFAULT_COLORS = [
        Qt.QColor(31,  119, 180),  # blue
        Qt.QColor(214,  39,  40),  # red
        Qt.QColor( 44, 160,  44),  # green
        Qt.QColor(255, 127,  14),  # orange
        Qt.QColor(148, 103, 189),  # purple
        Qt.QColor(140,  86,  75),  # brown
        Qt.QColor(227, 119, 194),  # pink
        Qt.QColor(127, 127, 127),  # grey
        Qt.QColor(188, 189,  34),  # olive
        Qt.QColor( 23, 190, 207),  # cyan
    ]

    def plot_start(self,nameList):
        #remove current plots
        if self.plotRunning == True:
            for i in range(0, len(self.cWt)):
                self.cWt[i].detach()
            self.plotRunning = False
        if self.plotRunning == False :
            self.ui.qwtPlot.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.RightLegend)
            self.ui.qwtPlot.setAxisTitle(Qwt.QwtPlot.xBottom, 'time')
            self.ui.qwtPlot.setAxisTitle(Qwt.QwtPlot.yLeft, 'value')
            self.ui.qwtPlot.setCanvasBackground(QtCore.Qt.white)
            
            self.x = [] # x values to plot
            self.xVals  = []#actual x values
            self.yVals = defaultdict(list) #actual y values
            self.y = defaultdict(list) # y value list for plot (scaled)
            self.cWt = {} # curve list
            for i in range (0,len(nameList)):
                # insert curves
                self.cWt[i] = Qwt.QwtPlotCurve(nameList[i])
                # Use user-chosen color if available, otherwise pick from default palette
                if i in self.channelColors:
                    color = self.channelColors[i]
                else:
                    color = self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)]
                    self.channelColors[i] = color
                    # Update the color button to reflect the default color
                    if hasattr(self, 'colorButtons') and i in self.colorButtons:
                        self.colorButtons[i].setStyleSheet(
                            "background-color: %s; border: 1px solid #555;" % color.name())
                self.cWt[i].setPen(Qt.QPen(color, 2))
                self.cWt[i].attach(self.ui.qwtPlot)
                
                # make Numeric arrays for the horizontal data
                self.y[i] = [0]
                self.cWt[i].setSamples(self.x, self.y[i])
            
            self.plotRunning = True
        

    def valueUpdate(self,boxName,lineOfdata, calHappening ):#put data values in the boxes/buttons
        if calHappening == False:
            for i in range (3, len(lineOfdata)):
                QApplication.processEvents()#this makes the UI update before going on.
                boxNum = i-3
                #boxNum = i
                #boxName[boxNum].setText(lineOfdata[i])
                if boxName[boxNum].getTextMargins() != (0, 0, 0, 1): #not displaying captured average
                    boxName[boxNum].setText(lineOfdata[i])
    
    def pickChannelColor(self, chanIndex):
        """Open a color dialog for chanIndex and apply the chosen color immediately."""
        initial = self.channelColors.get(chanIndex, Qt.QColor(0, 0, 200))
        color = QColorDialog.getColor(initial, self, "Pick color for channel %d" % chanIndex)
        if color.isValid():
            self.channelColors[chanIndex] = color
            # Persist the chosen color so it survives a restart
            self.settings.setValue("color_%d" % chanIndex, color.name())
            # Update the button background to match the new color
            self.colorButtons[chanIndex].setStyleSheet(
                "background-color: %s; border: 1px solid #555;" % color.name())
            # Apply to live curve immediately if plot is running
            if self.plotRunning and chanIndex in self.cWt:
                self.cWt[chanIndex].setPen(Qt.QPen(color, 2))
                self.ui.qwtPlot.replot()

    def addChanBoxes(self, nameList): #load the channels into the UI
        self.showSeriesBoxes  = {}
        self.buttons = {}
        self.colorButtons = {}  # color picker buttons (new in 2.1)
        self.scaleBoxes = {}
        self.refBoxes = {}
        self.zeroBoxes = {}
        self.spanBoxes = {}
        self.buttonGroup = {}
        self.readingBoxes = defaultdict(list)
        i = 0
        #clearing out last grid:
        for i in reversed(list(range(self.ui.gridLayout_2.count()))): 
            try:
                self.ui.gridLayout_2.itemAt(i).widget().setParent(None)
            except: 
                pass
        print("namelist used for setting up chanboxes", nameList)
        for i in range(len(nameList)):
            
            #add buttons with names for average capture: 
            self.buttons[i] = QtWidgets.QPushButton(self)
            self.buttons[i].setObjectName(_fromUtf8("pushButton_0_"+nameList[i]))
            self.buttons[i].setText(nameList[i])
            self.buttons[i].setMinimumHeight(25)
            self.ui.gridLayout_2.addWidget(self.buttons[i],i,0,1, 1, QtCore.Qt.AlignLeft)

            # --- color picker button (new in 2.1) ---
            # Seed color: use previously chosen color if it exists, else pick from default palette
            if i not in self.channelColors:
                self.channelColors[i] = self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)]
            seedColor = self.channelColors[i]
            self.colorButtons[i] = QtWidgets.QPushButton(self)
            self.colorButtons[i].setObjectName(_fromUtf8("colorBtn_"+str(i)))
            self.colorButtons[i].setFixedSize(20, 20)
            self.colorButtons[i].setToolTip("Click to choose plot color for this channel")
            self.colorButtons[i].setStyleSheet(
                "background-color: %s; border: 1px solid #555;" % seedColor.name())
            self.ui.gridLayout_2.addWidget(self.colorButtons[i],i,7,1,1, QtCore.Qt.AlignLeft)
            self.colorButtons[i].clicked.connect(
                lambda dummy, num=i: self.pickChannelColor(num))
            # -----------------------------------------
            
            #add reading boxes:
            self.readingBoxes[i] =QtWidgets.QLineEdit(self)
            self.readingBoxes[i].setObjectName(_fromUtf8("lineEdit"+ str(i)))
            self.readingBoxes[i].setMinimumHeight(25)
            self.readingBoxes[i].setMinimumWidth(60)
            self.readingBoxes[i].setMaxLength(9) #max number of characters, may need to increase, or remove
            self.ui.gridLayout_2.addWidget(self.readingBoxes[i],i,1,1, 1, QtCore.Qt.AlignLeft)
            
            #add scale boxes 
            self.scaleBoxes[i] = QtWidgets.QDoubleSpinBox(self)
            self.scaleBoxes[i].setObjectName(_fromUtf8("doubleSpinBox1"+nameList[i]))
            self.scaleBoxes[i].setValue(1.000)
            self.scaleBoxes[i].setRange(0.00001, 1000000)
            self.scaleBoxes[i].setMinimum(0.001)
            self.scaleBoxes[i].setDecimals(3)
            self.scaleBoxes[i].setSingleStep(.1)
            self.scaleBoxes[i].setMinimumHeight(25)
            self.scaleBoxes[i].setMinimumWidth(60)
            self.ui.gridLayout_2.addWidget(self.scaleBoxes[i],i,2,1, 1, QtCore.Qt.AlignLeft)
            
            #add show plot checkboxes
            self.showSeriesBoxes[i] = QtWidgets.QCheckBox(self)
            self.showSeriesBoxes[i].setObjectName(_fromUtf8("checkBox2"+nameList[i]))
            self.showSeriesBoxes[i].setChecked(False) 
            self.showSeriesBoxes[i].setMinimumHeight(25)
            self.showSeriesBoxes[i].setMinimumWidth(40)
            self.ui.gridLayout_2.addWidget(self.showSeriesBoxes[i],i,3,1, 1, QtCore.Qt.AlignLeft)
            
            #add ref boxes:
            self.refBoxes[i] = QtWidgets.QDoubleSpinBox(self)
            self.refBoxes[i].setObjectName(_fromUtf8("doubleSpinBox"+nameList[i]))
            self.refBoxes[i].setDecimals(3)
            self.refBoxes[i].setMaximum(100000.0)
            self.refBoxes[i].setMinimumHeight(25)
            self.refBoxes[i].setMinimumWidth(75)
            self.ui.gridLayout_2.addWidget(self.refBoxes[i],i,4,1, 1, QtCore.Qt.AlignLeft)
            
            #add zero checkboxes
            self.zeroBoxes[i] = QtWidgets.QCheckBox(self)
            self.zeroBoxes[i].setObjectName(_fromUtf8("checkBox0"+nameList[i]))
            self.zeroBoxes[i].setMinimumHeight(25)
            self.zeroBoxes[i].setMinimumWidth(40)
            self.ui.gridLayout_2.addWidget(self.zeroBoxes[i],i,5,1, 1, QtCore.Qt.AlignLeft)
            
            #add span checkboxes
            self.spanBoxes[i] = QtWidgets.QCheckBox(self)
            self.spanBoxes[i].setObjectName(_fromUtf8("checkBox1"+nameList[i]))
            self.spanBoxes[i].setMinimumHeight(25)
            self.spanBoxes[i].setMinimumWidth(40)
            self.ui.gridLayout_2.addWidget(self.spanBoxes[i],i,6,1, 1, QtCore.Qt.AlignLeft)
        
            #connect signals:
            self.scaleBoxes[i].valueChanged.connect(lambda: self.updatePlotLineScale2())
            self.showSeriesBoxes[i].clicked.connect(lambda: self.updatePlotLineScale2())
            self.buttons[i].clicked.connect(lambda dummy, boxName = self.readingBoxes, num = i: caputre(boxName, num, self.serialComClient))
            self.zeroBoxes[i].clicked.connect(lambda dummy, boxName = self.zeroBoxes, boxNameOther = self.spanBoxes, num = i: self.toggleCheck(boxName,boxNameOther, num))
            self.spanBoxes[i].clicked.connect(lambda dummy, boxName = self.spanBoxes, boxNameOther = self.zeroBoxes, num = i: self.toggleCheck(boxName,boxNameOther, num))
        
        #spacer to push to top
        rowCount = int(self.ui.gridLayout_2.rowCount())
        if rowCount < 1000: #1000 is a row so far down that no channels will ever go here)
            self.spacerItem_2 = QtWidgets.QSpacerItem( 20, 40 , QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.ui.gridLayout_2.addItem(self.spacerItem_2,1000,1)
        #toggle view to straighten it up:
        self.showCal()
        self.hideCal()
        
        # dynamically align headers with columns
        QtCore.QTimer.singleShot(100, self.alignHeaders)

    def alignHeaders(self):
        try:
            if self.ui.gridLayout_2.count() == 0: return
            
            def get_x(col):
                item = self.ui.gridLayout_2.itemAtPosition(0, col)
                if item and item.widget():
                    return item.widget().geometry().x()
                return 0
                
            self.ui.label_8.move(get_x(0), self.ui.label_8.y()) # Capture
            self.ui.label_9.move(get_x(1), self.ui.label_9.y()) # Value
            self.ui.label_10.move(get_x(2), self.ui.label_10.y()) # Scale
            self.ui.label_11.move(get_x(3), self.ui.label_11.y()) # Plot
            self.ui.label_5.move(get_x(4), self.ui.label_5.y()) # Reference
            self.ui.label_6.move(get_x(5), self.ui.label_6.y()) # Zero
            self.ui.label_7.move(get_x(6), self.ui.label_7.y()) # Span
        except Exception as e:
            print("Error aligning headers:", e)

class ThreadedClient:
    
    """
    Launches the worker thread.
    foreground fuctions could reside in the main part, but putting them here
    means that you have all the thread controls in a single place.
    """

    
    def __init__(self):
        self.StartUpCheck = False
        self.inputsFound = False
        self.headersFound = False
        self.headerIDFound = False
        self.ser_portOpened = False
        self.readHeaderLines = 0
        
        self.Avals = ""
        self.Bvals = ""
        self.Cvals = ""
        self.Dvals = ""
        self.units = ""
        
        
        self.chanNames = ""
        self.headerID = ""
        self.numberOfInputs = 0
        self.valuesToAverag = {}
        
        self.queueRecv = queue.Queue()# Create the queue for receiving data
        self.queueSend = queue.Queue()# Create the queue for sending data
        self.calHappening = False

    ###
    ###
    ###foreground:
    ###
    ###
    def makeMainWindow(self,nameList):
        self.window = MainWindow(nameList,self) 
        self.window.setWindowTitle("Ratnoze")
        self.window.show()
        self.window.plot_start(nameList)
        self.makeLogFile()
        
    def makeLogFile(self):
        # create logfile with current date and time
        date = str(time.strftime("%Y%m%d%H%M%S"))
        if not os.path.exists("logs"):
            os.makedirs("logs")
        self.datafile = open('logs/%s.csv' % date, 'w', newline='')
        self.datafile.write("# Timestamp: "+date+"\n")
        ##% things that could be in log file if needed
        #self.datafile.write(str(self.Avals).rstrip('\n'))
        #self.datafile.write(str(self.Bvals).rstrip('\n'))
        #self.datafile.write(str(self.chanNames).rstrip('\n'))
        self.datafile.flush()
    
    def startThread(self):
        # A timer to periodically call something to check the queue
        self.timer = QtCore.QTimer()
        ###QtCore.QObject.connect(self.timer,
        ###                    QtCore.SIGNAL("timeout()"),
        ###                    self.periodicCall)#this is what is called every timer tick
        self.timer.timeout.connect(self.periodicCall)
        #self.timer.start(1000)#ms
        self.timer.start(100)#ms
        # Set up the thread to do asynchronous I/O. More can be made if necessary      
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()
        print("timer and thread started")
        
    def periodicCall(self):
        if not self.running:
            self.timer.stop()
            print("timer stopped")
        else:
            #check message:
            self.processIncoming()

    def endApplication(self):
        try:
            self.timer.stop()
            print("thread:",self.thread1.is_alive())
        except: print("no thread running")
        self.running = 0
        
    def setVals(self,paraList):
        self.calInfoList = ["**CAL**"]
        DList = []
        paralistSplit = paraList.split(":")
        #name, value, chan
        for i in range(len(paralistSplit)-1):
            DList.append(paralistSplit[i+1].split(','))

        #send parameters to make dialog:
        self.dialog = SubDialog() # (self) would send it seialcomclient, may be needed?)
        self.dialog.addRows(DList)
        result = self.dialog.exec_()
        if result == 1:
            #self.paraName,self.paraVal,self.paraNewVal,self.paraUpdate,
            for i in range (len(self.dialog.paraName)):
                print("Name of D",self.dialog.paraName[i].text())
                if self.dialog.paraUpdate[i].isChecked():
                    calMsg = "D:0:"
                    boxVal = self.dialog.paraNewVal[i].value()
                    calMsg +=str(boxVal)#D
                    calMsg += ":"
                    calMsg += DList[i][2]
                    calMsg += ":"
                    calMsg += str(0)# if 1 => co2 channel, 0 => normal channel
                    self.calInfoList.append(calMsg)
        else: self.ser.write(self.ResetNum.encode()) #reset
        if len(self.calInfoList) >1:
            self.queueSend.put(self.calInfoList)
            self.calHappening = True
        else: 
            self.ser.write(self.ResetNum.encode()) #reset beacuse nothing checked
            self.calHappening = False

    
    def processIncoming(self):#called periodically by periodicCall, called by timer
        ###states:   StartUpCheck, GettingNames, Running,  SettingTime,  Calibrating, inputsFound  (fix this note, these have changed)
        self.lineOfdata = ""
        #print"checking for message FROM thread",
        
        while self.queueRecv.qsize():#if queue has something in
            try:
                self.lineOfdata = self.queueRecv.get(0)
                if isinstance(self.lineOfdata, str):##% can only handle strings now, could here for string for other things like int or list
                    if len(self.lineOfdata)>0: #put serial output in screen:
                        self.datafile.write(self.lineOfdata)
                        self.datafile.flush()
                        self.window.ui.textBrowser.setText(self.lineOfdata)
                        self.window.ui.textBrowser_2.append(self.lineOfdata.rstrip())
                        
                        if "<bkd> params" in self.lineOfdata:  
                            self.setVals(self.lineOfdata)
                        
                        if '#' in self.lineOfdata and self.StartUpCheck == False and self.calHappening == False:
                            print("DAQ is starting")
                            self.inputsFound = False
                            self.headersFound = False 
                            self.headerIDFound = False  
                            self.StartUpCheck = True   
                        
                        ##get dataset info from header:
                        if self.StartUpCheck == True:  
                            
                            #get number of inputs from header:
                            if self.inputsFound == False :
                                index=self.lineOfdata.find("inputs:")
                                index2 = self.lineOfdata.find("\r") # this works even if doesn't end with \r because returns -1
                                if index > 0:
                                    index = index +7
                                    self.inputsFound = True
                                    number = self.lineOfdata[index:index2]
                                    self.numberOfInputs = int(number)
                                    print(("number of inputs"), end=' ')
                                    print(self.numberOfInputs) 
                                    self.inputsFound = True
                            #get A,B,C,Dvals, and channames from header :
                            #collect header lines if triggered by finding "header" below:
                            if self.readHeaderLines == 1:
                                self.Avals = self.lineOfdata
                                print("found Avals:" , self.Avals, end=' ')
                                self.readHeaderLines = 2
                            elif self.readHeaderLines == 2:
                                self.Bvals =  self.lineOfdata
                                print("found Bvals:" , self.Bvals, end=' ')
                                self.readHeaderLines = 3
                            elif self.readHeaderLines == 3:
                                self.Cvals =  self.lineOfdata
                                print("found Cvals:" , self.Cvals, end=' ')
                                self.readHeaderLines = 4
                            elif self.readHeaderLines == 4:
                                self.Dvals =  self.lineOfdata
                                print("found Dvals:" , self.Dvals, end=' ')
                                self.readHeaderLines = 5
                            elif self.readHeaderLines == 5:
                                self.units =  self.lineOfdata
                                print("found Units:" , self.units, end=' ')
                                self.readHeaderLines = 6        
                            elif self.readHeaderLines == 6:
                                self.chanNames =  self.lineOfdata
                                print("found names:" , self.chanNames, end=' ')
                                self.readHeaderLines = 7
                                self.headersFound = True 
                            if self.headersFound == False :
                                index=self.lineOfdata.find("headers:")
                                if index > 0:
                                    self.readHeaderLines = 1 #loop will collect the next line
                            #get header ID    
                            if self.headerIDFound == False and self.headersFound == True:
                                self.getHeaderID()
                        #if everything found ( inputsFound, headersfound, headerIDfound, ) 
                        
                        if self.StartUpCheck == True and self.inputsFound == True and self.headersFound == True and self.headerIDFound == True:
                            #record header in database
                            
                            self.newNamelist = self.setupUIwithNames() 
                            if "?" in self.newNamelist:
                                print("unamed cols, not saving")
                            else:    
                                print("updating database")
                                foundmatch = False
                                fn ='./headerlist.txt'
                                f = open(fn)
                                output = []
                                for line in f:
                                    index0=line.find(' ') #find the space after the headerID
                                    headernumber = line[0:(index0)]
                                    if self.headerID == headernumber:
                                        output.append(headernumber+' '+self.chanNames)
                                        foundmatch = True
                                    else:
                                        output.append(line) 
                                f.close()
                                if foundmatch == True:
                                    f = open(fn, 'w')
                                    f.writelines(output)
                                else:
                                    f = open(fn, 'a')
                                    f.writelines(self.headerID+' '+self.chanNames)
                                f.close()
                            self.StartUpCheck = False
                            print("startup check done") 
                            
                        ##already streaming, get dataset info from database:
                        if self.headerIDFound == False and self.StartUpCheck == False:
                            #get header ID from stream
                            if self.getHeaderID() == True:
                                #count number of inputs:
                                self.numberOfInputs = self.lineOfdata.count(',') -2
                                print("number of inputs",self.numberOfInputs)
                                self.inputsFound = True
                    
                                #check for header ID in fdatabase
                                foundInDatabase = False
                                fn ='./headerlist.txt'
                                f = open(fn)
                                for line in f:
                                    index0=line.find(' ') #find the space after the headerID
                                    headernumber = line[0:(index0)]
                                    if self.headerID == headernumber:
                                        foundInDatabase = True
                                        self.chanNames = line[index0+1:len(line)]
                                        print("Found header in database")
                                        print(self.chanNames.rstrip("\n")) 

                                if foundInDatabase == False: #make a default header:
                                    print("ID not found in database, using defaults.\n Start this program before starting the DAQ to get headers")
                                    self.chanNames = "time,seconds,headID,"
                                    for i in range (0,self.numberOfInputs):
                                        #add fake name
                                        self.chanNames = self.chanNames+"data"+str(i)+','
                                    self.chanNames = self.chanNames[:-1]+'\r\n'  
                                self.newNamelist = self.setupUIwithNames()
                       
                    #now process data:
                    ##proposed, may or may have been implemented:
                    #if starting: get names, update database 
                    #if already running get ID and load up UI
                    #if running: validate data, split, plot and update boxes,update averages
                    #if setting time: look for necessary prompts, send commands
                    #if calibrating: look for necessary prompts, send commands
                    
                    if self.lineOfdata.find('#') == -1 and self.headerIDFound == True: #stream line not header or debug
                        #could count commas here to verify
                        valuelist = self.lineOfdata.rstrip('\n').split(",")
                        # ── Derived channels ──────────────────────────────────────────────
                        # Computed here, after the raw line has already been written to the
                        # log (datafile.write happens above), so the CSV stays unmodified.
                        # We build a name→float dict from the real channels, then evaluate
                        # each formula and append the result to valuelist.  This keeps
                        # everything positionally consistent with the extended newNamelist
                        # that setupUIwithNames() produced at startup.
                        if DERIVED_CHANNELS:
                            n_real = len(self.newNamelist) - len(DERIVED_CHANNELS)
                            # Map real channel names to their current float values.
                            ch = {}
                            for idx, name in enumerate(self.newNamelist[:n_real]):
                                try:
                                    ch[name] = float(valuelist[idx + 3])  # +3 skips date/seconds/headID
                                except (ValueError, IndexError):
                                    ch[name] = 0.0
                            # Evaluate each formula and append to valuelist.
                            for _derivedName, formula in DERIVED_CHANNELS:
                                try:
                                    result = formula(ch)
                                    valuelist.append("" if result is None else "%.4f" % result)
                                except Exception as e:
                                    print("Derived channel error (%s): %s" % (_derivedName, e))
                                    valuelist.append("")
                        # ── End derived channels ──────────────────────────────────────────
                        self.window.valueUpdate(self.window.readingBoxes,valuelist, self.calHappening)
                        self.window.plot_update(valuelist, self.newNamelist, self.calHappening)
                        #put values into list for averaging when requested:
                        for i in range (len(self.valuesToAverage)-1):#first shift
                            self.valuesToAverage[i] = self.valuesToAverage[i+1]
                        self.valuesToAverage[-1] = valuelist
                    
                    QApplication.processEvents()
            except queue.Empty:
                print("M T")
                pass
    ###
    ###
    ###background:
    ###
    ###
    
    def getHeaderID(self):
        print("getting header ID from stream")
        if self.lineOfdata.find('#') == -1:    #if there is no # in the line
            # this assumes the header ID is the third column
            index0=self.lineOfdata.find(',')+1 #find the first comma
            index1=self.lineOfdata.find(',',index0)+1 #find the second comma
            index2=self.lineOfdata.find(',',index1) #find the third comma
            self.headerID = self.lineOfdata[(index1):(index2)]
            if len(self.headerID)>0 and self.headerID.isdigit():
                print("found headerID", self.headerID)
                self.headerIDFound = True
                return True
        else: 
            return False
    
    def setupUIwithNames(self):
        Namelist = self.chanNames.split(",")
        Namelist[-1] = (Namelist[-1])[:-2]#fix up namelist
        for i in range (len(Namelist),self.numberOfInputs+3):
            Namelist.append("?")
        #remove first three items date, time, ID
        Namelist.pop(0)
        Namelist.pop(0)
        Namelist.pop(0)
        # Append a name for every derived channel so they get their own row in
        # the channel panel (reading box, checkbox, scale, colour button) and
        # their own plot curve, in the same positional scheme as real channels.
        for derivedName, _ in DERIVED_CHANNELS:
            Namelist.append(derivedName)
        #Update plot lines:
        self.window.plot_start(Namelist) 
        #update channel boxes:
        self.window.addChanBoxes(Namelist)
        #Update average list
        # Size covers real inputs + 3 header cols + any derived channels so
        # that the average-capture button works on derived channels too.
        totalCols = self.numberOfInputs + 3 + len(DERIVED_CHANNELS)
        self.valuesToAverage = [["0" for i in range(totalCols)] for value in range(10)]##% groups of daq output, 10 of them.   valueToAverage [car][daqVals]
        #the +3 above is so the list has space for time, seconds, headID even though not used
        return Namelist
        
    
    def workerThread1(self): #check the queue and run the logging loop here
        self.ser_portOpened = False
        #this has no timer, just a short delay.  It's just a continuous loop when "running"
        self.task = ["**IDLE**"]#this has the task and the data for time setting
        self.calList = ["**IDLE**"] # this list is oaded by a cal message from the foreground
        self.aCalData = ["**IDLE**"] # This gets the individual cal data form each one in calList

        self.oldSpanList = {} #read in from Ratnose
        self.newSpanList = {} #read in from Ratnose
        self.oldZeroList = {} #read in from Ratnose
        self.newZeroList = {} #read in from Ratnose
        self.valNames = {} #read in from Ratnose
        self.valValues = {} #read in from Ratnose
        self.prevLine = ""
        self.prevLine2 = ""
        self.line = ""
        ###############################
        ##  Ratnoze menu commands: ####
        ###############################
        self.AmenuNum = "1\n" 
        self.BmenuNum = "2\n"
        self.CmenuNum = "3\n"
        self.DmenuNum = "4\n"
        self.ResetNum = "11\n"
        self.SaveNum = "10\n"
        self.TimeNum = "5\n"
        self.BackToMain = "100\n"
        
        while self.running:
            time.sleep(.01) ##% reduce cpu load?
            msg = {}
            got_msg = False
            #time.sleep(.01)#needs this or says msg is unbounded if loop is short
            #Check the queue FROM THE GUI:
            if self.queueSend.qsize() >0:#if queue has something in it
                try:
                    msg = self.queueSend.get(0)
                    got_msg = True
                except queue.Empty:
                    pass
            if got_msg == True:
                print("<bkd> got:",msg)
                if type(msg) is str:     #string styke message
                    #message is a port:
                    if msg[:8] == "/dev/tty" or msg.upper().startswith("COM"): #open port in thread now:
                        self.ser = serial.Serial(port = msg,
                            baudrate = 9600,
                            bytesize = serial.EIGHTBITS,
                            parity = serial.PARITY_NONE,
                            stopbits = serial.STOPBITS_ONE,
                            timeout = .1) ##%
                        self.ser_portOpened = True 
                    #port is open, tend to messages and pass allong data
                    if msg == "**CLOSE**" and self.ser_portOpened == True:   #close  port
                        self.ser.close()
                        self.ser_portOpened = False
                        #self.timer.stop
                        print("<bkd> port closed in logging loop")
                        self.ser.close() #closes if loop ends (because self.ser.readable() ==False) probably redundant
                    
                    ###if there is data to send, pass on to sertial port
                    if msg[:8] ==  "**SEND**" and self.ser_portOpened == True:
                        print("<bkd> sending  ", msg[8:])
                        self.ser.write(msg[8:].encode())
                        
                    ###flush  sertial port
                    if msg[:9] ==  "**FLUSH**" and self.ser_portOpened == True:
                        self.ser.flushInput()
                    ###set time
                    if msg[:8] ==  "**TIME**" and self.ser_portOpened == True:
                        print("<bkd> setting time")
                        print(msg)
                        print(self.task)
                        #self.task = msg.rstrip('\n').split(":")#split the time message into parts (: seperated)
                        self.task[0] = "**TIME**"
                        timestrmsg=msg[9:]
                        print(timestrmsg)
                        #timestrmsg = timestrmsg.rstrip('\n')
                        #print(timestrmsg)
                        self.task.append(timestrmsg)
                        self.task.append("startTimeSet")
                        #print("<bkd> msg split (task)", self.task) 
                    #"**SET_VALS**"
                    if msg[:12] ==  "**SET_VALS**" and self.ser_portOpened == True:
                        self.task = msg.rstrip('\n').split(":")
                        self.task.append("startParaUpdate")
                        print("<bkd> msg split (task)", self.task)
                        self.ser.write('cal'.encode()) #put in cal mode

                        
                elif type(msg) is list:
                    print("<bkd> msg is a list")
                    #"**CAL**" 
                    if "**CAL**" in msg:
                        self.calList = msg
                        print("<bkd> sending cal ")
                        self.queueRecv.put("<bkd> sending cal ")
                        print("<bkd> aCalData : ", self.aCalData)
                        self.aCalData.append("GO")
                        self.ser.write('cal\n'.encode()) #put in cal mode
                   
 
            ###read line of data and send to UI:
            if self.ser_portOpened == True:
                self.prevLine2 = self.prevLine#preserve last lines received
                self.prevLine = self.line 
                try: 
                    self.line = self.ser.readline().decode('utf-8', errors='ignore')
                except: 
                    print("<bkd> port in use") 
                    self.queueRecv.put("port in use")
                if self.line == ".": #keep dots bythemselves from being lines
                    self.line = ""
            ##% ### if portin use, this throws error.  
                else:
                    if len(self.line)>0:
                        ##%print  "<bkd> data recvd."
                        self.queueRecv.put(self.line)
                        
                        #####################################
##########################VVVVVV###### CAL  #######VVVVVVV##############################################
                ####
                #### if message is a cal list:
                ####
                if self.calList[0] == "**CAL**" :
                    #the last [-1] item in the list aCalData is used as a command/status message and is changed as it moves through the process: 
                    #
                    # "GO" , "getPrevSpans" , "StartgetPrevZeros" , "getPrevZeros" , "startNextCal" , "startCal", "allChansDone"
                    # "doNextCal" , "A_selected" , "B_selected" , "B_sel_chan" , "A_sel_chan" , "getNewSpans" , "StartgetNewZeros"
                    # "getNewZeros" , "readback"
                    #
                    #
                    #the rest of aCalData is the cal data for the individual channel, and is read out of calList which is send down from the UI
                    ##first get current values:
                    #set status to get span list
                    if self.aCalData[-1] == "GO"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> getting list of current A ")
                        self.ser.write(self.AmenuNum.encode())#send menue choice for A's 
                        self.line = ""   #clear previous "enter>"
                        self.oldSpanList = []
                        self.aCalData[-1] = "getPrevSpans"
                    #read in spans:
                    if self.aCalData[-1] == "getPrevSpans":
                        ##%    "    "  must be in firmware for this to recognize lines that are span and cal readbacks
                        if self.line.find("    ") >-1: #only value lines in A menu have four spaces
                            splitVal = self.line.split("    ") 
                            if len(splitVal) >1 and splitVal[0].find(":")>-1 : #avoid blank line
                                self.oldSpanList.append(splitVal[1].strip())
                        if len(self.oldSpanList)>2 and "enter>" in self.line: # list filled up
                            #readback spanlist:
                            self.queueRecv.put("<bkd> As received: ")
                            self.queueRecv.put(str(self.oldSpanList))
                            self.queueRecv.put("<bkd> going back to main menu ")
                            self.line = ""   #clear previous "enter>"
                            self.ser.write(self.BackToMain.encode())
                            self.aCalData[-1] = "StartgetPrevZeros"
                    #set status to get zero list:
                    if self.aCalData[-1] == "StartgetPrevZeros"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> getting list of current B ")
                        self.ser.write(self.BmenuNum.encode())#send menue choice for B's 
                        #self.line = ""   #clear previous "enter>"
                        self.oldZeroList = []
                        self.aCalData[-1] = "getPrevZeros"
                    #read in current zeros:
                    if self.aCalData[-1] == "getPrevZeros":
                        ##%    "    "  must be in firmware for this to recognize lines that are span and cal readbacks
                        if self.line.find("    ") >-1: #only value lines in A menu have four spaces
                            splitVal = self.line.split("    ") 
                            if len(splitVal) >1 and splitVal[0].find(":")>-1 : #avoid blank line
                                self.oldZeroList.append(splitVal[1].strip())
                        if len(self.oldZeroList)>2 and "enter>" in self.line: # list filled up
                            #readback spanlist:
                            self.queueRecv.put("<bkd> Bs received: ")
                            self.queueRecv.put(str(self.oldZeroList))
                            self.queueRecv.put("<bkd> going back to main menu ")
                            self.line = ""   #clear previous "enter>"
                            self.ser.write(self.BackToMain.encode())
                            self.aCalData[-1] = "startNextCal"

                    ##load aCallist and pop off from calList (IDLE means it is ready to do the next cal in the list)
                    if "**IDLE**" in self.aCalData and self.aCalData[-1] == "startNextCal" :
                        print("<bkd> calList[0]: ", self.calList[0])
                        if len(self.calList)>1:
                            self.aCalData = self.calList[1].split(":")
                            self.calList.pop(1)
                            self.aCalData[-1] = ("startCal")
                            print("<bkd> aCalData to do: ", self.aCalData)
                            self.aCalData[-1] = "doNextCal"
                        elif len(self.calList) ==1:
                            self.aCalData[-1] = "allChansDone" #go on to doing readback below

                    ##Start the calibration of each channel:
                    if self.aCalData[-1] == "doNextCal"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> starting cal for channel "+ str(self.aCalData[3]))
                        #########span setting: ##########
                        if self.aCalData[0] == "span":
                            self.queueRecv.put("<bkd> Setting Span")
                            ##%calculate newSpan= oldSpan*ref/span
                            oldSpanCalc = float(self.oldSpanList[int(self.aCalData[3])])
                            if float(self.aCalData[1]) > 0.000000000001 or float(self.aCalData[1]) < -0.000000000001:
                                newSpanCalc = oldSpanCalc * (float(self.aCalData[1]) / float(self.aCalData[2]))
                                newSpanString = ('%s' % float('%.7g' % newSpanCalc))[:7]
                            else:
                                newSpanString = str(oldSpanCalc)
                                self.queueRecv.put("<bkd> SPAN CANNOT BE ZERO, saving previous span ")
                            if newSpanString.find("nan") >-1 :
                                newSpanString = str(oldSpanCalc)
                                self.queueRecv.put("<bkd> SPAN CANNOT BE NAN , saving previous span")
                            if newSpanString[-1] == '.': #take off . if left hanging
                                newSpanString = newSpanString[:6] 
                            self.queueRecv.put("<bkd> oldSpan "+ str(oldSpanCalc))
                            self.queueRecv.put("<bkd> ref "+ str(self.aCalData[1]))
                            self.queueRecv.put("<bkd> span "+ str(self.aCalData[2]))
                            self.queueRecv.put("<bkd> newSpan "+ newSpanString)
                            #send 1 (A)
                            self.ser.write(self.AmenuNum.encode())
                            self.aCalData[-1] = "A_selected" 
                            self.queueRecv.put("<bkd> selecting A")
                        #########zero setting: ##########
                        if self.aCalData[0] == "zero":
                            self.queueRecv.put("<bkd> Setting Zero")
                            ##%calculate: Bnew = Bold+(yref-yread)/A
                            oldZeroCalc = float(self.oldZeroList[int(self.aCalData[3])])  #Bold
                            oldSpanCalc = float(self.oldSpanList[int(self.aCalData[3])])  #A
                            newZeroCalc = oldZeroCalc + (float(self.aCalData[1]) - float(self.aCalData[2]))/oldSpanCalc
                            newZeroString = ('%s' % float('%.7g' % newZeroCalc))[:7]
                            if newZeroString.find("nan") >-1 :
                                newZeroString = str(oldZeroCalc)
                                self.queueRecv.put("<bkd> zero cannot be NAN ")
                            if newZeroString[-1] == '.': #take off . if left hanging
                                newZeroString = newZeroString[:6] 
                            self.queueRecv.put("<bkd> oldZero "+ str(oldZeroCalc))
                            self.queueRecv.put("<bkd> ref "+ str(self.aCalData[1]))
                            self.queueRecv.put("<bkd> Zero "+ str(self.aCalData[2]))
                            self.queueRecv.put("<bkd> newZero "+ newZeroString)
                            #send 2 (B)
                            self.ser.write(self.BmenuNum.encode())
                            self.aCalData[-1] = "B_selected" 
                            self.queueRecv.put("<bkd> selecting B")
                        if self.aCalData[0] == "D":
                            self.queueRecv.put("<bkd> Setting D")
                            #send D to menu
                            self.ser.write(self.DmenuNum.encode())
                            self.aCalData[-1] = "D_selected" 
                            self.queueRecv.put("<bkd> selecting D")
                    #select menu item 
                    if self.aCalData[-1] == "D_selected" and "enter>" in self.line:    
                        #send chan # for Zero
                        self.ser.write((str(self.aCalData[3])+"\n").encode())
                        self.aCalData[-1] = "D_sel_chan"
                        self.queueRecv.put("<bkd> sending  chan")
                    
                    
                    if self.aCalData[-1] == "B_selected" and "enter>" in self.line:    
                        #send chan # for Zero
                        self.ser.write((str(self.aCalData[3])+"\n").encode())
                        self.aCalData[-1] = "B_sel_chan"
                        self.queueRecv.put("<bkd> sending  chan")    
                    if self.aCalData[-1] == "A_selected" and "enter>" in self.line:    
                        #send chan # for Span
                        self.ser.write((str(self.aCalData[3])+"\n").encode())
                        self.aCalData[-1] = "A_sel_chan"
                        self.queueRecv.put("<bkd> sending  chan")     
                    #Send value
                    if self.aCalData[-1] == "D_sel_chan" and self.line.find("new D")>-1:    
                        #send value for D 
                        self.ser.write((self.aCalData[2]+"\n").encode())
                        self.queueRecv.put("<bkd> sending  new D")
                        self.line = ""   #clear previous "enter>"
                        self.aCalData = ["**IDLE**"]
                        self.aCalData.append("startNextCal")
                        self.ser.write(self.BackToMain.encode())
                    if self.aCalData[-1] == "B_sel_chan" and self.line.find("new B")>-1:    
                        #send value for B (Zero)
                        self.ser.write((newZeroString+"\n").encode())
                        self.queueRecv.put("<bkd> sending  new B")
                        self.line = ""   #clear previous "enter>"
                        self.aCalData = ["**IDLE**"]
                        self.aCalData.append("startNextCal")
                        self.ser.write(self.BackToMain.encode())
                    if self.aCalData[-1] == "A_sel_chan" and self.line.find("new A")>-1:    
                        #send value for A (Span)
                        self.ser.write((newSpanString+"\n").encode())
                        self.queueRecv.put("<bkd> sending  new A")
                        self.line = ""   #clear previous "enter>"
                        self.aCalData = ["**IDLE**"]
                        self.aCalData.append("startNextCal")
                        self.ser.write(self.BackToMain.encode())
                    
                    
                    
                    ##get new lists of spans and zeros:
                    if self.aCalData[-1] == "allChansDone"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> getting list of new A ")
                        self.ser.write(self.AmenuNum.encode())#send menue choice for A's 
                        self.line = ""   #clear previous "enter>"
                        self.newSpanList = []
                        self.aCalData[-1] = "getNewSpans"
                    if self.aCalData[-1] == "getNewSpans":
                        ##%    "    "  must be in firmware for this to recognize lines that are span and cal readbacks
                        if self.line.find("    ") >-1: #only value lines in A menu have four spaces
                            splitVal = self.line.split("    ") 
                            if len(splitVal) >1 and splitVal[0].find(":")>-1 : #avoid blank line
                                self.newSpanList.append(splitVal[1].strip())
                        if len(self.newSpanList)>2 and "enter>" in self.line: # list filled up
                            ##%readback spanlist: (take away once debugged
                            self.queueRecv.put("<bkd> As received: ")
                            self.queueRecv.put(str(self.newSpanList))
                            self.queueRecv.put("<bkd> going back to main menu ")
                            self.line = ""   #clear previous "enter>"
                            self.ser.write(self.BackToMain.encode())
                            self.aCalData[-1] = "StartgetNewZeros"
                    #set status to get zero list:
                    if self.aCalData[-1] == "StartgetNewZeros"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> getting list of new B ")
                        self.ser.write(self.BmenuNum.encode())#send menue choice for B's 
                        #self.line = ""   #clear previous "enter>"
                        self.newZeroList = []
                        self.aCalData[-1] = "getNewZeros"
                    #read in current zeros:
                    if self.aCalData[-1] == "getNewZeros":
                        ##%    "    "  must be in firmware for this to recognize lines that are span and cal readbacks
                        if self.line.find("    ") >-1: #only value lines in B menu have four spaces
                            splitVal = self.line.split("    ") 
                            if len(splitVal) >1 and splitVal[0].find(":")>-1 : #avoid blank line
                                self.newZeroList.append(splitVal[1].strip())
                        if len(self.newZeroList)>2 and "enter>" in self.line: # list filled up
                            #readback zerolist:
                            self.queueRecv.put("<bkd> new Bs received: ")
                            self.queueRecv.put(str(self.newZeroList))
                            self.queueRecv.put("<bkd> going back to main menu ")
                            self.line = ""   #clear previous "enter>"
                            self.ser.write(self.BackToMain.encode())
                            self.aCalData[-1] = "readback"
                            
                    if self.aCalData[-1] == "readback"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        #output report:
                        self.queueRecv.put("<bkd> Span Readback: name,old,new")    
                        for i in range(len(self.oldSpanList)):
                            chanName = self.newNamelist[i]
                            self.queueRecv.put("<bkd>    "+str(self.newNamelist[i])+" ,  "+str(self.oldSpanList[i]) +" ,  "+str(self.newSpanList[i])+ "\n")
                        self.queueRecv.put("\n<bkd> Zero Readback: name,old,new")    
                        for i in range(len(self.oldZeroList)):
                            self.queueRecv.put("<bkd>    "+str(self.newNamelist[i])+" ,  "+str(self.oldZeroList[i]) +" ,  "+str(self.newZeroList[i])+ "\n")
                        self.aCalData[-1] = "reset"
                        #save and reset RatNose:
                    if self.aCalData[-1] == "reset"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.queueRecv.put("<bkd> all cals done, ~30 sec to save and reset.")
                        self.ser.write(self.SaveNum.encode()) #save to eemem
                        time.sleep(30)    
                        self.ser.write(self.ResetNum.encode()) #reset
                        self.calHappening = False
                        self.aCalData = ["**IDLE**"]

                    
                    
######################^^^^^^#####END CAL#####^^^^^^###################                    
                ##########################################
            
                
                ####setting other parameters C and D:

                if self.task[0] == "**SET_VALS**":   # "startParaUpdate"  is first flag
                    #the last [-1] item in the list task is used as a command/status message and is changed as it moves through the process: 
                    #
                    # "startParaUpdate" , "getValNames" , "getValVals"
                    #

                    if self.task[-1] == "startParaUpdate"  and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:
                        self.ser.write(self.CmenuNum.encode())#send menue choice for C's 
                        self.line = ""   #clear previous "enter>"
                        self.valNames = []
                        self.valVals = []
                        self.valChans = []
                        self.task[-1] = "getValNames"
                    #need to get names and channel number index here
                    if self.task[-1] == "getValNames":
#                        ##%    "    "  must be in firmware for this to recognize lines that are C and D readbacks
#                        if self.line.find("    ") >-1: #only value lines in C menu have four spaces
#                            splitVal = self.line.split("    ") 
#                            if len(splitVal) >1 and splitVal[0].find(":")>-1: #mavoid blank lines
#                                #print "splitvalC",splitVal[1], splitVal[1].find("nan")
#                                if splitVal[1].find("nan") != 0 and len(splitVal[1])>1 :
#                                    self.valNames.append(splitVal[1].strip())
#                                    splitValc = splitVal[0].split(":")
#                                    self.valChans.append(splitValc[0] )

                    
                        if self.line.find(":") >-1: #only value lines in C menu have :
                            if "100: Back to main menu" not in self.line: #has a : but is not a value line
                                splitVal = self.line.split(":") 
                                #if len(splitVal) >1 and splitVal[0].find(":")>-1: #avoid blank lines
                                print("splitvalC",splitVal[1], splitVal[1].find("nan"))
                                if splitVal[1].find("nan") != 1 and len(splitVal[1])>1 :
                                    self.valNames.append(splitVal[1].strip())
                                    splitValc = splitVal[0].split(":")
                                    self.valChans.append(splitValc[0] )

                        if "enter>" in self.line: # list filled up
                            self.queueRecv.put("#<bkd> going back to main menu from C's")
                            self.line = ""   #clear previous "enter>"
                            self.task[-1] = "getValVals"
                            self.ser.write(self.BackToMain.encode())




                    #need to get values from the chan indexes above only
                    if self.task[-1] == "getValVals":
                        if "enter>" in self.line and checkAtMainMenu(self.line, self.prevLine, self.prevLine2) == True:        
                            self.ser.write(self.DmenuNum.encode())#send menue choice for D's 
                        else:
                            ##%    "    "  must be in firmware for this to recognize lines that are C and D readbacks
                            if self.line.find("    ") >-1: #only value lines in D menu have four spaces
                                splitVal = self.line.split("    ") 
                                if len(splitVal) >1 and splitVal[0].find(":")>-1 : #avoid blank line
                                    for i in range (len(self.valChans)):
                                        splitValc = splitVal[0].split(":")
                                        if (splitValc[0] ) == self.valChans[i]:
                                            self.valVals.append(splitVal[1].strip())
                            if "enter>" in self.line: # list filled up
                                self.queueRecv.put("#<bkd> going back to main menu ")
                                self.line = ""   #clear previous "enter>"
                                self.ser.write(self.BackToMain.encode())
                                
                                #readback list (this also triggers Dialog to start:
                                
                                stringToSend = "#<bkd> params"
                                
                                for i in range (len(self.valNames)):#name,chan,val:name,chan,val:name,chan,val
                                    stringToSend =stringToSend+":"+self.valNames[i]+","+self.valVals[i]+","+self.valChans[i]
                                
                                self.queueRecv.put(stringToSend)
                                self.task = ["**IDLE**"]
                                """
                                self.task[-1] = "get.."
                                self.calHappening = False      ####for test##### TAKE OUT to move on
                                self.task = ["**IDLE**"]   ####for test##### TAKE OUT to move on
                                self.ser.write(self.ResetNum)  ####for test##### TAKE OUT to move on
                                """
                        
                ####time setting tasks        
                #### do task if there is one:
                # adap this to the cal task method 
                if self.task[0] == "**TIME**": #cal      5     Change? (y/n)> y      enter time string  
                    if self.task[-1] == "startTimeSet":
                        print("<bkd> sending cal ")
                        self.queueRecv.put("<bkd> sending cal ")
                        self.ser.write("cal".encode())
                        self.task[-1] = "sentCal"
                        
                    if self.task[-1] == "sentCal" and "enter>" in self.line:
                        print("<bkd> cal received")
                        self.queueRecv.put("<bkd> sending 5 ")
                        self.ser.write(self.TimeNum.encode())
                        self.task[-1] = "sayYestoChange"
                        
                    if self.task[-1] == "sayYestoChange" and "Change? (y/n)>" in self.line:
                        print("<bkd> change y")
                        self.queueRecv.put("<bkd> sending y ")
                        self.ser.write("y\n".encode())
                        self.task[-1] = "putTimeString"
                    
                    if self.task[-1] == "putTimeString" and "SS )>" in self.line:
                        print("<bkd> enter time string>")
                        self.queueRecv.put("<bkd> sending time string rtn ")
                        self.ser.write(self.task[1].encode())##timeset put self.task[x] once sent proper format setup
                        self.ser.write("\n".encode())
                        self.task[-1] = "finishTimeSet"
    
                    if self.task[-1] == "finishTimeSet" and "enter>" in self.line:
                        print("<bkd> resetting")    
                        self.ser.write(self.ResetNum.encode()) #reset
                        self.task[0] = "**IDLE**"
                        self.calHappening = False        
                        
                
                    

                        

                            
                   


##### functions 

 
   
 
#gets an average reading:  
def caputre(boxName, num, serialComClient):
        print("reading: ", end=' ')
        print(num)
        
        font = QtGui.QFont()
        font.setPointSize(8)
        #font.setWeight(75)
        boxName[num].setFont(font)
    
        #test for margins as a flag:
        if boxName[num].getTextMargins() == (0, 0, 0, 1):
            print("averaged displayed")
            boxName[num].setTextMargins(0,0,0,0)
            boxName[num].setStyleSheet("QLineEdit {background-color: white;}")
            return
        
        boxName[num].setStyleSheet("QLineEdit {background-color: yellow;}")
        boxName[num].setTextMargins(0,0,0,1)

        ####average this channel:
        print("col req'd", num)
        total = 0
        for i in range(len(serialComClient.valuesToAverage)):
            total = total+float(serialComClient.valuesToAverage[i][num+3])#+3 if because this list has date, time ID in it
        average = total/len(serialComClient.valuesToAverage)
        print("average", average)
        boxName[num].setText(str(average))
 

def checkAtMainMenu(line, prevLine, prevLine2 ):#check if at main menu
    if  "enter>" in line and  ( prevLine.find("Reset") >-1 or prevLine2.find("Reset") >-1): 
        return True
    else: return False


      
def connectSerPort():
        notFirstTry = False
        while True:
            active_ports = [p.device for p in serial.tools.list_ports.comports()]
            port = active_ports[0] if active_ports else ''
            serDialog = QDialog()
            port_ui = Ui_SerialPortDialog()
            port_ui.setupUi(serDialog)
            port_ui.comboBox.setEditable(True)
            if active_ports:
                port_ui.comboBox.clear()
                port_ui.comboBox.addItems(active_ports)
                port_ui.comboBox.setCurrentIndex(0)
            if notFirstTry == True:
                port_ui.label.setText(port+" not valid.\n Choose another port:")
            result = serDialog.exec_()
            
            print("ser diag done", result)
            if result ==1:
                port = str(port_ui.comboBox.currentText())#get new name of port here
                try:
                    ser = serial.Serial(port = port,
                        baudrate = 9600,
                        bytesize = serial.EIGHTBITS,
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        timeout = 10)
                except serial.SerialException as e: 
                    print(str(e))
                    print("wrong port")
                    notFirstTry = True
                else:
                    if ser.isOpen():
                        print("%s is a valid port" % ser.name)
                        ser.close()
                        return port
            if result ==0:
                print("canceled, please close terminal")
                break   
        return "abort"
        

    
    
################   The program:        
def main():
    app = QApplication(sys.argv)#makes a QtGui thing
    #list of before and after values:
    #[name, zeroOrSpan, beforeVal, afterVal],[],[]...
    beforeAfterList = [["name", "parameter", "old", "sent", "new"]]
    
    ###Start UI with some defaults:
    #defaultNameList = ["Data0","Data1", "Data2","Data3","Data4", "Data5", "Data6","Data7", "Data8","Data9","Data10", "Data11", "Data12","Data13","Data14", "Data15","Data16","Data17", "Data18", "Data19","Data20", "Data20","Data22","Data23", "Data24", "Data25","Data26","Data27","Data28", "Data29", "Data30", "Data31","Data32","Data33","Data34", "Data35", "Data36", "Data37","Data38","Data39","Data40", "Data41", "Data42","Data043","Data44", "Data45","Data46","Data47", "Data48","Data49","Data50"]
    #defaultNameList = ["Data0","Data1", "Data2","Data3","Data4", "Data5"]
    defaultNameList = []
    if "time" in defaultNameList: defaultNameList.remove("time")
    if "seconds" in defaultNameList: defaultNameList.remove("seconds")
    if "headID" in defaultNameList: defaultNameList.remove("headID")
    try:
        defaultNameList[-1] = defaultNameList[-1].rstrip()
    except: print("no items in list")
    
    serialComClient = ThreadedClient()#create an instance of thread client
    serialComClient.makeMainWindow(defaultNameList)#make and run the main window
    print("main window started")

    ####get serial port UI:
    serialPort = connectSerPort()
    if serialPort == "abort": 
        #sys.exit(app.exec_()) # give up
        #go on to main windo w/o connecting
        pass
        
    else:    
        ####Start background logging thread
        serialComClient.startThread()#starts the logging thread
        serialComClient.queueSend.put(str(serialPort))# "send port", serialPort, "to thread"
        

    sys.exit(app.exec_())
    
if __name__=='__main__':
    main()
    



