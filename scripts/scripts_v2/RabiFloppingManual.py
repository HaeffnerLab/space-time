from common.devel.bum.sequences.pulse_sequence import pulse_sequence
#from pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict

class RabiFloppingManual(pulse_sequence):
                            #(self, scan_param, minim, maxim, steps, unit)
    scannable_params = {
        'Excitation_729.rabi_excitation_duration':  [(0., 50., 2., 'us'), 'rabi'],
        'Excitation_729.rabi_excitation_frequency':  [(-30., 30., 10., 'MHz'), 'spectrum']
      
              }

    show_params= ['Excitation_729.channel_729',
                  'Excitation_729.rabi_excitation_amplitude',
                  'StateReadout.threshold_list'
                  ]
    
    def sequence(self):
        # from StatePreparation import StatePreparation
        from subsequences.DopplerCooling import DopplerCooling
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.OpticalPumping import OpticalPumping
        from subsequences.StateReadout import StateReadout
        from subsequences.TurnOffAll import TurnOffAll
        
        
        
        # building the sequence
        self.end = U(10., 'us')
        self.addSequence(TurnOffAll)
        self.addSequence(DopplerCooling)
        print " adding Optical pumpmin"
        self.addSequence(OpticalPumping)
        self.addSequence(RabiExcitation)     
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


        