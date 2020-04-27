import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey_CompositePulse import Ramsey_CompositePulse

class contrast_composite(Ramsey_CompositePulse):
    scannable_params = {'RamseyComposite.final_pulse_phase': [(0.0, 360.0, 30.0, 'deg') ,'ramsey_phase_scan'],}
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        rot = parameters_dict.Rotation
        rcw = parameters_dict.RotationCW
        if rot.rotation_enable:
            old_freq = rcw.drive_frequency['kHz']
            old_phase = rcw.start_phase['deg']
            old_amp = rcw.voltage_pp['V']
            cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase) 

        data_y = data.sum(1)
        fit_params = cls.sin_fit(data_x, data_y, return_all_params = True)
        return 2.*fit_params[0]

class RamseyContrast_CompositePulse(pulse_sequence):

    scannable_params = {'RamseyComposite.ramsey_time': [(0.2, 10, 0.2, 'ms'), 'ramsey_contrast']}

    sequence = contrast_composite