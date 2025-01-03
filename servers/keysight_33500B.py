'''
### BEGIN NODE INFO
[info]
name = KEYSIGHT_33500B
version = 1.0
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
import struct
from warnings import warn
import time

from labrad.units import WithUnit as U

#SERVERNAME = 'KEYSIGHT_33500B'
#SIGNALID = 190234 ## this needs to change


class KEYSIGHT_33500B(LabradServer):
    name = 'KEYSIGHT_33500B'
    instr = None
    
    def initServer(self):
        serverHost = '192.168.169.182' #IP address of the awg
        serverPort = 5025 #random number over 1024, #5025
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

    def spin_up_spin_down_linear(self, start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,channel): #in s and Hz
    
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        phi0 = start_phase                                  #phase where spin-up starts
        phi1 = phi0 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-up ends
        phi2 = phi1 + 2*np.pi*sin_freq*middle_hold          #phase where spin-down starts
        phi3 = phi2 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-down ends
        extra_phase = 2*np.pi - np.mod(phi3-phi0, 2*np.pi)  #needed to make final phase match initial phase
        extra_time = extra_phase/(2*np.pi*sin_freq)

        middle_hold = middle_hold + extra_time
        phi2 = phi2 + extra_phase
        phi3 = phi3 + extra_phase

        total_time = start_hold + freq_ramp_time + middle_hold + freq_ramp_time + end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        start_points = int(round(num_points*start_hold/total_time))
        freq_ramp_points = int(round(num_points*freq_ramp_time/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf = np.ones(start_points + freq_ramp_points + middle_points + freq_ramp_points + end_points)
        
        #define phase curve
        time_step = total_time/float(num_points)

        times_start     = time_step * np.arange(start_points)
        times_spin_up   = time_step * np.arange(freq_ramp_points)
        times_middle    = time_step * np.arange(middle_points)
        times_spin_down = time_step * np.arange(freq_ramp_points)
        times_end       = time_step * np.arange(end_points)

        phase_curve = phi0*np.ones(start_points)
        phase_curve = np.append(phase_curve, phi0 + 1/2.0*2*np.pi*sin_freq/freq_ramp_time*times_spin_up**2)
        phase_curve = np.append(phase_curve, phi1 + 2*np.pi*sin_freq*times_middle)
        phase_curve = np.append(phase_curve, phi3 - 1/2.0*2*np.pi*sin_freq/freq_ramp_time*(freq_ramp_time-times_spin_down)**2)
        phase_curve = np.append(phase_curve, phi3*np.ones(end_points))

        #define final waveform
        if channel == 1:
            final_wf = np.multiply(awf, np.sin(phase_curve))
        elif channel == 2:
            final_wf = np.multiply(awf, np.sin(phase_curve + np.pi/2.0))

        return self.pack_keysight_packet(final_wf)



    def spin_up_spin_down_sin(self, start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,channel): #in s and Hz
    
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        phi0 = start_phase                                  #phase where spin-up starts
        phi1 = phi0 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-up ends
        phi2 = phi1 + 2*np.pi*sin_freq*middle_hold          #phase where spin-down starts
        phi3 = phi2 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-down ends
        extra_phase = 2*np.pi - np.mod(phi3-phi0, 2*np.pi)  #needed to make final phase match initial phase
        extra_time = extra_phase/(2*np.pi*sin_freq)

        middle_hold = middle_hold + extra_time
        phi2 = phi2 + extra_phase
        phi3 = phi3 + extra_phase

        total_time = start_hold + freq_ramp_time + middle_hold + freq_ramp_time + end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        start_points = int(round(num_points*start_hold/total_time))
        freq_ramp_points = int(round(num_points*freq_ramp_time/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf = np.ones(start_points + freq_ramp_points + middle_points + freq_ramp_points + end_points)
        
        #define phase curve
        time_step = total_time/float(num_points)

        times_start     = time_step * np.arange(start_points)
        times_spin_up   = time_step * np.arange(freq_ramp_points)
        times_middle    = time_step * np.arange(middle_points)
        times_spin_down = time_step * np.arange(freq_ramp_points)
        times_end       = time_step * np.arange(end_points)

        phase_curve = phi0*np.ones(start_points)
        phase_curve = np.append(phase_curve, phi0 + 2*np.pi*sin_freq * (times_spin_up/2 - freq_ramp_time/(2*np.pi)*np.sin(np.pi*times_spin_up/freq_ramp_time)))
        phase_curve = np.append(phase_curve, phi1 + 2*np.pi*sin_freq*times_middle)
        phase_curve = np.append(phase_curve, phi3 - 2*np.pi*sin_freq * ((freq_ramp_time-times_spin_down)/2 - freq_ramp_time/(2*np.pi)*np.sin(np.pi*(freq_ramp_time-times_spin_down)/freq_ramp_time)))
        phase_curve = np.append(phase_curve, phi3*np.ones(end_points))

        #define final waveform
        if channel == 1:
            final_wf = np.multiply(awf, np.sin(phase_curve))
        elif channel == 2:
            final_wf = np.multiply(awf, np.sin(phase_curve + np.pi/2.0))

        return self.pack_keysight_packet(final_wf)


                       
    #@setting(1, "Make Awf", freq_ramp_time = 'v', start_hold = 'v',amp_ramp_time = 'v',end_hold = 'v',sin_freq = 'v',channel='i')  
    def free_rotation(self, start_phase,start_hold,freq_ramp_time,middle_hold, amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf =[]
        awf = np.ones(start_points+int(freq_ramp_points)+middle_points)
        awf = np.append(awf, 1.-np.arange(int(amp_ramp_points))/amp_ramp_points)
        awf = np.append(awf, np.zeros(end_points))
        
        #definte frequency curve
        frequency = np.zeros(start_points)
        frequency = np.append(frequency, np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(middle_points + int(amp_ramp_points)+end_points))
   

        time_step = total_time/float(num_points)

        i1 = start_points
        i2 = int(freq_ramp_points+start_points)

        ##definition through frequency ramp
        if channel == 1:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step), awf)
        if channel == 2:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step + np.pi/2.), awf)
        waveform1 = waveform1[:i2]

        #defination after frequency ramp
        phi_0= 2.*np.pi*((0.5*frequency[i2])*(i2-i1)*time_step)
        if channel == 1:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step), awf)
        if channel == 2:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step + np.pi/2.), awf)
        waveform2 = waveform2[i2:]

        final_wf = np.append(waveform1,waveform2)
    
        return self.pack_keysight_packet(final_wf)
    
    def free_rotation_no_amp_ramp(self, start_phase,start_hold,freq_ramp_time,middle_hold, amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf = np.ones(int(num_points))
    

        #definte frequency curve
        frequency = np.zeros(start_points)
        frequency = np.append(frequency, np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(middle_points + int(amp_ramp_points)+end_points))
   

        time_step = total_time/float(num_points)

        i1 = start_points
        i2 = int(freq_ramp_points+start_points)

        ##definition through frequency ramp
        if channel == 1:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step), awf)
        if channel == 2:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step + np.pi/2.), awf)
        waveform1 = waveform1[:i2]

        #defination after frequency ramp
        phi_0= 2.*np.pi*((0.5*frequency[i2])*(i2-i1)*time_step)
        if channel == 1:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step), awf)
        if channel == 2:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step + np.pi/2.), awf)
        waveform2 = waveform2[i2:]
        final_wf = np.append(waveform1,waveform2)
        return self.pack_keysight_packet(final_wf)

    def free_rotation_sin_spin(self, start_phase,start_hold,freq_ramp_time,middle_hold, amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        phi0 = start_phase                                  #phase where spin-up starts
        phi1 = phi0 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-up ends

        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        #define amplitude curve
        awf =[]
        awf = np.ones(start_points+int(freq_ramp_points)+middle_points)
        awf = np.append(awf, 1.-np.arange(int(amp_ramp_points))/amp_ramp_points)
        awf = np.append(awf, np.zeros(end_points))
        
        #definte phase curve
        frequency = np.zeros(start_points)
        frequency = np.append(frequency, np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(middle_points + int(amp_ramp_points)+end_points))
   
        time_step = total_time/float(num_points)

        times_start     = time_step * np.arange(start_points)
        times_spin_up   = time_step * np.arange(freq_ramp_points)
        times_final   = time_step * np.arange(middle_points+amp_ramp_points+end_points)

        phase_curve = phi0*np.ones(start_points)
        phase_curve = np.append(phase_curve, phi0 + 2*np.pi*sin_freq * (times_spin_up/2 - freq_ramp_time/(2*np.pi)*np.sin(np.pi*times_spin_up/freq_ramp_time)))
        phase_curve = np.append(phase_curve, phi1 + 2*np.pi*sin_freq*times_final)

        ##definition through frequency ramp
        if channel == 1:
            final_wf = np.multiply(np.sin(phase_curve), awf)
        if channel == 2:
            final_wf = np.multiply(np.sin(phase_curve + np.pi/2.), awf)
    
        return self.pack_keysight_packet(final_wf)
    
    def free_rotation_sin_spin_no_amp_ramp(self, start_phase,start_hold,freq_ramp_time,middle_hold, amp_ramp_time,end_hold,sin_freq,channel): #in s and Hz
        
        #makes string with values to form arbitrary wave form. 
        # freq ramp up,hold spinning, amplitude ramp down, hold with no pinning
        
        phi0 = start_phase                                  #phase where spin-up starts
        phi1 = phi0 + 1/2.0*2*np.pi*sin_freq*freq_ramp_time #phase where spin-up ends

        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        awf = np.ones(int(freq_ramp_points + start_points + middle_points + amp_ramp_points + end_points))

        
        #definte phase curve
        frequency = np.zeros(start_points)
        frequency = np.append(frequency, np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(middle_points + int(amp_ramp_points)+end_points))
   
        time_step = total_time/float(num_points)

        times_start     = time_step * np.arange(start_points)
        times_spin_up   = time_step * np.arange(freq_ramp_points)
        times_final   = time_step * np.arange(middle_points+amp_ramp_points+end_points)

        phase_curve = phi0*np.ones(start_points)
        phase_curve = np.append(phase_curve, phi0 + 2*np.pi*sin_freq * (times_spin_up/2 - freq_ramp_time/(2*np.pi)*np.sin(np.pi*times_spin_up/freq_ramp_time)))
        phase_curve = np.append(phase_curve, phi1 + 2*np.pi*sin_freq*times_final)

        ##definition through frequency ramp
        if channel == 1:
            final_wf = np.multiply(np.sin(phase_curve), awf)
        if channel == 2:
            final_wf = np.multiply(np.sin(phase_curve + np.pi/2.), awf)
    
        return self.pack_keysight_packet(final_wf)



    def free_rotation_nlinrel(self, start_phase, start_hold, freq_ramp_time, middle_hold, amp_ramp_time, speedfactor, end_hold, sin_freq, channel):
        """Makes string with values to form arbitrary wave form.
        Freq ramp up,hold spinning, amplitude ramp down, hold with no pinning.
        Amplitude ramp is nonlinear; follows scaling of 1/(1 + at)^2 for some constant a
        such that at the amplitude ramp time, the amplitude is 1/1000 of its starting value"""

        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        num_points = self.samp_rate * total_time

        print "Number of points = ", num_points
        print "Total time = ", total_time, "s"

        freq_ramp_points = round(num_points*freq_ramp_time/total_time)
        start_points = int(round(num_points*start_hold/total_time))
        middle_points = int(round(num_points*middle_hold/total_time))
        amp_ramp_points = round(num_points*amp_ramp_time/total_time)
        end_points = int(round(num_points*end_hold/total_time))
        
        # define amplitude curve
        awf = []
        awf = np.ones(start_points+int(freq_ramp_points)+middle_points)
        awf = np.append(awf, 1.0/(1+speedfactor*30.6*(np.arange(int(amp_ramp_points))/amp_ramp_points))**2)
        awf = np.append(awf, np.zeros(end_points))
        
        #definte frequency curve
        frequency = np.zeros(start_points)
        frequency = np.append(frequency, np.arange(int(freq_ramp_points))*sin_freq/(2.*float(freq_ramp_points)))
        frequency = np.append(frequency, sin_freq*np.ones(middle_points + int(amp_ramp_points)+end_points))

        time_step = total_time/float(num_points)
        i1 = start_points
        i2 = int(freq_ramp_points+start_points)

        ##definition through frequency ramp
        if channel == 1:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step), awf)
        if channel == 2:
            waveform1 = np.multiply(np.sin(start_phase + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i1))*time_step + np.pi/2.), awf)
        waveform1 = waveform1[:i2]

        #definition after frequency ramp
        phi_0= 2.*np.pi*((0.5*frequency[i2])*(i2-i1)*time_step)
        if channel == 1:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step), awf)
        if channel == 2:
            waveform2 = np.multiply(np.sin(start_phase + phi_0 + 2*np.pi*np.multiply(frequency, np.subtract(range(len(awf)),i2))*time_step + np.pi/2.), awf)
        waveform2 = waveform2[i2:]

        final_wf = np.append(waveform1,waveform2)
    
        return self.pack_keysight_packet(final_wf)
    
    
    @setting(5, "Program Awf", start_phase='v', start_hold='v', freq_ramp_time='v', middle_hold='v', amp_ramp_time='v', end_hold='v', vpp='v', sin_freq='v', waveform_label='s')
    def program_awf(self, c, start_phase, start_hold, freq_ramp_time, middle_hold, amp_ramp_time, end_hold, vpp, sin_freq, waveform_label): #in ms and kHz
        start_phase = start_phase * np.pi/180.0
        start_hold = start_hold * 1e-3
        amp_ramp_time = amp_ramp_time * 1e-3
        middle_hold = middle_hold * 1e-3
        end_hold = end_hold * 1e-3 
        sin_freq = sin_freq * 1e3
        freq_ramp_time = freq_ramp_time*1e-3
        total_time = start_hold+freq_ramp_time + middle_hold + amp_ramp_time+end_hold
        print(waveform_label)

        if waveform_label == 'free_rotation': #with frequency ramp and amplitude ramp to get free rotation
            wf_str1 = self.free_rotation(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time,end_hold,sin_freq,1)
            wf_str2 = self.free_rotation(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time,end_hold,sin_freq,2)
        elif waveform_label == 'free_rotation_nlinrel':
            wf_str1 = self.free_rotation_nlinrel(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, speedfactor, end_hold,sin_freq,1)
            wf_str2 = self.free_rotation_nlinrel(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, speedfactor, end_hold,sin_freq,2)
        elif waveform_label == 'free_rotation_sin_spin':
            wf_str1 = self.free_rotation_sin_spin(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, end_hold,sin_freq,1)
            wf_str2 = self.free_rotation_sin_spin(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, end_hold,sin_freq,2)
        elif waveform_label == 'spin_up_spin_down_linear': #ramp up frequency then ramp down
            wf_str1 = self.spin_up_spin_down_linear(start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,1)
            wf_str2 = self.spin_up_spin_down_linear(start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,2)
        elif waveform_label ==  'spin_up_spin_down_sin':
            wf_str1 = self.spin_up_spin_down_sin(start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,1)
            wf_str2 = self.spin_up_spin_down_sin(start_phase,start_hold,freq_ramp_time,middle_hold,end_hold,sin_freq,2)
        elif waveform_label == 'free_rotation_no_amp_ramp':
            wf_str1 = self.free_rotation_no_amp_ramp(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time,end_hold,sin_freq,1)
            wf_str2 = self.free_rotation_no_amp_ramp(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time,end_hold,sin_freq,2)
        elif waveform_label == 'free_rotation_sin_spin_no_amp_ramp':
            wf_str1 = self.free_rotation_sin_spin_no_amp_ramp(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, end_hold,sin_freq,1)
            wf_str2 = self.free_rotation_sin_spin_no_amp_ramp(start_phase,start_hold,freq_ramp_time, middle_hold, amp_ramp_time, end_hold,sin_freq,2)
        else:
            print "Error: no waveform by the name {}".format(waveform_label)

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
        self.write(self.instr,'SOUR1:VOLT '+str(vpp/2.0))
        self.write(self.instr,'SOUR2:VOLT '+str(vpp/2.0))
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

    @setting(6, "Rotation run initial", state_prep_time='v', total_time='v', scan_param_name='s', scan_param_value='v')
    def rotation_run_initial(self, c, state_prep_time, total_time, scan_param_name=None, scan_param_value=None):
        # To be added to the run_initial method of scripts conditioned on rotation being enabled

        # This function begins by constructing a dictionary called rp which stores the parameters for rotation
        # This is basically a reconstruction of parameters_dict from the script scanner
        # Done this way because I can't find a way to pass the full parameters_dict to a server like the Keysight through labrad.
        # One parameter (presumably the one being scanned) may be overwritten;
            # this requires passing its name and value as the two optional arguments since the scriptscanner server doesn't know the current scan parameter value

        ss = self.client.scriptscanner

        # create a dictionary with all the rotation parameters
        rotation_parameter_names = ['voltage_pp',
                                    'drive_frequency',
                                    'start_phase',
                                    'start_hold',
                                    'middle_hold',
                                    'ramp_down_time', 
                                    'end_hold',
                                    'frequency_ramp_time',
                                    'waveform_label']
        rp = {} # rotation parameters dictionary
        for param_name in rotation_parameter_names:
            if param_name == scan_param_name:
                rp[param_name] = scan_param_value
            else:
                rp[param_name] = yield ss.get_parameter('Rotation', param_name)

        state_prep_time -= U(0.4, 'ms')  # Compensate for 400 us cushion put into state prep
        state_prep_time_minus_rotation = state_prep_time - (rp['start_hold'] + rp['frequency_ramp_time'] + rp['middle_hold'] + rp['ramp_down_time'] + rp['end_hold'])

        if rp['waveform_label'] == 'free_rotation_no_amp_ramp' or rp['waveform_label'] == 'free_rotation_sin_spin_no_amp_ramp':
            self.program_awf(c,
                            rp['start_phase']['deg'],
                            state_prep_time_minus_rotation['ms'] + 0.2 + rp['start_hold']['ms'], # 200 us cushion at the beginning (the other 200 us is thus at the end)
                            rp['frequency_ramp_time']['ms'],
                            rp['middle_hold']['ms'],
                            rp['ramp_down_time']['ms'],
                            total_time['ms'] - (state_prep_time_minus_rotation['ms'] + 0.2 + rp['start_hold']['ms']) - rp['frequency_ramp_time']['ms'] -1,
                            rp['voltage_pp']['V'],
                            rp['drive_frequency']['kHz'],
                            rp['waveform_label'])
        else:
            self.program_awf(c,
                            rp['start_phase']['deg'],
                            state_prep_time_minus_rotation['ms'] + 0.2 + rp['start_hold']['ms'], # 200 us cushion at the beginning (the other 200 us is thus at the end)
                            rp['frequency_ramp_time']['ms'],
                            rp['middle_hold']['ms'],
                            rp['ramp_down_time']['ms'],
                            rp['end_hold']['ms'],
                            rp['voltage_pp']['V'],
                            rp['drive_frequency']['kHz'],
                            rp['waveform_label'])

    @setting(7, "Rotation run finally")
    def rotation_run_finally(self, c):
        # To be added to the run_finally method of scripts conditioned on rotation being enabled
        ss = self.client.scriptscanner
        old_freq = yield ss.get_parameter('RotationCW', 'drive_frequency')
        old_amp = yield ss.get_parameter('RotationCW', 'voltage_pp')
        old_phase = yield ss.get_parameter('RotationCW', 'start_phase')
        self.update_awg(c, old_freq['Hz'], old_amp['V'], old_phase['deg'])

    @setting(8, "Program Square Wave", frequency='v', amplitude='v', offset='v', dutyCycle='v')
    def program_square_wave(self, c, frequency, amplitude, offset, dutyCycle):
        # Input parameters must be floats rather than integers for some reason
        frequency = abs(frequency)*1e6  #originally in MHz
        self.write(self.instr,'FUNC SQU')
        self.write(self.instr,'FUNC:SQU:DCYC ' + str(dutyCycle))
        self.write(self.instr,'FREQ ' + str(frequency))
        self.write(self.instr,'SOUR:VOLT ' + str(amplitude))
        self.write(self.instr,'SOUR:VOLT:OFFS ' + str(offset))
        self.set_state(c, 1, 1)

__server__ = KEYSIGHT_33500B()
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
