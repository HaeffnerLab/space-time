from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit 
from space_time.scripts.PulseSequences.advanceDACsShuttle import advance_DACs_shuttle
from space_time.scripts.PulseSequences.resetDACs import reset_DACs

class reset_dac(pulse_sequence):
    
    required_parameters = [ ('Ramp', 'duration'),
                            ('Ramp', 'initial_field'),
                            ('Ramp', 'final_field'),
                            ('Ramp', 'total_steps'),
                            ('Ramp', 'multipole'),

                            ('advanceDACs', 'times'),
                            ('advanceDACs', 'pulse_length')
    ]

    
    def sequence(self):
        delay = WithUnit(1, 'us')
        pl = self.parameters.advanceDACs.pulse_length
        self.addTTL('rst', self.start, 3*pl)
        self.addTTL('adv', self.start+pl, pl)
        self.end = self.start + 3*pl + delay
        
#        self.dac_server.set_first_voltages()
#        self.seq = reset_DACs(self.parameters)
#        self.doSequence()