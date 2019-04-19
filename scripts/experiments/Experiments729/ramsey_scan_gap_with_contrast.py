from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.ramsey_scanphase_two_modes_rotating import ramsey_scanphase_two_modes_rotating
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import time
import numpy as np
import labrad

class ramsey_scan_gap_with_contrast(experiment):

    name = 'RamseyScanGap_with_contrast'

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
                           ('RamseyScanGap', 'scangap')
                           ]

    # parameters to overwrite
    remove_parameters = [
        ('Ramsey', 'ramsey_time')
        ]

    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(ramsey_scanphase_two_modes_rotating.all_required_parameters()))
        parameters = list(parameters)
        for p in cls.remove_parameters:
            parameters.remove(p)
        return parameters
    
    
    def initialize(self, cxn, context, ident):

        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.scan_phase = self.make_experiment(ramsey_scanphase_two_modes_rotating)
        
        self.scan_phase.initialize(cxn, context, ident)

        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
        #self.dds_cw = cxn.dds_cw
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):

        if self.parameters.StateReadout.pmt_mode =='exci_and_parity':
            output_size = 2
        else:
            output_size = 1

        dv_args = {'output_size': output_size,
                    'experiment_name' : self.name,
                    'window_name': 'ramsey_contrast',
                    'dataset_name' : 'coherence_scan'
                    }

        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)

        scan_param = self.parameters.RamseyScanGap.scangap

        self.scan = scan_methods.simple_scan(scan_param, 'us')

        for i,gap_time in enumerate(self.scan):
            #should_stop = self.pause_or_stop()
            #if should_stop: break
       
            replace = TreeDict.fromdict({
                                    'Ramsey.ramsey_time':gap_time,
                                    'Documentation.sequence':'RamseyScanGap_with_contrast',
                                       })
            
            self.scan_phase.set_parameters(replace)
            #self.calibrate_temp.set_progress_limits(0, 33.0)
   
            contrast = self.scan_phase.run(cxn, context)

            
            submission = [gap_time['us']]
            submission.extend(contrast)
            #print nbar
            self.dv.add(submission, context = self.save_context)
   
    def finalize(self, cxn, context):
        self.scan_phase.finalize(cxn, context)

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = ramsey_scan_gap_with_contrast(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
