'''
### BEGIN NODE INFO
[info]
name = RIGOL_DG4062_ROTATION
version = 1.0
description =
instancename = RIGOL_DG4062_ROTATION

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = RIGOL_DG4062_ROTATION

from labrad.server import LabradServer, setting, inlineCallbacks

#import usb
import usbtmc
import numpy as np
from matplotlib import pyplot as plt
import time

#SERVERNAME = 'RIGOL DG4062_ROTATION'
#SIGNALID = 190234 ## this needs to change


class RIGOL_DG4062_ROTATION(LabradServer):
    name = 'RIGOL_DG4062_ROTATION'
    instr = None
    
    @inlineCallbacks
    def initServer(self):
        idProduct = 0x1ab1
        idVendor = 0x0641        

        #iSerialNumber = 'DG4D152500730'

        #iSerialNumber = 'DG4D152500738'
        iSerialNumber = 'DG4D152500730'

        try:
            self.instr = usbtmc.Instrument(idProduct,idVendor,iSerialNumber)
            print "Successfully connected"
        except:
            print "Could not connect"
        
        #initialize off
        yield self.write(self.instr,':OUTPut1:STATe OFF')
        yield self.write(self.instr,':OUTPut2:STATe OFF')

    @inlineCallbacks
    def ask(self, instr, q):
        try:
            yield instr.ask(q)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    @inlineCallbacks
    def write(self, instr, q):
        try:
            yield instr.write(q)# + ' \n')
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    @inlineCallbacks
    def read(self, instr, q):
        try:
            yield instr.read(q)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)
    
    
    @setting(0, "Set State", channel = 'i', state = 'i')
    def set_state(self, c, channel, state):
        if state == 1:
            yield self.write(self.instr,':OUTPut' +str(channel) + ':STATe ' + 'ON')
        if state == 0:
            yield self.write(self.instr,':OUTPut' +str(channel) + ':STATe ' + 'OFF')

    @setting(1, "Get State", channel = 'i')
    def get_state(self, c, channel):
        yield self.ask(self.instr,':OUTPut' +str(channel) + ':STATe?')

    @setting(2, "Set Freq", channel = 'i', freq = 'v')
    def set_freq(self, c, channel, freq):
        yield self.write(self.instr,'SOURce'+str(channel) +':FREQuency:FIXed ' + str(freq))

    @setting(3, "Get Freq", channel = 'i')
    def get_freq(self, c, channel):
        yield self.ask(self.instr,'SOURce'+str(channel) +':FREQuency:FIXed?')

    @setting(4, "Set Phase", channel = 'i', phase = 'v')        
    def set_phase(self, c, channel, phase):
        if not 0<=phase<=360:
            phase = phase % 360
        yield self.write(self.instr,'SOURce' +str(channel) + ':PHASe ' + str(phase))

    @setting(5, "Get Phase", channel = 'i')
    def get_phase(self, c, channel):
        yield self.ask(self.instr,'SOURce' +str(channel) + ':PHASe?')

    @setting(6, "Sync Phases")   
    def sync_phases(self, c):
        yield self.write(self.instr,':SOUR1:PHAS:INIT')
        yield self.write(self.instr,':SOUR2:PHAS:INIT')

    @setting(7, "Set Amplitude", channel = 'i', amplitude = 'v')    
    def set_amplitude(self, c, channel,amplitude):
        yield self.write(self.instr,':SOUR'+str(channel)+ ':VOLT ' + str(amplitude))

    @setting(8, "Get Amplitude", channel = 'i')    
    def get_amplitude(self, c, channel):
        yield self.ask(self.instr,':SOUR'+str(channel)+ ':VOLT?')
        
    @setting(9, "To Sine", channel = 'i')        
    def to_sine(self, c, channel):
        yield self.write(self.instr,':SOUR'+str(channel)+':BURS:STAT OFF')
        yield self.write(self.instr,':SOUR' + str(channel) + ':APPL:SIN')

    @setting(10, "Unmodulate")
    def unmodulate(self,c):
        yield self.write(self.instr,':SOUR1:MOD:STAT OFF')
        yield self.write(self.instr,':SOUR2:MOD:STAT OFF')
     
    @setting(11, "rotation", drive_frequency = 'v', amplitude = 'v')
    def rotation(self, c, drive_frequency, amplitude): #in kHz
        drive_frequency = drive_frequency * 1e3


        yield self.to_sine(c,1)
        yield self.to_sine(c,1)
        yield self.set_freq(c,1,drive_frequency)
        yield self.set_freq(c,2,drive_frequency)
        yield self.set_phase(c,1,0)
        yield self.set_phase(c,2,90)

        yield self.set_amplitude(c, 1, amplitude)
        yield self.set_amplitude(c, 2, amplitude)

        yield self.set_state(c,1,1)
        yield self.set_state(c,2,1)
        yield self.sync_phases(c)

        yield self.write(self.instr, 'SOUR1:MOD:STAT ON')
        yield self.write(self.instr, 'SOUR2:MOD:STAT ON')
        yield self.write(self.instr, 'SOUR1:MOD:TYPE AM')
        yield self.write(self.instr, 'SOUR2:MOD:TYPE AM')
        yield self.write(self.instr, 'SOUR1:MOD:AM:SOUR EXT')
        yield self.write(self.instr, 'SOUR2:MOD:AM:SOUR EXT')


        
__server__ = RIGOL_DG4062_ROTATION()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
