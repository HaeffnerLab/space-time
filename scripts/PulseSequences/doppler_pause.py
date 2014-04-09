from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.DopplerCooling import doppler_cooling
from subsequences.TurnOffAll import turn_off_all
from labrad.units import WithUnit
from treedict import TreeDict

class doppler_pause(pulse_sequence):

    required_parameters = [
                            ('Heating', 'background_heating_time')
                            ]
    required_subsequences = [doppler_Cooling, turn_off_all]

    replaced_parameters = {empty_sequence:[('EmptySequence','empty_sequence_duration')]
                           }

    def sequence(self):
        p = self.parameters
        self.addSequence(turn_off_all)
        self.addSequence(doppler_cooling)
        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':p.Heating.background_heating_time}))
        self.addSequence(doppler_cooling)
        
