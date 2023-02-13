import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey import Ramsey

class ramsey_gap(Ramsey):
    scannable_params = {'Ramsey.ramsey_time': [(0, 1000.0, 50.0, 'us') ,'ramsey'],}
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()

        data_y = data.sum(1)
        fit_params = cls.rot_ramsey_fit(data_x, data_y, return_all_params = True)
        return fit_params[0]

class Diffusion(pulse_sequence):

    scannable_params = {'EmptySequency.empty_sequence_duration': [(0.0, 80.0, 10.0, 'ms'), 'sigma_ell']}

    sequence = ramsey_gap