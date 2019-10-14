from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class TurnOffAll(pulse_sequence):
    
    def sequence(self):
        dur = WithUnit(50, 'us')
        for channel in ['729horiz','729vert','729extra','729extra2','397DP','854DP','866DP','397Extra']:
            self.addDDS(channel, self.start, dur, WithUnit(0, 'MHz'), WithUnit(-63., 'dBm') )
        #currently starts rotation AWG
        self.addTTL('start_exp', self.start, dur )
        self.end = self.start + dur
