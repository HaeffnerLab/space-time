from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
#from treedict import TreeDict

class StateReadout(pulse_sequence):
    '''
    Pulse sequence for reading out the state of the ion. 
    '''



    def sequence(self):
        st = self.parameters.StateReadout
        readout_mode = st.readout_mode
        repump_additional = self.parameters.DopplerCooling.doppler_cooling_repump_additional# need the doppler paramters for the additional repumper time 
        readout_duration=st.state_readout_duration 
        duration_397=readout_duration
        duration_866=readout_duration + repump_additional
        
        # #code added to test 854 weirdness
        # power_extra854 = U(-63.,'dBm')
        # frequency_extra854 = U(80.,'MHz')
        # self.addDDS('854DP',self.start,duration_866,frequency_extra854,power_extra854)
        # #end added code

        # # code added to test 866 + 854 crosstalk
        # extra866_time = U(1.,'ms')
        # extra866_amplitude = U(-5.,'dBm')
        # #end added code

        self.addTTL('ReadoutCount', self.start, readout_duration)
        
        #self.addDDS('866DP',self.start, extra866_time, st.state_readout_frequency_866, extra866_amplitude)
        self.addDDS ('397Extra',self.start, duration_397, st.state_readout_frequency_397, st.state_readout_amplitude_397)
        self.addDDS ('866DP',self.start, duration_866, st.state_readout_frequency_866, st.state_readout_amplitude_866)
                    
        self.end = self.start + duration_866
        
