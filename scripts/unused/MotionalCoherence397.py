from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class MotionalCoherence397(pulse_sequence):
    
    scannable_params = {
        'PulseTrain397.modulation_frequency': [(0.1, 10.0, 1.0, 'MHz') ,'other'],
        'PulseTrain397.empty_duration': [(0.1, 100000.0, 1.0, 'us') ,'other'],
        'PulseTrain397.modulation_detuning': [(-1000.0, 1000.0, 1.0, 'kHz') ,'other'],
        'PulseTrain397.amplitude_397': [(-63, -5, 1, 'dBm') ,'other']
        }

    show_params= [
                  'Excitation729.line_selection',
                  'Excitation729.amplitude729',
                  'Excitation729.duration729',
                  'Excitation729.sideband_selection',
                  'Excitation729.channel729',
                  'Excitation729.stark_shift_729',
                  'SidebandCoolingContinuous.sideband_cooling_continuous_cycles',
                  'SidebandCoolingContinuous.sideband_cooling_continuous_duration',
                  'SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_cycles',
                  'SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_duration',
                  'SidebandCoolingContTwoTone.channel_729_secondary',
                  'SidebandCoolingContTwoTone.stage2_line',
                  'SidebandCoolingContTwoTone.stage3_line',
                  'SidebandCoolingContTwoTone.stage4_line',
                  'SidebandCoolingContTwoTone.stage5_line',
                  'PulseTrain397.amplitude_397',
                  'PulseTrain397.duty_cycle',
                  'PulseTrain397.empty_duration',
                  'PulseTrain397.frequency_397',
                  'PulseTrain397.modulation_detuning',
                  'PulseTrain397.n_pulses',
                  'PulseTrain397.sideband_selection'
                  ]


    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.PulseTrain397 import PulseTrain397
    
        pulsetrain = self.parameters.PulseTrain397
        e = self.parameters.Excitation729
        
        if e.frequency_selection == "auto":
            freq_729_pos = self.calc_freq_from_array(e.line_selection, [sb*e.invert_sb for sb in e.sideband_selection])
            freq_729 = freq_729_pos + e.stark_shift_729 + e.frequency729
            print "FREQUENCY 729 = {}".format(freq_729)
        elif e.frequency_selection == "manual":
            freq_729 = e.frequency729
        else:
            raise Exception ('Incorrect frequency selection type {0}'.format(e.frequency_selection))

        # building the sequence
        self.addSequence(StatePreparation)
        
        self.addSequence(PulseTrain397)

        self.addSequence(RabiExcitation, {'Excitation729.frequency729': freq_729,
                                         'Excitation729.rabi_change_DDS': True})

        self.addSequence(StateReadout)
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        pass
     
    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass  

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        pass