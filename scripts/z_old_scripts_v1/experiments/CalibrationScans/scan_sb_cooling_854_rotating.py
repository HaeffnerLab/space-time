from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.rabi_flop_scannable import rabi_flopping_scannable as rf
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import numpy as np
import labrad

class scan_sb_cooling_854_rotating(experiment):

    name = 'ScanSBC_854_rotating'
    required_parameters = [('CalibrationScans', 'sbc_854_scan'),

                           ('Rotation','drive_frequency'),
                           ('Rotation','voltage_pp'),
                           ('Rotation','start_hold'),
                           ('Rotation','frequency_ramp_time'),
                           ('Rotation','ramp_down_time'),
                           ('Rotation','end_hold'),
                           ('Rotation','start_phase'),
                           ('Rotation','middle_hold')]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(rf.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('SidebandCooling','sideband_cooling_amplitude_854'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.rabi_flop = self.make_experiment(rf)
        self.rabi_flop.initialize(cxn, context, ident)
        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.awg_rotation = cxn.keysight_33500b
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):
        
        self.program_rotation()

        dv_args = {'output_size':self.rabi_flop.excite.output_size,
                   'experiment_name': self.name,
                   'window_name': 'other',
                   'dataset_name': '854_scan'
                   }
        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)
        
        scan_param = self.parameters.CalibrationScans.sbc_854_scan
        self.scan = scan_methods.simple_scan(scan_param, 'dBm')
        
        for i,ampl in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            replace = TreeDict.fromdict({
                                     'SidebandCooling.sideband_cooling_amplitude_854':ampl
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation = self.rabi_flop.run(cxn, context)
            if excitation is None: break 
            submission = [ampl['dBm']]
            submission.extend([excitation])
            self.dv.add(submission, context = self.save_context)
            self.update_progress(i)

    def program_rotation(self):
        rp = self.parameters.Rotation
        frequency_ramp_time = rp.frequency_ramp_time
        start_hold = rp.start_hold
        ramp_down_time = rp.ramp_down_time
        start_phase = rp.start_phase
        middle_hold = rp.middle_hold
        end_hold = rp.end_hold
        voltage_pp = rp.voltage_pp
        drive_frequency = rp.drive_frequency
        self.awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation_sin_spin')

    def finalize(self, cxn, context):
        old_freq = self.pv.get_parameter('RotationCW','drive_frequency')['kHz']
        old_phase = self.pv.get_parameter('RotationCW','start_phase')['deg']
        old_amp =self.pv.get_parameter('RotationCW','voltage_pp')['V']
        self.awg_rotation.update_awg(old_freq*1e3,old_amp,old_phase)
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
    exprt = scan_sb_cooling_854_rotating(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
