from common.abstractdevices.script_scanner.scan_methods import experiment
from space-time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from numpy import linspace
from space-time.scripts.PulseSquences.doppler_pause import doppler_pause
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
        min_time,max_time,steps = self.parameters.DopplerRecooling.heating_scan
        min_time = min_time['ms']; max_time = max_time['ms']
        self.heating_times = linspace(min_time,max_time,steps)
       
        self.save_context = cxn.context()
        self.setup_data_vault()
        

    
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
        self.dv.new(self.datasetName,[('Iteration','Arb')],[('PMT Counts','Counts','Counts')],context = self.save_context)
        self.dv.add_parameter('plotLive',True)

    def run(self,cxn,context):
        for heat_time in self.heating_times:
            self.set_parameters(TreeDict.fromdict({
                                'Heating.background_heating_time':heat_time
                                }))
            #do the dopplerpause sequence

        #somehow save/graph this stuff

    def finalize(self, cxn, context):
        #self.save_parameters(self.dv, cxn, self.cxnlab, self.temp_save_context)
        #self.spectrum.finalize(cxn, context)
        #self.flop.finalize(cxn, context)
        pass

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)

if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = doppler_recooling(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


    
