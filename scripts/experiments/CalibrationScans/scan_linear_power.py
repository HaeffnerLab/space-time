from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.spectrum import spectrum
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from fitters import peak_fitter
from labrad.units import WithUnit
from treedict import TreeDict
import time
import numpy as np
import labrad

class scan_linear_power(experiment):

    name = 'ScanLinearPower'

    required_parameters = []

    # parameters to overwrite
    remove_parameters = []

    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(spectrum.all_required_parameters()))
        parameters = list(parameters)
        #for p in cls.remove_parameters:
        #    parameters.remove(p)
        return parameters
    
    
    def initialize(self, cxn, context, ident):

        self.ident = ident
        
        self.spectrum = self.make_experiment(spectrum)
        self.spectrum.initialize(cxn, context, ident, use_camera_override = False)

        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):

        dv_args = {'output_size': 1,
                    'experiment_name' : self.name,
                    'window_name': 'other',
                    'dataset_name' : 'Scan linear power'
                    }

        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)

        #scan_which_parameter = 'EitCooling.eit_cooling_zeeman_splitting'
        #my_unit = 'MHz'
        #avg_value = 13.1517
        #delta_value = 2.0
        #min_value = avg_value - delta_value
        #max_value = avg_value + delta_value
        #
        #no_of_steps = 30

        #scan_which_parameter = 'EitCooling.eit_cooling_amplitude_397_linear'
        #my_unit = 'dBm'
        #min_value = -40.0
        #max_value = -5.0
        #no_of_steps = 30.0
        
        #scan_which_parameter = 'EitCooling.eit_cooling_amplitude_397_sigma'
        #my_unit = 'dBm'
        #min_value = -30.0
        #max_value = -5.0
        #no_of_steps = 30.0

        scan_which_parameter = 'EitCooling.eit_cooling_linear_397_freq_offset'
        my_unit = 'MHz'
        min_value = -20.0
        max_value = +20.0
        no_of_steps = 50.0


        my_linear_offset = 1.8
        # define the frequency at which to take the spectrum points
        #spec_min_value = -6.869
        #spec_max_value = spec_min_value
        my_729_amplitude = -18
        my_729_duration = 160
        spec_avg_value = -10.7237
        spec_delta = 0.001
        spec_no_of_points = 1

        scan_param = [WithUnit(min_value, my_unit), WithUnit(max_value, my_unit), no_of_steps]

        self.scan = scan_methods.simple_scan(scan_param, my_unit)

        for i,vary_param in enumerate(self.scan):
            print vary_param

            should_stop = self.pause_or_stop()
            if should_stop: break

            replace = TreeDict.fromdict({
                                    scan_which_parameter:vary_param,
                                    #'EitCooling.linear_offset_scan':WithUnit(my_linear_offset, 'MHz'),
                                    'Documentation.sequence':scan_which_parameter,
                                    'Spectrum.manual_scan':(WithUnit(spec_avg_value - spec_delta, 'MHz'), WithUnit(spec_avg_value + spec_delta, 'MHz'), spec_no_of_points),
                                    'Spectrum.scan_selection':'manual',
                                    'Spectrum.manual_amplitude_729':WithUnit(my_729_amplitude, 'dBm'),
                                    'Spectrum.manual_excitation_time':WithUnit(my_729_duration, 'us')
                                       })
            
            self.spectrum.set_parameters(replace)
   
            (fr, ex) = self.spectrum.run(cxn, context)

            #print ex

            fr = np.array(fr)
            ex = np.array(ex)
            ex = ex.flatten()
            ex = np.mean(ex)

            submission = [vary_param[my_unit]]
            submission.extend([ex])
            
            self.dv.add(submission, context = self.save_context)
   
    def finalize(self, cxn, context):
        self.spectrum.finalize(cxn, context)

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_linear_power(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
