#!/usr/bin/python
#
# Queues for buffering commands to various pieces
# of hardware. These queues are based on PyQt threads.
# They are currently implemented for:
#
# Coherent Cube405 laser connected via serial port.
#
# Crystal Technologies AOTF connected via USB.
#
# National Instruments card installed in the computer.
#
# Hazen 6/09
#

from PyQt4 import QtCore

#
# Remove settings that apply to the current channel. This way
# when you move the slider and generate 100 events only the last
# one gets acted on, but pending events for other channels are not lost.
#
def removeChannelDuplicates(queue, channel):
    final_queue = []
    for item in queue:
        if item[1] == channel:
            continue
        final_queue.append(item)
    return final_queue


#
# Cube communication thread.
#
# This "buffers" communication with a Coherent cube laser.
#
# All communication with a cube should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#
class QCubeThread(QtCore.QThread):
    def __init__(self, port = None, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.cube_mutex = QtCore.QMutex()
        self.running = 1

        import coherent.cube405 as cube405
        if port:
            self.cube = cube405.Cube405(port)
        else:
            self.cube = cube405.Cube405()
        if not(self.cube.getStatus()):
            self.cube.shutDown()
            self.cube = 0

    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, amplitude])
        self.buffer_mutex.unlock()

    def analogModulationOff(self):
        self.cube_mutex.lock()
        if self.cube:
            self.cube.setExtControl(0)
        self.cube_mutex.unlock()

    def analogModulationOn(self):
        self.cube_mutex.lock()
        if self.cube:
            self.cube.setExtControl(1)
        self.cube_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        self.cube_mutex.lock()
        if self.cube:
            if on:
                self.cube.setPower(amplitude)
            else:
                self.cube.setPower(0)
        else:
            if on:
                print "CUBE: ", amplitude
            else:
                print "CUBE: ", 0
        self.cube_mutex.unlock()

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.cube:
            self.cube.shutDown()

#
# Stradus communication thread.
#
# This "buffers" communication with a Stradus laser.
#
# All communication with the Stradus should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#

class QStradusThread(QtCore.QThread):
    def __init__(self, port, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.stradus_mutex = QtCore.QMutex()
        self.running = 1

        import vortran.stradus as stradus
        self.stradus = stradus.Stradus(port)
        if not(self.stradus.getStatus()):
            self.stradus.shutDown()
            self.stradus = 0

    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, amplitude])
        self.buffer_mutex.unlock()

    def analogModulationOff(self):
        self.stradus_mutex.lock()
        if self.stradus:
            self.stradus.setExtControl(0)
        self.stradus_mutex.unlock()

    def analogModulationOn(self):
        self.stradus_mutex.lock()
        if self.stradus:
            self.stradus.setExtControl(1)
        self.stradus_mutex.unlock()

    def pulseModeOff(self):
        self.stradus_mutex.lock()
        if self.stradus:
            print "pulseMode off"
            self.stradus.setPulseMode(0)
        self.stradus_mutex.unlock()

    def pulseModeOn(self):
        self.stradus_mutex.lock()
        if self.stradus:
            print "pulseMode on"
            self.stradus.setPulseMode(1)
        self.stradus_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        print "setAmplitude"
        self.stradus_mutex.lock()
        if self.stradus:
            if on:
                self.stradus.setPower(amplitude)
            else:
                self.stradus.setPower(0)
        else:
            if on:
                print "STRADUS: ", amplitude
            else:
                print "STRADUS: ", 0
        self.stradus_mutex.unlock()

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.stradus:
            print "stopThread"
            self.stradus.shutDown()


## QSerialComm
#
# Generic serial device communication.
#
# This "buffers" communication with a serial device.
#
class QSerialComm(QtCore.QThread):

    ## __init__
    #
    # @param sdevice A serial device object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, sdevice, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.sdevice_mutex = QtCore.QMutex()
        self.running = 1

        self.sdevice = sdevice
        if not (self.sdevice.getStatus()):
            self.sdevice.shutDown()
            self.sdevice = False

    ## run
    #
    # Processes the most recent request in the queue, deletes all the others.
    #
    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    ## addRequest
    #
    # Add a request to the command queue.
    #
    # @param on True/False.
    # @param amplitude The desired amplitude.
    #
    def addRequest(self, on, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, amplitude])
        self.buffer_mutex.unlock()

    ## setAmplitude
    #
    # Directly set the amplitude.
    #
    # @param on True/False.
    # @param amplitude The desired amplitude.
    #
    def setAmplitude(self, on, amplitude):
        pass

    ## stopThread
    #
    # Stop the command processing queue and shutdown the serial device.
    #
    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.sdevice:
            self.sdevice.shutDown()

            
