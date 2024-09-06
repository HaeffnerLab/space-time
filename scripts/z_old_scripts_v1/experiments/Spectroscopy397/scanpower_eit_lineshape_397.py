import labrad
import numpy as np
from common.abstractdevices.script_scanner.scan_methods import experiment
from excitation_eit_397 import excitation_eit_397 #replace this
from treedict import TreeDict
import time
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.experiments.CalibrationScans.fitters import scat_rate_fitter

class scanpower_eit_lineshape_397(experiment):
    
    name = 'measure_eit_lineshape_397'
    required_parameters = [
                           ('DopplerCooling','doppler_cooling_frequency_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397'), 
                           ('DopplerCooling','doppler_cooling_amplitude_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397Extra'),
                           ('DopplerCooling','doppler_cooling_repump_additional'),
                           ('DopplerCooling','doppler_cooling_frequency_866'),
                           ('DopplerCooling','doppler_cooling_include_second_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397'),
                           ('DopplerCooling','doppler_cooling_amplitude_866'),
                           ('DopplerCooling','doppler_cooling_amplitude_397Extra'),
                           ('DopplerCooling','doppler_cooling_duration'),
                           
                           ('StatePreparation','channel_397_linear'),
                           ('StatePreparation','channel_397_sigma'),
                           ('StatePreparation','eit_cooling_enable'),
                           ('StatePreparation','optical_pumping_enable'),
                           ('StatePreparation','sideband_cooling_enable'),

                           ('StateReadout','repeat_each_measurement'),

                           ('EitCooling', 'linear_offset_scan'),
                           ('EitCooling', 'eit_cooling_zeeman_splitting'),
                           ('EitCooling', 'eit_cooling_delta'),
                           ('EitCooling', 'eit_cooling_frequency_866'),
                           ('EitCooling', 'eit_cooling_linear_397_freq_offset'),
                           ('EitCooling', 'eit_cooling_duration'),
                           ('EitCooling', 'eit_cooling_amplitude_397_sigma'),
                           ('EitCooling', 'eit_cooling_amplitude_866'),
                           ('EitCooling', 'eit_cooling_amplitude_397_linear'),

                           ('Spectroscopy_397','power_scan'),
                           ('Spectroscopy_397','readout_duration'),
                           ('Spectroscopy_397','calibration_channel_397'),
                           ('Spectroscopy_397','frequency_397')
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = list(parameters)
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.dv = cxn.data_vault
        self.pulser = cxn.pulser
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') 
        
        self.excite = self.make_experiment(excitation_eit_397)  #needs right experiment
        self.excite.initialize(cxn, context, ident)        
        
        self.measure_eit_lineshape_save_context = cxn.context()
        self.fitter = scat_rate_fitter()
        
        #try:
        #    self.grapher = cxn.grapher #might not be right yet...
        #except: self.grapher = None

    def setup_sequence_parameters(self):       
        spec = self.parameters.Spectroscopy_397
        minim,maxim,steps = spec.power_scan
        minim = minim['dBm']; maxim = maxim['dBm']
        self.scan = np.linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'dBm') for pt in self.scan]      

    def run(self, cxn, context):
        import time
        
        self.setup_sequence_parameters()
        
        dv_args = {'output_size': 1,
                   'experiment_name' : self.name,
                   'window_name': 'spectroscopy_397_power',
                   'dataset_name' : 'eit_scan_397_power'
                   }

        scan_methods.setup_data_vault(cxn, self.measure_eit_lineshape_save_context, dv_args)
        
        freq_arr = []
        exci = []

        for i,pwr in enumerate(self.scan):
            print pwr
            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.do_get_excitation(cxn, context, pwr)
            if excitation is None: break
            else:
                submission = [pwr['dBm']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.measure_eit_lineshape_save_context)
            freq_arr.append(submission[0])
            exci.append(excitation)
        
      
   
        freq_arr = np.array(freq_arr)
        exci = np.array(exci)
        exci = exci.flatten()
   
        #alpha1 = self.fitter.fit(freq_arr, exci, self.parameters.Spectroscopy_397.readout_duration['us'])
        #
        #print alpha1
           
        #sb_1 = WithUnit(abs(sb_1), 'MHz')
        
        
        #return pwr, exci
    
    
    
    def do_get_excitation(self, cxn, context, pwr):
        self.parameters['EitCooling.eit_cooling_amplitude_397_sigma'] = pwr
        #self.parameters['EitCooling.eit_cooling_linear_397_freq_offset'] = 
        self.excite.set_parameters(self.parameters)
        excitation, readouts = self.excite.run(cxn, context)
        return excitation
            
    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)
        cxnlab.disconnect()
    
    def finalize(self, cxn, context):
        pass

if __name__ == '__main__':
    #normal way to launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scanpower_eit_lineshape_397(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
