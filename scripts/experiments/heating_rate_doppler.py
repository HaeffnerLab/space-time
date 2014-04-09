from common.abstractdevices.script_scanner.scan_methods import experiment
from space-time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
import time
import labrad

'''
Doppler ReCooling Experiment
'''

class doppler_recooling(experiment):
    
    name = "DopplerRecooling"

    required_parameters = [
        ('DopplerRecooling', 'heating_scan')
        ]
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.cxnlab = labrad.connect('192.168.169.49')
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
    
        self.nbars = []
        self.heating_times = self.make_heating_times(self.parameters.DopplerRecooling.heating_scan)
       
        self.setup_data_vault()
        self.save_context = cxn.context()
       
    def make_heating_times(self, (min_time, max_time,num_steps)):
        heating_times = []
        min_time = min_time['ms']; max_time = max_time['ms']
        step_size = (max_time-min_time)/num_steps
        current = min_time
        while(current<=max_time):
             heating_times.append(current)
             current = current + step_size
        return heating_times
    
    def setup_data_vault(self):
        localtime = time.localtime()
        try:
            direc = self.parameters.get('DopplerRecooling.save_directory') 
            self.directory = ['']
            self.directory.extend(direc.split('.'))
        except KeyError:
            dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
            self.datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
            
            directory = ['','Experiments']
            directory.extend([self.name])
            directory.extend(dirappend)
        
        self.datasetName = 'Readout {}'.format(self.datasetNameAppend)
        self.dv.cd(directory,True,context = self.save_context)
        self.dv.new(self.datasetName,[('Iteration','Arb')],[('Readout Counts','Arb','Arb')],context = self.save_context)
