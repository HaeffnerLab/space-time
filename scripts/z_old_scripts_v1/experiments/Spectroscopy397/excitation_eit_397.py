from common.abstractdevices.script_scanner.scan_methods import experiment
from labrad.units import WithUnit
import numpy
import time
from space_time.scripts.PulseSequences.eit_lineshape_397 import eit_lineshape_397
       
class excitation_eit_397(experiment):
    name = 'excitation_eit_397'  
    excitation_required_parameters = [
                            ('StateReadout', 'repeat_each_measurement'),
                            ('StateReadout', 'pmt_readout_duration'),
                           ]
    pulse_sequence = eit_lineshape_397
    
    @classmethod
    def all_required_parameters(cls):
        params = set(cls.excitation_required_parameters)
        params = params.union(set(cls.pulse_sequence.all_required_parameters()))
        params = list(params)
        params.remove(('OpticalPumping', 'optical_pumping_frequency_729'))
        #params.remove(('SidebandCooling', 'sideband_cooling_frequency_729'))
        params.remove(('OpticalPumpingAux', 'aux_optical_frequency_729'))
        #params.remove(('StateReadout', 'state_readout_duration'))
        #params.remove(('SequentialSBCooling', 'frequency'))
        return params
    
    def initialize(self, cxn, context, ident, use_camera_override=None):
        self.pulser = cxn.pulser
        self.dv = cxn.data_vault
        self.total_readouts = []
        self.readout_save_context = cxn.context()
        self.histogram_save_context = cxn.context()
        self.readout_save_iteration = 0
        
        self.excitation_prob = self.parameters.StateReadout.excitation_prob
        
#        self.setup_sequence_parameters()
        self.setup_data_vault()
                   
    def setup_data_vault(self):
        localtime = time.localtime()
        self.datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        self.save_directory = ['','Experiments']
        self.save_directory.extend([self.name])
        self.save_directory.extend(dirappend)
        self.dv.cd(self.save_directory ,True, context = self.readout_save_context)
        self.dv.new('Readout {}'.format(self.datasetNameAppend),[('Iteration', 'Arb')],[('Readout Counts','Arb','Arb')], context = self.readout_save_context)        
    
#    def setup_sequence_parameters(self):
#        op = self.parameters.OpticalPumping
#        optical_pumping_frequency = cm.frequency_from_line_selection(op.frequency_selection, op.manual_frequency_729, op.line_selection, self.drift_tracker, sp.optical_pumping_enable)
#        self.parameters['OpticalPumping.optical_pumping_frequency_729'] = optical_pumping_frequency
#        aux = self.parameters.OpticalPumpingAux
#        aux_optical_pumping_frequency = cm.frequency_from_line_selection('auto', WithUnit(0,'MHz'),  aux.aux_op_line_selection, self.drift_tracker, aux.aux_op_enable)
#        self.parameters['OpticalPumpingAux.aux_optical_frequency_729'] = aux_optical_pumping_frequency
#        sc = self.parameters.SidebandCooling
#        sideband_cooling_frequency = cm.frequency_from_line_selection(sc.frequency_selection, sc.manual_frequency_729, sc.line_selection, self.drift_tracker, sp.sideband_cooling_enable)
#        trap = self.parameters.TrapFrequencies
#        if sc.frequency_selection == 'auto': 
#            #trap = self.parameters.TrapFrequencies
#            sideband_cooling_frequency = cm.add_sidebands(sideband_cooling_frequency, sc.sideband_selection, trap)
#        self.parameters['SidebandCooling.sideband_cooling_frequency_729'] = sideband_cooling_frequency
#        #print "sbc"
#        #print sideband_cooling_frequency
#        sc2 = self.parameters.SequentialSBCooling
#        sc2freq = cm.frequency_from_line_selection(sc.frequency_selection, sc.manual_frequency_729, sc.line_selection, self.drift_tracker, sp.sideband_cooling_enable)
#        sc2freq = cm.add_sidebands(sc2freq, sc2.sideband_selection, trap)
#        self.parameters['SequentialSBCooling.frequency'] = sc2freq
#        #print sc2freq

    def plot_current_sequence(self, cxn):
        from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
        dds = cxn.pulser.human_readable_dds()
        ttl = cxn.pulser.human_readable_ttl()
        channels = cxn.pulser.get_channels()
        sp = SequencePlotter(ttl, dds.aslist, channels)
        sp.makePlot()
        
    def run(self, cxn, context):
        # set state readout time
        self.parameters['StateReadout.state_readout_duration'] = self.parameters.StateReadout.pmt_readout_duration
        repetitions = int(self.parameters.StateReadout.repeat_each_measurement)
        pulse_sequence = self.pulse_sequence(self.parameters)
                
        pulse_sequence.programSequence(self.pulser)

        #self.plot_current_sequence(cxn)
            
        
        self.pulser.start_number(repetitions)
        
        self.pulser.wait_sequence_done()
        
        self.pulser.stop_sequence()
        
        readouts = self.pulser.get_readout_counts()
            
        self.save_data(readouts)            
        if len(readouts):
            ion_state = [numpy.sum(readouts) / float(len(readouts))]
        else:
            #got no readouts
            ion_state = -1.0                 
            
        return ion_state, readouts    
    
    @property
    def output_size(self):
        return 1

    def finalize(self, cxn, context):
        pass

    def save_data(self, readouts):
        #save the current readouts
        iters = numpy.ones_like(readouts) * self.readout_save_iteration
        self.dv.add(numpy.vstack((iters, readouts)).transpose(), context = self.readout_save_context)
        self.readout_save_iteration += 1
        self.total_readouts.extend(readouts)
        if (len(self.total_readouts) >= 500):
            hist, bins = numpy.histogram(self.total_readouts, 50)
            self.dv.cd(self.save_directory ,True, context = self.histogram_save_context)
            self.dv.new('Histogram {}'.format(self.datasetNameAppend),[('Counts', 'Arb')],[('Occurence','Arb','Arb')], context = self.histogram_save_context )
            self.dv.add(numpy.vstack((bins[0:-1],hist)).transpose(), context = self.histogram_save_context )
            self.dv.add_parameter('Histogram729', True, context = self.histogram_save_context )
            self.total_readouts = []
    