## QSerialLaserComm
#
# Serial port controlled laser.
#
# This "buffers" communication with a laser.
#
# All communication with the device should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#
class QSerialLaserComm(QSerialComm):

    ## __init__
    #
    # @param sdevice A serial device object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, sdevice, parent = None):
        QSerialComm.__init__(self, sdevice, parent)

    ## analogModulationOff
    #
    # Turn off the lasers analog modulation feature.
    #
    def analogModulationOff(self):
        self.sdevice_mutex.lock()
        if self.sdevice:
            self.sdevice.setExtControl(0)
        self.sdevice_mutex.unlock()

    ## analogModulationOn
    #
    # Turn on the lasers analog modulation feature.
    #
    def analogModulationOn(self):
        self.sdevice_mutex.lock()
        if self.sdevice:
            self.sdevice.setExtControl(1)
        self.sdevice_mutex.unlock()

    ## setAmplitude
    #
    # Set the power output of the laser.
    #
    # @param on True/False
    # @param amplitude The desired output power of the laser.
    #
    def setAmplitude(self, on, amplitude):
        self.sdevice_mutex.lock()
        if self.sdevice:
            if on:
                self.sdevice.setPower(amplitude)
                print "commandQueues.py:: Laser to amplitude: ", amplitude
            else:
                self.sdevice.setPower(0)
        else:
            if on:
                print "commandQueues.py:: LASER: ", amplitude
            else:
                print "commandQueues.py:: LASER: ", 0
        self.sdevice_mutex.unlock()



#------------------------------------test thread below--------------------------------------#

class QSapphTESTThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.sapphire_mutex = QtCore.QMutex()

        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol
        #self.addRequest(1,"PCIe-6353",0, 9.1)       # this command sets the "baseline" AOM voltage (AO0)
        self.running = 1
            
    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, board, channel, voltage):
        #self.buffer_mutex.lock()
        task = self.nicontrol.VoltageOutput(board, channel)
        if on:
##            print "TEST: not outputting voltage"
            print "writing voltage = " + str(voltage) + " to analog-out-" + str(channel)
            task.outputVoltage(voltage)
##        else:
##            print "writing voltage = 0" + " to analog-out-" + str(channel)
##            task.outputVoltage(0.0)
        task.clearTask()
        #self.buffer_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        # setAmplitude writes to analog out 1 regardless of shutter on/off state
        
        print "AOM: setting amplitude"
        # Not buffered
        #self.sapphire_mutex.lock()
        #task = self.nicontrol.VoltageOutput("PCIe-6323", 1)
        if on:
            self.addRequest(1, "PCIe-6353", 0, amplitude) #Change 3rd arg. to 0 (on analog output 0)
        #task.outputVoltage(amplitude)
        else:
            self.addRequest(1, "PCIe-6353", 0, 0)
            #task.outputVoltage(amplitude)
        #self.stradus_mutex.unlock()
        #task.clearTask()

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
##        if self.sapphire:
##            print "stopThread"
##            self.stradus.shutDown()

#---------------------test thread above --------------------------------------#

#
# QThorlabsLED Thread below
#
class QThorlabsLEDThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.sapphire_mutex = QtCore.QMutex()

        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol
        #self.addRequest(1,"PCIe-6323", channel)
        self.running = 1
            
    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, board, channel, voltage):
        #self.buffer_mutex.lock()
        task = self.nicontrol.VoltageOutput(board, channel)
        if on:
            print "writing voltage = " + str(voltage) + " to analog-out-" + str(channel)
            task.outputVoltage(voltage)
        task.clearTask()
        #self.buffer_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        # setAmplitude writes to analog out 1 regardless of shutter on/off state
        
        print "AOM: setting amplitude"
        #self.sapphire_mutex.lock()
        #task = self.nicontrol.VoltageOutput("PCIe-6323", 1)
        if on:
            self.addRequest(1, "PCIe-6353", 1, amplitude)
        else:
            self.addRequest(1, "PCIe-6353", 1, 0)
        #self.stradus_mutex.unlock()

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
##        if self.sapphire:
##            print "stopThread"
##            self.stradus.shutDown()


