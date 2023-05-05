from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class MotionAnalysisRamsey(pulse_sequence):

    scannable_params = {
        'MotionAnalysis.ramsey_time': [(0, 10.0, 0.5, 'ms') ,'ramsey']
        }

    show_params= [

                  'MotionAnalysis.pulse_width_397',
                  'MotionAnalysis.amplitude_397',
                  'MotionAnalysis.diagnosis_sideband',
                  'MotionAnalysis.diagnosis_line',
                  'MotionAnalysis.detuning',
                  'MotionAnalysis.ramsey_time',
                  'MotionAnalysis.channel729',
                  'MotionAnalysis.duration729',
                  'MotionAnalysis.amplitude729'
                  ]

    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        awg = cxn.keysight_33600a

        tf = parameters_dict.TrapFrequencies
        ma = parameters_dict.MotionAnalysis
        sideband_selection = ma.diagnosis_sideband
        sideband_frequencies = [tf.radial_frequency_1, tf.radial_frequency_2, tf.axial_frequency, tf.rf_drive_frequency, tf.rotation_frequency]
        
        freq = U(0,'MHz')
        for order,sideband_frequency in zip(sideband_selection, sideband_frequencies):
            freq += order * sideband_frequency

        freq = freq + ma.detuning
        awg.program_square_wave(freq['kHz'],5.,0.,50.)


    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data_so_far, data_x):
        pass

    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, x):
        awg = cxn.keysight_33600a
        awg.set_state(1,0) 

    def sequence(self):

        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.EmptySequence import EmptySequence
        from subsequences.MotionAnalysis import MotionAnalysis
        from subsequences.OpticalPumping import OpticalPumping

        # additional optical pumping duration
        duration_op = self.parameters.SidebandCooling.sideband_cooling_optical_pumping_duration

        # calculate the final diagnosis params
        ma = self.parameters.MotionAnalysis
        freq_729 = self.calc_freq_from_array(ma.diagnosis_line, ma.diagnosis_sideband)
        freq_729_op = self.calc_freq_from_array(self.parameters.OpticalPumping.line_selection)

        # print out some diagnostics
        print "Using freq 729: ", freq_729
        print "Using detuning: ", ma.detuning
        print "Ramsey wait time: ", ma.ramsey_time

        # state preparation
        self.addSequence(StatePreparation)

        # 397 excitation and small optical pumping after the motion excitation
        self.addSequence(MotionAnalysis)
        # self.addSequence(OpticalPumping, { 'OpticalPumpingContinuous.optical_pumping_continuous_duration': duration_op,
        #                                    'OpticalPumping.optical_pumping_frequency_729':freq_729_op })

        # wait for desired time
        self.addSequence(EmptySequence,  { 'EmptySequence.empty_sequence_duration' : ma.ramsey_time})

        # 397 excitation and small optical pumping after the motion excitation
        self.addSequence(MotionAnalysis)
        self.addSequence(OpticalPumping, { 'OpticalPumpingContinuous.optical_pumping_continuous_duration': duration_op,
                                           'OpticalPumping.optical_pumping_frequency_729':freq_729_op })

        # 729 excitation to transfer the motional DOF to the electronic DOF
        # running the excitation from the Rabi flopping
        self.addSequence(RabiExcitation, {'Excitation729.frequency729': freq_729,
                                          'Excitation729.amplitude729': ma.amplitude729,
                                          'Excitation729.duration729':  ma.duration729,
                                          'Excitation729.rabi_change_DDS':True,
                                          "Excitation729.channel729":ma.channel729})
        self.addSequence(StateReadout)