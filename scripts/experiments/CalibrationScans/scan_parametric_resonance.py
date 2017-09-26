from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.rabi_flop_scannable import rabi_flopping_scannable as rf
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import numpy as np
import labrad

class scan_parametric_resonance(experiment):

    name = 'ScanParametricResonance'
    required_parameters = [
                           ('Rotation', 'drive_frequency_scan_interval'),
                           ('Rotation','drive_frequency'),
                           ('Rotation','voltage_pp'),
                           ('Rotation','frequency_ramp_time'),
                           ('Rotation','start_phase'),
                           ('Rotation','middle_hold'),

                           ('DopplerCooling','doppler_cooling_duration'),
                           ('SidebandCooling','sideband_cooling_optical_pumping_duration'),
                           ('SidebandCooling','sideband_cooling_cycles'),
                           ('SidebandCoolingContinuous','sideband_cooling_continuous_duration'),
                           ('StateReadout','pmt_readout_duration'),
                           ('StatePreparation','sideband_cooling_enable'),
                            ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(rf.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Rotation','drive_frequency'))
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
        
        dv_args = {'output_size':self.rabi_flop.excite.output_size,
                   'experiment_name': self.name,
                   'window_name': 'other',
                   'dataset_name': 'parametric_resonanace_scan'
                   }

        rp = self.parameters.Rotation
        frequency_ramp_time = rp.frequency_ramp_time
        if self.parameters.StatePreparation.sideband_cooling_enable:
            sideband_cooling_time  = (self.parameters.SidebandCooling.sideband_cooling_optical_pumping_duration + self.parameters.SidebandCoolingContinuous.sideband_cooling_continuous_duration)*self.parameters.SidebandCooling.sideband_cooling_cycles + WithUnit(1.0,'ms')
        else:
            sideband_cooling_time = WithUnit(0,'ms')
        start_hold = self.parameters.DopplerCooling.doppler_cooling_duration + sideband_cooling_time + WithUnit(0.5,'ms')
        start_phase = rp.start_phase
        middle_hold = rp.middle_hold
        end_hold = self.parameters.StateReadout.pmt_readout_duration + WithUnit(1,'ms')
        voltage_pp = rp.voltage_pp

        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)
        
        scan_param = self.parameters.Rotation.drive_frequency_scan_interval
        self.scan = scan_methods.simple_scan(scan_param, 'kHz')
        
        for i,freq in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break

    #prgroam AWG!
            drive_frequency = freq
            self.awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],0.0,end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'spin_up_spin_down')
            heat_time = 2*frequency_ramp_time + middle_hold + WithUnit(0.5, 'ms')

            replace = TreeDict.fromdict({
                                     'Heating.background_heating_time':heat_time
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation = self.rabi_flop.run(cxn, context)
            if excitation is None: break 
            submission = [freq['kHz']]
            submission.extend([excitation])
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
    exprt = scan_parametric_resonance(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
