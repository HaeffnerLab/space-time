from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.RepumpDwithDoppler import doppler_cooling_after_repump_d
from subsequences.SidebandCooling import sideband_cooling
from subsequences.OpticalPumping import optical_pumping
from subsequences.Tomography import tomography_readout
from subsequences.TurnOffAll import turn_off_all
from subsequences.RamseyWithEIT import ramsey_excitation_with_eit

from labrad.units import WithUnit
           
class ramsey_with_eit(pulse_sequence):
    
    required_parameters = [
                           ('StatePreparation','optical_pumping_enable'), 
                           ('StatePreparation','sideband_cooling_enable'),
                           ]

    required_subsequences = [doppler_cooling_after_repump_d, optical_pumping, 
                             tomography_readout, turn_off_all, sideband_cooling, ramsey_excitation_with_eit]
                             
    def sequence(self):
        p = self.parameters
        self.end = WithUnit(10, 'us')
        self.addSequence(turn_off_all)

        self.addSequence(doppler_cooling_after_repump_d)
        if p.StatePreparation.optical_pumping_enable:
            self.addSequence(optical_pumping)
        if p.StatePreparation.sideband_cooling_enable:
            self.addSequence(sideband_cooling)
        self.addSequence(ramsey_excitation_with_eit)
        self.addSequence(tomography_readout)

