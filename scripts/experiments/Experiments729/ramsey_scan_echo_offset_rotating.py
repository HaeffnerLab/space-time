from common.abstractdevices.script_scanner.scan_methods import experiment
from excitations import excitation_ramsey_two_mode
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace

class ramsey_scan_echo_offset_rotating(experiment):
    
    name = 'RamseyScanEchoOffset_rotating'
    ramsey_required_parameters = [
                           ('RamseyScanGap', 'detuning'),
                           ('RamseyScanGap', 'scangap'),

                           ('Rotation','drive_frequency'),
                           ('Rotation','voltage_pp'),
                           ('Rotation','start_hold'),
                           ('Rotation','frequency_ramp_time'),
                           ('Rotation','ramp_down_time'),
                           ('Rotation','end_hold'),
                           ('Rotation','start_phase'),
                           ('Rotation','middle_hold'),

                           ('Ramsey','echo_frequency_selection'),
                           ('Ramsey','echo_manual_frequency_729'),
                           ('Ramsey','echo_line_selection'),
                           ('Ramsey','echo_sideband_selection'),
                           ('Ramsey','scan_echo_offset'),
                           #('Ramsey','echo_frequency'),

                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),
                           
                           ('TrapFrequencies','axial_frequency'),
                           ('TrapFrequencies','radial_frequency_1'),
                           ('TrapFrequencies','radial_frequency_2'),
                           ('TrapFrequencies','rf_drive_frequency'),
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.ramsey_required_parameters)
        parameters = parameters.union(set(excitation_ramsey_two_mode.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Ramsey','first_pulse_frequency'))
        parameters.remove(('Ramsey','second_pulse_frequency'))
        parameters.remove(('Ramsey','echo_frequency'))
        # parameters.remove(('Ramsey','second_pulse_phase'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_ramsey_two_mode)
        self.excite.initialize(cxn, context, ident)
        self.scan = []
        self.amplitude = None
        self.offset = None
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.awg_rotation = cxn.keysight_33500b
        self.data_save_context = cxn.context()     
        try:
            self.grapher = cxn.grapher
        except: self.grapher = None
        self.cxn = cxn
        
        self.setup_sequence_parameters()     
        self.setup_data_vault()
    
    def setup_sequence_parameters(self):
        r = self.parameters.Ramsey
        flop = self.parameters.RabiFlopping
        first_pulse_frequency = cm.frequency_from_line_selection(r.frequency_selection, r.first_pulse_manual_frequency_729, r.first_pulse_line, self.drift_tracker)
        second_pulse_frequency = cm.frequency_from_line_selection(r.frequency_selection, r.second_pulse_manual_frequency_729, r.second_pulse_line, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if r.frequency_selection == 'auto':
            first_pulse_frequency = cm.add_sidebands(first_pulse_frequency, r.first_pulse_sideband_selection, trap)   
            second_pulse_frequency = cm.add_sidebands(second_pulse_frequency, r.second_pulse_sideband_selection, trap)   
        first_pulse_frequency += self.parameters.RamseyScanGap.detuning 
        second_pulse_frequency += self.parameters.RamseyScanGap.detuning
        self.parameters['Ramsey.second_pulse_frequency'] = second_pulse_frequency
        self.parameters['Ramsey.first_pulse_frequency'] = first_pulse_frequency
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729

        rp = self.parameters.Rotation
        frequency_ramp_time = rp.frequency_ramp_time
        start_hold = rp.start_hold
        ramp_down_time = rp.ramp_down_time
        start_phase = rp.start_phase
        middle_hold = rp.middle_hold
        end_hold = rp.end_hold
        voltage_pp = rp.voltage_pp
        drive_frequency = rp.drive_frequency
        self.awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation')

        r = self.parameters.Ramsey
        echo_frequency = cm.frequency_from_line_selection(r.echo_frequency_selection, r.echo_manual_frequency_729, r.echo_line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if r.frequency_selection == 'auto':
            echo_frequency = cm.add_sidebands(echo_frequency, r.echo_sideband_selection, trap)   
        self.parameters['Ramsey.echo_frequency'] = echo_frequency

        # flop = self.parameters.RabiFlopping
        # frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        # trap = self.parameters.TrapFrequencies
        # if flop.frequency_selection == 'auto':
        #     frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)   
        # frequency += self.parameters.RamseyScanGap.detuning
        # #print frequency
        # self.parameters['Excitation_729.rabi_excitation_frequency'] = frequency
        # self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729
        
        minim,maxim,steps = self.parameters.Ramsey.scan_echo_offset
        minim = minim['us']; maxim = maxim['us']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'us') for pt in self.scan]
        
        #print self.scan
        
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        self.dv.cd(directory, True,context = self.data_save_context)
        
        
        #self.dv.new('{0} {1}'.format(self.name, datasetNameAppend),[('Excitation', 'us')], dependants , context = self.data_save_context)
        #window_name = self.parameters.get('RamseyScanGap.window_name', ['Ramsey Gap Scan'])
        #self.dv.add_parameter('Window', window_name, context = self.data_save_context)
        #self.dv.add_parameter('plotLive', True, context = self.data_save_context)
        
        
        ds = self.dv.new('Ramsey {}'.format(datasetNameAppend),[('Excitation', 'us')], dependants , context = self.data_save_context)
        #window_name = self.parameters.get('RamseyScanGap.window_name', ['Ramsey Gap Scan'])[0]
        window_name = 'ramsey'
               
       # print window_name    
               
        self.dv.add_parameter('Window', [window_name], context = self.data_save_context)
        #self.dv.add_parameter('plotLive', False, context = self.spectrum_save_context)
        self.save_parameters(self.dv, self.cxn, self.cxnlab, self.data_save_context)
        sc = []
        if self.parameters.Display.relative_frequencies:
            sc =[x - self.carrier_frequency for x in self.scan]
        else: sc = self.scan
        
        #print sc
        
        if self.grapher is not None:
            self.grapher.plot_with_axis(ds, window_name, sc, False)


  
        
    def run(self, cxn, context):
        #self.setup_sequence_parameters()
        for i,offset in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            self.parameters['Ramsey.echo_offset'] = offset
            self.excite.set_parameters(self.parameters)
            excitation, readouts = self.excite.run(cxn, context)
            submission = [offset['us']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.data_save_context)
            self.update_progress(i)
     
    def finalize(self, cxn, context):
        old_freq = self.pv.get_parameter('RotationCW','drive_frequency')['kHz']
        old_phase = self.pv.get_parameter('RotationCW','start_phase')['deg']
        old_amp =self.pv.get_parameter('RotationCW','voltage_pp')['V']
        self.awg_rotation.update_awg(old_freq*1e3,old_amp,old_phase)
        #self.save_parameters(self.dv, cxn, self.cxnlab, self.data_save_context)
        pass
    
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
    exprt = ramsey_scan_echo_offset_rotating(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
