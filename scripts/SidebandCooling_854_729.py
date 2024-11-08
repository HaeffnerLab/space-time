from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from Excitation729 import Excitation729

class scan_854_power(Excitation729):
    scannable_params = {'SidebandCooling.sideband_cooling_amplitude_854': [(-25.,-5., 1., 'dBm'), 'sideband_cooling__854_power'],}
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        return 0.0

    
class SidebandCooling_854_729(pulse_sequence):
    scannable_params = {'SidebandCooling.sideband_cooling_amplitude_729': [(-20.0, -7.0, 1.0, 'dBm'), 'other']}
    sequence = scan_854_power