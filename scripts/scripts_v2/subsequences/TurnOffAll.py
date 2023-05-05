from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class TurnOffAll(pulse_sequence):
    
    def sequence(self):
        dur = WithUnit(50, 'us')
        #self.addDDS('854DP', self.start, WithUnit(10, 'us'), WithUnit(200, 'MHz'), WithUnit(-20.0, 'dBm'))
        for channel in ['729horiz', '729vert', '729horizExtra', '729vertExtra', '397DP', 'AAAAAA', '866DP']:
            self.addDDS(channel, self.start, dur, WithUnit(0, 'MHz'), WithUnit(-63., 'dBm') )
        #currently starts rotation AWG
        self.addTTL('start_exp', self.start, dur )
        self.end = self.start + dur
