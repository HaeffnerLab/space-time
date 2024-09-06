from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class Excitation729_Calibration3(pulse_sequence):
    scannable_params = {
        'DopplerCooling.doppler_cooling_frequency_397':  [(180., 210., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_397':  [(-30., -15., .5, 'dBm'), 'other'],
        'DopplerCooling.doppler_cooling_frequency_866':  [(60., 85., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'other'],
        'Excitation729Cal3.duration729':  [(0., 200., 2., 'us'), 'rabi'],
        'Excitation729Cal3.frequency729': [(-50., 50., 5., 'kHz'), 'spectrum',True],
        'SidebandCooling.sideband_cooling_amplitude_854': [(-30.,-10., 1., 'dBm'), 'scan_854'],
              }

    show_params= [
                  'Excitation729Cal3.line_selection',
                  'Excitation729Cal3.amplitude729',
                  'Excitation729Cal3.duration729',
                  'Excitation729Cal3.sideband_selection',
                  'Excitation729Cal3.channel729',
                  'Excitation729Cal3.stark_shift_729',
                  'Excitation729Cal3.sideband_cooling_enable',
                  'Excitation729Cal3.rotation_enable',
                  'Excitation729Cal3.empty_sequence_duration',
                  'Excitation729Cal3.readout_mode',
                  'Excitation729Cal3.rf_modulation_enable',
                  'Rotation.drive_frequency',
                  'Rotation.end_hold',
                  'Rotation.frequency_ramp_time',
                  'Rotation.middle_hold',
                  'Rotation.ramp_down_time',
                  'Rotation.start_hold',
                  'Rotation.start_phase',
                  'Rotation.voltage_pp',
                  ]


    def sequence(self):

      from Excitation729 import Excitation729

      e729c = self.parameters.Excitation729Cal3

      self.addSequence(Excitation729,{'Excitation729.amplitude729': e729c.amplitude729,
                                      'Excitation729.channel729': e729c.channel729,
                                      'Excitation729.duration729': e729c.duration729,
                                      'Excitation729.frequency729': e729c.frequency729,
                                      'Excitation729.line_selection': e729c.line_selection,
                                      'Excitation729.sideband_selection': e729c.sideband_selection,
                                      'Excitation729.stark_shift_729': e729c.stark_shift_729,
                                      'RFModulation.enable': e729c.rf_modulation_enable,
                                      'StatePreparation.sideband_cooling_enable': e729c.sideband_cooling_enable,
                                      'StatePreparation.rotation_enable': e729c.rotation_enable,
                                      'EmptySequence.empty_sequence_duration': e729c.empty_sequence_duration,
                                      'StateReadout.readout_mode': e729c.readout_mode})
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      e729c = parameters_dict.Excitation729Cal3
      
      # Add rotation if necessary
      if e729c.rotation_enable:
          # Modify parameters_dict for this calibration scan's state prep parameters
          parameters_dict_calibration = parameters_dict
          parameters_dict_calibration.StatePreparation.sideband_cooling_enable = e729c.sideband_cooling_enable
          parameters_dict_calibration.StatePreparation.rotation_enable = e729c.rotation_enable

          from subsequences.StatePreparation import StatePreparation
          state_prep_time = StatePreparation(parameters_dict_calibration).end
          cxn.keysight_33500b.rotation_run_initial(state_prep_time)
        

      
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
        for order,sideband_frequency in zip([sb*e729c.invert_sb for sb in e729c.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency
      else:
        #shift by sideband + carrier (spectrum "0" will be AO center frequency)
        shift += parameters_dict.Carriers[carrier_translation[e729c.line_selection]]
        for order,sideband_frequency in zip([sb*e729c.invert_sb for sb in e729c.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency

      pv = cxn.parametervault
      pv.set_parameter('Display','shift',shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        if parameters_dict.Excitation729Cal3.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()