import labrad
import numpy as np
from common.abstractdevices.script_scanner.scan_methods import experiment
from lineshape_397 import lineshape_397 #replace this
from treedict import TreeDict
import time
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.experiments.CalibrationScans.fitters import scat_rate_fitter

class measure_397_lineshape(experiment):
    
    name = 'measure_397_lineshape'
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

                           ('StateReadout','repeat_each_measurement'),

                           ('Spectroscopy_397','frequency_scan_397'),
                           ('Spectroscopy_397','calibration_channel_397'),
                           ('Spectroscopy_397','power_397'),
                           ('Spectroscopy_397','readout_duration'),
                           # ('Spectroscopy_397','frequency_397'),

                           ('Spectroscopy_397','power_866'),
                           ('Spectroscopy_397','frequency_866'),
                           
                           ('StatePreparation','channel_397_linear'),
                           ('StatePreparation','channel_397_sigma')
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        # parameters = parameters.union(set(cls.pulse_sequence.all_required_parameters()))
        parameters = list(parameters)
        # parameters.remove(('Spectrosocpy_397', 'frequency_397'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.dv = cxn.data_vault
        self.pulser = cxn.pulser
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') 
        
        self.excite = self.make_experiment(lineshape_397)  #needs right experiment
        self.excite.initialize(cxn, context, ident)        
        
        self.measure_397_lineshape_save_context = cxn.context()
        self.fitter = scat_rate_fitter()
        
        #try:
        #    self.grapher = cxn.grapher #might not be right yet...
        #except: self.grapher = None

    def setup_sequence_parameters(self):       
        spec = self.parameters.Spectroscopy_397
        minim,maxim,steps = spec.frequency_scan_397
        minim = minim['MHz']; maxim = maxim['MHz']
        self.scan = np.linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'MHz') for pt in self.scan]      

    def run(self, cxn, context):
        import time
        
        self.setup_sequence_parameters()
        
        dv_args = {'output_size': 1,
                   'experiment_name' : self.name,
                   'window_name': 'spectroscopy_397_frequency',
                   'dataset_name' : 'spectroscopy_397_frequency'
                   }

        scan_methods.setup_data_vault(cxn, self.measure_397_lineshape_save_context, dv_args)
        
        freq_arr = []
        exci = []

        for i,freq in enumerate(self.scan):
            print freq
            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.do_get_excitation(cxn, context, freq)
            if excitation is None: break
            else:
                submission = [freq['MHz']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.measure_397_lineshape_save_context)
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
    
    
    
    def do_get_excitation(self, cxn, context, freq):
        self.parameters['Spectroscopy_397.frequency_397'] = freq #WithUnit(220.0,'MHz') + (freq/2.0)
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
    exprt = measure_397_lineshape(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
