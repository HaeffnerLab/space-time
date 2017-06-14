'''
### BEGIN NODE INFO
[info]
name = RIGOL_DG4062
version = 1.0
description =
instancename = RIGOL_DG4062

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = RIGOL_DG4062

from labrad.server import LabradServer, setting, inlineCallbacks

import usb
import usbtmc
import numpy as np

#SERVERNAME = 'RIGOL DG4062'
#SIGNALID = 190234 ## this needs to change


class RIGOL_DG4062(LabradServer):
    name = 'RIGOL_DG4062'
    instr = None
    
    @inlineCallbacks
    def initServer(self):
        idProduct = 0x1ab1
        idVendor = 0x0641
        iSerialNumber = 'DG4E170900409'
        try:
            self.instr = usbtmc.Instrument(idProduct,idVendor)
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
            yield instr.write(q)
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
                        
    #@setting(10, "Make Awf", start_hold = 'v',ramp_time = 'v',end_hold = 'v',sin_freq = 'v')
    def make_awf(self, start_hold,ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        #hold pinned and rotatings, amp ramp down, hold no rotation

        num_points = 10000 #(limit ~16000)
        total_time = start_hold+ramp_time+end_hold
        
        ramp_points = round(num_points*ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        end_points = int(round(num_points*end_hold/total_time))
        
        awf =[]
        awf = np.ones(start_points)
        for i in range(0,int(ramp_points)+1):
            awf = np.append(awf,1.-float(i)/ramp_points)
        awf = np.append(awf, np.zeros(end_points))

        time_step = total_time/float(num_points)              
        for i,el in enumerate(awf):
            if channel == 1:
                awf[i] = el*np.sin(2.*np.pi*sin_freq*i*time_step)
            if channel == 2:
                awf[i] = el*np.sin(2.*np.pi*sin_freq*i*time_step+np.pi/2.)
        
        out_str = ''
        for el in awf:
            out_str  = out_str + str(el)[:8]  +','
        out_str = out_str[:-1]
        
        print out_str
        
        return out_str
    
    def make_awf_with_freq_ramp(self, start_hold,freq_ramp_time,amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        #hold pinned, freq ramp up, amplitude ramp down, hold with no pinning

        num_points = 10000 #(limit ~16000)
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold
        
        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        end_points = int(round(num_points*end_hold/total_time))
        
        awf =[]
        awf = np.ones(start_points+int(freq_ramp_points))
        for i in range(0,int(amp_ramp_points)+1):
            awf = np.append(awf,1.-float(i)/amp_ramp_points)
        awf = np.append(awf, np.zeros(end_points))
            
        frequency = []
        frequency = np.zeros(start_points)
        for i in range(0,int(freq_ramp_points)+1):
            frequency = np.append(frequency,float(i)*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(int(amp_ramp_points)+end_points))
        
        time_step = total_time/float(num_points)              
        for i,el in enumerate(awf):
            if channel == 1:
                awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step)
            if channel == 2:
                awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step+np.pi/2.)
        
        out_str = ''
        for el in awf:
            out_str  = out_str + str(el)[:8] +','
        out_str = out_str[:-1]
        
        return out_str
    
    def make_awf_freq_ramp_heating(self, start_hold,freq_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        #hold pinned, freq ramp up, then down, then hold pinned

        num_points = 10000 #(limit ~16000)
        total_time = start_hold+2.*freq_ramp_time +end_hold
        
        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        end_points = int(round(num_points*end_hold/total_time))
        
        awf =[]
        awf = np.ones(start_points+2*int(freq_ramp_points))
        awf = np.append(awf, np.ones(end_points))
            
        frequency = []
        
        frequency = np.zeros(start_points)        
        for i in range(0,int(freq_ramp_points)+1):
            frequency = np.append(frequency,float(i)*sin_freq/(float(freq_ramp_points)))
        for i in range(0,int(freq_ramp_points)+1):
            frequency = np.append(frequency,(float(freq_ramp_points)-float(i))*sin_freq/(float(freq_ramp_points)))
        frequency = np.append(frequency, np.zeros(end_points))
        
       
        time_step = total_time/float(num_points)              
        for i,el in enumerate(awf):
            if i<start_points:
                if channel == 1:
                    awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step)
                if channel == 2:
                    awf[i] = el*np.cos(2.*np.pi*frequency[i]*i*time_step)
            elif i< start_points + int(freq_ramp_points):
                i_0 = start_points
                phi_0 = time_step*i_0*frequency[i_0]
                if channel == 1:
                    awf[i] = el*np.sin(phi_0 + 2.*np.pi*(frequency[i]*(i-i_0)*time_step/2.0))
                if channel == 2:
                    awf[i] = el*np.cos(phi_0 + 2.*np.pi*(frequency[i]*(i-i_0)*time_step/2.0))  
                
                phi_next1 = phi_0 + 2.*np.pi*(frequency[i]*(i-i_0)*time_step/2.0)    
                
            elif i< start_points + 2*int(freq_ramp_points):
                i_0 = start_points+int(freq_ramp_points)
                f_0 = frequency[i_0]
                phi_0 = phi_next1
                
                if channel == 1:
                    awf[i] = el*np.sin(phi_0 + 2.*np.pi*((f_0+frequency[i])*(i-i_0)*time_step/2.0))
                if channel == 2:
                    awf[i] = el*np.cos(phi_0 + 2.*np.pi*((f_0+frequency[i])*(i-i_0)*time_step/2.0))
                    
                phi_next2 = phi_0 + 2.*np.pi*((f_0+frequency[i])*(i-i_0)*time_step/2.0)
            else:
                i_0 = start_points+2*int(freq_ramp_points)
                f_0 = frequency[i_0]
                phi_0 = phi_next2
                
                if channel == 1:
                    awf[i] = el*np.sin(phi_0 + 2.*np.pi*((f_0+frequency[i])*(i-i_0)*time_step/2.0))
                if channel == 2:
                    awf[i] = el*np.cos(phi_0 + 2.*np.pi*((f_0+frequency[i])*(i-i_0)*time_step/2.0))
                                       
        out_str = ''
        for el in awf:
            out_str  = out_str + str(el)[:8] +','
        out_str = out_str[:-1]
        
        return out_str
    
    
    @setting(10, "Program Awf", start_hold = 'v',freq_ramp_time = 'v', amp_ramp_time = 'v',end_hold = 'v',vpp = 'v', sin_freq = 'v')
    def program_awf(self, c, start_hold,freq_ramp_time,amp_ramp_time,end_hold,vpp,sin_freq): #in ms and kHz
        start_hold = start_hold * 1e-3
        amp_ramp_time = amp_ramp_time * 1e-3
        end_hold = end_hold * 1e-3 
        sin_freq = sin_freq * 1e3
        freq_ramp_time = freq_ramp_time*1e-3
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold
     
     
        yield self.write(self.instr,':SOUR1:APPL:USER')
        yield self.write(self.instr,':SOUR2:APPL:USER')
        
       #if freq_ramp_time == 0.0:
       #     wf_str1 = self.make_awf(start_hold,amp_ramp_time,end_hold,sin_freq,1)
       #     wf_str2 = self.make_awf(start_hold,amp_ramp_time,end_hold,sin_freq,2)    
       #else:
       #     wf_str1 = self.make_awf_with_freq_ramp(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,1)
       #     wf_str2 = self.make_awf_with_freq_ramp(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,2)        

        wf_str1 = self.make_awf_freq_ramp_heating(start_hold,freq_ramp_time,end_hold,sin_freq,1)
        wf_str2 = self.make_awf_freq_ramp_heating(start_hold,freq_ramp_time,end_hold,sin_freq,2)     

        yield self.write(self.instr,':SOUR1:DATA VOLATILE,' + wf_str1)
        yield self.write(self.instr,':SOUR2:DATA VOLATILE,' + wf_str2)

        yield self.set_amplitude(c, 1, vpp)
        yield self.set_amplitude(c, 2, vpp)
        yield self.write(self.instr,':SOUR1:FUNC:ARB:FREQ ' +str(1/total_time))
        yield self.write(self.instr,':SOUR2:FUNC:ARB:FREQ ' +str(1/total_time))
        yield self.write(self.instr,':SOUR1:BURS ON')
        yield self.write(self.instr,':SOUR2:BURS ON')
        yield self.write(self.instr,':SOUR1:BURS:MODE TRIG')
        yield self.write(self.instr,':SOUR2:BURS:MODE TRIG')        
        yield self.write(self.instr,':SOUR1:BURS:TRIG:SOUR EXT') 
        yield self.write(self.instr,':SOUR2:BURS:TRIG:SOUR EXT')
        yield self.write(self.instr,':SOUR1:BURS:NCYC 1')
        yield self.write(self.instr,':SOUR2:BURS:NCYC 1')
        yield self.set_state(c,1,1)
        yield self.set_state(c,2,1)
        yield self.sync_phases(c)
        

        
__server__ = RIGOL_DG4062()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
