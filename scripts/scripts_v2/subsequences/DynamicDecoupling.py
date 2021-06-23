from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class DynamicDecoupling(pulse_sequence):
    
    def sequence(self):
        
        dd = self.parameters.DynamicDecoupling
        r = self.parameters.Ramsey
        ampl_off = WithUnit(-63.0, 'dBm')
        frequency_advance_duration = WithUnit(6, 'us')
        self.end = self.start + dd.dd_duration

        dd_echo_frequency = self.calc_freq_from_array(dd.dd_line_selection, dd.dd_sideband)+r.detuning
        
        if r.dynamic_decoupling_enable:
            if dd.dd_repititions != 0:
                echo_centers = [(i-0.5)*dd.dd_duration/(dd.dd_repetitions) for i in range(1,int(dd.dd_repetitions+1))] #CPMG sequence
                self.addDDS(dd.dd_channel_729, self.start, frequency_advance_duration, dd_echo_frequency, ampl_off)
            dur = echo_centers[0]-0.5*dd.dd_pi_time
            for i in range(0,int(dd.dd_repetitions)):
                # echo_phase = (((-1)**(i+1))*(45)) + 45  #XY phase configuration
                # print echo_phase
                echo_phase = 0
                self.addDDS(dd.dd_channel_729, self.start + echo_centers[i] - 0.5*dd.dd_pi_time, dd.dd_pi_time, dd_echo_frequency, dd.dd_amplitude_729, WithUnit(echo_phase,'deg'))
        



