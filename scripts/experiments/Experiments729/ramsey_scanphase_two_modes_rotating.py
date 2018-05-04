from common.abstractdevices.script_scanner.scan_methods import experiment
from excitations import excitation_ramsey_two_mode
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace

class ramsey_scanphase_two_modes_rotating(experiment):
    
    name = 'RamseyScanPhase_TwoModes_rotating'
    required_parameters = [
                           ('RamseyScanPhase', 'scanphase'),
                           
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),

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
                           ('Ramsey','echo_frequency'),
                           
                           ('TrapFrequencies','axial_frequency'),
                           ('TrapFrequencies','radial_frequency_1'),
                           ('TrapFrequencies','radial_frequency_2'),
                           ('TrapFrequencies','rf_drive_frequency'),
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(excitation_ramsey_two_mode.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        #parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        parameters.remove(('Ramsey','first_pulse_frequency'))
        parameters.remove(('Ramsey','second_pulse_frequency'))
        parameters.remove(('Ramsey','second_pulse_phase'))
        parameters.remove(('Ramsey','echo_frequency'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_ramsey_two_mode)
        self.excite.initialize(cxn, context, ident)
        self.scan = []
        self.amplitude = None
        self.duration = None
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.data_save_context = cxn.context()
        self.awg_rotation = cxn.keysight_33500b
        self.grapher=cxn.grapher
        # self.setup_data_vault()
    
    def setup_sequence_parameters(self):
        r = self.parameters.Ramsey
        flop = self.parameters.RabiFlopping
        first_pulse_frequency = cm.frequency_from_line_selection(r.frequency_selection, r.first_pulse_manual_frequency_729, r.first_pulse_line, self.drift_tracker)
        second_pulse_frequency = cm.frequency_from_line_selection(r.frequency_selection, r.second_pulse_manual_frequency_729, r.second_pulse_line, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if r.frequency_selection == 'auto':
            first_pulse_frequency = cm.add_sidebands(first_pulse_frequency, r.first_pulse_sideband_selection, trap)   
            second_pulse_frequency = cm.add_sidebands(second_pulse_frequency, r.second_pulse_sideband_selection, trap)    
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


        #import IPython
        #IPython.embed()
        
        #self.parameters['Ramsey.first_pulse_duration'] = self.parameters.Ramsey.rabi_pi_time / 2.0
        #self.parameters['Ramsey.second_pulse_duration'] = self.parameters.Ramsey.rabi_pi_time / 2.0
        
        r = self.parameters.Ramsey
        echo_frequency = cm.frequency_from_line_selection(r.echo_frequency_selection, r.echo_manual_frequency_729, r.echo_line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if r.frequency_selection == 'auto':
            echo_frequency = cm.add_sidebands(echo_frequency, r.echo_sideband_selection, trap)   
        self.parameters['Ramsey.echo_frequency'] = echo_frequency
        
        minim,maxim,steps = self.parameters.RamseyScanPhase.scanphase
        minim = minim['deg']; maxim = maxim['deg']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'deg') for pt in self.scan]
        
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
        ds = self.dv.new('{0} {1}'.format(self.name, datasetNameAppend),[('Second pulse phase', 'deg')], dependants , context = self.data_save_context)
        window_name = self.parameters.get('RamseyScanPhase.window_name', ['ramsey'])[0]
        self.dv.add_parameter('Window', window_name, context = self.data_save_context)
        self.dv.add_parameter('plotLive', True, context = self.data_save_context)
        self.grapher.plot_with_axis(ds,window_name,self.scan,False)
        
    def run(self, cxn, context):
        self.setup_sequence_parameters()
        self.setup_data_vault()
        for i,duration in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            self.parameters['Ramsey.second_pulse_phase'] = duration
            self.excite.set_parameters(self.parameters)
            excitation, readouts = self.excite.run(cxn, context)
            submission = [duration['deg']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.data_save_context)
            self.update_progress(i)
            
    @property
    def output_size(self):
        if self.use_camera:
            return int(self.parameters.IonsOnCamera.ion_number)
        else:
            return 1
     
    def finalize(self, cxn, context):
        old_freq = self.pv.get_parameter('RotationCW','drive_frequency')['kHz']
        old_phase = self.pv.get_parameter('RotationCW','start_phase')['deg']
        old_amp =self.pv.get_parameter('RotationCW','voltage_pp')['V']
        self.awg_rotation.update_awg(old_freq*1e3,old_amp,old_phase)
        self.save_parameters(self.dv, cxn, self.cxnlab, self.data_save_context)

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
    exprt = ramsey_scanphase_two_modes_rotating(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)