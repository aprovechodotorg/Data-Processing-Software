#import /usr/share/pyshared/PyQt4/uic/pyuic
#/usr/share/pyshared/PyQt4/uic/pyuic.py -x mainwindow.ui -o mainwindow_ui.py

import subprocess
from subprocess import call
import os

print ("compile main .ui:",)
call("pyuic5 -x MainWindow.ui -o MainWindow_ui.py", shell=True) 
print ("done.")


print ("compile serialPort.ui:",)
call("pyuic5 -x serialPort.ui -o serialPort_ui.py", shell=True) 
print ("done")

print ("compile CandD.ui:",)
call("pyuic5 -x CandD.ui -o CandD_ui.py", shell=True) 
print ("done")

print ("compile Notes.ui:",)
call("pyuic5 -x Notes.ui -o Notes_ui.py", shell=True) 
print ("done")


#os.chdir("./graphics")

print ("compile icons:",)
call("pyrcc5 "+"./graphics/pics.qrc "+"-o pics_rc.py", shell=True) 
print ("done.")


#os.chdir("..")

#Note: to get svg to work in windows:
#In application directory, create /imageformats/ directory and put qsvg4.dll



