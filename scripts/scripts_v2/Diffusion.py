import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey import Ramsey

class ramsey_gap(Ramsey):
    scannable_params = {'Ramsey.ramsey_time': [(100, 1000.0, 50.0, 'us') ,'ramsey'],}
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()

        diff = parameters_dict.DiffusionFit
        params = {}
        params['Delta_l'] = diff.sideband_order
        params['f_trap_MHz'] = diff.horizontal_trap_frequency['MHz']
        params['f_rot_kHz'] = diff.rotation_frequency['kHz']

        data_y = data.sum(1)
        fit_params = cls.rot_ramsey_fit(data_x, data_y, params, return_all_params = True)
        if fit_params is not None:
            print 'sigma_l = {}'.format(fit_params[0])
            print 'Omega_kHz = {}'.format(fit_params[1])
            print 'delta_kHz = {}'.format(fit_params[2])
        return fit_params[0]

class Diffusion(pulse_sequence):

    scannable_params = {'EmptySequence.empty_sequence_duration': [(0.0, 80.0, 10.0, 'ms'), 'sigma_ell']}

    show_params= ['DiffusionFit.horizontal_trap_frequency',
                  'DiffusionFit.rotation_frequency',
                  'DiffusionFit.sideband_order',]

    sequence = ramsey_gap