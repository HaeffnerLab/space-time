from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence

class SOSBeam(pulse_sequence):
   
    def sequence(self):
        sos = self.parameters.SOSBeam

        if sos.match_866_frequency_to_doppler:
            frequency_866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
        else:
            frequency_866 = sos.sos_866_frequency
        self.addTTL('397 SOS Beam', self.end, sos.sos_duration)
        self.addDDS('866DP', self.end, sos.sos_duration+sos.sos_866_repump_additional, frequency_866, sos.sos_866_amplitude)

        self.end = self.start + sos.sos_duration + sos.sos_866_repump_additional