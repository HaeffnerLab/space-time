'''
### BEGIN NODE INFO
[info]
name = RIGOL_DG4062_MODULATION
version = 1.0
description =
instancename = RIGOL_DG4062_MODULATION

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = RIGOL_DG4062_MODULATION

from labrad.server import LabradServer, setting, inlineCallbacks

#import usb
import usbtmc
import numpy as np
from matplotlib import pyplot as plt
import time

#SERVERNAME = 'RIGOL DG4062'
#SIGNALID = 190234 ## this needs to change


class RIGOL_DG4062_MODULATION(LabradServer):
    name = 'RIGOL_DG4062_MODULATION'
    instr = None
    
    @inlineCallbacks
    def initServer(self):
        idProduct = 0x1ab1
        idVendor = 0x0641
        iSerialNumber = 'DG4E170900409'

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
        yield self.write(self.instr,'PHAS:SYNC')

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
                        
   
    def make_modulation(self,ramp_up_time, start_hold,ramp_down_time,end_hold): #in s
        
        #makes string with values to form arbitrary wave form. 
        # amplitude ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        num_points = 7000 #(limit ~8000)
        total_time = ramp_up_time + start_hold+ ramp_down_time+end_hold
        
        ramp_up_points = round(num_points*ramp_up_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        ramp_down_points = round(num_points*ramp_down_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf =[]
        for i in range(0,int(ramp_up_points)+1):
            awf = np.append(awf,-1.+2*float(i)/ramp_up_points)
        awf = np.append(awf,np.ones(start_points))
        for i in range(0,int(ramp_down_points)+1):
            awf = np.append(awf,1.-2*float(i)/ramp_down_points)
        awf = np.append(awf, -np.ones(end_points))
                   
        out_str = ''
        for el in awf:
            out_str  = out_str + str(round(el,8)) +','
        out_str = out_str[:-1]
        
        return out_str

    
    @setting(10, "Program Modulation", ramp_up_time = 'v', start_hold = 'v', ramp_down_time = 'v',end_hold = 'v')
    def program_modulation(self, c, ramp_up_time, start_hold,ramp_down_time,end_hold): #in ms
        ramp_up_time = ramp_up_time * 1e-3
        start_hold = start_hold * 1e-3
        ramp_down_time = ramp_down_time * 1e-3
        end_hold = end_hold * 1e-3 
        total_time = ramp_up_time + start_hold +ramp_down_time+end_hold
        
        mod_wf = self.make_modulation(ramp_up_time, start_hold,ramp_down_time,end_hold)        

        #print mod_wf

        yield self.write(self.instr,':SOUR1:APPL:USER')

        yield self.write(self.instr,':SOUR1:DATA VOLATILE,' + mod_wf)
        time.sleep(2)

        yield self.set_amplitude(c, 1, 6.6) 
        yield self.write(self.instr,':SOUR1:VOLT:OFF -0.15')
        yield self.write(self.instr,':SOUR1:FUNC:ARB:FREQ ' +str(1/total_time))
        yield self.write(self.instr,':SOUR1:BURS ON')
        yield self.write(self.instr,':SOUR1:BURS:MODE TRIG')       
        yield self.write(self.instr,':SOUR1:BURS:TRIG:SOUR EXT') 
        yield self.write(self.instr,':SOUR1:BURS:NCYC 1')
        yield self.set_state(c,1,1)
        

        
__server__ = RIGOL_DG4062_MODULATION()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
