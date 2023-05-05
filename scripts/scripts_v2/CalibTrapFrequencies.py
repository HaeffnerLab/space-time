import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from common.client_config import client_info as cl

class CalibSideband1(pulse_sequence):

    scannable_params = {'CalibTrapFreqs.sideband1_detuning' : [(-150, 150, 15, 'kHz'), 'sideband1', True]}

    def sequence(self):

        from Excitation729 import Excitation729

        ctf = self.parameters.CalibTrapFreqs
        
        # Construct sideband_selection list from selection of sideband and its order
        sideband_selection = [0, 0, 0, 0, 0]
        sidebands = ['radial_frequency_1', 'radial_frequency_2', 'axial_frequency', 'rf_drive_frequency', 'rotation_frequency']
        sideband_index = sidebands.index(ctf.sideband1_sideband_selection)
        sideband_selection[sideband_index] = ctf.sideband1_order

        self.addSequence(Excitation729,{'Excitation729.amplitude729': ctf.sideband1_amplitude729,
                                        'Excitation729.channel729': ctf.sideband1_channel729,
                                        'Excitation729.duration729': ctf.sideband1_duration729,
                                        'Excitation729.frequency729': ctf.sideband1_detuning,
                                        'Excitation729.line_selection': ctf.sideband1_line_selection_729,
                                        'Excitation729.sideband_selection': sideband_selection,
                                        'Excitation729.stark_shift_729': U(0, 'kHz'),
                                        'StatePreparation.sideband_cooling_enable': False,
                                        'StatePreparation.rotation_enable': False,
                                        'EmptySequence.empty_sequence_duration': U(0, 'ms'),
                                        'EmptySequence.noise_enable': False,
                                        'StateReadout.repeat_each_measurement': 100,
                                        'StateReadout.readout_mode': "pmt_excitation"})


    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        ctf = parameters_dict.CalibTrapFreqs

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
                              'S-1/2D+3/2':'c9',}

        trapfreq = parameters_dict.TrapFrequencies
        sidebands = ['radial_frequency_1', 'radial_frequency_2', 'axial_frequency', 'rf_drive_frequency', 'rotation_frequency']
        sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency, trapfreq.rotation_frequency]
        shift = U(0.,'MHz')
        if parameters_dict.Display.relative_frequencies:
            # shift by sideband only (spectrum "0" will be carrier frequency)
            sideband_index = sidebands.index(ctf.sideband1_sideband_selection)
            order = ctf.sideband1_order
            shift += order*sideband_frequencies[sideband_index]
            print "shift"
            print shift
        else:
            #shift by sideband + carrier (spectrum "0" will be AO center frequency)
            shift += parameters_dict.Carriers[carrier_translation[ctf.sideband1_line_selection_729]]

        pv = cxn.parametervault
        pv.set_parameter('Display', 'shift', shift)


    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data, x):
        pass


    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, x):
        if parameters_dict.CalibrationControl.save_calibrations:
            ctf = parameters_dict.CalibTrapFreqs

            # Fit peak and compute sideband frequency
            data_y = data.sum(1)
            peak_fit = cls.gaussian_fit(x, data_y)
            peak_fit = U(np.round(peak_fit, decimals=4), 'MHz')
            sideband_frequency = peak_fit / ctf.sideband1_order

            # Submit to script scanner
            ss = cxn.scriptscanner
            prev_value = ss.get_parameter('TrapFrequencies', ctf.sideband1_sideband_selection)
            ss.set_parameter('PreviousCalibrationValues', ctf.sideband1_sideband_selection, prev_value)
            ss.set_parameter('TrapFrequencies', ctf.sideband1_sideband_selection, sideband_frequency)


