from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np
import math as m
import time

class Ramsey_CompositePulse(pulse_sequence):
    """
    This pulse sequence performs a Ramsey experiment with an arbitrary number of dynaimcal decoupling pulses in the CPMG sequence, with each individual pulse generalized in the following way:
    Each "pi/2" pulse can be composite, made up of up to 5 729 pulses immediately following one another.
    Once this composite "pi/2" pulse is defined, the rest of the pulses are defined as well. In particular...
        The final "pi/2" composite pulse is the same as the initial one but with the constituent pulses in reverse order. E.g. for 3 pulses, the first "pi/2" is pulse1+pulse2+pulse3, while the last one is pulse3+pulse2+pulse1
        The detuning RamseyComposite.detuning is applied only to pulse1. The Ramsey phase RamseyComposite.final_pulse_phase is applied only to the FINAL instance of pulse1, in the final "pi/2" composite pulse.
        The intermediate composite "pi" pulses, if any are chosen, are comprised of the consituent pulses in reverse order and then in forward order. E.g. for a composite pulse of 3 consituent pulses the "pi" pulse looks like 3+2+1+1+2+3.
    The spacing between pulses is calculated such that the appropriate wait times are between centers of the composite pulses. The math to calculate this is somewhat ugly.
    There is no frequency switching wait time ("frequency advance duration") inserted between pulses in a composite pulse; it's assumed that if they're at different frequencies, then the user wants them to remain phase-coherent and thus uses different channels for the different frequencies.
    """


    scannable_params = {

                'RamseyComposite.ramsey_time': [(0.1, 10, 0.1, 'ms'), 'ramsey'],
                'RamseyComposite.final_pulse_phase': [(0.0, 360.0, 30.0, 'deg'), 'ramsey_phase_scan'],

    }

    show_params = ['RamseyComposite.pulses',
                   'RamseyComposite.detuning',
                   'RamseyComposite.final_pulse_phase',
                   'RamseyComposite.dd_repetitions',
                   'RamseyComposite.ramsey_time',

                   'RamseyComposite.pulse1_channel',
                   'RamseyComposite.pulse1_line',
                   'RamseyComposite.pulse1_sideband',
                   'RamseyComposite.pulse1_amplitude',
                   'RamseyComposite.pulse1_duration',

                   'RamseyComposite.pulse2_channel',
                   'RamseyComposite.pulse2_line',
                   'RamseyComposite.pulse2_sideband',
                   'RamseyComposite.pulse2_amplitude',
                   'RamseyComposite.pulse2_duration',

                   'RamseyComposite.pulse3_channel',
                   'RamseyComposite.pulse3_line',
                   'RamseyComposite.pulse3_sideband',
                   'RamseyComposite.pulse3_amplitude',
                   'RamseyComposite.pulse3_duration',

                   'RamseyComposite.pulse4_channel',
                   'RamseyComposite.pulse4_line',
                   'RamseyComposite.pulse4_sideband',
                   'RamseyComposite.pulse4_amplitude',
                   'RamseyComposite.pulse4_duration',

                   'RamseyComposite.pulse5_channel',
                   'RamseyComposite.pulse5_line',
                   'RamseyComposite.pulse5_sideband',
                   'RamseyComposite.pulse5_amplitude',
                   'RamseyComposite.pulse5_duration',

                   'Rotation.rotation_enable',
                   'Rotation.drive_frequency',
                   'Rotation.end_hold',
                   'Rotation.frequency_ramp_time',
                   'Rotation.middle_hold',
                   'Rotation.ramp_down_time',
                   'Rotation.start_hold',
                   'Rotation.start_phase',
                   'Rotation.voltage_pp',

                   'EmptySequence.empty_sequence_duration',
                   ]


    def sequence(self):

        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.EmptySequence import EmptySequence

        ampl_off = U(-63.0, 'dBm')
        frequency_advance_duration = U(6, 'us')

        rc = self.parameters.RamseyComposite
        
        pulse_channels =    [rc.pulse1_channel,
                             rc.pulse2_channel,
                             rc.pulse3_channel,
                             rc.pulse4_channel,
                             rc.pulse5_channel]
        pulse_frequencies = [self.calc_freq_from_array(rc.pulse1_line, rc.pulse1_sideband) + rc.detuning,
                             self.calc_freq_from_array(rc.pulse2_line, rc.pulse2_sideband),
                             self.calc_freq_from_array(rc.pulse3_line, rc.pulse3_sideband),
                             self.calc_freq_from_array(rc.pulse4_line, rc.pulse4_sideband),
                             self.calc_freq_from_array(rc.pulse5_line, rc.pulse5_sideband),
                            ]
        pulse_amplitudes =  [rc.pulse1_amplitude,
                             rc.pulse2_amplitude,
                             rc.pulse3_amplitude,
                             rc.pulse4_amplitude,
                             rc.pulse5_amplitude,]
        pulse_durations =   [rc.pulse1_duration,
                             rc.pulse2_duration,
                             rc.pulse3_duration,
                             rc.pulse4_duration,
                             rc.pulse5_duration,]

        def add_pulse_n(n, final_pulse=False):
            if final_pulse:
                 self.addSequence(RabiExcitation, {"Excitation_729.channel729": pulse_channels[n-1],
                                                   "Excitation_729.frequency729": pulse_frequencies[n-1],
                                                   "Excitation_729.amplitude729": pulse_amplitudes[n-1],
                                                   "Excitation_729.duration729": pulse_durations[n-1],
                                                   "Excitation_729.phase729": rc.final_pulse_phase,
                                                   "Excitation_729.rabi_change_DDS": False
                                                  })
            else:
                 self.addSequence(RabiExcitation, {"Excitation_729.channel729": pulse_channels[n-1],
                                                   "Excitation_729.frequency729": pulse_frequencies[n-1],
                                                   "Excitation_729.amplitude729": pulse_amplitudes[n-1],
                                                   "Excitation_729.duration729": pulse_durations[n-1],
                                                   "Excitation_729.phase729": U(0, 'deg'),
                                                   "Excitation_729.rabi_change_DDS": False
                                                  })

        N = int(rc.pulses)
        dd_reps = int(rc.dd_repetitions)

        self.addSequence(StatePreparation)
        self.addSequence(EmptySequence)
        for n in range(1, N+1):
            self.addDDS(pulse_channels[n-1], self.end, frequency_advance_duration, pulse_frequencies[n-1], ampl_off)
            self.end = self.end + frequency_advance_duration

        # First composite "pi/2" pulse
        for n in range(1, N+1):
            add_pulse_n(n)

        ## Wait time, including dynamical decoupling if necessary
        # calculate wait times
        T = rc.ramsey_time                # total ramsey time
        t_pulse = U(0, 'us')              # total time of composite pulse
        for n in range(1, N+1):
            t_pulse = t_pulse + pulse_durations[n-1]
        # add dd pulses if necessary
        if dd_reps == 0:
            self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":T-t_pulse})
        else:
            tau = T/(2.0*dd_reps)   # time between centers of pi/2 pulse and pi pulse
            t_wait_1 = tau - 1.5*t_pulse      # actual wait time between pi/2 pulse and pi pulse
            t_wait_2 = 2*tau - 2*t_pulse      # actual wait time between pi pulses
            # Wait time until first dd pulse
            self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":t_wait_1})
            # Each dd pulse is composed of the composite pulse backwards then forwards. Add the first dd_reps-1 dd pulses, each followed by a wait time
            for i in range(dd_reps-1):
                for n in range(N, 0, -1)+range(1, N+1):
                    add_pulse_n(n)
                self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":t_wait_2})
            # Add the final dd pulse
            for n in range(N, 0, -1)+range(1, N+1):
                add_pulse_n(n)
            # Add the final wait time until the final pi/2 pulse
            self.addSequence(EmptySequence, {"EmptySequence.empty_sequence_duration":t_wait_1})

        # Final composite "pi/2" pulse
        for n in range(N, 1, -1):
            add_pulse_n(n)
        add_pulse_n(1, final_pulse=True)

        self.addSequence(StateReadout)


    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        ## add rotation if necessary
        rot = parameters_dict.Rotation
        if rot.rotation_enable:
            rot = parameters_dict.Rotation
            awg_rotation = cxn.keysight_33500b

            frequency_ramp_time = rot.frequency_ramp_time
            start_hold = rot.start_hold
            ramp_down_time = rot.ramp_down_time
            start_phase = rot.start_phase
            middle_hold = rot.middle_hold
            end_hold = rot.end_hold
            voltage_pp = rot.voltage_pp
            drive_frequency = rot.drive_frequency

            awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation_sin_spin')

    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, x):
        ## if rotating set back to pinning parameters
        rot = parameters_dict.Rotation
        rcw = parameters_dict.RotationCW
        if rot.rotation_enable:
            old_freq = rcw.drive_frequency['kHz']
            old_phase = rcw.start_phase['deg']
            old_amp = rcw.voltage_pp['V']
            cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase)