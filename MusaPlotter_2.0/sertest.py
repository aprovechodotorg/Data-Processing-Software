


import serial



def readFromMachine(ser,waitForString):
    OKline = False
    ser.flushInput()
    for x in range (100):
        line = ser.readline()
        print line.rstrip()
        if waitForString in line:
            OKline = True
            
            break
        #time.sleep(.1)
    return OKline


"""    
def readFromMachine(ser,waitForString):
    
    line = ""
    while True:
        #bytesToRead = ser.inWaiting()
        #if bytesToRead > 0:
            #line = line + ser.read(bytesToRead)
            character = ser.read(1000)
            print character,
    
    
    OKline = False
    stringRead = ""
    for i in range(30):
        while True:
            bytesToRead = ser.inWaiting()
            character = ser.read(bytesToRead)
            print character,
            stringRead = stringRead + character
            if character =='\n':
                #print stringRead.rstrip()
                break
        if waitForString == stringRead:
            OKline = True
            break
    return OKline
"""

ser = serial.Serial(port = '/dev/ttyS5',
                        baudrate = 9600,
                        bytesize = serial.EIGHTBITS,
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        timeout = 1)
                        
                        
print "\nPLEASE RESET MACHINE NOW\n"
        
if readFromMachine(ser,"# type cal (in 5 sec)"):#serial read wait for "# type cal (in 5 sec)"
    ser.write("cal\n")
else:
    print "faied to enter cal mode"
    sys.exit(app.exec_()) # give up
if readFromMachine(ser," enter>"): # look for enter
    print "Now can apply cal constants"
