from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class MotionAnalysisSpectrum(pulse_sequence):
    
                          
    scannable_params = {'MotionAnalysis.detuning': [(-5.0, 5.0, 0.5, 'kHz'), 'spectrum'],
                        'MotionAnalysis.amplitude_397': [(-25.0,-13.0, 1.0, 'dBm'), 'other'],
                        'MotionAnalysis.duration729': [(0.0, 100.0, 10.0, 'us'), 'rabi'],
                        'MotionAnalysis.pulse_width_397': [(0.0, 1000.0, 10.0, 'us'), 'other'] }
 

    show_params= [
                  'MotionAnalysis.pulse_width_397',
                  'MotionAnalysis.amplitude_397',
                  'MotionAnalysis.diagnosis_sideband',
                  'MotionAnalysis.diagnosis_line',
                  'MotionAnalysis.detuning',
                  'MotionAnalysis.channel729',
                  'MotionAnalysis.duration729',
                  'MotionAnalysis.amplitude729'

                ]

    fixed_params = {'Display.relative_frequencies': True

                    }
    
    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        
        awg = cxn.keysight_33500b

        tf = parameters_dict.TrapFrequencies
        ma = parameters_dict.MotionAnalysis
        sideband_selection = ma.diagnosis_sideband
        sideband_frequencies = [tf.radial_frequency_1, tf.radial_frequency_2, tf.axial_frequency, tf.rf_drive_frequency, tf.rotation_frequency]
        
        freq = U(0,'MHz')
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            freq += order * sideband_frequency

        freq = freq + ma.detuning
        awg.program_square_wave(freq['MHz'],5.,0.,50.)
    
    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data_so_far,data_x):
        awg = cxn.keysight_33500b

        tf = parameters_dict.TrapFrequencies
        ma = parameters_dict.MotionAnalysis
        sideband_selection = ma.diagnosis_sideband
        sideband_frequencies = [tf.radial_frequency_1, tf.radial_frequency_2, tf.axial_frequency, tf.rf_drive_frequency, tf.rotation_frequency]
         
        freq = U(0,'MHz')
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            freq += order * sideband_frequency

        freq = freq + ma.detuning
        awg.program_square_wave(freq['MHz'],5.,0.,50.)
        

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        awg = cxn.keysight_33500b
        awg.set_state(1,0) 

        
    def sequence(self):        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.EmptySequence import EmptySequence
        from subsequences.MotionAnalysis import MotionAnalysis
        from subsequences.OpticalPumping import OpticalPumping
        
        # additional optical pumping duratrion 
        duration_op= self.parameters.SidebandCooling.sideband_cooling_optical_pumping_duration

        ## calculate the final diagnosis params
        ma = self.parameters.MotionAnalysis
        freq_729 = self.calc_freq_from_array(ma.diagnosis_line, ma.diagnosis_sideband)
        freq_729_op = self.calc_freq_from_array(self.parameters.OpticalPumping.line_selection) 
        print freq_729

        self.addSequence(StatePreparation)
        # 397 excitation 
        self.addSequence(MotionAnalysis)
        # small optical pumping after the motion excitation
        self.addSequence(OpticalPumping, {'OpticalPumpingContinuous.optical_pumping_continuous_duration':duration_op,
                                          'OpticalPumping.optical_pumping_frequency_729':freq_729_op})

        # 729 excitation to transfer the motional DOF to the electronic DOF
        # running the excitation from the Rabi flopping 
        self.addSequence(RabiExcitation, {'Excitation729.frequency729': freq_729,
                                          'Excitation729.amplitude729': ma.amplitude729,
                                          'Excitation729.duration729':  ma.duration729,
                                          'Excitation729.rabi_change_DDS':True,
                                          "Excitation729.channel729":ma.channel729})

        
        self.addSequence(StateReadout)





