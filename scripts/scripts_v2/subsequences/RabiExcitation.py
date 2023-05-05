from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

  
class RabiExcitation(pulse_sequence):

    def sequence(self):
        e = self.parameters.Excitation729
        
        ampl_off = WithUnit(-63.0, 'dBm')
        fad = WithUnit(6, 'us')
        
        freq_729 = e.frequency729
        duration_729 = e.duration729
        phase_729 = e.phase729
        amp_729 = e.amplitude729
        channel_729 = e.channel729
        changeDDS = e.rabi_change_DDS
        

        #first advance the frequency if changing DDS channels but keep amplitude low 
        start = self.start

        if changeDDS:       
            self.addDDS(channel_729, self.start, fad, freq_729, ampl_off)
            start = self.start+fad
        #then do actual 729 pulse
        self.addDDS(channel_729, start, duration_729, freq_729, amp_729, phase_729)
        self.end = start + duration_729
                    
    