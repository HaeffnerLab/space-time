from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class DynamicDecoupling_stark(pulse_sequence):
    
    def sequence(self):
        
        dd = self.parameters.DynamicDecoupling
        bfi = self.parameters.BfieldIncoh
        bf2 = self.parameters.Bfield2
        ac = self.parameters.ACStarkShift
        r = self.parameters.Ramsey
        ampl_off = WithUnit(-63.0, 'dBm')
        frequency_advance_duration = WithUnit(6, 'us')
        self.end = self.start + dd.dd_duration

        dd_echo_frequency = self.calc_freq_from_array(dd.dd_line_selection, dd.dd_sideband)+r.detuning
        ac_stark_freq_729 = self.calc_freq_from_array(ac.line_selection) + ac.frequency729
            
        if dd.dd_repititions != 0:
            echo_centers = [(i-0.5)*dd.dd_duration/(dd.dd_repetitions) for i in range(1,int(dd.dd_repetitions+1))] #CPMG sequence
            self.addDDS(dd.dd_channel_729, self.start, frequency_advance_duration, dd_echo_frequency, ampl_off)
        
        if r.dynamic_decoupling_enable:
            dur = echo_centers[0]-0.5*dd.dd_pi_time
            if (bfi.bfield_enable or bf2.bfield_enable) and ac.acstark_enable:
                self.addDDS(ac.channel729, self.start, dur, ac_stark_freq_729, ac.amplitude729)
                
            for i in range(0,int(dd.dd_repetitions)):
                echo_phase = 0
                if ((bfi.bfield_enable and not bfi.first_only) or (bf2.bfield_enable and not bf2.first_only)) and ac.acstark_enable:
                    if i < dd.dd_repetitions - 1:
                        dur = echo_centers[i+1] - echo_centers[i] - dd.dd_pi_time
                    else: 
                        dur = r.ramsey_time - echo_centers[i] - 0.5*dd.dd_pi_time
                    self.addDDS(ac.channel729, self.start + echo_centers[i] + 0.5*dd.dd_pi_time, dur, ac_stark_freq_729, ac.amplitude729)
                self.addDDS(dd.dd_channel_729, self.start + echo_centers[i] - 0.5*dd.dd_pi_time, dd.dd_pi_time, dd_echo_frequency, dd.dd_amplitude_729, WithUnit(echo_phase,'deg'))
        


