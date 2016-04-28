from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit 
from space_time.scripts.PulseSequences.advanceDACsShuttle import advance_DACs_shuttle
from space_time.scripts.PulseSequences.resetDACs import reset_DACs

class ramp_voltage_up(pulse_sequence):
    
    required_parameters = [ ('Ramp', 'duration'),
                            ('Ramp', 'initial_field'),
                            ('Ramp', 'final_field'),
                            ('Ramp', 'total_steps'),
                            ('Ramp', 'multipole'),

                            ('advanceDACs', 'times'),
                            ('advanceDACs', 'pulse_length')
    ]

    
    def sequence(self):
        delay =  WithUnit(1, 'us')
        pl = self.parameters.advanceDACs.pulse_length
        times = self.parameters.advanceDACs.times
        for t in times:
            self.addTTL('adv', self.start+WithUnit(t, 's'), pl)
        self.end = self.start + self.parameters.Ramp.duration 

        
#        self.dac_server.set_first_voltages()
#        self.seq = reset_DACs(self.parameters)
#        self.doSequence()