from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from TurnOffAll import TurnOffAll
from RepumpD import RepumpD
from StateReadout import StateReadout

class CheckForIon(pulse_sequence):
   
    def sequence(self):
        sos = self.parameters.SOSBeamConditional
        
        # Start by trying to repump out of D states
        self.addSequence(TurnOffAll)
        self.addSequence(RepumpD, {'RepumpD52.repump_d_duration':sos.repump_duration})
        
        # Use readout parameters to try to make the ion fluoresce
        self.addSequence(StateReadout, {'StateReadout.state_readout_duration':sos.sos_duration})
