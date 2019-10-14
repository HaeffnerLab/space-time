from common.devel.bum.sequences.pulse_sequence import pulse_sequence
#from pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

#class RabiFloppingMulti(pulse_sequence):
#    is_multi = True
#    sequences = [RabiFlopping, Spectrum]

class RabiFlopping(pulse_sequence):
    scannable_params = {
        'DopplerCooling.doppler_cooling_frequency_397':  [(200., 210., .5, 'MHz'), 'current'],
        'DopplerCooling.doppler_cooling_amplitude_397':  [(-30., -15., .5, 'dBm'), 'current'],
        'DopplerCooling.doppler_cooling_frequency_866':  [(80., 100., .5, 'MHz'), 'current'],
        'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'current'],
        'SidebandCooling.sideband_cooling_amplitude_854': [(-40.,-10., .5, 'dBm'), 'scan_854']
        'RabiFlopping.duration':  [(0., 60., 2., 'us'), 'rabi']
        'RabiFlopping'
              }

    show_params= ['RabiFlopping.line_selection',
                  'RabiFlopping.rabi_amplitude_729',
                  'RabiFlopping.duration',
                  'RabiFlopping.sideband_selection',
                  'StatePreparation.channel_729',
                  'RabiFlopping.channel_729',
                  'RabiFlopping.rabi_stark_shift'
                  ]


    def sequence(self):
      from StatePreparation import StatePreparation
      from subsequences.RabiExcitation import RabiExcitation
      from subsequences.StateReadout import StateReadout
      from subsequences.TurnOffAll import TurnOffAll
        
        ## calculate the scan params
      rf = self.parameters.RabiFlopping 
      
      if rf.frequency_selection == "auto":
        freq_729=self.calc_freq_from_array(rf.line_selection, rf.sideband_selection)
        freq_729 = freq_729 + rf.rabi_stark_shift
        amp_729 = rf.rabi_amplitude_729
      elif rf.frequency_selection == "manual":
        freq_729 = rf.manual_frequency_729
        amp_729 = rf.manual_amplitude_729
      else:
        raise Exception ('Incorrect frequency selection type {0}'.format(rf.frequency_selection))
        
      # building the sequence
      self.end = U(10., 'us')
      self.addSequence(TurnOffAll)
      self.addSequence(StatePreparation)
      self.addSequence(RabiExcitation,{  'Excitation_729.rabi_excitation_frequency': freq_729,
                                         'Excitation_729.rabi_excitation_amplitude': amp729,
                                         'Excitation_729.rabi_excitation_duration':  rf.duration,
                                          'rabi_change_DDS': True})
      self.addSequence(StateReadout)
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        pass

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        pass
        
