import numpy as np
from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey import Ramsey

class ramsey_phase(Ramsey):

    scannable_params = {'Ramsey.second_pulse_phase': [(0, 360., 36, 'deg') ,'ramsey_phase__phase'],}


    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        if parameters_dict.StatePreparation.rotation_enable:
            from subsequences.StatePreparation import StatePreparation
            state_prep_time = StatePreparation(parameters_dict).end
            frequency_ramp_time = parameters_dict.Rotation.frequency_ramp_time
            cxn.keysight_33500b.rotation_run_initial(state_prep_time, 'frequency_ramp_time', frequency_ramp_time)


    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()
        
        data_y = data.sum(1)
        fit_params = cls.sin_fit(data_x, data_y, return_all_params = True)
        return 2.0*fit_params[0]


class ramsey_contrast(pulse_sequence):
    
    scannable_params = {'Ramsey.ramsey_time': [(100, 1000.0, 50.0, 'us'), 'ramsey_phase__contrast'],}


    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()
        
        rrf = parameters_dict.RotRamseyFit
        params = {}
        params['Delta_l'] = rrf.sideband_order
        params['f_trap_MHz'] = rrf.horizontal_trap_frequency['MHz']
        params['f_rot_kHz'] = rrf.rotation_frequency['kHz']

        fit_params = cls.rot_ramsey_fit(data_x, data, params, y_is_contrast=True, return_all_params=True)
        if fit_params is not None:
            print 'sigma_l = {}'.format(fit_params[0])
            print 'scale = {}'.format(fit_params[1])
            print 'contrast = {}'.format(fit_params[2])
            return fit_params[0]
        else:
            return 0.0


    sequence = ramsey_phase


class RotSpinup_ScanRamseyContrast(pulse_sequence):

    scannable_params = {'Rotation.frequency_ramp_time': [(45.0, 70.0, 1.0, 'us'), 'ramsey_gap__sigma_ell']}

    show_params = ['RotRamseyFit.horizontal_trap_frequency',
                   'RotRamseyFit.rotation_frequency',
                   'RotRamseyFit.sideband_order',]

    sequence = ramsey_contrast