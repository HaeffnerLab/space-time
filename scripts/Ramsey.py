from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np
import math as m
import time

class Ramsey(pulse_sequence):
    
    #name = 'Ramsey'

    scannable_params = {
                        
        'Ramsey.ramsey_time': [(100.0, 1000.0, 50.0, 'us') ,'ramsey'],
        'Ramsey.second_pulse_phase': [(0, 360., 36, 'deg') ,'ramsey_phase_scan'],

        }

    show_params= ['Ramsey.ramsey_time',
                  'Ramsey.detuning',
                  'Ramsey.amplitude_729',
                  'Ramsey.channel_729',
                  'Ramsey.dynamical_decoupling_enable',
                  'Ramsey.noise_enable',

                  'Ramsey.first_pulse_line',
                  'Ramsey.first_pulse_sideband',
                  'Ramsey.first_pulse_duration',

                  'Ramsey.second_pulse_line',
                  'Ramsey.second_pulse_sideband',
                  'Ramsey.second_pulse_duration',
                  'Ramsey.second_pulse_phase',

                  'DynamicalDecoupling.dd_line_selection',
                  'DynamicalDecoupling.dd_sideband',
                  'DynamicalDecoupling.dd_channel_729',
                  'DynamicalDecoupling.dd_repetitions',
                  'DynamicalDecoupling.dd_pi_time',
                  'DynamicalDecoupling.dd_amplitude_729',

                  'Rotation.drive_frequency',
                  'Rotation.end_hold',
                  'Rotation.frequency_ramp_time',
                  'Rotation.middle_hold',
                  'Rotation.ramp_down_time',
                  'Rotation.start_hold',
                  'Rotation.start_phase',
                  'Rotation.voltage_pp',

                  'RFModulation.enable',
                  'RFModulation.turn_on_before',

                  'EmptySequence.empty_sequence_duration',
                  'EmptySequence.noise_enable',
                      ]

    
    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.DynamicalDecoupling import DynamicalDecoupling
        from subsequences.EmptySequence import EmptySequence
        from subsequences.RFModulation import RFModulation
        
        r = self.parameters.Ramsey   
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

        self.addSequence(RabiExcitation, { "Excitation729.frequency729": initial_freq_729,
                                           "Excitation729.duration729": r.first_pulse_duration,
                                           "Excitation729.amplitude729": r.amplitude_729,
                                           "Excitation729.phase729": U(0, 'deg'),
                                           "Excitation729.channel729":r.channel_729,
                                           "Excitation729.rabi_change_DDS":True
                                          })

        self.addSequence(DynamicalDecoupling,  {"DynamicalDecoupling.dd_duration" : r.ramsey_time - (r.first_pulse_duration+r.second_pulse_duration)/2.0})
        
        self.addSequence(RabiExcitation, { "Excitation729.frequency729": final_freq_729,
                                           "Excitation729.duration729": r.second_pulse_duration,
                                           "Excitation729.amplitude729": r.amplitude_729,
                                           "Excitation729.phase729": r.second_pulse_phase,
                                           "Excitation729.channel729":r.channel_729,
                                           "Excitation729.rabi_change_DDS":False
                                          })
        
        time_start_readout = self.end # This is for RF modulation
        self.addSequence(StateReadout)
        
        # Add RF modulation TTL pulse if applicable
        if self.parameters.RFModulation.enable:
            RFModulation(self, time_start_readout)

    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        # Add rotation if necessary
        if parameters_dict.StatePreparation.rotation_enable:
            from subsequences.StatePreparation import StatePreparation
            state_prep_time = StatePreparation(parameters_dict).end
            cxn.keysight_33500b.rotation_run_initial(state_prep_time)

     
    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass  

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()