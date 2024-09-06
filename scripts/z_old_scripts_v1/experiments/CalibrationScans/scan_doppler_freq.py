from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.rabi_flop_scannable import rabi_flopping_scannable as rf
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import numpy as np
import labrad
import time

class scan_doppler_freq(experiment):

    name = 'ScanDopplerFreq'
    required_parameters = []
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(rf.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        #parameters.remove(('SidebandCooling','stark_shift'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.rabi_flop = self.make_experiment(rf)
        self.rabi_flop.initialize(cxn, context, ident)
        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.dac_server = cxn.dac_server
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):
        
        dv_args = {'output_size': 3, #self.rabi_flop.excite.output_size,
                   'experiment_name': self.name,
                   'window_name': 'other',
                   'dataset_name': 'det_scan'
                   }
        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)
        
        start = 170.0
        stop = 220.0
        steps = 40
       
        #carrier_time = self.parameters.MicromotionCalibration.carrier_time

        doppler_cooling_power = self.parameters.DopplerCooling.doppler_cooling_amplitude_397
        self.scan = np.linspace(start, stop, steps)
        
        for i, freq_value in enumerate(self.scan):

            should_stop = self.pause_or_stop()
            if should_stop: break

            replace = TreeDict.fromdict({
                                     'DopplerCooling.doppler_cooling_amplitude_397':doppler_cooling_power,
                                     'DopplerCooling.doppler_cooling_frequency_397':WithUnit(freq_value, 'MHz')
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation_carr = self.rabi_flop.run(cxn, context)
            if excitation_carr is None: break 

            # -3 dBm less power
            should_stop = self.pause_or_stop()
            if should_stop: break

            replace = TreeDict.fromdict({
                                     'DopplerCooling.doppler_cooling_amplitude_397':doppler_cooling_power - WithUnit(3.0, 'dBm'),
                                     'DopplerCooling.doppler_cooling_frequency_397':WithUnit(freq_value, 'MHz')
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation_carr_m3 = self.rabi_flop.run(cxn, context)
            if excitation_carr_m3 is None: break 

            # +3 dBm less power
            should_stop = self.pause_or_stop()
            if should_stop: break

            replace = TreeDict.fromdict({
                                     'DopplerCooling.doppler_cooling_amplitude_397':doppler_cooling_power + WithUnit(3.0, 'dBm'),
                                     'DopplerCooling.doppler_cooling_frequency_397':WithUnit(freq_value, 'MHz')
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation_carr_p3 = self.rabi_flop.run(cxn, context)
            if excitation_carr_p3 is None: break 

            # submit all three scans
            submission = [freq_value]
            submission.extend([excitation_carr, excitation_carr_m3, excitation_carr_p3])
            
            self.dv.add(submission, context = self.save_context)
            self.update_progress(i)

    def finalize(self, cxn, context):
        
        self.save_parameters(self.dv, cxn, self.cxnlab, self.save_context)
        self.rabi_flop.finalize(cxn, context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)     

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_doppler_freq(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
