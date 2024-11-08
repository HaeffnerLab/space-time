from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class EmptySequence(pulse_sequence):
    
    def sequence(self):
        
        es = self.parameters.EmptySequence

        duration = es.empty_sequence_duration

        if es.noise_enable and (duration > U(50, 'us')):
            self.addTTL('rot_switch_awg_off', self.start-U(135, 'us'), duration-U(50, 'us'))
            self.addTTL('rot_switch_noise_on', self.start-U(120, 'us'), duration-U(5, 'us'))

        if es.enable729:
            freq_729_pos = self.calc_freq_from_array(es.line_selection, [0.0, 0.0, 0.0, 0.0, 0.0])
            freq_729 = freq_729_pos + es.stark_shift_729
            self.addDDS(es.channel729, self.start, duration, freq_729, es.amplitude729)
        if es.enable866:
            self.addDDS('866DP', self.start, duration, es.frequency866, es.amplitude866)

        self.end = self.start + duration
