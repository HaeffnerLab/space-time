from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from RabiExcitation import rabi_excitation, rabi_excitation_no_offset
from EmptySequence import empty_sequence
from treedict import TreeDict
from labrad.units import WithUnit
from EitCooling import eit_cooling

class ramsey_excitation_with_eit(pulse_sequence):
    
    required_parameters = [ 
                           ('Ramsey','ramsey_time'),
                           ('Ramsey','first_pulse_duration'),
                           ('Ramsey','second_pulse_duration'),
                           ('Ramsey','second_pulse_phase'),
                           ('Ramsey', 'channel_729'),
                          ]

    required_subsequences = [rabi_excitation, rabi_excitation_no_offset, eit_cooling]
    replaced_parameters = {
                           rabi_excitation:[('Excitation_729','rabi_excitation_duration'),
                                            ('Excitation_729','rabi_excitation_phase'),
                                            ('Excitation_729', 'channel_729'),
                                            ],
                           rabi_excitation_no_offset:[('Excitation_729','rabi_excitation_duration'),
                                                      ('Excitation_729','rabi_excitation_phase'),
                                                      ('Excitation_729', 'channel_729'),
                                                      ],
                           eit_cooling:[
                               ('EitCooling','eit_cooling_amplitude_397_linear'),
                               ('EitCooling','eit_cooling_duration')
                               ]
                           }
    
    def sequence(self):
        r = self.parameters.Ramsey
        
        # First ramsey pulse
        replace = TreeDict.fromdict({
                                     'Excitation_729.rabi_excitation_duration':r.first_pulse_duration,
                                     'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                                     'Excitation_729.channel_729':r.channel_729,
                                     })
        self.addSequence(rabi_excitation, replace)

        # EIT Cooling
        replace = TreeDict.fromdict({
                           'EitCooling.eit_cooling_amplitude_397_linear':WithUnit(-63.0, 'dBm'),
                           'EitCooling.eit_cooling_duration':r.ramsey_time
                           })
        self.addSequence(eit_cooling, replace)

        # Second ramsey pulse
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.second_pulse_duration,
                             'Excitation_729.rabi_excitation_phase':r.second_pulse_phase,
                             'Excitation_729.channel_729':r.channel_729,
                             })
        self.addSequence(rabi_excitation_no_offset, replace)



