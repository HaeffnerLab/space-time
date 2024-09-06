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

class scan_rotation_parameter(experiment):
    
    name = 'ScanRotationParameter'
    trap_frequencies = [
                        ('TrapFrequencies','rotation_frequency'),
                        ('TrapFrequencies','axial_frequency'),
                        ('TrapFrequencies','radial_frequency_1'),
                        ('TrapFrequencies','radial_frequency_2'),
                        ('TrapFrequencies','rf_drive_frequency'),                       
                        ]
    rabi_required_parameters = [
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_scan'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),
                           ('RabiFlopping','rabi_stark_shift'),
                           ('RabiFlopping_Sit','sit_on_excitation'),
                           
                           ('Rotation','drive_frequency'),
                           ('Rotation','voltage_pp'),
                           ('Rotation','start_hold'),
                           ('Rotation','frequency_ramp_time'),
                           ('Rotation','ramp_down_time'),
                           ('Rotation','end_hold'),
                           ('Rotation','start_phase'),
                           ('Rotation','middle_hold'),
                           ('Rotation','rot_parameter_to_scan'),
                           ('Rotation','rot_parameter_scan'),
                           
                           ('Crystallization', 'auto_crystallization'),
                           ('Crystallization', 'camera_record_exposure'),
                           ('Crystallization', 'camera_threshold'),
                           ('Crystallization', 'max_attempts'),
                           ('Crystallization', 'max_duration'),
                           ('Crystallization', 'min_duration'),
                           ('Crystallization', 'pmt_record_duration'),
                           ('Crystallization', 'pmt_threshold'),
                           ('Crystallization', 'use_camera'),
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.rabi_required_parameters)
        parameters = parameters.union(set(cls.trap_frequencies))
        parameters = parameters.union(set(excitation_729.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Excitation_729','rabi_excitation_duration'))
        parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_729)
        self.excite.initialize(cxn, context, ident)
        if self.parameters.Crystallization.auto_crystallization:
            self.crystallizer = self.make_experiment(crystallization)
            self.crystallizer.initialize(cxn, context, ident)
        self.scan = []
        self.amplitude = None
        self.duration = None
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.awg_rotation = cxn.keysight_33500b
        self.ramp_scan_save_context = cxn.context()
        self.grapher = cxn.grapher
    
    def setup_sequence_parameters(self):
        self.load_frequency()
        flop = self.parameters.RabiFlopping
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729
        self.parameters['Excitation_729.rabi_excitation_duration'] = self.parameters.RabiFlopping_Sit.sit_on_excitation

        rp = self.parameters.Rotation
        minim,maxim,steps = rp.rot_parameter_scan   
        minim = minim['ms']; maxim = maxim['ms']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'ms') for pt in self.scan]

    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        self.dv.cd(directory ,True, context = self.ramp_scan_save_context)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        ds = self.dv.new('ScanRampDownTime {}'.format(datasetNameAppend),[('Excitation', 'ms')], dependants , context = self.ramp_scan_save_context)
        self.dv.add_parameter('Window', ['other'], context = self.ramp_scan_save_context)
        #self.dv.add_parameter('plotLive', True, context = self.rabi_flop_save_context)
        if self.grapher is not None:
            self.grapher.plot_with_axis(ds, 'other', self.scan)
    
    def load_frequency(self):
        #reloads trap frequencies and gets the latest information from the drift tracker
        self.reload_some_parameters(self.trap_frequencies) 
        flop = self.parameters.RabiFlopping
        frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if flop.frequency_selection == 'auto':
            frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)
        frequency += flop.rabi_stark_shift
        self.parameters['Excitation_729.rabi_excitation_frequency'] = frequency
        
    def run(self, cxn, context):
        self.setup_sequence_parameters()
        self.setup_data_vault()
        t = []
        ex = []
        for i,scan_param in enumerate(self.scan):
            rp = self.parameters.Rotation
            start_hold = rp.start_hold
            start_phase = rp.start_phase
            frequency_ramp_time = rp.frequency_ramp_time
            middle_hold = rp.middle_hold
            ramp_down_time = rp.ramp_down_time
            end_hold = rp.end_hold
            voltage_pp = rp.voltage_pp
            drive_frequency = rp.drive_frequency
            if rp.rot_parameter_to_scan == 'frequency_ramp_time':
                frequency_ramp_time = scan_param
            elif rp.rot_parameter_to_scan == 'middle_hold':
                middle_hold = scan_param
            elif rp.rot_parameter_to_scan == 'ramp_down_time':
                ramp_down_time = scan_param
            self.awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation')

            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.get_excitation_crystallizing(cxn, context, scan_param)
            if excitation is None: break 
            submission = [scan_param['ms']]
            submission.extend(excitation)
            t.append(scan_param['ms'])
            ex.append(excitation)
            self.dv.add(submission, context = self.ramp_scan_save_context)
            self.update_progress(i)
        return np.array(t), np.array(ex)
    
    def get_excitation_crystallizing(self, cxn, context, scan_param):
        excitation = self.do_get_excitation(cxn, context, scan_param)
        if self.parameters.Crystallization.auto_crystallization:
            initally_melted, got_crystallized = self.crystallizer.run(cxn, context)
            #if initially melted, redo the point
            while initally_melted:
                if not got_crystallized:
                    #if crystallizer wasn't able to crystallize, then pause and wait for user interaction
                    self.cxn.scriptscanner.pause_script(self.ident, True)
                    should_stop = self.pause_or_stop()
                    if should_stop: return None
                excitation = self.do_get_excitation(cxn, context, scan_param)
                initally_melted, got_crystallized = self.crystallizer.run(cxn, context)
        return excitation
    
    def do_get_excitation(self, cxn, context, scan_param):
        self.load_frequency()
        rp = self.parameters.Rotation
        if rp.rot_parameter_to_scan == 'frequency_ramp_time':
            self.parameters['Rotation.frequency_ramp_time'] = scan_param
        elif rp.rot_parameter_to_scan == 'middle_hold':
            self.parameters['Rotation.middle_hold'] = scan_param
        elif rp.rot_parameter_to_scan == 'ramp_down_time':
            self.parameters['Rotation.ramp_down_time'] = scan_param
        self.excite.set_parameters(self.parameters)
        excitation, readouts = self.excite.run(cxn, context)
        return excitation
     
    def finalize(self, cxn, context):
        old_freq = self.pv.get_parameter('RotationCW','drive_frequency')['kHz']
        old_phase = self.pv.get_parameter('RotationCW','start_phase')['deg']
        old_amp =self.pv.get_parameter('RotationCW','voltage_pp')['V']
        self.awg_rotation.update_awg(old_freq*1e3,old_amp,old_phase)
        self.save_parameters(self.dv, cxn, self.cxnlab, self.ramp_scan_save_context)
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
    exprt = scan_rotation_parameter(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
