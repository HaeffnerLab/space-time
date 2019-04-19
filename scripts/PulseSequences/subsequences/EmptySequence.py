from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class empty_sequence(pulse_sequence):
    
    
    required_parameters =  [('EmptySequence','empty_sequence_duration')]

    def sequence(self):
        self.end = self.start + self.parameters.EmptySequence.empty_sequence_duration

class empty_sequence_with_echo(pulse_sequence):
    
    
    required_parameters =  [('EmptySequence','empty_sequence_duration'),
    						('Ramsey', 'echo_channel_729'),
    						('Ramsey','echo_repitions'),
    						('Ramsey','echo_duration'),
    						('Ramsey','echo_amplitude'),
    						('Ramsey','echo_frequency'),
                            ('Ramsey','echo_offset'),
                            ]

    def sequence(self):
    	p = self.parameters.Excitation_729
    	r = self.parameters.Ramsey
    	ampl_off = WithUnit(-63.0, 'dBm')
    	frequency_advance_duration = WithUnit(6, 'us')
        self.end = self.start + self.parameters.EmptySequence.empty_sequence_duration
        self.addDDS(r.echo_channel_729, self.start, frequency_advance_duration, r.echo_frequency, ampl_off)

    	# echo_center = self.parameters.EmptySequence.empty_sequence_duration/2.
    	# echo_start = echo_center - 0.5*r.echo_duration

    	# echo_centers = [i*self.parameters.EmptySequence.empty_sequence_duration/(r.echo_repitions+1.) for i in range(1,int(r.echo_repitions+1))]  #original w/ evenly space pulses

        echo_centers = [(i-0.5)*self.parameters.EmptySequence.empty_sequence_duration/(r.echo_repitions) for i in range(1,int(r.echo_repitions+1))] #CPMG sequence
    	for i in range(0,int(r.echo_repitions)):
            echo_phase = (((-1)**(i+1))*(45)) + 45  #XY phase configuration
            print echo_phase
            echo_phase = 0
            self.addDDS(r.echo_channel_729, self.start + echo_centers[i] - 0.5*r.echo_duration+r.echo_offset, r.echo_duration, r.echo_frequency, r.echo_amplitude, WithUnit(echo_phase,'deg'))
