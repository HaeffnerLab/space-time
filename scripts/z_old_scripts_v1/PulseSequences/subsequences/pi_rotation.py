from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class pi_rotation(pulse_sequence):
    
    
    required_parameters = [
                  ('PiRotation','pi_rotation_amplitude'),
                  ('PiRotation','pi_rotation_duration'),
                  ('PiRotation','pi_rotation_frequency'),
                  
                  ('StatePreparation', 'channel_729')
                  ]

    def sequence(self):
        pr = self.parameters.PiRotation
        channel_729 = self.parameters.StatePreparation.channel_729
        frequency_advance_duration = WithUnit(6, 'us')
        self.end = self.start + pr.pi_rotation_duration + frequency_advance_duration
        ampl_off = WithUnit(-63.0, 'dBm')
        self.addDDS(channel_729, self.start, frequency_advance_duration, pr.pi_rotation_frequency, ampl_off)
        self.addDDS(channel_729, self.start+frequency_advance_duration, pr.pi_rotation_duration, pr.pi_rotation_frequency, pr.pi_rotation_amplitude)