#
# Generic AOTF communication thread
#
# This "buffers" communication with an AOTF, that doesn't
# respond very quickly to requests. It sends the most recent request
# and discards any backlog of older requests. It is necessary to
# keep the slider moving "smoothly" when the user tries to drag it
# up and down w/ the AOTF on.
#
# All communication with AOTF should go through this thread to avoid
# two processes trying to talk to the AOTF at the same time.
#
class QAOTFThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.aotf_mutex = QtCore.QMutex()
        self.running = 1
        self.aotf = False

    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, channel, amplitude] = self.buffer.pop()
                self.buffer = removeChannelDuplicates(self.buffer, channel)
                self.buffer_mutex.unlock()
                self.setAmplitude(on, channel, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, channel, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, channel, amplitude])
        self.buffer_mutex.unlock()

    def analogModulationOff(self):
        pass

    def analogModulationOn(self):
        pass

    def fskOnOff(self, channel, on):
        pass

    def setAmplitude(self, on, channel, amplitude):
        pass

    def setFrequencies(self, channel, frequencies):
        pass

    def setFrequency(self, channel, frequency):
        pass

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.aotf:
            self.aotf.shutDown()
            self.aotf = 0


#
# AA Opto-Electronics AOTF communication thread.
#
class QAAAOTFThread(QAOTFThread):
    def __init__(self, parent = None):
        QAOTFThread.__init__(self, parent)

        import aaopto.AOTF as AOTF
        self.aotf = AOTF.AOTF()
        if not(self.aotf.getStatus()):
            self.aotf = 0

    def setAmplitude(self, on, channel, amplitude):
        self.aotf_mutex.lock()
        if self.aotf:
            if on:
                if (amplitude > 0):
                    self.aotf.channelOnOff(channel, True)
                else:
                    self.aotf.channelOnOff(channel, False)
                if (amplitude > 13):
                    power = (float(amplitude)-15.0)/10.0 - 7.0
                    self.aotf.setAmplitude(channel, power)
                    self.aotf.offsetFrequency(channel, 0.0)
                else:
                    freq_offset = 0.65 - float(amplitude)/20.0
                    self.aotf.setAmplitude(channel, -7.4)
                    self.aotf.offsetFrequency(channel, freq_offset)
            else:
                self.aotf.channelOnOff(channel, False)
        self.aotf_mutex.unlock()

    def setFrequency(self, channel, frequency):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequency(channel, frequency)
        self.aotf_mutex.unlock()


#
# Crystal Technologies AOTF communication thread.
#
class QCTAOTFThread(QAOTFThread):
    def __init__(self, parent = None):
        QAOTFThread.__init__(self, parent)

        import crystalTechnologies.AOTF as AOTF
        self.aotf = AOTF.AOTF()
        if not(self.aotf.getStatus()):
            self.aotf = 0

    def analogModulationOff(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOff()
        self.aotf_mutex.unlock()

    def analogModulationOn(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOn()
        self.aotf_mutex.unlock()

    def fskOnOff(self, channel, on):
        self.aotf_mutex.lock()
        if self.aotf:
            if on:
                self.aotf.fskOn(channel)
            else:
                self.aotf.fskOff(channel)
        self.aotf_mutex.unlock()

    def setAmplitude(self, on, channel, amplitude):
        self.aotf_mutex.lock()
        if self.aotf:
            if on:
                self.aotf.setAmplitude(channel, amplitude)
            else:
                self.aotf.setAmplitude(channel, 0)
        else:
            print "AOTF:"
            if on:
                print "\t", channel, amplitude
            else:
                print "\t", channel, 0
        self.aotf_mutex.unlock()

    def setFrequencies(self, channel, frequencies):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequencies(channel, frequencies)
        self.aotf_mutex.unlock()

    def setFrequency(self, channel, frequency):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequency(channel, frequency)
        self.aotf_mutex.unlock()



#
# National Instruments analog communication. This is so
# fast that we don't even bother to buffer.
#

class QNiAnalogComm():
    def __init__(self, on_voltage):
        self.filming = 0
        self.on_voltage = on_voltage
        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol

    def addRequest(self, on, board, channel):
        if not self.filming:
            task = self.nicontrol.VoltageOutput(board, channel)
            if on:
                task.outputVoltage(self.on_voltage)
            else:
                task.outputVoltage(0.0)
            task.clearTask()

    def setFilming(self, flag):
        self.filming = flag

#
# National Instruments digital communication. We ignore
# the filming flag as the shutters should not be used
# to modulate the light in sync with the camera. They
# are used to backup whatever we are using to actaully
# do the light modulation.
#

class QNiDigitalComm():
    def __init__(self):
        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol

    def setShutter(self, on, board, channel):
        task = self.nicontrol.DigitalOutput(board, channel)
        if on:
            task.output(True)
        else:
            task.output(False)
        task.clearTask()

    # Copied from analog class. Seems to be needed. 09/11 Joerg
    def setFilming(self, flag):
        self.filming = flag

#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
