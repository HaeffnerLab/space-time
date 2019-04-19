from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from RabiExcitation import rabi_excitation, rabi_excitation_no_offset
from EmptySequence import empty_sequence, empty_sequence_with_echo
from treedict import TreeDict
from labrad.units import WithUnit
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm

class ramsey_two_mode_excitation(pulse_sequence):
    
    required_parameters = [ 
                           ('Ramsey','spin_echo_enable'),
                           ('Ramsey','ramsey_time'),
                           ('Ramsey','first_pulse_duration'),                           
                           ('Ramsey','second_pulse_duration'),
                           ('Ramsey','second_pulse_phase'),
                           ('Ramsey', 'channel_729'),
                           ('Ramsey','frequency_selection'),

                           ('Ramsey','first_pulse_line'),
                           ('Ramsey','first_pulse_manual_frequency_729'),
                           ('Ramsey','first_pulse_sideband_selection'),
                           ('Ramsey','first_pulse_frequency'),

                           ('Ramsey','second_pulse_line'),
                           ('Ramsey','second_pulse_manual_frequency_729'),
                           ('Ramsey','second_pulse_sideband_selection'),
                           ('Ramsey','second_pulse_frequency'),

                           ('Ramsey','echo_offset'),
                          ]

    required_subsequences = [rabi_excitation, empty_sequence, rabi_excitation_no_offset,empty_sequence_with_echo]
    replaced_parameters = {
                           rabi_excitation:[('Excitation_729','rabi_excitation_duration'),
                                            ('Excitation_729','rabi_excitation_phase'),
                                            ('Excitation_729', 'channel_729'),
                                            ('Excitation_729','rabi_excitation_frequency'),
                                            ],
                           rabi_excitation_no_offset:[('Excitation_729','rabi_excitation_duration'),
                                                      ('Excitation_729','rabi_excitation_phase'),
                                                      ('Excitation_729', 'channel_729'),
                                                      ('Excitation_729','rabi_excitation_frequency'),
                                                      ],
                           empty_sequence:[('EmptySequence','empty_sequence_duration')],
                           empty_sequence_with_echo:[('EmptySequence','empty_sequence_duration')]
                           }


    def sequence(self):
        r = self.parameters.Ramsey
        replace = TreeDict.fromdict({
                                     'Excitation_729.rabi_excitation_duration':r.first_pulse_duration,
                                     'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                     'Excitation_729.channel_729':r.channel_729,
                                     'Excitation_729.rabi_excitation_frequency':r.first_pulse_frequency
                                     }) 
        awg_wait_time = WithUnit(2,'ms')

        self.addTTL('awg_off',self.start,awg_wait_time+r.ramsey_time+r.first_pulse_duration+r.second_pulse_duration)
        #self.addTTL('awg_on',self.start,awg_wait_time+r.ramsey_time+r.first_pulse_duration+r.second_pulse_duration)
        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':awg_wait_time}))
        self.addSequence(rabi_excitation, replace)
        if r.spin_echo_enable:
          self.addSequence(empty_sequence_with_echo, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':r.ramsey_time}))
        else:
          self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':r.ramsey_time}))
        #self.addDDS('radial', self.end, r.ramsey_time, WithUnit(220.0,'MHz'), WithUnit(-13.0,'dBm'))
        #self.end = self.end + r.ramsey_time
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.second_pulse_duration,
                             'Excitation_729.rabi_excitation_phase':r.second_pulse_phase,
                             'Excitation_729.channel_729':r.channel_729,
                             'Excitation_729.rabi_excitation_frequency':r.second_pulse_frequency
                             })
        self.addSequence(rabi_excitation_no_offset, replace)
        # self.addSequence(rabi_excitation_no_offset, replace) #this is technically correct but can't do pulses shorter than 6us
        # print(r.first_pulse_frequency,r.second_pulse_frequency,r.first_pulse_frequency-r.second_pulse_frequency)
        # print(r.second_pulse_duration,r.first_pulse_duration)