from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.RepumpDwithDoppler import doppler_cooling_after_repump_d
from subsequences.SidebandCooling import sideband_cooling
from subsequences.OpticalPumping import optical_pumping
from subsequences.Tomography import tomography_readout
from subsequences.TurnOffAll import turn_off_all
from subsequences.EmptySequence import empty_sequence
from subsequences.RamseyJuggledMz import ramsey_juggled_mz_excitation
from subsequences.ScrambleGroundState import scramble_ground_state
from treedict import TreeDict

from labrad.units import WithUnit
           
class ramsey_juggled_mz(pulse_sequence):
    
    required_parameters = [
                           ('Heating', 'background_heating_time'),
                           ('StatePreparation','optical_pumping_enable'), 
                           ('StatePreparation','sideband_cooling_enable'),
                           ('StatePreparation','scramble_ground_state_enable'),
                           ]

    required_subsequences = [doppler_cooling_after_repump_d, optical_pumping, 
                             tomography_readout, turn_off_all, sideband_cooling, ramsey_juggled_mz_excitation, empty_sequence,scramble_ground_state]

    replaced_parameters = {empty_sequence:[('EmptySequence','empty_sequence_duration'),]}

                             
    def sequence(self):
        p = self.parameters
        self.end = WithUnit(10, 'us')
        self.addSequence(turn_off_all)
        #self.addSequence(sample_pid)
        
        self.addSequence(doppler_cooling_after_repump_d)
        if p.StatePreparation.optical_pumping_enable:
            self.addSequence(optical_pumping)
        if p.StatePreparation.sideband_cooling_enable:
            self.addSequence(sideband_cooling)
        if p.StatePreparation.scramble_ground_state_enable:
            self.addSequence(scramble_ground_state)
        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':p.Heating.background_heating_time}))
        self.addSequence(ramsey_juggled_mz_excitation)
        self.addSequence(tomography_readout)
