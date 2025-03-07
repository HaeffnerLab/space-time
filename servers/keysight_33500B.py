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
import matplotlib.pyplot as plt
from labrad.units import WithUnit as U
from treedict import TreeDict

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


    ################################# ROTATION WAVEFORMS #################################
    
    def plot_amp_and_freq_vs_time(self, amplitude_curve, phase_curve):
            # Create a plot of ampltude and frequency vs time
            time = np.linspace(0, len(amplitude_curve)/self.samp_rate, len(amplitude_curve)) * 1e6
            frequency_curve = np.diff(phase_curve, prepend=phase_curve[0])*self.samp_rate / (2*np.pi) * 1e-3

            (fig, ax1) = plt.subplots()
            ax2 = ax1.twinx()
            ax1.plot(time, amplitude_curve)
            ax2.plot(time, frequency_curve, color='C1')
            ax1.set_xlabel('Time (us)')
            ax1.set_ylabel('Relative amplitude')
            ax2.set_ylabel('Frequency (kHz)')

            plt.show()

    def construct_waveforms(self, amplitude_curve, phase_curve):
        waveform1 = amplitude_curve * np.sin(phase_curve)
        waveform2 = amplitude_curve * np.cos(phase_curve)
        return waveform1, waveform2

    
    ################ Spin up then release ################
    def linear_spinup__linear_release(self, start_phase, start_hold, spinup_time, middle_hold, release_time, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_middle = start_hold + spinup_time
        t_release = start_hold + spinup_time + middle_hold

        # Time array   
        total_time = start_hold + spinup_time + middle_hold + release_time
        t = np.linspace(0, total_time, int(self.samp_rate * total_time))

        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_middle)
        middle_region = (t >= t_middle) & (t < t_release)
        release_region = (t >= t_release)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)
        amplitude_curve[release_region] = 1.0 - (t[release_region] - t_release)/release_time

        # Phase curve
        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2
        middle_end_phase = spinup_end_phase + final_drive_angular_freq*middle_hold

        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase + final_drive_angular_freq/(2*spinup_time)*(t[spinup_region] - start_hold)**2
        phase_curve[middle_region] = spinup_end_phase + final_drive_angular_freq * (t[middle_region] - t_middle)
        phase_curve[release_region] = middle_end_phase + final_drive_angular_freq * (t[release_region] - t_release)

        return amplitude_curve, phase_curve
    
    def sin2_spinup__linear_release(self, start_phase, start_hold, spinup_time, middle_hold, release_time, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_middle = start_hold + spinup_time
        t_release = start_hold + spinup_time + middle_hold

        # Time array   
        total_time = start_hold + spinup_time + middle_hold + release_time
        t = np.linspace(0, total_time, int(self.samp_rate * total_time))
        
        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_middle)
        middle_region = (t >= t_middle) & (t < t_release)
        release_region = (t >= t_release)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)
        amplitude_curve[release_region] = 1.0 - (t[release_region] - t_release)/release_time

        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2
        middle_end_phase = spinup_end_phase + final_drive_angular_freq*middle_hold

        # Phase curve
        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase \
                                        + final_drive_angular_freq*(t[spinup_region]-t_spinup)/2 \
                                        - final_drive_angular_freq*spinup_time/(2*np.pi) * np.sin(np.pi*(t[spinup_region]-t_spinup)/spinup_time)
        phase_curve[middle_region] = spinup_end_phase + final_drive_angular_freq * (t[middle_region] - t_middle)
        phase_curve[release_region] = middle_end_phase + final_drive_angular_freq * (t[release_region] - t_release)
        
        return amplitude_curve, phase_curve
    
    def linear_spinup__adiabatic_release(self, start_phase, start_hold, spinup_time, middle_hold, release_time, final_drive_freq):
        """
        Release function is of the form A(t) = 1/(1+a*t)^2
        The constant a is set such that at the end of the release_time, A(t) = 10^-3 A(0)
        """
        final_drive_angular_freq = 2*np.pi * final_drive_freq

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_middle = start_hold + spinup_time
        t_release = start_hold + spinup_time + middle_hold

        # Time array   
        total_time = start_hold + spinup_time + middle_hold + release_time
        t = np.linspace(0, total_time, int(self.samp_rate * total_time))
        
        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_middle)
        middle_region = (t >= t_middle) & (t < t_release)
        release_region = (t >= t_release)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)
        amplitude_curve[release_region] = 1.0 / (1 + 30.6*(t[release_region] - t_release)/release_time)**2

        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2
        middle_end_phase = spinup_end_phase + final_drive_angular_freq*middle_hold

        # Phase curve
        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase + final_drive_angular_freq/(2*spinup_time)*(t[spinup_region] - start_hold)**2
        phase_curve[middle_region] = spinup_end_phase + final_drive_angular_freq * (t[middle_region] - t_middle)
        phase_curve[release_region] = middle_end_phase + final_drive_angular_freq * (t[release_region] - t_release)
        
        return amplitude_curve, phase_curve


    ################ Spin up then spin down ################
    def linear_spinup__linear_spindown(self, start_phase, start_hold, spinup_time, middle_hold, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq

        # Add extra "pad" time to the middle hold phase in order to make the ions return to their initial position at the end
        total_phase = start_phase + final_drive_angular_freq*spinup_time/2 + final_drive_angular_freq*middle_hold + final_drive_angular_freq*spinup_time/2
        leftover_phase = np.mod(total_phase - start_phase, 2*np.pi)
        pad_phase = 2*np.pi - leftover_phase
        pad_time = pad_phase / final_drive_angular_freq
        middle_hold += pad_time

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_middle = start_hold + spinup_time
        t_spindown = start_hold + spinup_time + middle_hold

        # Time array
        total_time = start_hold + 2 * spinup_time + middle_hold 
        t = np.linspace(0, total_time, int((self.samp_rate*total_time)))

        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_middle)
        middle_region = (t >= t_middle) & (t < t_spindown)
        spindown_region = (t >= t_spindown)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)

        # Phase curve
        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2
        middle_end_phase = spinup_end_phase + final_drive_angular_freq*middle_hold
        
        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase + (final_drive_angular_freq/(2*spinup_time)) * (t[spinup_region] - t_spinup)**2
        phase_curve[middle_region] = spinup_end_phase + final_drive_angular_freq * (t[middle_region] - t_middle) 
        phase_curve[spindown_region] = middle_end_phase \
                                        + final_drive_angular_freq * (t[spindown_region] - t_spindown) \
                                        - (final_drive_angular_freq/(2*spinup_time)) * (t[spindown_region] - t_spindown)**2
        
        return amplitude_curve, phase_curve
    
    def sin2_spinup__sin2_spindown(self, start_phase, start_hold, spinup_time, middle_hold, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq
        
        # Add extra "pad" time to the middle hold phase in order to make the ions return to their initial position at the end
        total_phase = start_phase + final_drive_angular_freq*spinup_time/2 + final_drive_angular_freq*middle_hold + final_drive_angular_freq*spinup_time/2
        leftover_phase = np.mod(total_phase - start_phase, 2*np.pi)
        pad_phase = 2*np.pi - leftover_phase
        pad_time = pad_phase / final_drive_angular_freq
        middle_hold += pad_time

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_middle = start_hold + spinup_time
        t_spindown = start_hold + spinup_time + middle_hold
        
        # Time array
        total_time = start_hold + 2 * spinup_time + middle_hold 
        t = np.linspace(0, total_time, int((self.samp_rate*total_time)))

        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_middle)
        middle_region = (t >= t_middle) & (t < t_spindown)
        spindown_region = (t >= t_spindown)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)

        # Phase curve
        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2
        middle_end_phase = spinup_end_phase + final_drive_angular_freq*middle_hold

        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase \
                                        + final_drive_angular_freq*(t[spinup_region]-t_spinup)/2 \
                                        - final_drive_angular_freq*spinup_time/(2*np.pi) * np.sin(np.pi*(t[spinup_region]-t_spinup)/spinup_time)
        phase_curve[middle_region] = spinup_end_phase + final_drive_angular_freq*(t[middle_region] - t_middle)
        phase_curve[spindown_region] = middle_end_phase \
                                        + final_drive_angular_freq*(t[spindown_region]-t_spindown)/2 \
                                        + final_drive_angular_freq*spinup_time/(2*np.pi) * np.sin(np.pi*(t[spindown_region]-t_spindown)/spinup_time)
        
        return amplitude_curve, phase_curve


    ################ Spin up then hold at constant rotation frequency ################
    def linear_spinup__continue_rotation(self, start_phase, start_hold, spinup_time, time_after_spinup, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq
        
        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_endhold = start_hold + spinup_time
        
        # Time array
        total_time = start_hold + spinup_time + time_after_spinup
        t = np.linspace(0, total_time, int(self.samp_rate * total_time))

        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_endhold)
        endhold_region = (t >= t_endhold)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)

        # Phase curve
        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2

        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase + final_drive_angular_freq/(2*spinup_time)*(t[spinup_region] - t_spinup)**2
        phase_curve[endhold_region] = spinup_end_phase + final_drive_angular_freq*(t[endhold_region] - t_endhold)

        return amplitude_curve, phase_curve
        
    def sin2_spinup__continue_rotation(self, start_phase, start_hold, spinup_time, time_after_spinup, final_drive_freq):
        final_drive_angular_freq = 2*np.pi * final_drive_freq

        # Reference times (labelled by the time at which a section begins, NOT by the duration of that section)
        t_spinup = start_hold
        t_endhold = start_hold + spinup_time
        
        # Time array
        total_time = start_hold + spinup_time + time_after_spinup
        t = np.linspace(0, total_time, int(self.samp_rate * total_time))

        # Reference regions
        spinup_region = (t >= t_spinup) & (t < t_endhold)
        endhold_region = (t >= t_endhold)

        # Amplitude curve
        amplitude_curve = np.ones_like(t)

        # Phase curve
        spinup_end_phase = start_phase + final_drive_angular_freq*spinup_time/2

        phase_curve = start_phase * np.ones_like(t)
        phase_curve[spinup_region] = start_phase \
                                        + final_drive_angular_freq*(t[spinup_region]-t_spinup)/2 \
                                        - final_drive_angular_freq*spinup_time/(2*np.pi) * np.sin(np.pi*(t[spinup_region]-t_spinup)/spinup_time)
        phase_curve[endhold_region] = spinup_end_phase + final_drive_angular_freq*(t[endhold_region] - t_endhold)
        
        return amplitude_curve, phase_curve
    

    ######################## LABRAD SETTINGS ########################

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
        

    @setting(5, "Program Awf", waveform1='*v', waveform2='*v', Vpp='v')
    def program_awf(self, c, waveform1, waveform2, Vpp): 
        #create packed waveform strings
        wf_str1 = self.pack_keysight_packet(waveform1)
        wf_str2 = self.pack_keysight_packet(waveform2)

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
        self.write(self.instr,'SOUR1:VOLT ' + str(Vpp/2.0))
        self.write(self.instr,'SOUR2:VOLT ' + str(Vpp/2.0))
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
        self.set_state(c, 1, 1)
        self.set_state(c, 2, 1)
        #yield self.sync_phases(c)
        #self.read_error_queue()


    @setting(6, "Rotation run initial", state_prep_time='v', total_time='v', scan_param_name='s', scan_param_value='v')
    def rotation_run_initial(self, c, state_prep_time, total_time, scan_param_name=None, scan_param_value=None):
        """
        To be added to the run_initial method of scripts conditioned on rotation being enabled

        This function begins by constructing a dictionary called rp which stores the parameters for rotation
        This is basically a reconstruction of parameters_dict from the script scanner
        Done this way because one cannot pass the full parameters_dict to a server like the Keysight through labrad.
        One parameter (presumably the one being scanned) may be overwritten;
            this requires passing its name and value as the two optional arguments since the scriptscanner server doesn't know the current scan parameter value.
        """
            
        ss = self.client.scriptscanner

        # Create a dictionary with all the rotation parameters
        rotation_parameter_names = yield ss.get_parameter_names('Rotation')
        rp = TreeDict() # rotation parameters dictionary
        for param_name in rotation_parameter_names:
            if param_name == scan_param_name:
                rp[param_name] = scan_param_value
            else:
                rp[param_name] = yield ss.get_parameter('Rotation', param_name)

        # Compute amount of time "before" and "after" the rotation waveform in case needed
        state_prep_time -= U(0.4, 'ms')  # Compensate for 400 us cushion put into state prep
        state_prep_time_minus_rotation = state_prep_time - (rp.spinup_time + rp.middle_hold + rp.release_time) + U(0.2, 'ms')  # 200 us cushion at the beginning (the other 200 us is thus at the end)
        time_after_spinup = total_time - (state_prep_time_minus_rotation + U(0.2, 'ms')) - rp.spinup_time - U(1.0, 'ms')

        # Compute amplitude and phase curves for the selected waveform
        if rp.waveform_label == 'linear_spinup__linear_release':
            (amp, phase) = self.linear_spinup__linear_release(rp.start_phase['rad'],
                                                              state_prep_time_minus_rotation['s'],
                                                              rp.spinup_time['s'],
                                                              rp.middle_hold['s'],
                                                              rp.release_time['s'],
                                                              rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'sin2_spinup__linear_release':
            (amp, phase) = self.sin2_spinup__linear_release(rp.start_phase['rad'],
                                                            state_prep_time_minus_rotation['s'],
                                                            rp.spinup_time['s'],
                                                            rp.middle_hold['s'],
                                                            rp.release_time['s'],
                                                            rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'linear_spinup__adiabatic_release':
            (amp, phase) = self.linear_spinup__adiabatic_release(rp.start_phase['rad'],
                                                                 state_prep_time_minus_rotation['s'], 
                                                                 rp.spinup_time['s'],
                                                                 rp.middle_hold['s'],
                                                                 rp.release_time['s'],
                                                                 rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'linear_spinup__linear_spindown':
            (amp, phase) = self.linear_spinup__linear_spindown(rp.start_phase['rad'],
                                                               state_prep_time_minus_rotation['s'],
                                                               rp.spinup_time['s'],
                                                               rp.middle_hold['s'],
                                                               rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'sin2_spinup__sin2_spindown':
            (amp, phase) = self.sin2_spinup__sin2_spindown(rp.start_phase['rad'],
                                                           state_prep_time_minus_rotation['s'],
                                                           rp.spinup_time['s'],
                                                           rp.middle_hold['s'],
                                                           rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'linear_spinup__continue_rotation':
            (amp, phase) = self.linear_spinup__continue_rotation(rp.start_phase['rad'],
                                                          state_prep_time_minus_rotation['s'],
                                                          rp.spinup_time['s'],
                                                          time_after_spinup['s'],
                                                          rp.final_drive_frequency['Hz'])
        elif rp.waveform_label == 'sin2_spinup__continue_rotation':
            (amp, phase) = self.sin2_spinup__continue_rotation(rp.start_phase['rad'],
                                                        state_prep_time_minus_rotation['s'],
                                                        rp.spinup_time['s'],
                                                        time_after_spinup['s'],
                                                        rp.final_drive_frequency['Hz'])
        else:
            print "Error: no waveform by the name {}".format(rp.waveform_label)

        # Uncomment the below line to debug waveform (the code will not continue until the matplotlib window is closed)
        # self.plot_amp_and_freq_vs_time(amp, phase)

        # Program the waveforms to the two AWG channels
        (waveform1, waveform2) = self.construct_waveforms(amp, phase)
        self.program_awf(c, waveform1, waveform2, rp.voltage_pp['V'])


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
