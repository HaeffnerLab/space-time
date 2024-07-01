from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class PulseTrain397(pulse_sequence):
   
    def sequence(self):
        p = self.parameters.PulseTrain397 
        trapfreq = self.parameters.TrapFrequencies
        sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency, trapfreq.rotation_frequency]
        sbfreq = WithUnit(0.0, 'MHz')
        for order,sideband_frequency in zip(p.sideband_selection, sideband_frequencies):
            sbfreq += order * sideband_frequency
        pulse_duration = (1 / (sbfreq + p.modulation_detuning)).inUnitsOf('us')
        pulse_on_time = pulse_duration * p.duty_cycle
        pulse_off_time = pulse_duration - pulse_on_time
        pulse_start_time_2nd = self.start + p.n_pulses * pulse_duration + p.empty_duration
        for i in range(int(p.n_pulses)):
            self.addDDS ('397DP', self.start + i*pulse_duration, pulse_on_time, p.frequency_397, p.amplitude_397)
            self.addDDS ('397DP', self.start + i*pulse_duration + pulse_on_time, pulse_off_time, p.frequency_397, WithUnit(-63., 'dBm'))
            self.addDDS ('397DP', pulse_start_time_2nd + i*pulse_duration, pulse_on_time, p.frequency_397, p.amplitude_397)
            self.addDDS ('397DP', pulse_start_time_2nd + i*pulse_duration + pulse_on_time, pulse_off_time, p.frequency_397, WithUnit(-63., 'dBm'))
        
        self.end = pulse_start_time_2nd + p.n_pulses * pulse_duration