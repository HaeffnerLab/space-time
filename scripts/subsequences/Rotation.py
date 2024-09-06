from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U

class Rotation(pulse_sequence):

    def sequence(self):
        from EmptySequence import EmptySequence
        rot = self.parameters.Rotation

        rot_prep_time = rot.start_hold + rot.frequency_ramp_time + rot.middle_hold + rot.ramp_down_time + rot.end_hold
        # Add empty sequence for rotation AWF plus 400 us cushion (200 us before, 200 us after)
        self.addSequence(EmptySequence, {'EmptySequence.empty_sequence_duration':rot_prep_time + U(400.0, 'us'),
                                         'EmptySequence.noise_enable':False})
        