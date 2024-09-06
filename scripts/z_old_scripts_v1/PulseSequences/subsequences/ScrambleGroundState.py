from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class scramble_ground_state(pulse_sequence):
    
    required_parameters = [
                          ('ScrambleGroundState', 'channel_729'),
                          ('ScrambleGroundState','pi_time'),
                          ('ScrambleGroundState','line_selection'),
                          ('ScrambleGroundState','repump_time'),
                          ('ScrambleGroundState','excitation_amplitude'),
                          ('ScrambleGroundState','excitation_frequency'),
                          ]

    def sequence(self):
        #this hack will be not needed with the new dds parsing methods
        p = self.parameters.ScrambleGroundState
        print 'sgs',p.excitation_frequency  
        frequency_advance_duration = WithUnit(6, 'us')
        ampl_off = WithUnit(-63.0, 'dBm')
        self.end = self.start + frequency_advance_duration + p.pi_time + p.repump_time
        #first advance the frequency but keep amplitude low        
        self.addDDS(p.channel_729, self.start, frequency_advance_duration, p.excitation_frequency, ampl_off)
        self.addDDS(p.channel_729, self.start + frequency_advance_duration, p.pi_time, p.excitation_frequency, p.excitation_amplitude,WithUnit(0,'deg'))
        self.addDDS('854DP',self.start + frequency_advance_duration + p.pi_time, p.repump_time, WithUnit(80.0,'MHz'), WithUnit(-10.0,'dBm'),WithUnit(0,'deg'))
