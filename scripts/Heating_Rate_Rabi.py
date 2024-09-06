import numpy as np
from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Excitation729 import Excitation729

class Rabi(Excitation729):

    scannable_params = {'Excitation729.duration729':  [(0., 50., 1.5, 'us'), 'temp_rabi']}

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        if parameter_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()
        
        data_y = data.sum(1)
        eta = parameter_dict.HeatingRateRabiFit.lamb_dicke
        nbar = cls.rabi_fit(data_x, data_y, eta, return_all_params = False)
        return nbar


class Heating_Rate_Rabi(pulse_sequence):
    show_params = ['HeatingRateRabiFit.lamb_dicke',
                    ]

    scannable_params = {'EmptySequence.empty_sequence_duration': [(0., 40., 10., 'ms'), 'nbar']}

    sequence = Rabi