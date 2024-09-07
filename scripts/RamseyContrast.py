import numpy as np
from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey import Ramsey

class contrast(Ramsey):
    scannable_params = {'Ramsey.second_pulse_phase': [(0, 360., 36, 'deg') ,'ramsey_phase__phase'],}
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()
        
        data_y = data.sum(1)
        fit_params = cls.sin_fit(data_x, data_y, return_all_params = True)
        return 2.0*fit_params[0]

class RamseyContrast(pulse_sequence):

    scannable_params = {'Ramsey.ramsey_time': [(0.1, 8., .1, 'ms'), 'ramsey_phase__contrast']}

    sequence = contrast