from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from LadderExcitation import ladder_excitation_no_offset, ladder_excitation_reverse_no_offset
from EmptySequence import empty_sequence
from treedict import TreeDict
from labrad.units import WithUnit

class ramsey_ladder_excitation(pulse_sequence):
    
    required_parameters = [ 
                           ('Ramsey','spin_echo_enable'),
                           ('Ramsey','ramsey_time'),
                           ('Ramsey','ladder_blue_channel_729'),
                           ('Ramsey','ladder_red_channel_729'),
                           ('Ramsey','ladder_blue_frequency'),
                           ('Ramsey','ladder_red_frequency'),
                           ('Ramsey','ladder_number_pi_steps'),
                           ('Ramsey','ladder_blue_pi_duration'),
                           ('Ramsey','ladder_red_pi_duration'),
                          ]

    required_subsequences = [ladder_excitation_no_offset, ladder_excitation_reverse_no_offset, empty_sequence]
    replaced_parameters = {
                           empty_sequence:[('EmptySequence', 'empty_sequence_duration')],
                           ladder_excitation_reverse_no_offset:[('Ramsey', 'second_pulse_phase')]
                           }
    
    def sequence(self):
        r = self.parameters.Ramsey
        p = self.parameters.Excitation_729
        
        # Add the 6 us waits manually here before starting the ladder sequence
        frequency_advance_duration = WithUnit(6, 'us')
        ampl_off = WithUnit(-63.0, 'dBm')
        self.addDDS(r.ladder_blue_channel_729, self.start,                            frequency_advance_duration, r.ladder_blue_frequency, ampl_off)
        self.addDDS(r.ladder_red_channel_729,  self.start+frequency_advance_duration, frequency_advance_duration, r.ladder_red_frequency, ampl_off)
        ramsey_start = self.start+WithUnit(12, 'us')

        # First set of pulses
        self.addSequence(ladder_excitation_no_offset, position=ramsey_start)

        # Set of echo pulses
        if r.spin_echo_enable:
            # First calculate how much time the echo pulses will take
            n_blue_pulses = r.ladder_number_pi_steps + ((r.ladder_number_pi_steps+1)%2)
            n_red_pulses = r.ladder_number_pi_steps + (r.ladder_number_pi_steps%2)
            echo_time = n_blue_pulses*r.ladder_blue_pi_duration + n_red_pulses*r.ladder_red_pi_duration

            # Now add the pulses. Wait times will have half the echo time subtracted off.
            self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':(r.ramsey_time-echo_time)/2}))
            self.addSequence(ladder_excitation_reverse_no_offset, TreeDict.fromdict({'Ramsey.second_pulse_phase':WithUnit(0, 'deg')})) #There should be no extra phase on this pulse since it's just supposed to be the echo
            self.addSequence(ladder_excitation_no_offset)
            self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':(r.ramsey_time-echo_time)/2}))
        else:
            self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':r.ramsey_time}))
        
        # Final set of pulses
        self.addSequence(ladder_excitation_reverse_no_offset)