from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np
import math as m
import time

class Ramsey(pulse_sequence):
    
    #name = 'Ramsey'

    scannable_params = {
                        
        'Ramsey.ramsey_time': [(0, 1.0, 0.05, 'ms') ,'ramsey'],
        'Ramsey.second_pulse_phase': [(0, 360., 30, 'deg') ,'ramsey_phase_scan'],

        }

    show_params= ['Ramsey.ramsey_time',
                  'Ramsey.detuning',
                  'Ramsey.amplitude_729',
                  'Ramsey.channel_729',
                  'Ramsey.dynamic_decoupling_enable',

                  'Ramsey.first_pulse_line',
                  'Ramsey.first_pulse_sideband',
                  'Ramsey.first_pulse_duration',

                  'Ramsey.second_pulse_line',
                  'Ramsey.second_pulse_sideband',
                  'Ramsey.second_pulse_duration',
                  'Ramsey.second_pulse_phase',

                  'DynamicDecoupling.dd_line_selection',
                  'DynamicDecoupling.dd_sideband',
                  'DynamicDecoupling.dd_channel_729',
                  'DynamicDecoupling.dd_repetitions',
                  'DynamicDecoupling.dd_pi_time',
                  'DynamicDecoupling.dd_amplitude_729',

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
                  'StateReadout.repeat_each_measurement',
                      ]

    
    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.DynamicDecoupling import DynamicDecoupling
        from subsequences.EmptySequence import EmptySequence
        
        
        r = self.parameters.Ramsey   
        rot = self.parameters.Rotation
        dd = self.parameters.DynamicDecoupling
        initial_freq_729 = self.calc_freq_from_array(r.first_pulse_line, r.first_pulse_sideband)
        final_freq_729 = self.calc_freq_from_array(r.second_pulse_line, r.second_pulse_sideband)

        # adding the Ramsey detuning
        initial_freq_729 += self.parameters.Ramsey.detuning
        final_freq_729 += self.parameters.Ramsey.detuning

        ampl_off = U(-63.0, 'dBm')
        fad = U(6, 'us')

        
        # building the sequence
        self.addSequence(StatePreparation)     
        self.addSequence(EmptySequence)

        self.addSequence(RabiExcitation, { "Excitation_729.frequency729": initial_freq_729,
                                           "Excitation_729.duration729": r.first_pulse_duration,
                                           "Excitation_729.amplitude729": r.amplitude_729,
                                           "Excitation_729.phase729": U(0, 'deg'),
                                           "Excitation_729.channel729":r.channel_729,
                                           "Excitation_729.rabi_change_DDS":True
                                          })

        self.addSequence(DynamicDecoupling,  {"DynamicDecoupling.dd_duration" : r.ramsey_time})
        
        self.addSequence(RabiExcitation, { "Excitation_729.frequency729": final_freq_729,
                                           "Excitation_729.duration729": r.second_pulse_duration,
                                           "Excitation_729.amplitude729": r.amplitude_729,
                                           "Excitation_729.phase729": r.second_pulse_phase,
                                           "Excitation_729.channel729":r.channel_729,
                                           "Excitation_729.rabi_change_DDS":False
                                          })

        self.addSequence(StateReadout)
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      pd = parameters_dict
      rot = pd.Rotation
      
      ## add rotation if necessary
      if rot.rotation_enable:
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
    def run_in_loop(cls,cxn, parameters_dict, data, x):
      pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
      ## if rotating set back to pinning parameters
      rot = parameters_dict.Rotation
      rcw = parameters_dict.RotationCW

      if rot.rotation_enable:
        old_freq = rcw.drive_frequency['kHz']
        old_phase = rcw.start_phase['deg']
        old_amp = rcw.voltage_pp['V']
        cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase)
