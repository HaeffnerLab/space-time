from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.calibrate_temperature_rotating import calibrate_temperature_rotating
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from space_time.scripts.experiments.CalibrationScans.fitters import peak_fitter
from labrad.units import WithUnit
from treedict import TreeDict
import time
import numpy as np
import labrad

class scan_drive_frequency(experiment):

    name = 'scan_drive_frequency'

    required_parameters = [('DriftTracker', 'line_selection_1'),
                           ('DriftTracker', 'line_selection_2'),
                           ('CalibrationScans', 'do_rabi_flop_carrier'),
                           ('CalibrationScans', 'do_rabi_flop_radial1'),
                           ('CalibrationScans', 'do_rabi_flop_radial2'),
                           ('CalibrationScans', 'carrier_time_scan'),
                           ('CalibrationScans', 'radial1_time_scan'),
                           ('CalibrationScans', 'radial2_time_scan'),
                           ('CalibrationScans', 'carrier_excitation_power'),
                           ('CalibrationScans', 'radial1_excitation_power'),
                           ('CalibrationScans', 'radial2_excitation_power'),
                           #('CalibrationScans', 'heating_rate_scan_interval')
                           ('Rotation','drive_frequency_scan_interval')
                           ]

    # parameters to overwrite
    remove_parameters = [
        ('Rotation','drive_frequency')
        #('Heating', 'background_heating_time')
        ]

    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(calibrate_temperature_rotating.all_required_parameters()))
        parameters = list(parameters)
        for p in cls.remove_parameters:
            parameters.remove(p)
        return parameters
    
    
    def initialize(self, cxn, context, ident):

        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.calibrate_temp = self.make_experiment(calibrate_temperature_rotating)
        
        self.calibrate_temp.initialize(cxn, context, ident)

        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
        #self.dds_cw = cxn.dds_cw
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):

        dv_args = {'output_size': 1,
                    'experiment_name' : self.name,
                    'window_name': 'rotation_temps',
                    'dataset_name' : 'temperature_vs_drive_frequency'
                    }

        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)

        scan_param = self.parameters.Rotation.drive_frequency_scan_interval

        self.scan = scan_methods.simple_scan(scan_param, 'kHz')

        for i,drive_freq in enumerate(self.scan):
            #should_stop = self.pause_or_stop()
            #if should_stop: break
       
            replace = TreeDict.fromdict({
                                    'Rotation.drive_frequency':drive_freq,
                                    'Documentation.sequence':'scan_drive_frequency',
                                       })
            
            self.calibrate_temp.set_parameters(replace)
            #self.calibrate_temp.set_progress_limits(0, 33.0)
   
            (rsb_ex, bsb_ex) = self.calibrate_temp.run(cxn, context)

            fac = rsb_ex/bsb_ex
            nbar = fac/(1.0-fac)

            submission = [drive_freq['kHz']]
            submission.extend([nbar])
            #print nbar
            self.dv.add(submission, context = self.save_context)
   
    def finalize(self, cxn, context):
        self.calibrate_temp.finalize(cxn, context)

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_frequency_ramp_time(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
