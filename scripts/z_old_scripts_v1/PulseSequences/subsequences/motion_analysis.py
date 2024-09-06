from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from treedict import TreeDict
from OpticalPumping import optical_pumping
from labrad.units import WithUnit

class motion_analysis(pulse_sequence):
    '''
    Pulse sequence for reading out the state of the ion. 
    '''
    required_parameters = [
                           ('Motion_Analysis','amplitude_397'),
                           ('Motion_Analysis','amplitude_866'),
                           ('Motion_Analysis','pulse_width_397'),
                           ('Motion_Analysis','ramsey_time'),
                           ('Motion_Analysis','rf_modulation')                           
                           ]
    required_subsequences = [optical_pumping]
    def sequence(self):
        ma = self.parameters.Motion_Analysis
        
        freq_397 = WithUnit(215.0, 'MHz')
        freq_866 = WithUnit(70.0, 'MHz')
        
        if ma.rf_modulation:
          amp_397 = WithUnit(-63,'dBm')
          amp_866 = WithUnit(-63,'dBm')
          mod_channel = 'rfmod'
        else:
          amp_397 = ma.amplitude_397
          amp_866 = ma.amplitude_866
          mod_channel = '397mod'


        self.addTTL(mod_channel, self.start, ma.pulse_width_397 + WithUnit(2, 'us')) # 2 us for safe TTL switch on        
        self.addDDS('397Extra', self.start + WithUnit(1, 'us'), ma.pulse_width_397, freq_397, amp_397)
        self.addDDS('866DP', self.start + WithUnit(1, 'us'), ma.pulse_width_397, freq_866, amp_866)

        start = self.start + ma.pulse_width_397 + WithUnit(2, 'us') + ma.ramsey_time
        
        self.addTTL(mod_channel, start, ma.pulse_width_397 + WithUnit(2, 'us'))
        self.addDDS('397Extra', start + WithUnit(1, 'us'), ma.pulse_width_397, freq_397, amp_397)
        self.addDDS('866DP', start + WithUnit(1, 'us'), ma.pulse_width_397, freq_866, amp_866)        
        
        self.end = start + ma.pulse_width_397 + WithUnit(2, 'us')
        
        #self.end = self.start + ma.pulse_width_397 + WithUnit(2, 'us')
        self.addSequence(optical_pumping)