class CalibSideband2(pulse_sequence):

    scannable_params = {'CalibTrapFreqs.sideband2_detuning' : [(-150, 150, 15, 'kHz'), 'sideband2', True]}

    def sequence(self):

        from Excitation729 import Excitation729

        ctf = self.parameters.CalibTrapFreqs
        
        # Construct sideband_selection list from selection of sideband and its order
        sideband_selection = [0, 0, 0, 0, 0]
        sidebands = ['radial_frequency_1', 'radial_frequency_2', 'axial_frequency', 'rf_drive_frequency', 'rotation_frequency']
        sideband_index = sidebands.index(ctf.sideband2_sideband_selection)
        sideband_selection[sideband_index] = ctf.sideband2_order

        self.addSequence(Excitation729,{'Excitation729.amplitude729': ctf.sideband2_amplitude729,
                                        'Excitation729.channel729': ctf.sideband2_channel729,
                                        'Excitation729.duration729': ctf.sideband2_duration729,
                                        'Excitation729.frequency729': ctf.sideband2_detuning,
                                        'Excitation729.line_selection': ctf.sideband2_line_selection_729,
                                        'Excitation729.sideband_selection': sideband_selection,
                                        'Excitation729.stark_shift_729': U(0, 'kHz'),
                                        'StatePreparation.sideband_cooling_enable': False,
                                        'StatePreparation.rotation_enable': False,
                                        'EmptySequence.empty_sequence_duration': U(0, 'ms'),
                                        'EmptySequence.noise_enable': False,
                                        'StateReadout.repeat_each_measurement': 100,
                                        'StateReadout.readout_mode': "pmt_excitation"})


    @classmethod
    def run_initial(cls, cxn, parameters_dict):
        ctf = parameters_dict.CalibTrapFreqs

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
                              'S-1/2D+3/2':'c9',}

        trapfreq = parameters_dict.TrapFrequencies
        sidebands = ['radial_frequency_1', 'radial_frequency_2', 'axial_frequency', 'rf_drive_frequency', 'rotation_frequency']
        sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency, trapfreq.rotation_frequency]
        shift = U(0.,'MHz')
        if parameters_dict.Display.relative_frequencies:
            # shift by sideband only (spectrum "0" will be carrier frequency)
            sideband_index = sidebands.index(ctf.sideband2_sideband_selection)
            order = ctf.sideband2_order
            shift += order*sideband_frequencies[sideband_index]
            print "shift"
            print shift
        else:
            #shift by sideband + carrier (spectrum "0" will be AO center frequency)
            shift += parameters_dict.Carriers[carrier_translation[ctf.sideband2_line_selection_729]]

        pv = cxn.parametervault
        pv.set_parameter('Display', 'shift', shift)


    @classmethod
    def run_in_loop(cls, cxn, parameters_dict, data, x):
        pass


    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, x):
        if parameters_dict.CalibrationControl.save_calibrations:
            ctf = parameters_dict.CalibTrapFreqs

            # Fit peak and compute sideband frequency
            peak_fit = cls.gaussian_fit(x, data[:,0])
            peak_fit = U(np.round(peak_fit, decimals=4), 'MHz')
            sideband_frequency = peak_fit / ctf.sideband2_order

            # Submit to script scanner
            ss = cxn.scriptscanner
            prev_value = ss.get_parameter('TrapFrequencies', ctf.sideband2_sideband_selection)
            ss.set_parameter('PreviousCalibrationValues', ctf.sideband2_sideband_selection, prev_value)
            ss.set_parameter('TrapFrequencies', ctf.sideband2_sideband_selection, sideband_frequency)


class CalibTrapFrequencies(pulse_sequence):
    is_composite = True
            
    sequence = [CalibSideband1, CalibSideband2] 

    show_params= ['CalibTrapFreqs.sideband1_line_selection_729',
                  'CalibTrapFreqs.sideband1_amplitude729',
                  'CalibTrapFreqs.sideband1_duration729',
                  'CalibTrapFreqs.sideband1_channel729',
                  'CalibTrapFreqs.sideband1_sideband_selection',
                  'CalibTrapFreqs.sideband1_order',
                  'CalibTrapFreqs.sideband2_line_selection_729',
                  'CalibTrapFreqs.sideband2_amplitude729',
                  'CalibTrapFreqs.sideband2_duration729',
                  'CalibTrapFreqs.sideband2_channel729',
                  'CalibTrapFreqs.sideband2_sideband_selection',
                  'CalibTrapFreqs.sideband2_order',
                  ]