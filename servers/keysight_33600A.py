'''
### BEGIN NODE INFO
[info]
name = KEYSIGHT_33600A
version = 1.0
description =
instancename = KEYSIGHT_33600A

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

#instancename = KEYSIGHT_33600A

from labrad.server import LabradServer, setting, inlineCallbacks
from twisted.internet.defer import DeferredLock, Deferred

from socket import *
import select
import numpy as np
import struct
from warnings import warn
import cmath
import time

from labrad.units import WithUnit as U

#SERVERNAME = 'KEYSIGHT_33600A'
#SIGNALID = 190234 ## this needs to change


class KEYSIGHT_33600A(LabradServer):
    name = 'KEYSIGHT_33600A'
    instr = None
    
    def initServer(self):
        serverHost = '192.168.169.103' #IP address of the awg
        serverPort = 5025 
        self.instr = socket(AF_INET, SOCK_STREAM)

        self.samp_rate = 1e7 #max 2e8 or 2e6 total  points

        try:
            self.instr.connect((serverHost, serverPort))
            self.instr.settimeout(10)
            print "Successfully connected" 
        except:
            print "Could not connect"
        
        #initialize off
        self.write(self.instr,'OUTPut1:STATe OFF')

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

    @setting(2, "Update AWG", frequency = 'v', amplitude= 'v', phase='v')
    def update_awg(self,c,frequency,amplitude,phase):
    	amplitude = amplitude/2.0
        self.write(self.instr,'SOUR1:BURS:STAT OFF')
        self.write(self.instr,'SOUR2:BURS:STAT OFF')
        if frequency != 0.0:
            self.write(self.instr,'SOUR1:APPL:SIN')
            self.write(self.instr,'SOUR2:APPL:SIN')
            self.write(self.instr,'SOUR1:FREQ ' + str(frequency))
            self.write(self.instr,'SOUR2:FREQ ' + str(frequency))
            self.write(self.instr,'SOUR1:VOLT ' + str(amplitude))
            self.write(self.instr,'SOUR2:VOLT ' + str(amplitude))
            self.set_phase(c,1,phase)
            self.set_phase(c,2,(phase + 90) % 360)
            self.write(self.instr,'PHAS:SYNC')
        else:
            offset1 = 0.5 * amplitude * np.sin(np.pi*phase/180.)
            offset2 = 0.5 * amplitude * np.sin(np.pi*(phase+90.)/180.)
            self.write(self.instr,'SOUR1:APPL:DC DEF,DEF,'+str(offset1))
            self.write(self.instr,'SOUR2:APPL:DC DEF,DEF,'+str(offset2))
            

    @setting(3, "Set Phase", channel = 'i', phase = 'v')        
    def set_phase(self, c, channel, phase):
        if not 0<=phase<=360:
            phase = phase % 360
        self.write(self.instr,'SOURce' +str(channel) + ':PHASe ' + str(phase))

    @setting(4, "Sync Phases")
    def sync_phases(self,c):
        self.write(self.instr,'PHAS:SYNC')
        
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
                       
    def noise_waveform(self, bandwidth, center_frequency): #in Hz
        #makes string with values to form arbitrary wave form. 
        
        total_time = 20e-3 #one second waveform
        ts = np.linspace(0.,total_time,int(self.samp_rate*total_time))

        print "Total time = ", total_time, "s"

        frequency_spacing = 10. # Hz (10 ms experiment/2pi)
        #sum sine waves

        awf =np.zeros_like(ts)
        frequencies = np.arange(center_frequency-bandwidth/2.,center_frequency+bandwidth/2.,frequency_spacing)
        for f in frequencies:
            sine_wave = np.sin(2.*np.pi*(f*ts+np.random.random()))
            awf+=sine_wave
        
        rms = np.sqrt(np.mean(awf**2.))
        awf = awf/(4.*rms) #set the rms at one quarter the max programmable number

        return self.pack_keysight_packet(awf)


    @setting(5, "Program Noise", center_frequency = 'v', bandwidth= 'v',amplitude = 'v')
    def program_noise(self, c, center_frequency,bandwidth,amplitude): #in Hz and arbitrary

        wf_str = self.noise_waveform(bandwidth,center_frequency)

        print "released"
        #initialize
        self.write(self.instr,'*RST;*CLS')
        self.write(self.instr,'FORM:BORD NORM')
        self.write(self.instr,'SOUR1:DATA:VOL:CLE')

        #program awf
        self.write(self.instr,':SOUR1:FUNC ARB')
        self.write(self.instr,':SOUR1:DATA:ARB channel1_awf,{}'.format(wf_str))
        self.write(self.instr,':SOUR1:FUNC:ARB channel1_awf')

        #set waveform settings
        self.write(self.instr,'SOUR1:VOLT '+str(amplitude))
        self.write(self.instr,'SOUR1:VOLT:OFFS 0')
        self.write(self.instr,'OUTP1:LOAD 50')    
        self.write(self.instr,'SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))

        ##set triggering
        # self.write(self.instr,'TRIG1:SOUR EXT')
        # self.write(self.instr,':SOUR1:BURS:MODE TRIG')     
        # self.write(self.instr,':SOUR1:BURS:NCYC 1')
        # self.write(self.instr,':SOUR1:BURS:STAT ON')
        self.set_state(c,1,1)
        #yield self.sync_phases(c)

        #self.read_error_queue()


    @setting(6,"Program Square Wave", frequency = 'v', amplitude= 'v', offset = 'v', dutyCycle = 'v' )
    def programSquareWave(self,c,frequency,amplitude,offset,dutyCycle):
        frequency = abs(frequency)*1e3 # originally in kHz
        self.write(self.instr,'FUNC SQU')
        self.write(self.instr,'FUNC:SQU:DCYC '+str(dutyCycle))
        self.write(self.instr,'FREQ '+str(frequency))
        self.write(self.instr,'SOUR:VOLT '+str(amplitude))
        self.write(self.instr,'SOUR:VOLT:OFFS '+str(offset))
        self.set_state(c,1,1)

        self.read_error_queue()


    @setting(7, "DC Bias Waveform", )
    def dcBiasWaveform(self, )

        
__server__ = KEYSIGHT_33600A()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
