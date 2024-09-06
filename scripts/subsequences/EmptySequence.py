from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class EmptySequence(pulse_sequence):
    
    def sequence(self):
        
        es = self.parameters.EmptySequence

        duration = es.empty_sequence_duration

        if es.noise_enable and (duration > U(50, 'us')):
            self.addTTL('rot_switch_awg_off', self.start-U(135, 'us'), duration-U(50, 'us'))
            self.addTTL('rot_switch_noise_on', self.start-U(120, 'us'), duration-U(5, 'us'))

        self.end = self.start + duration
