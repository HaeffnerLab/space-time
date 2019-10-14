from common.devel.bum.sequences.pulse_sequence import pulse_sequence
#from treedict import TreeDict
#from OpticalPumping import optical_pumping
from labrad.units import WithUnit

class MotionAnalysis(pulse_sequence):
    '''
    Pulse sequence for reading out the state of the ion. 
    '''
   
    
    def sequence(self):
        ma = self.parameters.Motion_Analysis
        dc = self.parameters.DopplerCooling
        
        freq_397 = dc.doppler_cooling_frequency_397
        freq_866 = dc.doppler_cooling_frequency_866
        amp_866 = dc.doppler_cooling_amplitude_866
        
        self.addTTL('awg_on', self.start, ma.pulse_width_397 + WithUnit(2, 'us')) # 2 us for safe TTL switch on  

        self.addDDS('397Extra', self.start + WithUnit(1, 'us'), ma.pulse_width_397, freq_397, ma.amplitude_397)
        self.addDDS('866DP', self.start + WithUnit(1,'us'), ma.pulse_width_397, freq_866, amp_866 )

        self.end = self.start + ma.pulse_width_397 + WithUnit(2, 'us')
