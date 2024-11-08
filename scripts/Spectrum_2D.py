from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from Excitation729 import Excitation729

class spectrum2d(Excitation729):
    scannable_params = {'Excitation729.frequency729': [(-50., 50., 5., 'kHz'), 'spectrum', True],}
    
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        return 0.0

    
class Spectrum_2D(pulse_sequence):
    scannable_params = {'Excitation729.duration729':  [(0., 200., 2., 'us'), 'other'],}
    sequence = spectrum2d