from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict

class StatePreparation(pulse_sequence):
    
    #name = 'State preparation'

    scannable_params = {
                        }

    show_params= [

                  ]

    def sequence(self):
        from TurnOffAll import TurnOffAll
        from RepumpD import RepumpD
        from SOSBeam import SOSBeam
        from DopplerCooling import DopplerCooling
        from OpticalPumping import OpticalPumping
        from SidebandCooling import SidebandCooling
        from Rotation import Rotation
        from EmptySequence import EmptySequence
        from GatePulse import GatePulse
        from RFModulation import RFModulation

        sp = self.parameters.StatePreparation
        rfmod = self.parameters.RFModulation

        self.end = U(10., 'us')

        self.addSequence(TurnOffAll)

        self.addSequence(RepumpD)

        if sp.sos_enable:
            self.addSequence(SOSBeam)

        self.addSequence(DopplerCooling) 

        if sp.optical_pumping_enable:
            freq729 = self.calc_freq_from_array(self.parameters.OpticalPumping.line_selection)
            self.addSequence(OpticalPumping, {'OpticalPumping.optical_pumping_frequency_729':freq729})

        if sp.sideband_cooling_enable:
            if rfmod.turn_on_before == 'sideband_cooling':
                self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":rfmod.padtime})
            self.addSequence(SidebandCooling)

        self.addSequence(GatePulse)
        
        if sp.rotation_enable:
            if rfmod.turn_on_before == 'rotational_state_prep':
                self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":rfmod.padtime})
            self.addSequence(Rotation)
        if (rfmod.turn_on_before == 'wait_time'):
            self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":rfmod.padtime})
            