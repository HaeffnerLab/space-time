'''
### BEGIN NODE INFO
[info]
name = RIGOL_DG1032Z
version = 1.0
description =
instancename = RIGOL_DG1032Z

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = RIGOL_DG1032Z

from labrad.server import LabradServer, setting, inlineCallbacks

from socket import *
import select
import numpy as np
from matplotlib import pyplot as plt
import time

#SERVERNAME = 'RIGOL DG4062'
#SIGNALID = 190234 ## this needs to change


class RIGOL_DG1032Z(LabradServer):
    name = 'RIGOL_DG1032Z'
    instr = None
    
    @inlineCallbacks
    def initServer(self):
        #idProduct = 0x1ab1
        #idVendor = 0x0642
        #iSerialNumber = 'DG1ZA192101818'
        serverHost = '192.168.169.182' #IP address of the awg
        serverPort = 5555 #random number over 1024
        self.instr = socket(AF_INET, SOCK_STREAM)

        self.samp_rate = 2e6 #max 2e8 or 2e6 total  points

        try:
            self.instr.connect((serverHost, serverPort))
            self.instr.settimeout(2)
            print "Successfully connected"
        except:
            print "Could not connect"
        
        #initialize off
        yield self.write(self.instr,':OUTPut1:STATe OFF')
        yield self.write(self.instr,':OUTPut2:STATe OFF')

    @inlineCallbacks
    def ask(self, instr, q):
        try:
            yield instr.send(q + " \n")
            data = yield self.instr.recv(50)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    @inlineCallbacks
    def write(self, instr, q):
        try:
            yield instr.send(q+ "\n")
            #time.sleep(1)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    @inlineCallbacks
    def read(self, instr, q):
        try:
            data = yield instr.recv(50)
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

        total_time = start_hold+amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time #(limit ~16000)
        
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
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time #(limit ~16000)
        
        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf =[]
        awf = np.ones(start_points+int(freq_ramp_points))
        for i in range(0,int(amp_ramp_points)+1):
            awf = np.append(awf,1.-float(i)/amp_ramp_points)
        awf = np.append(awf, np.zeros(end_points))
        
        #definte frequency curve
        frequency = []
        #frequency = np.zeros(start_points)
        for i in range(0,int(freq_ramp_points)+1):
            frequency = np.append(frequency,float(i)*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(int(amp_ramp_points)+end_points+start_points))
        
        time_step = total_time/float(num_points)              
        for i,el in enumerate(awf):
            
            if i<freq_ramp_points:
                if channel == 1:
                    awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step)
                if channel == 2:
                    awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step+np.pi/2.)
            else:
                i_0 = int(freq_ramp_points)
                #phi_0 = time_step*i_0*frequency[i_0]/2.0
                
                phi_0= 2.*np.pi*((frequency[i_0])*(i_0)*time_step)
                     
                if channel == 1:
                    awf[i] = el*np.sin(phi_0+2.*np.pi*frequency[i]*(i-i_0)*time_step)
                if channel == 2:
                    awf[i] = el*np.sin(phi_0+2.*np.pi*frequency[i]*(i-i_0)*time_step+np.pi/2.)
        
        
        #for i in range(0,len(awf)):
        #    awf[i] = round(awf[i],8)
        #plt.plot(awf,'o')
        #plt.show()
            
        
        #build the string to be sent to the awg

        packet_length = 1100 #(max 16k)
        out_str = []
        num_full_packets = int(len(awf)/float(packet_length))

        for i in range(0,num_full_packets):
            packet_str = ''
            for j in range(packet_length*i,packet_length*(i+1)):
                print j
                el = awf[j]
                el = hex(int(16384*el-1)).split('x')[-1]
                packet_str  = packet_str + el + ','
                #out_str  = out_str + str(round(el,8)) +','
            out_str.append((packet_length,packet_str[:-1]))

        for j in range(packet_length*num_full_packets,len(awf)):
            packet_str = ''
            print j
            el = awf[j]
            el = hex(int(16384*el-1)).split('x')[-1]
            packet_str  = packet_str + el + ','
            #out_str  = out_str + str(round(el,8)) +','
            #print packet_str
        out_str.append((len(awf)-packet_length*(num_full_packets), packet_str[:-1]))

        return out_str
    
    
    @setting(10, "Program Awf", start_hold = 'v',freq_ramp_time = 'v', amp_ramp_time = 'v',end_hold = 'v',vpp = 'v', sin_freq = 'v')
    def program_awf(self, c, start_hold,freq_ramp_time,amp_ramp_time,end_hold,vpp,sin_freq): #in ms and kHz
        start_hold = start_hold * 1e-3
        amp_ramp_time = amp_ramp_time * 1e-3
        end_hold = end_hold * 1e-3 
        sin_freq = sin_freq * 1e3
        freq_ramp_time = freq_ramp_time*1e-3
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold

        wf_str1 = self.make_awf_with_freq_ramp(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,1)
        wf_str2 = self.make_awf_with_freq_ramp(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,2)        

        yield self.write(self.instr,':SOUR1:APPL:USER')
        yield self.write(self.instr,':SOUR2:APPL:USER')

        yield self.write(self.instr,':SOUR1:FUNC:ARB:MODE SRAT')
        yield self.write(self.instr,':SOUR2:FUNC:ARB:MODE SRAT')

        yield self.write(self.instr,':SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))
        yield self.write(self.instr,':SOUR2:FUNC:ARB:SRAT ' + str(self.samp_rate))

        time.sleep(1)

        for i in range(0,len(wf_str1)-1):
            yield self.write(self.instr,':SOUR1:TRAC:DATA:DAC16 VOLATILE,CON,#' + str(len(str(wf_str1[i][0]))) + str(wf_str1[i][0]) + wf_str1[i][1])
            print ':SOUR1:TRAC:DATA:DAC16 VOLATILE,CON,#' + str(len(str(wf_str1[i][0]))) + str(wf_str1[i][0]) + wf_str1[i][1]
        yield self.write(self.instr,':SOUR1:TRAC:DATA:DAC16 VOLATILE,END,#' + str(len(str(wf_str1[-1][0]))) + str(wf_str1[-1][0]) + wf_str1[-1][1])
        
        #for i in range(0,len(wf_str2)-1):
        #    yield self.write(self.instr,':SOUR2:TRAC:DATA:DAC16 VOLATILE,CON,#' + str(len(str(wf_str2[i][0]))) + str(wf_str2[i][0]) + wf_str2[i][1])
        #yield self.write(self.instr,':SOUR2:TRAC:DATA:DAC16 VOLATILE,END,#' + str(len(str(wf_str2[-1][0]))) + str(wf_str2[-1][0]) + wf_str2[-1][1])    

        #yield self.set_amplitude(c, 1, vpp)
        #yield self.set_amplitude(c, 2, vpp)
            #yield self.write(self.instr,':SOUR1:FUNC:ARB:FREQ ' +str(1/total_time))
            #yield self.write(self.instr,':SOUR2:FUNC:ARB:FREQ ' +str(1/total_time))
        #yield self.write(self.instr,':SOUR1:BURS ON')
        #yield self.write(self.instr,':SOUR2:BURS ON')
        #yield self.write(self.instr,':SOUR1:BURS:MODE TRIG')
        #yield self.write(self.instr,':SOUR2:BURS:MODE TRIG')        
        #yield self.write(self.instr,':SOUR1:BURS:TRIG:SOUR EXT') 
        #yield self.write(self.instr,':SOUR2:BURS:TRIG:SOUR EXT')
        #yield self.write(self.instr,':SOUR1:BURS:NCYC 1')
        #yield self.write(self.instr,':SOUR2:BURS:NCYC 1')
        yield self.set_state(c,1,1)
        yield self.set_state(c,2,1)
        yield self.sync_phases(c)
        

        
__server__ = RIGOL_DG1032Z()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
