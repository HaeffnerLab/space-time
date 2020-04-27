'''
### BEGIN NODE INFO
[info]
name = KEYSIGHT_33500B
version = 2.0
description =
instancename = KEYSIGHT_33500B

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = KEYSIGHT_33500B

from labrad.server import LabradServer, setting, inlineCallbacks
from twisted.internet.defer import DeferredLock, Deferred

from socket import *
import select
import numpy as np
from matplotlib import pyplot as plt
import struct
from warnings import warn
import time

#SERVERNAME = 'KEYSIGHT_33500B'
#SIGNALID = 190234 ## this needs to change


class KEYSIGHT_33500B(LabradServer):
    name = 'KEYSIGHT_33500B'
    instr = None
    
    def initServer(self):
        serverHost = '192.168.169.182' #IP address of the awg
        serverPort = 5025 #random number over 1024
        self.instr = socket(AF_INET, SOCK_STREAM)

        self.samp_rate = 1e7 #max 2e8 or 2e6 total  points

        try:
            self.instr.connect((serverHost, serverPort))
            self.instr.settimeout(2)
            print "Successfully connected"
        except:
            print "Could not connect"
        
        #initialize off
        self.write(self.instr,'OUTPut1:STATe OFF')
        self.write(self.instr,'OUTPut2:STATe OFF')

        self.lock = DeferredLock()

    def ask(self, instr, q):
        try:
            instr.send(q + "\n")
            data = self.instr.recv(4096)
            print data
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    def write(self, instr, q):
        try:
            instr.sendall(q+ "\n")
            #time.sleep(1)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)    

    def read(self, instr, q):
        try:
            data = instr.recv(1024)
        except AttributeError as ex:
            print 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            print 'Instrument is not connected... ' + str(ex)

    def read_error_queue(self):
        errors = []
        for _ in range(10):
            try:
                errors.append(self.ask(self.instr,"SYST:ERR?"))
            except Exception as e:
                print(e)
                break
            if errors[-1] == '+0,"No error"\n':
                errors.pop()
                break
            return errors

    @setting(0, "Set State", channel = 'i', state = 'i')
    def set_state(self, c, channel, state):
        if state == 1:
            self.write(self.instr,':OUTPut' +str(channel) + ' ON')
        if state == 0:
            self.write(self.instr,':OUTPut' +str(channel) + ' OFF')

    @setting(1, "Get State", channel = 'i')
    def get_state(self, c, channel):
        self.ask(self.instr,':OUTPut' +str(channel) + ':STATe?')

    @setting(2, "Set Freq", channel = 'i', freq = 'v')
    def set_freq(self, c, channel, freq):
        if freq == 0.0:
            freq = 1e-6
        self.write(self.instr,'SOURce'+str(channel) +':FREQuency:FIXed ' + str(freq))
        self.sync_phases(c)

    @setting(3, "Get Freq", channel = 'i')
    def get_freq(self, c, channel):
        self.ask(self.instr,'SOURce'+str(channel) +':FREQuency:FIXed?')

    @setting(4, "Set Phase", channel = 'i', phase = 'v')        
    def set_phase(self, c, channel, phase):
        if not 0<=phase<=360:
            phase = phase % 360
        self.write(self.instr,'SOURce' +str(channel) + ':PHASe ' + str(phase))
        self.sync_phases(c)

    @setting(5, "Get Phase", channel = 'i')
    def get_phase(self, c, channel):
        self.ask(self.instr,'SOURce' +str(channel) + ':PHASe?')

    @setting(6, "Sync Phases")   
    def sync_phases(self, c):
        self.write(self.instr,'PHAS:SYNC')

    @setting(7, "Set Amplitude", channel = 'i', amplitude = 'v')    
    def set_amplitude(self, c, channel,amplitude):
        self.write(self.instr,':SOUR'+str(channel)+ ':VOLT ' + str(amplitude))

    @setting(8, "Get Amplitude", channel = 'i')    
    def get_amplitude(self, c, channel):
        self.ask(self.instr,':SOUR'+str(channel)+ ':VOLT?')
        
    @setting(9, "To Sine", channel = 'i')        
    def to_sine(self, c, channel):
        self.write(self.instr,':SOUR'+str(channel)+':BURS:STAT OFF')
        self.write(self.instr,':SOUR' + str(channel) + ':APPL:SIN')
        if channel == 1:
            self.set_phase(c, channel, 0.)
        elif channel == 2:
            self.set_phase(c, channel, 90.)


    def pack_keysight_packet(self, data):
        """Constructs a binary datapacket as described in the keysight documentation:
        http://literature.cdn.keysight.com/litweb/pdf/33500-90901.pdf?id=2197440
        page 240
            Accepts - 
                data - float data array between -1 and 1
            returns -
                string - a packed binary string of the data with appropriate header"""
        
        # data has to be floats from -1 to 1,
        # numpy has a nice function which clips the data to this range
        if np.max(np.abs(data)) > 1:
            warn("Data has values outside the allowed values of -1 to 1, clipping it hard to be within range.")
        data = np.clip(data, -1, 1)
        packed_binary = struct.pack('>{}f'.format(len(data)), *data)
        binary_len = len(packed_binary)+1
        len_of_binary_len = len(str(binary_len))

        return "#{}{}{}".format(len_of_binary_len, binary_len, packed_binary)
                        
    #@setting(1, "Make Awf", freq_ramp_time = 'v', start_hold = 'v',amp_ramp_time = 'v',end_hold = 'v',sin_freq = 'v',channel='i')  
    def make_awf(self, freq_ramp_time,start_hold,amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf =[]
        awf = np.ones(start_points+int(freq_ramp_points))
        awf = np.append(awf, 1.-np.arange(int(amp_ramp_points))/amp_ramp_points)
        #slow old code
        #for i in range(0,int(amp_ramp_points)+1):
        #    awf = np.append(awf,1.-float(i)/amp_ramp_points)
        awf = np.append(awf, np.zeros(end_points))
        
        #definte frequency curve
        frequency = np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points))
        frequency = np.append(frequency, sin_freq*np.ones(int(amp_ramp_points)+end_points+start_points))
        #slow old code
        #frequency = []
        #for i in range(0,int(freq_ramp_points)+1):
        #    frequency = np.append(frequency,float(i)*sin_freq/(2.*float(freq_ramp_points)))
        #frequency = np.append(frequency, sin_freq*np.ones(int(amp_ramp_points)+end_points+start_points))


        time_step = total_time/float(num_points)
        i_0 = int(freq_ramp_points)

        ##definition through frequency ramp
        if channel == 1:
            waveform1 = np.multiply(np.sin(2*np.pi*np.multiply(frequency, range(len(awf)))*time_step), awf)
        if channel == 2:
            waveform1 = np.multiply(np.sin(2*np.pi*np.multiply(frequency, range(len(awf)))*time_step + np.pi/2.), awf)
        waveform1 = waveform1[:i_0]

        #defination after frequency ramp
        phi_0= 2.*np.pi*((frequency[i_0])*(i_0)*time_step)
        if channel == 1:
            waveform2 = np.multiply(np.sin(phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i_0))*time_step), awf)
        if channel == 2:
            waveform2 = np.multiply(np.sin(phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i_0))*time_step + np.pi/2.), awf)
        waveform2 = waveform2[i_0:]

        final_wf = np.append(waveform1,waveform2)
    
       ##too slow old code
        #for i,el in enumerate(awf):    
            # if i<freq_ramp_points:
            #     if channel == 1:
            #         awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step)
            #     if channel == 2:
            #         awf[i] = el*np.sin(2.*np.pi*frequency[i]*i*time_step+np.pi/2.)
            # else:
            #     i_0 = int(freq_ramp_points)
            #     #phi_0 = time_step*i_0*frequency[i_0]/2.0
                
            #     phi_0= 2.*np.pi*((frequency[i_0])*(i_0)*time_step)
                     
            #     if channel == 1:
            #         awf[i] = el*np.sin(phi_0+2.*np.pi*frequency[i]*(i-i_0)*time_step)
            #     if channel == 2:
            #         awf[i] = el*np.sin(phi_0+2.*np.pi*frequency[i]*(i-i_0)*time_step+np.pi/2.)

        #for i in range(0,len(awf)):
        #    awf[i] = round(awf[i],8)
        return self.pack_keysight_packet(final_wf)
    
    
    @setting(11, "Program Awf", start_hold = 'v',freq_ramp_time = 'v', amp_ramp_time = 'v',end_hold = 'v',vpp = 'v', sin_freq = 'v')
    def program_awf(self, c, start_hold,freq_ramp_time,amp_ramp_time,end_hold,vpp,sin_freq): #in ms and kHz
        start_hold = start_hold * 1e-3
        amp_ramp_time = amp_ramp_time * 1e-3
        end_hold = end_hold * 1e-3 
        sin_freq = sin_freq * 1e3
        freq_ramp_time = freq_ramp_time*1e-3
        total_time = start_hold+freq_ramp_time + amp_ramp_time+end_hold

        wf_str1 = self.make_awf(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,1)
        wf_str2 = self.make_awf(start_hold,freq_ramp_time, amp_ramp_time,end_hold,sin_freq,2)        

        #initialize
        self.write(self.instr,'*RST;*CLS')
        self.write(self.instr,'FORM:BORD NORM')
        self.write(self.instr,'SOUR1:DATA:VOL:CLE')
        self.write(self.instr,'SOUR2:DATA:VOL:CLE')

        #program awf
        self.write(self.instr,':SOUR1:FUNC ARB')
        self.write(self.instr,':SOUR2:FUNC ARB')
        self.write(self.instr,':SOUR1:DATA:ARB channel1_awf,{}'.format(wf_str1))
        self.write(self.instr,':SOUR2:DATA:ARB channel2_awf,{}'.format(wf_str2))
        self.write(self.instr,':SOUR1:FUNC:ARB channel1_awf')
        self.write(self.instr,':SOUR2:FUNC:ARB channel2_awf')

        #set waveform settings
        self.write(self.instr,'SOUR1:VOLT '+str(vpp))
        self.write(self.instr,'SOUR2:VOLT '+str(vpp))
        self.write(self.instr,'SOUR1:VOLT:OFFS 0')
        self.write(self.instr,'SOUR2:VOLT:OFFS 0')
        self.write(self.instr,'OUTP1:LOAD 50')
        self.write(self.instr,'OUTP2:LOAD 50')        
        self.write(self.instr,'SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))
        self.write(self.instr,'SOUR2:FUNC:ARB:SRAT ' + str(self.samp_rate))

        ##set triggering
        self.write(self.instr,'TRIG1:SOUR EXT')
        self.write(self.instr,'TRIG2:SOUR EXT')
        self.write(self.instr,':SOUR1:BURS:MODE TRIG')
        self.write(self.instr,':SOUR2:BURS:MODE TRIG')        
        self.write(self.instr,':SOUR1:BURS:NCYC 1')
        self.write(self.instr,':SOUR2:BURS:NCYC 1')
        self.write(self.instr,':SOUR1:BURS:STAT ON')
        self.write(self.instr,':SOUR2:BURS:STAT ON')
        self.set_state(c,1,1)
        self.set_state(c,2,1)
        #yield self.sync_phases(c)

        #self.read_error_queue()
        
__server__ = KEYSIGHT_33500B()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
