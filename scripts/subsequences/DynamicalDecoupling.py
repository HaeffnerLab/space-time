from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class DynamicalDecoupling(pulse_sequence):
    
    def sequence(self):
        
        dd = self.parameters.DynamicalDecoupling
        r = self.parameters.Ramsey
        ampl_off = U(-63.0, 'dBm')
        frequency_advance_duration = U(6, 'us')
        self.end = self.start + dd.dd_duration

        dd_echo_frequency = self.calc_freq_from_array(dd.dd_line_selection, dd.dd_sideband)+r.detuning
        
        if r.noise_enable:
            self.addTTL('rot_switch_awg_off', self.start-U(135, 'us'), dd.dd_duration+U(0, 'us'))
            self.addTTL('rot_switch_noise_on', self.start-U(220, 'us'), dd.dd_duration+U(130, 'us'))

        if r.dynamical_decoupling_enable:
            if dd.dd_repititions != 0:
                echo_centers = [(i-0.5)*dd.dd_duration/(dd.dd_repetitions) for i in range(1,int(dd.dd_repetitions+1))] #CPMG sequence
                self.addDDS(dd.dd_channel_729, self.start, frequency_advance_duration, dd_echo_frequency, ampl_off)
            dur = echo_centers[0]-0.5*dd.dd_pi_time
            for i in range(0,int(dd.dd_repetitions)):
                # echo_phase = (((-1)**(i+1))*(45)) + 45  #XY phase configuration
                # print echo_phase
                echo_phase = 0
                self.addDDS(dd.dd_channel_729, self.start + echo_centers[i] - 0.5*dd.dd_pi_time, dd.dd_pi_time, dd_echo_frequency, dd.dd_amplitude_729, U(echo_phase,'deg'))
