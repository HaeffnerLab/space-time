from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class Excitation729_Calibration1(pulse_sequence):
    scannable_params = {
        'DopplerCooling.doppler_cooling_frequency_397':  [(180., 210., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_397':  [(-30., -15., .5, 'dBm'), 'other'],
        'DopplerCooling.doppler_cooling_frequency_866':  [(50., 80., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'other'],
              }

    show_params= [
                  'Excitation_729_Cal1.line_selection',
                  'Excitation_729_Cal1.amplitude729',
                  'Excitation_729_Cal1.duration729',
                  'Excitation_729_Cal1.sideband_selection',
                  'Excitation_729_Cal1.channel729',
                  'Excitation_729_Cal1.stark_shift_729',
                  'Excitation_729_Cal1.sideband_cooling_enable',
                  'Excitation_729_Cal1.empty_sequence_duration',
                  ]


    def sequence(self):

      from Excitation729 import Excitation729

      ec1 = self.parameters.Excitation_729_Cal1

      self.addSequence(Excitation729,{  'Excitation_729.amplitude729': ec1.amplitude729,
                                        'Excitation_729.channel729': ec1.channel729,
                                        'Excitation_729.duration729': ec1.duration729,
                                        'Excitation_729.line_selection': ec1.line_selection,
                                        'Excitation_729.sideband_selection': ec1.sideband_selection,
                                        'Excitation_729.stark_shift_729': ec1.stark_shift_729,
                                        'EmptySequence.empty_sequence_duration': ec1.empty_sequence_duration,
                                        'StatePreparation.sideband_cooling_enable': ec1.sideband_cooling_enable})
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      ec1 = parameters_dict.Excitation_729_Cal1
      
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
      sideband_frequencies = [trapfreq.radial_frequency_1, trapfreq.radial_frequency_2, trapfreq.axial_frequency, trapfreq.rf_drive_frequency]
      shift = U(0.,'MHz')
      if parameters_dict.Display.relative_frequencies:
        # shift by sideband only (spectrum "0" will be carrier frequency)
        for order,sideband_frequency in zip([sb*ec1.invert_sb for sb in ec1.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency
      else:
        #shift by sideband + carrier (spectrum "0" will be AO center frequency)
        shift += parameters_dict.Carriers[carrier_translation[ec1.line_selection]]
        for order,sideband_frequency in zip([sb*ec1.invert_sb for sb in ec1.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency

      pv = cxn.parametervault
      pv.set_parameter('Display','shift',shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        pass        
