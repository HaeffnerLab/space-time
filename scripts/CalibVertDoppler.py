from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class CalibVertDoppler(pulse_sequence):
    scannable_params = {'DopplerCooling.doppler_cooling_frequency_866':  [(60., 85., .5, 'MHz'), 'doppler_cooling__frequency']}

    show_params= [
                  'CalibVertDoppler.line_selection',
                  'CalibVertDoppler.amplitude729',
                  'CalibVertDoppler.duration729',
                  'CalibVertDoppler.channel729',
                  'CalibVertDoppler.stark_shift_729',
                  ]


    def sequence(self):

        from Excitation729 import Excitation729

        cvd = self.parameters.CalibVertDoppler
          
        self.addSequence(Excitation729,{'Excitation729.amplitude729': cvd.amplitude729,
                                        'Excitation729.channel729': cvd.channel729,
                                        'Excitation729.duration729': cvd.duration729,
                                        'Excitation729.frequency729': U(0, 'MHz'),
                                        'Excitation729.line_selection': cvd.line_selection,
                                        'Excitation729.sideband_selection': [0, 0, 0, 0, 0],
                                        'Excitation729.stark_shift_729': cvd.stark_shift_729,
                                        'StatePreparation.sideband_cooling_enable': False,
                                        'StatePreparation.rotation_enable': False,
                                        'EmptySequence.empty_sequence_duration': U(0, 'ms'),
                                        'EmptySequence.noise_enable': False,
                                        'StateReadout.repeat_each_measurement': 100,
                                        'StateReadout.readout_mode': "pmt_excitation"})

    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        pass

    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, x):
        if parameters_dict.CalibrationControl.save_calibrations:
            data_y = data.sum(1)
            
            # Find optimal Doppler cooling frequency by fitting to a 9th order polynomial
            f_opt = cls.polyfit_maximize(x, data_y, 9)
            f_opt = U(f_opt, 'MHz')

            # Submit to script scanner
            ss = cxn.scriptscanner
            prev_value = ss.get_parameter('DopplerCooling', 'doppler_cooling_frequency_866')
            ss.set_parameter('PreviousCalibrationValues', 'doppler_cooling_frequency_866', prev_value)
            ss.set_parameter('DopplerCooling', 'doppler_cooling_frequency_866', f_opt)