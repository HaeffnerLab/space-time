from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.RepumpDwithDoppler import doppler_cooling_after_repump_d
from subsequences.TurnOffAll import turn_off_all
from subsequences.Excitation_with_397 import excite_with_397
from labrad.units import WithUnit
from treedict import TreeDict

class lineshape_397(pulse_sequence):
    
    required_parameters = [ 
                           ]
    
    required_subsequences = [doppler_cooling_after_repump_d,
                             turn_off_all, excite_with_397]
    

    def sequence(self):
        p = self.parameters
        self.end = WithUnit(10, 'us')
        self.addSequence(turn_off_all)
        
        self.addSequence(doppler_cooling_after_repump_d)

        
        self.addSequence(excite_with_397)
                    
                
