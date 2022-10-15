from common.devel.bum.sequences.pulse_sequence import pulse_sequence
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
        from ScrambleGroundState import ScrambleGroundState
        from EmptySequence import EmptySequence

        p = self.parameters
        sp = p.StatePreparation
        rot = p.Rotation
        
        self.end = U(10., 'us')
        self.addSequence(TurnOffAll)
        self.addSequence(RepumpD) # initializing the state of the ion
        self.addSequence(DopplerCooling) 
        
        if sp.optical_pumping_enable:
            freq729 = self.calc_freq_from_array(p.OpticalPumping.line_selection)
            self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729})
        if sp.eit_cooling_enable:
            print "EIT cooling not yet implemented"
            #self.addSequence(EITcooling)
        if sp.sideband_cooling_enable:
            self.addSequence(SidebandCooling)
        if sp.scramble_ground_state_enable:
            self.addSequence(ScrambleGroundState)
        if rot.rotation_enable:
            rot_prep_time = rot.start_hold + rot.frequency_ramp_time + rot.middle_hold + rot.ramp_down_time + rot.end_hold
            # Add empty sequence for rotation AWF plus 400 us cushion (200 us before, 200 us after)
            self.addSequence(EmptySequence, {'EmptySequence.empty_sequence_duration':rot_prep_time + U(400.0, 'us')})