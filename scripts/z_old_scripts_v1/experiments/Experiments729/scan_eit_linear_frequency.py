from common.abstractdevices.script_scanner.scan_methods import experiment
from excitations import excitation_729
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
from space_time.scripts.experiments.Crystallization.crystallization import crystallization
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace
import numpy as np
from space_time.scripts.scriptLibrary import scan_methods

class scan_eit_linear_frequency(experiment):
    
    name = 'scan_eit_linear_frequency'
    trap_frequencies = [
                        ('TrapFrequencies','axial_frequency'),
                        ('TrapFrequencies','radial_frequency_1'),
                        ('TrapFrequencies','radial_frequency_2'),
                        ('TrapFrequencies','rf_drive_frequency'),                       
                        ]
    rabi_required_parameters = [
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),
                           
                           #('Excitation_729','rabi_excitation_frequency'), set in Rabi flopping
                           ('Excitation_729','rabi_excitation_duration'),

                           ('EitCooling','linear_offset_scan')
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.rabi_required_parameters)
        parameters = parameters.union(set(cls.trap_frequencies))
        parameters = parameters.union(set(excitation_729.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('EitCooling','eit_cooling_linear_397_freq_offset'))
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_729)
        self.excite.initialize(cxn, context, ident)
        self.scan = []
        self.amplitude = None
        self.duration = None
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.linear_scan_save_context = cxn.context()
        self.grapher = cxn.grapher
    
    def setup_sequence_parameters(self):
        self.load_frequency()
        flop = self.parameters.RabiFlopping
        eit = self.parameters.EitCooling
        minim,maxim,steps = eit.linear_offset_scan
        minim = minim['MHz']; maxim = maxim['MHz']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'MHz') for pt in self.scan]
        
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        self.dv.cd(directory ,True, context = self.linear_scan_save_context)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        ds = self.dv.new('Rabi Flopping {}'.format(datasetNameAppend),[('Excitation', 'us')], dependants , context = self.linear_scan_save_context)
        self.dv.add_parameter('Window', ['Rabi Flopping'], context = self.linear_scan_save_context)
        #self.dv.add_parameter('plotLive', True, context = self.rabi_flop_save_context)
        if self.grapher is not None:
            self.grapher.plot_with_axis(ds, 'rabi', self.scan)
    
    def load_frequency(self):
        #reloads trap frequencies and gets the latest information from the drift tracker
        self.reload_some_parameters(self.trap_frequencies) 
        flop = self.parameters.RabiFlopping
        frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if flop.frequency_selection == 'auto':
            frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)
        self.parameters['Excitation_729.rabi_excitation_frequency'] = frequency
        
    def run(self, cxn, context):
        self.setup_sequence_parameters()
        
        dv_args = {'output_size': 1,
                   'experiment_name' : self.name,
                   'window_name': 'spectroscopy_397_frequency',
                   'dataset_name' : 'linear_frequency_offset'
                   }

        scan_methods.setup_data_vault(cxn, self.linear_scan_save_context, dv_args)
        
        t = []
        ex = []
        for i,offset in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.do_get_excitation(cxn, context, offset)
            if excitation is None: break 
            submission = [offset['MHz']]
            submission.extend([10.0*excitation[0]])
            t.append(offset['MHz'])
            ex.append(excitation)
            self.dv.add(submission, context = self.linear_scan_save_context)
            self.update_progress(i)
        return np.array(t), np.array(ex)
    
    def do_get_excitation(self, cxn, context, offset):
        self.load_frequency()
        self.parameters['EitCooling.eit_cooling_linear_397_freq_offset'] = offset
        self.excite.set_parameters(self.parameters)
        excitation, readouts = self.excite.run(cxn, context)
        print excitation
        return excitation
     
    def finalize(self, cxn, context):
        self.save_parameters(self.dv, cxn, self.cxnlab, self.linear_scan_save_context)
        self.excite.finalize(cxn, context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)
        cxnlab.disconnect()   

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_eit_linear_frequency(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
