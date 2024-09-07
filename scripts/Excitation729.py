from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class Excitation729(pulse_sequence):
    scannable_params = {
        'DopplerCooling.doppler_cooling_frequency_397':  [(170., 195., .5, 'MHz'), 'doppler_cooling__frequency'],
        'DopplerCooling.doppler_cooling_amplitude_397':  [(-30., -15., .5, 'dBm'), 'doppler_cooling__amplitude'],
        'DopplerCooling.doppler_cooling_frequency_866':  [(60., 85., .5, 'MHz'), 'doppler_cooling__frequency'],
        'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'doppler_cooling__amplitude'],
        'SidebandCooling.sideband_cooling_amplitude_854': [(-25.,-5., 1., 'dBm'), 'sideband_cooling__854_power'],
        'Excitation729.duration729':  [(0., 200., 2., 'us'), 'rabi'],
        'Excitation729.frequency729': [(-50., 50., 5., 'kHz'), 'spectrum', True],
        #'SidebandCooling.stark_shift': [(-20., 20., 2., 'kHz'), 'other'],
        #'EmptySequence.empty_sequence_readout_duration': [(0.,1000.,100.,'us'),'rabi'],
        'OpticalPumping.optical_pumping_amplitude_854':  [(-30., -10., .5, 'dBm'), 'optical_pumping__854_power'],
        'SidebandCoolingContinuous.sideband_cooling_continuous_duration':  [(0., 3., 0.5, 'ms'), 'sideband_cooling__duration'],
        'SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_duration':  [(0., 30., 1., 'ms'), 'sideband_cooling__duration'],
        'SidebandCooling.stark_shift': [(-20., 20., 1., 'kHz'), 'sideband_cooling__stark_shift']
              }

    show_params= [
                  'Excitation729.line_selection',
                  'Excitation729.amplitude729',
                  'Excitation729.duration729',
                  'Excitation729.sideband_selection',
                  'Excitation729.channel729',
                  'Excitation729.stark_shift_729',
                  'Rotation.drive_frequency',
                  'Rotation.end_hold',
                  'Rotation.frequency_ramp_time',
                  'Rotation.middle_hold',
                  'Rotation.ramp_down_time',
                  'Rotation.start_hold',
                  'Rotation.start_phase',
                  'Rotation.voltage_pp',
                  'EmptySequence.empty_sequence_duration',
                  'EmptySequence.noise_enable',
                  # 'EmptySequence.empty_sequence_readout_duration',
                  'SidebandCoolingContinuous.sideband_cooling_continuous_cycles',
                  'SidebandCoolingContinuous.sideband_cooling_continuous_duration',
                  'SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_cycles',
                  'SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_duration',
                  'SidebandCoolingContTwoTone.channel_729_secondary',
                  'SidebandCoolingContTwoTone.stage2_line',
                  'SidebandCoolingContTwoTone.stage3_line',
                  'SidebandCoolingContTwoTone.stage4_line',
                  'SidebandCoolingContTwoTone.stage5_line',
                  'RFModulation.enable',
                  'RFModulation.turn_on_before',
                  ]


    def sequence(self):

        from subsequences.StatePreparation import StatePreparation
        from subsequences.EmptySequence import EmptySequence
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.RFModulation import RFModulation
        e = self.parameters.Excitation729
        #es = self.parameters.EmptySequence

          
        ## calculate the scan params
        if e.frequency_selection == "auto":
            freq_729_pos = self.calc_freq_from_array(e.line_selection, [sb*e.invert_sb for sb in e.sideband_selection])
            freq_729 = freq_729_pos + e.stark_shift_729 + e.frequency729
            print "FREQUENCY 729 = {}".format(freq_729)
        elif e.frequency_selection == "manual":
            freq_729 = e.frequency729
        else:
            raise Exception ('Incorrect frequency selection type {0}'.format(e.frequency_selection))

        ## build the sequence
        self.addSequence(StatePreparation)
        self.addSequence(EmptySequence)
        self.addSequence(RabiExcitation,{'Excitation729.frequency729': freq_729,
                                         'Excitation729.rabi_change_DDS': True})
        #self.addSequence(EmptySequence,{'EmptySequence.empty_sequence_duration':es.empty_sequence_readout_duration})
        time_start_readout = self.end # This is for RF modulation
        self.addSequence(StateReadout)

        # Add RF modulation TTL pulse if applicable
        if self.parameters.RFModulation.enable:
            RFModulation(self, time_start_readout)
                
        
        
    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        # Add rotation if necessary
        if parameters_dict.StatePreparation.rotation_enable:
            from subsequences.StatePreparation import StatePreparation
            state_prep_time = StatePreparation(parameters_dict).end
            cxn.keysight_33500b.rotation_run_initial(state_prep_time)
        
        e = parameters_dict.Excitation729

        ###### add shift for spectra purposes
        carrier_translation = {'S+1/2D-3/2':'c0',
                              'S-1/2D-5/2':'c1',
                              'S+1/2D-1/2':'c2',
                              'S-1/2D-3/2':'c3',
                              'S+1/2D+1/2':'c4',
                              'S-1/2D-1/2':'c5',
                              'S+1/2D+3/2':'c6',
                              'S-1/2D+1/2':'c7',
                              'S+1/2D+5/2':'c8',
                              'S-1/2D+3/2':'c9',
                                 }

        trapfreq = parameters_dict.TrapFrequencies
        sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency, trapfreq.rotation_frequency]
        shift = U(0.,'MHz')
        if parameters_dict.Display.relative_frequencies:
            # shift by sideband only (spectrum "0" will be carrier frequency)
            for order, sideband_frequency in zip([sb*e.invert_sb for sb in e.sideband_selection], sideband_frequencies):
                shift += order * sideband_frequency
        else:
            #shift by sideband + carrier (spectrum "0" will be AO center frequency)
            shift += parameters_dict.Carriers[carrier_translation[e.line_selection]]
            for order, sideband_frequency in zip([sb*e.invert_sb for sb in e.sideband_selection], sideband_frequencies):
                shift += order * sideband_frequency

        pv = cxn.parametervault
        pv.set_parameter('Display','shift', shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        if parameters_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()