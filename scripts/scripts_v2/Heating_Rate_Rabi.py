import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Excitation729 import Excitation729

class Rabi(Excitation729):

    scannable_params = {'Excitation_729.duration729':  [(0., 50., 1.5, 'us'), 'temp_rabi']}

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        data_y = data.sum(1)
        trap_frequency_MHz = parameter_dict.HeatingRateRabi.trap_frequency['MHz']
        n_ions = parameter_dict.HeatingRateRabi.n_ions
        nbar = cls.rabi_fit(data_x, data_y, trap_frequency_MHz, n_ions, return_all_params = False)
        return nbar


class Heating_Rate_Rabi(pulse_sequence):
    show_params = ['HeatingRateRabi.trap_frequency',
                   'HeatingRateRabi.n_ions'
                    ]

    scannable_params = {'EmptySequence.empty_sequence_duration': [(0., 40., 10., 'ms'), 'nbar']}

    sequence = Rabi