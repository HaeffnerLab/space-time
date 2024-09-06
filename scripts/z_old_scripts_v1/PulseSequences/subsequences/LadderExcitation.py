from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit
from RabiExcitation import rabi_excitation, rabi_excitation_no_offset
from treedict import TreeDict



class ladder_excitation_no_offset(pulse_sequence):
    # Same as ladder_excitation except without any DDS offset wait times.

    required_parameters = [
                          ('Ramsey','ladder_blue_amplitude'),
                          ('Ramsey','ladder_red_amplitude'),
                          ('Ramsey','ladder_blue_pi_duration'),
                          ('Ramsey','ladder_red_pi_duration'),
                          ('Ramsey','ladder_blue_channel_729'),
                          ('Ramsey','ladder_red_channel_729'),
                          ('Ramsey','ladder_blue_frequency'),
                          ('Ramsey','ladder_red_frequency'),
                          ('Ramsey','ladder_number_pi_steps'),
                          ]

    required_subsequences = [rabi_excitation_no_offset]

    replaced_parameters = {
                           rabi_excitation_no_offset:[('Excitation_729','rabi_excitation_frequency'),
                                                      ('Excitation_729','rabi_excitation_amplitude'),
                                                      ('Excitation_729','rabi_excitation_duration'),
                                                      ('Excitation_729','rabi_excitation_phase'),
                                                      ('Excitation_729', 'channel_729')
                                                      ]
                           }


    def sequence(self):
        r = self.parameters.Ramsey
        replace_pi2_blue = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_blue_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_blue_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_blue_pi_duration/2.0,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_blue_channel_729
                                             }) 
        replace_pi_blue = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_blue_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_blue_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_blue_pi_duration,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_blue_channel_729
                                             }) 
        replace_pi_red = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_red_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_red_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_red_pi_duration,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_red_channel_729
                                             })


        for i in range(int(r.ladder_number_pi_steps)+1):
            # Choose which pulse to do: pi/2, pi+, or pi-
            if i == 0:
                replace = replace_pi2_blue
            elif i % 2:
                replace = replace_pi_red
            else:
                replace = replace_pi_blue
            self.addSequence(rabi_excitation_no_offset, replace)




class ladder_excitation_reverse_no_offset(pulse_sequence):
    # Same as ladder_excitation_no_offset except backwards.

    required_parameters = [
                          ('Ramsey','ladder_blue_amplitude'),
                          ('Ramsey','ladder_red_amplitude'),
                          ('Ramsey','ladder_blue_pi_duration'),
                          ('Ramsey','ladder_red_pi_duration'),
                          ('Ramsey','ladder_blue_channel_729'),
                          ('Ramsey','ladder_red_channel_729'),
                          ('Ramsey','ladder_blue_frequency'),
                          ('Ramsey','ladder_red_frequency'),
                          ('Ramsey','ladder_number_pi_steps'),
                          ('Ramsey','second_pulse_phase'),
                          ]

    required_subsequences = [rabi_excitation_no_offset]

    replaced_parameters = {
                           rabi_excitation_no_offset:[('Excitation_729','rabi_excitation_frequency'),
                                                      ('Excitation_729','rabi_excitation_amplitude'),
                                                      ('Excitation_729','rabi_excitation_duration'),
                                                      ('Excitation_729','rabi_excitation_phase'),
                                                      ('Excitation_729', 'channel_729')
                                                      ]
                           }


    def sequence(self):
        r = self.parameters.Ramsey
        replace_pi2_blue = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_blue_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_blue_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_blue_pi_duration/2.0,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_blue_channel_729
                                             }) 
        replace_pi_blue = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_blue_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_blue_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_blue_pi_duration,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_blue_channel_729
                                             }) 
        replace_pi_red = TreeDict.fromdict({
                                             'Excitation_729.rabi_excitation_frequency':r.ladder_red_frequency,
                                             'Excitation_729.rabi_excitation_amplitude':r.ladder_red_amplitude,
                                             'Excitation_729.rabi_excitation_duration':r.ladder_red_pi_duration,
                                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                             'Excitation_729.channel_729':r.ladder_red_channel_729
                                             })

        N = int(r.ladder_number_pi_steps)
        for i in range(N+1):
            # Choose which pulse to do: pi/2, pi+, or pi-
            if i == N:
                replace = replace_pi2_blue
                replace['Excitation_729.rabi_excitation_phase'] = r.second_pulse_phase
            elif (N-i)%2:
                replace = replace_pi_red
            else:
                replace = replace_pi_blue
            self.addSequence(rabi_excitation_no_offset, replace)