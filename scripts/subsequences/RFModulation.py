from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

from TurnOffAll import TurnOffAll
from RepumpD import RepumpD
from SOSBeam import SOSBeam
from DopplerCooling import DopplerCooling
from OpticalPumping import OpticalPumping
from SidebandCooling import SidebandCooling
from EmptySequence import EmptySequence
from GatePulse import GatePulse
from Rotation import Rotation

# Not exactly a subsequence, but a convenience function for adding an RF modulation TTL pulse
def RFModulation(sequence, time_start_readout):
    params = sequence.parameters
    rfmod = params.RFModulation

    time_other_stateprep = TurnOffAll(params).end + RepumpD(params).end + DopplerCooling(params).end + U(10., 'us')
    if params.StatePreparation.sos_enable:
        time_other_stateprep += SOSBeam(params).end
    if params.StatePreparation.optical_pumping_enable:
        time_other_stateprep += OpticalPumping(params).end
    
    time_sbc = SidebandCooling(params).end if params.StatePreparation.sideband_cooling_enable else U(0, 's')
    time_rot_state_prep = Rotation(params).end if params.StatePreparation.rotation_enable else U(0, 's')
    time_gate = GatePulse(params).end

    if rfmod.turn_on_before == 'sideband_cooling':
        time_rf_mod_start = time_other_stateprep
    elif rfmod.turn_on_before == 'rotational_state_prep':
        time_rf_mod_start = time_other_stateprep + time_sbc + time_gate
    elif rfmod.turn_on_before == 'wait_time':
        time_rf_mod_start = time_other_stateprep + time_sbc + time_gate + time_rot_state_prep
    
    # Turns on 50 us (or whatever the overridden pad time is) early to make sure the RF power is finished changing
    sequence.addTTL('RF Modulation', sequence.start+time_rf_mod_start, time_start_readout-time_rf_mod_start)
 