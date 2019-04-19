from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.ramsey_scangap_two_modes_rotating import ramsey_scangap_two_modes_rotating
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import time
import numpy as np
import labrad

class diffusion_with_ramsey(experiment):

    name = 'DiffusionWithRamsey'

    required_parameters = [# ('DriftTracker', 'line_selection_1'),
                           # ('DriftTracker', 'line_selection_2'),
                           # ('CalibrationScans', 'do_rabi_flop_carrier'),
                           # ('CalibrationScans', 'do_rabi_flop_radial1'),
                           # ('CalibrationScans', 'do_rabi_flop_radial2'),
                           # ('CalibrationScans', 'carrier_time_scan'),
                           # ('CalibrationScans', 'radial1_time_scan'),
                           # ('CalibrationScans', 'radial2_time_scan'),
                           # ('CalibrationScans', 'carrier_excitation_power'),
                           # ('CalibrationScans', 'radial1_excitation_power'),
                           # ('CalibrationScans', 'radial2_excitation_power'),
                           # ('CalibrationScans', 'heating_rate_scan_interval')
                           ('Heating','additional_wait_time_scan')
                           ]

    # parameters to overwrite
    remove_parameters = [
        # ('Heating', 'background_heating_time')
        ]

    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(ramsey_scangap_two_modes_rotating.all_required_parameters()))
        parameters = list(parameters)
        for p in cls.remove_parameters:
            parameters.remove(p)
        return parameters
    
    
    def initialize(self, cxn, context, ident):

        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.ramsey_gap = self.make_experiment(ramsey_scangap_two_modes_rotating)
        
        self.ramsey_gap.initialize(cxn, context, ident)

        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
        #self.dds_cw = cxn.dds_cw
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):

        dv_args = {'output_size': 1,
                    'experiment_name' : self.name,
                    'window_name': 'sigma_ell',
                    'dataset_name' : 'Diffusion_Rate'
                    }

        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)

        scan_param = self.parameters.Heating.additional_wait_time_scan

        self.scan = scan_methods.simple_scan(scan_param, 'us')

        for i,heat_time in enumerate(self.scan):
            #should_stop = self.pause_or_stop()
            #if should_stop: break
            initial_wait = self.parameters.Heating.background_heating_time
            replace = TreeDict.fromdict({
                                    'Heating.background_heating_time':initial_wait+heat_time,
                                    'Documentation.sequence':'diffusion_with_ramsey',
                                       })
            
            self.ramsey_gap.set_parameters(replace)
            #self.calibrate_temp.set_progress_limits(0, 33.0)
   
            sigma_ell = self.ramsey_gap.run(cxn, context)

            submission = [heat_time['us']]
            submission.extend([sigma_ell])
            #print nbar
            self.dv.add(submission, context = self.save_context)
   
    def finalize(self, cxn, context):
        self.ramsey_gap.finalize(cxn, context)

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = diffusion_with_ramsey(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
