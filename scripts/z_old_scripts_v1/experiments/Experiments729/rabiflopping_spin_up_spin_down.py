from common.abstractdevices.script_scanner.scan_methods import experiment
from excitations import excitation_729
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
from space_time.scripts.experiments.Crystallization.crystallization import crystallization
import time
import labrad
from labrad.units import WithUnit
import numpy as np

class rabiflopping_spin_up_spin_down(experiment):
    
    name = 'RabiFlopping_spin_up_spin_down'
    rabiflopping_required_parameters = [
                           # ('Spectrum','custom'),
                           # ('Spectrum','normal'),
                           # ('Spectrum','fine'),
                           # ('Spectrum','ultimate'),
                           # ('Spectrum','car1_sensitivity'),
                           # ('Spectrum','car2_sensitivity'),
                           
                           # ('Spectrum','line_selection'),
                           # ('Spectrum','manual_amplitude_729'),
                           # ('Spectrum','manual_excitation_time'),
                           # ('Spectrum','manual_scan'),
                           # ('Spectrum','scan_selection'),
                           # ('Spectrum','sensitivity_selection'),
                           # ('Spectrum','sideband_selection'),

                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','manual_amplitude_729'),
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_scan'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','rabi_stark_shift'),

                           ('Heating','background_heating_time'),

                           ('TrapFrequencies','axial_frequency'),
                           ('TrapFrequencies','radial_frequency_1'),
                           ('TrapFrequencies','radial_frequency_2'),
                           ('TrapFrequencies','rf_drive_frequency'),
                           
                           ('Rotation','drive_frequency'),
                           ('Rotation','voltage_pp'),
                           #('Rotation','ramp_down_time'),
                           ('Rotation','start_hold'),
                           ('Rotation','frequency_ramp_time'),
                           ('Rotation','end_hold'),
                           ('Rotation','start_phase'),
                           ('Rotation','middle_hold'),
                           
                           ('Crystallization', 'auto_crystallization'),
                           ('Crystallization', 'camera_record_exposure'),
                           ('Crystallization', 'camera_threshold'),
                           ('Crystallization', 'max_attempts'),
                           ('Crystallization', 'max_duration'),
                           ('Crystallization', 'min_duration'),
                           ('Crystallization', 'pmt_record_duration'),
                           ('Crystallization', 'pmt_threshold'),
                           ('Crystallization', 'use_camera'),

                           ('DopplerCooling','doppler_cooling_duration'),
                           ('SidebandCooling','sideband_cooling_optical_pumping_duration'),
                           ('SidebandCooling','sideband_cooling_cycles'),
                           ('SidebandCoolingContinuous','sideband_cooling_continuous_duration'),
                           ('StateReadout','pmt_readout_duration'),
                           ('StatePreparation','sideband_cooling_enable'),

                           ('Display', 'relative_frequencies'),

                            ]
    
    rabiflopping_optional_parmeters = [
                          ('RabiFlopping', 'window_name')
                          ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.rabiflopping_required_parameters)
        parameters = parameters.union(set(excitation_729.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Excitation_729','rabi_excitation_duration'))
        parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        return parameters
    
    def initialize(self, cxn, context, ident, use_camera_override=None):
        self.ident = ident
        self.excite = self.make_experiment(excitation_729)
        self.excite.initialize(cxn, context, ident, use_camera_override)
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
        self.pv = cxn.parametervault
        self.rabi_save_context = cxn.context()
        try:
            self.grapher = cxn.grapher
        except: self.grapher = None
        self.cxn = cxn
        
    def setup_sequence_parameters(self):
        r = self.parameters.RabiFlopping
        # if r.frequency_selection == 'manual':
        #     frequency = r.manual_frequency_729
        #     self.carrier_frequency = WithUnit(0.0, 'MHz')
        # elif r.frequency_selection == 'auto':
        #     center_frequency = cm.frequency_from_line_selection(r.scan_selection, None , r.line_selection, self.drift_tracker)
        #     self.carrier_frequency = center_frequency
        #     frequency = cm.add_sidebands(center_frequency, r.sideband_selection, self.parameters.TrapFrequencies)
        # else:
        #     raise Exception("Incorrect Spectrum Scan Type")

        self.load_frequency()
        amplitude = r.rabi_amplitude_729
        minim,maxim,steps = r.manual_scan

        #making the scan
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = amplitude
        minim = minim['us']; maxim = maxim['us']
        self.scan = np.linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'us') for pt in self.scan]
        
        #set up the timing of the rotation awf
        rp = self.parameters.Rotation
        frequency_ramp_time = rp.frequency_ramp_time

        if self.parameters.StatePreparation.sideband_cooling_enable:
            sideband_cooling_time  = 2*(self.parameters.SidebandCooling.sideband_cooling_optical_pumping_duration + self.parameters.SidebandCoolingContinuous.sideband_cooling_continuous_duration)*self.parameters.SidebandCooling.sideband_cooling_cycles + WithUnit(1.0,'ms')
        else:
            sideband_cooling_time = WithUnit(0,'ms')

        start_hold =  rp.start_hold
        #start_hold = rp.start_hold
        #ramp_down_time = rp.ramp_down_time
        start_phase = rp.start_phase
        middle_hold = rp.middle_hold
        end_hold = self.parameters.StateReadout.pmt_readout_duration + WithUnit(1,'ms')
        #end_hold = rp.end_hold
        voltage_pp = rp.voltage_pp
        drive_frequency = rp.drive_frequency
        self.awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],0.0,end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'spin_up_spin_down')
        self.parameters['Heating.background_heating_time'] = 2*frequency_ramp_time + middle_hold + WithUnit(1.0, 'ms')
        #self.awg_rotation.rotation(frequency['kHz'],voltage_pp['V'])
        #self.awg_modulation.program_modulation(ramp_up_time['ms'],start_hold['ms'],ramp_down_time['ms'],end_hold['ms'])

    def load_frequency(self):
        #reloads trap frequencies and gets the latest information from the drift tracker
        flop = self.parameters.RabiFlopping
        frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if flop.frequency_selection == 'auto':
            frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)
        frequency += flop.rabi_stark_shift
        self.parameters['Excitation_729.rabi_excitation_frequency'] = frequency

    def get_window_name(self):
        return ['rabi']
                
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        self.dv.cd(directory ,True, context = self.rabi_save_context)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        ds = self.dv.new('RabiFlopping {}'.format(datasetNameAppend),[('Excitation', 'us')], dependants , context = self.rabi_save_context)
        window_name = self.parameters.get('Rabi.window_name', ['rabi'])[0]
        #window_name = self.get_window_name()
        self.dv.add_parameter('Window', [window_name], context = self.rabi_save_context)
        #self.dv.add_parameter('plotLive', False, context = self.spectrum_save_context)
        self.save_parameters(self.dv, self.cxn, self.cxnlab, self.rabi_save_context)
        sc = []
        sc = self.scan
        if self.grapher is not None:
            self.grapher.plot_with_axis(ds, window_name, sc, False)
        
    def run(self, cxn, context):
        import time
        #t0 = time.time()
        
        self.setup_sequence_parameters()
        self.setup_data_vault()
        

        fr = []
        exci = []
        
        for i,time in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.get_excitation_crystallizing(cxn, context, time)
            if excitation is None: break
            submission = [time['us']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.rabi_save_context)
            self.update_progress(i)
            fr.append(submission[0])
            exci.append(excitation)
            
        #t1 = time.time()
        
        #print t1 - t0    
        return fr, exci
    
    def get_excitation_crystallizing(self, cxn, context, time):
        excitation = self.do_get_excitation(cxn, context, time)
        if self.parameters.Crystallization.auto_crystallization:
            initally_melted, got_crystallized = self.crystallizer.run(cxn, context)
            #if initially melted, redo the point
            while initally_melted:
                if not got_crystallized:
                    #if crystallizer wasn't able to crystallize, then pause and wait for user interaction
                    self.cxn.scriptscanner.pause_script(self.ident, True)
                    should_stop = self.pause_or_stop()
                    if should_stop: return None
                excitation = self.do_get_excitation(cxn, context, time)
                initally_melted, got_crystallized = self.crystallizer.run(cxn, context)
        return excitation
    
    def do_get_excitation(self, cxn, context, time):
        self.parameters['Excitation_729.rabi_excitation_duration'] = time
        self.excite.set_parameters(self.parameters)
        excitation, readouts = self.excite.run(cxn, context)
        return excitation
    
    # def fit_lorentzian(self, timeout):
    #     #for lorentzian format is FWHM, center, height, offset
    #     scan = np.array([pt['MHz'] for pt in self.scan])
        
    #     fwhm_guess = (scan.max() - scan.min()) / 10.0
    #     center_guess = np.average(scan)
    #     self.dv.add_parameter('Fit', ['0', 'Lorentzian', '[{0}, {1}, {2}, {3}]'
    #                                   .format(fwhm_guess, center_guess, 0.5, 0.0)], context = self.spectrum_save_context)
    #     submitted = self.cxn.data_vault.wait_for_parameter('Accept-0', timeout, context = self.spectrum_save_context)
    #     if submitted:
    #         return self.cxn.data_vault.get_parameter('Solutions-0-Lorentzian', context = self.spectrum_save_context)
    #     else:
    #         return None
        
    def finalize(self, cxn, context):
        old_freq = self.pv.get_parameter('RotationCW','drive_frequency')['kHz']
        old_phase = self.pv.get_parameter('RotationCW','start_phase')['deg']
        old_amp =self.pv.get_parameter('RotationCW','voltage_pp')['V']
        self.awg_rotation.update_awg(old_freq*1e3,old_amp,old_phase)
        self.excite.finalize(cxn, context)
        #self.save_parameters(self.dv, cxn, self.cxnlab, self.spectrum_save_context)

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
    exprt = rabiflopping_spin_up_spin_down(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
