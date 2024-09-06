from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.RepumpDwithDoppler import doppler_cooling_after_repump_d
from subsequences.EmptySequence import empty_sequence
from subsequences.OpticalPumping import optical_pumping
from subsequences.TurnOffAll import turn_off_all
from subsequences.EitCooling_StateDetection import eit_cooling_statedetection
from subsequences.Excitation_with_397 import excite_with_397
from labrad.units import WithUnit
from treedict import TreeDict

class eit_lineshape_397(pulse_sequence):
    
    required_parameters = [ 
                           ('Heating', 'background_heating_time'),
                           ('StatePreparation','optical_pumping_enable'), 
                           ('StatePreparation','eit_cooling_enable'),
                           ]
    
    required_subsequences = [doppler_cooling_after_repump_d, empty_sequence, optical_pumping, 
                             turn_off_all ,eit_cooling_statedetection, excite_with_397]
    
    replaced_parameters = {empty_sequence:[('EmptySequence','empty_sequence_duration'),]}

    def sequence(self):
        p = self.parameters
        self.end = WithUnit(10, 'us')
        self.addSequence(turn_off_all)
        #self.addSequence(sample_pid)
        
        self.addSequence(doppler_cooling_after_repump_d)
        if p.StatePreparation.optical_pumping_enable:
            self.addSequence(optical_pumping)
        
        self.addSequence(eit_cooling_statedetection)
                    
                
