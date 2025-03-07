from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class GatePulse(pulse_sequence):
    
    def sequence(self):
        
        gp = self.parameters.GatePulse
        duration = gp.gate_pulse_duration
        frequency_advance_duration = U(6, 'us')

        if gp.enable729:
            freq_729_pos = self.calc_freq_from_array(gp.line_selection, [0.0, 0.0, 0.0, 0.0, 0.0])
            freq_729 = freq_729_pos + gp.stark_shift_729
            
            # Turn off 729 for 6 us while changing DDS frequency
            self.addDDS(gp.channel729, self.start, frequency_advance_duration, freq_729, U(-63.0, 'dBm'))
            # Do the actual pulse
            self.addDDS(gp.channel729, self.start + frequency_advance_duration, duration, freq_729, gp.amplitude729, U(0, 'deg'))

        if gp.enable866:
            self.addDDS('866DP', self.start, duration, gp.frequency866, gp.amplitude866)

        if gp.enable729:
            self.end = self.start + frequency_advance_duration + duration

        else:
            self.end = self.start + duration
