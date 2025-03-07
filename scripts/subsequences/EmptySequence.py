from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class EmptySequence(pulse_sequence):
    
    def sequence(self):
        
        es = self.parameters.EmptySequence
        duration = es.empty_sequence_duration

        if es.noise_enable and (duration > U(50, 'us')):
            self.addTTL('rot_switch_awg_off', self.start-U(135, 'us'), duration-U(50, 'us'))
            self.addTTL('rot_switch_noise_on', self.start-U(120, 'us'), duration-U(5, 'us'))

        #March 6, 2025: We are removing this functionality from EmptySequence because we are creating a new subsequence called GatePulse.

        #frequency_advance_duration = U(6, 'us')
        # if es.enable729:
        #     freq_729_pos = self.calc_freq_from_array(es.line_selection, [0.0, 0.0, 0.0, 0.0, 0.0])
        #     freq_729 = freq_729_pos + es.stark_shift_729
            
        #     # Turn off 729 for 6 us while changing DDS frequency
        #     self.addDDS(es.channel729, self.start, frequency_advance_duration, freq_729, U(-63.0, 'dBm'))
        #     # Do the actual pulse
        #     self.addDDS(es.channel729, self.start + frequency_advance_duration, duration, freq_729, es.amplitude729, U(0, 'deg'))

        # if es.enable866:
        #     self.addDDS('866DP', self.start, duration, es.frequency866, es.amplitude866)

        # if es.enable729:
        #     self.end = self.start + frequency_advance_duration + duration

        else:
            self.end = self.start + duration
