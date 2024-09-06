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
        print "STARTING STATE PREP"
        print self.start
        
        from TurnOffAll import TurnOffAll
        from RepumpD import RepumpD
        from DopplerCooling import DopplerCooling
        from OpticalPumping import OpticalPumping
        from SidebandCooling import SidebandCooling
        from EmptySequence import EmptySequence
        from ScrambleGroundState import ScrambleGroundState

        p = self.parameters
        sp = p.StatePreparation
        
        self.end = U(10., 'us')
        self.addSequence(TurnOffAll)
        self.addSequence(RepumpD) # initializing the state of the ion
        self.addSequence(DopplerCooling) 
        
        if sp.optical_pumping_enable:
            freq729 = self.calc_freq_from_array_universal(p.OpticalPumping.line_selection)
            self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729})
        if sp.eit_cooling_enable:
          print "EIT cooling not yet implemented"
          #self.addSequence(EITcooling)
        if sp.sideband_cooling_enable:
          self.addSequence(SidebandCooling)
        if sp.scramble_ground_state_enable:
          self.addSequence(ScrambleGroundState)