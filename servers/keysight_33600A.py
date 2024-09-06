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
        serverHost = '192.168.169.93' #IP address of the awg
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
                       
    #@setting(1, "Make Awf", freq_ramp_time = 'v', start_hold = 'v',amp_ramp_time = 'v',end_hold = 'v',sin_freq = 'v',channel='i')  
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



    def b_field_waveform(self, phase, frequency, start_hold, on_time, end_hold):
        """Makes string with values to form arbitrary wave form."""

        total_time = start_hold + on_time + end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        start_points = int(round(num_points*start_hold/total_time))
        on_points = int(round(num_points*on_time/total_time))
        end_points = int(round(num_points*end_hold/total_time))

        # define amplitude curve
        awf = []
        awf = np.zeros(start_points)
        awf = np.append(awf, np.ones(on_points))
        awf = np.append(awf, np.zeros(end_points))

        time_step = total_time/float(num_points)
        i1 = start_points

        ##definition
        waveform = np.multiply(np.sin(phase + 2.0*np.pi*frequency*np.subtract(range(len(awf)),i1)*time_step), awf)
        waveform = np.append(waveform,np.zeros(1))
        print "max = ", np.amax(waveform)
        print "min = ",np.amin(waveform)
    
        return self.pack_keysight_packet(waveform)

    def b_field_waveform_2freq(self, phases, freqs, start_hold, on_time, end_hold,ac):
        ''' Makes a waveform with two frequencies at two phases 
        '''
        print freqs
        total_time = start_hold + on_time + end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        start_points = int(round(num_points*start_hold/total_time))
        on_points = int(round(num_points*on_time/total_time))
        end_points = int(round(num_points*end_hold/total_time))

        start = np.zeros(start_points)
        end = np.zeros(end_points)

        time_step = total_time/float(num_points)

        waveform = np.zeros(on_points)
        for i in range(len(phases)):
            waveform = 0.5*np.sin(phases[i] + 2.0*np.pi*freqs[i]*np.array(range(on_points))*time_step) + waveform

        waveform = np.append(waveform,end)
        waveform = np.append(waveform,np.zeros(1))
        waveform = np.append(start,waveform)

        if ac:
            waveform = np.sqrt(0.5*(1+waveform))

        #if ac:
        #    waveform = [-1*np.sqrt(-1*x) if x<0 else np.sqrt(x) for x in waveform]
    
        return self.pack_keysight_packet(waveform)

    def noiseList(self,num_pts,fmax,fstep,amp):

        pts = np.arange(num_pts)*self.samp_rate

        sig = np.zeros(num_pts)
        for f in np.arange(fstep,fmax,fstep):
            sig = sig+np.sin(2*np.pi*(f*pts+np.random.random()))

        sig = sig/max(abs(sig))
        sig = sig*amp

        return sig

    def b_field_waveform_incoh(self,fs,fr,std,exp_time,n_exp,ac,noise,noise_amp):
        '''
         Makes a waveform of A1sin(w1t) + B1cos(w1t) + A2sin(w2t) + B2cos(w2t)
         A1,B1,A2,B2 are taken from a normal distribution with mean 0 and the std given.
         It should work over as many experiments as the number of points allow
         It should be 0 during state preparation and state readout
        '''
        w1 = 2.0*np.pi*(fs + fr/2.0)
        w2 = 2.0*np.pi*(fs - fr/2.0)
        print 'f1',w1/(2.0*np.pi)
        print 'f2',w2/(2.0*np.pi)

        total_time = n_exp*exp_time
        tot_points = int(self.samp_rate * total_time)

        print "Number of points = ", tot_points
        print "Total time = ", total_time, "s"

        time_step = total_time/float(tot_points)


        exp_points = int(self.samp_rate * exp_time)

        waveform = np.array([])
        
        for n in range(int(n_exp)):
            A1,B1,A2,B2 = np.random.normal(0,std,4)
            pts = np.arange(exp_points)*time_step
            sig = A1 * np.sin(w1*pts) + B1 * np.cos(w1*pts) + A2 * np.sin(w2*pts) + B2 * np.cos(w2*pts)
            
            waveform = np.append(waveform,sig)

        #add noise if necessary
        if noise:
            ns = self.noiseList(len(waveform),10e3,10,noise_amp)

            waveform = waveform + ns

        #normalize the waveform
        amp = max(abs(waveform))
        waveform = waveform / amp

        if ac:
            waveform = [-1*np.sqrt(-1*x) if x<0 else np.sqrt(x) for x in waveform]
            amp = np.sqrt(amp)
        print 'max',max(waveform)
        print 'a',amp


        return self.pack_keysight_packet(waveform),amp






    @setting(6, "Program B Field", phase = 'v', frequency = 'v', start_hold = 'v', on_time = 'v', end_hold = 'v',amplitude = 'v',offset = 'v')
    def program_b_field(self, c, phase, frequency, start_hold, on_time, end_hold, amplitude,offset): #in Hz and arbitrary
        phase = phase * np.pi/180.0
        start_hold = start_hold * 1e-3
        on_time = on_time * 1e-6
        end_hold = end_hold * 1e-3
        total_time = start_hold+on_time+end_hold
        frequency = frequency*1e3

        wf_str = self.b_field_waveform(phase, frequency, start_hold, on_time, end_hold)

        print "released"
        print amplitude/2+offset
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
        self.write(self.instr,'SOUR1:VOLT:OFFS '+str(offset))
        self.write(self.instr,'OUTP1:LOAD 50')    
        self.write(self.instr,'SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))

        ##set triggering 
        self.write(self.instr,'TRIG1:SOUR EXT')
        self.write(self.instr,':SOUR1:BURS:MODE TRIG')     
        self.write(self.instr,':SOUR1:BURS:NCYC 1')
        self.write(self.instr,':SOUR1:BURS:STAT ON')
        self.set_state(c,1,1)
        #yield self.sync_phases(c)

        self.read_error_queue()

    @setting(7, "Program B Field 2Freq", phases = '*v', center_freq = 'v', freq_sep = 'v', start_hold = 'v', on_time = 'v', end_hold = 'v',amplitude = 'v',ac = 'b')
    def program_b_field_2freq(self, c, phases, center_freq, freq_sep, start_hold, on_time, end_hold, amplitude,ac): 
        phases = [p*np.pi/180.0 for p in phases]
        start_hold = start_hold * 1e-3
        on_time = on_time * 1e-6
        end_hold = end_hold * 1e-3
        total_time = start_hold+on_time+end_hold
        freqs = [center_freq+freq_sep/2.0,center_freq-freq_sep/2.0]
        freqs = [f*1e3 for f in freqs]

        wf_str = self.b_field_waveform_2freq(phases, freqs, start_hold, on_time, end_hold,ac)

        off = 0

        if ac:
            amplitude = np.sqrt(amplitude)
        
        #off = amplitude

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
        self.write(self.instr,'SOUR1:VOLT:OFFS '+str(off))
        self.write(self.instr,'OUTP1:LOAD 50')    
        self.write(self.instr,'SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))

        ##set triggering 
        self.write(self.instr,'TRIG1:SOUR EXT')
        self.write(self.instr,':SOUR1:BURS:MODE TRIG')     
        self.write(self.instr,':SOUR1:BURS:NCYC 1')
        self.write(self.instr,':SOUR1:BURS:STAT ON')
        self.set_state(c,1,1)
        #yield self.sync_phases(c)

        self.read_error_queue()

    @setting(8,"Program B Field Incoh",fs = 'v', fr = 'v', std = 'v', tot_time = 'v',n_exp = 'v',n_points = 'v',ac ='b',noise='b',noise_amp='v')
    def program_b_field_incoh(self,c,fs,fr,std,tot_time,n_exp,n_points,ac,noise,noise_amp):
        #change everything to seconds in hz, given in kHz and ms
        fs = fs*1e3
        fr = fr*1e3
        tot_time = tot_time*1e-3

        self.samp_rate = fs*n_points
        print self.samp_rate

        wf_str, amplitude = self.b_field_waveform_incoh(fs,fr,std,tot_time,n_exp,ac,noise,noise_amp)

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
        self.write(self.instr,'SOUR1:VOLT:OFFS '+str(0))
        self.write(self.instr,'OUTP1:LOAD 50')    
        self.write(self.instr,'SOUR1:FUNC:ARB:SRAT ' + str(self.samp_rate))

        ##set triggering 
        self.write(self.instr,'TRIG1:SOUR EXT')
        self.write(self.instr,':SOUR1:BURS:MODE TRIG')     
        self.write(self.instr,':SOUR1:BURS:NCYC 1')
        self.write(self.instr,':SOUR1:BURS:STAT ON')
        self.set_state(c,1,1)

        self.read_error_queue()


    @setting(9,"Program Square Wave", frequency = 'v', amplitude= 'v', offset = 'v', dutyCycle = 'v' )
    def programSquareWave(self,c,frequency,amplitude,offset,dutyCycle):
        frequency = abs(frequency)*1e3 # originally in kHz
        self.write(self.instr,'FUNC SQU')
        self.write(self.instr,'FUNC:SQU:DCYC '+str(dutyCycle))
        self.write(self.instr,'FREQ '+str(frequency))
        self.write(self.instr,'SOUR:VOLT '+str(amplitude))
        self.write(self.instr,'SOUR:VOLT:OFFS '+str(offset))
        self.set_state(c,1,1)

        self.read_error_queue()
        
__server__ = KEYSIGHT_33600A()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)    
