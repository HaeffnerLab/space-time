from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class EmptySequence(pulse_sequence):
    
    def sequence(self):
        
        duration=self.parameters.EmptySequence.empty_sequence_duration

        #code added to test 854 weirdness
        #power_extra866 = U(-5.,'dBm')
        #frequency_extra866 = U(80.,'MHz')
        #power_extra854 = U(-33.,'dBm')
        #frequency_extra854 = U(80.,'MHz')
        #self.addDDS('854DP',self.start,duration,frequency_extra854,power_extra854)
        #self.addDDS('866DP',self.start,duration,frequency_extra866,power_extra866)
        #end added code

        self.end = self.start + duration
