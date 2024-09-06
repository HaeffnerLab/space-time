from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class ScrambleGroundState(pulse_sequence):

    def sequence(self):

        sgs = self.parameters.ScrambleGroundState
        fad = WithUnit(6,'us')
        ampl_off = WithUnit(-63.0,'dBm')
        self.end = self.start + fad + sgs.pi_time + sgs.repump_time
        self.addDDS(sgs.channel_729, self.start, fad, sgs.excitation_frequency, ampl_off)
        self.addDDS(sgs.channel_729, self.start + fad, sgs.pi_time, sgs.excitation_frequency, sgs.excitation_amplitude)
        self.addDDS('854DP', self.start + fad + sgs.pi_time, sgs.repump_time, sgs.repump_frequency, sgs,repump_pamplitude)

