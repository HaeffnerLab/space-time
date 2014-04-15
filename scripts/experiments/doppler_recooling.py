from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.scriptLibrary import dvParameters
from space_time.scripts.scriptLibrary.fly_processing import Binner
import numpy
from numpy import linspace
from space_time.scripts.PulseSequences.doppler_pause import doppler_pause
import time
from labrad.units import WithUnit

'''
Doppler ReCooling Experiment - do seperate exp to scan heating times
'''

class doppler_recooling(experiment):
    
    name = "DopplerRecooling"

    required_parameters = [
       # ('DopplerRecooling', 'heating_scan'),
        ('DopplerRecooling','iterations_cooling')
        ]
    
    required_parameters.extend(doppler_pause.all_required_parameters())
    
# required_parameters.remove(('Heating','background_heating_time'))
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.cxnlab = labrad.connect('192.168.169.49')
        self.dv = cxn.data_vault
        self.pv = cxn.parametervault
        
        #min_time,max_time,steps = self.parameters.DopplerRecooling.heating_scan
        #min_time = min_time['ms']; max_time = max_time['ms']
        #self.heating_times = linspace(min_time,max_time,steps)
       
        self.iterations = self.parameters.DopplerRecooling.iterations_cooling
        self.binner = Binner(self.cooling_duration,100e-9)
        
        self.save_context = cxn.context()
        self.timetag_save_context = cxn.context()
        self.binned_save_context = cxn.context()
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
        
        #self.datasetName = 'Timetags {}'.format(self.datasetNameAppend)
        self.dv.cd(directory,True,context = self.timetag.save_context)
        self.dv.new('Timetags {}'.format(self.datasetNameAppend),[('Time','sec')],[('Photons','Arb','Arb')],context = self.timetag_save_context)
        
        self.dv.cd(directory,context = self.binned_save_context)
        
        #not sure this is what I want to plot

    def plot_current_sequence(self,cxn):
        from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
        dds = cxn.pulser.human_readable_dds()
        ttl = cxn.pulser.human_readable_ttl()
        channels = cxn.pulser.get_channels().asarry
        sp = SequencePlotter(ttl.asarray,dds.aslist,channels)
        sp.makePlot()
        
    def program_pulser(self):
        self.pulser.reset_timetags()
        pulse_sequence = doppler_pause(self.parameters)
        pulse_sequence.programSequence(self.pulser)
        self.start_recording_timetags = pulse_sequence.start_recording_timetags
        self.cooling_duration = pulse_sequence.cooling_duration
        
    def get_timetags(self,iteration):
        self.pulser.start_sequence() #is this right?
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence
        timetags = self.pulser.get_timetags().asarray
        timetags = timetags - self.start_recording_timetags
        self.dv.add([iteration,timetags],context = self.timetag_save_context)
        return timetags
            
    def save_histogram(self):
        bins,hist = self.binner.getBinned(False)
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        #check the units on what i'm binning
        self.dv.new('Binned {}'.format(datasetNameAppend),[('Time','us')],[('CountRate','Counts/sec','Counts/sec')],context = self.binned_save_context)
        self.dv.add_parameter('plotLive',True, context = self.binned_save_context) 
        self.dv.add_parameter('Window',['ReCooling Histogram'], context = self.binned_save_context)
        self.dv.add(numpy.vstack((bins,hist)).transpose(),context = self.binned_save_context)
        
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)
        
    def run(self,cxn,context):
    
        #do the dopplerpause sequence a bunch of times and bin everything
        
        for index in range(self.iterations):
            timetags = self.get_timetags(index)
            self.binner.add(timetags)
            self.save_histogram()
            self.update_progress(index)
            should_stop = self.pause_or_stop()
            if should_stop: break
            
        self.plot_current_sequence(cxn)
        #somehow save/graph this stuff

    def finalize(self, cxn, context):
        self.save_parameters(self.dv, cxn, self.cxnlab, self.timetag_save_context)


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


    
