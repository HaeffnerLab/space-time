from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np


class Test(pulse_sequence):
    scannable_params = {
    'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'current'],
    'StateReadout.state_readout_duration': [(0.,10000.,1000.,'us'),'current']
    }

    show_params = ['StateReadout.repeat_each_measurement',
                    'StateReadout.state_readout_amplitude_397']

    def sequence(self):
        from subsequences.StateReadout import StateReadout
        #from subsequences.TurnOffAll import TurnOffAll
        #from subsequences.StateReadout import StateReadout
        st = self.parameters.StateReadout
        duration_397=st.state_readout_duration
        #readout_mode = 'pmt'  #st.readout_mode
        #self.addDDS('397DP',self.start+U(10.,'us'), duration_397, st.state_readout_frequency_397, st.state_readout_amplitude_397)
        self.end = U(10., 'us')
        self.addSequence(StateReadout)

    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        print "Initializing"
        pass

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        print "Running in loop Rabi_floping"
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        print "switching the 866 back to ON"
        pass
         
        # cxn.pulser.switch_manual('866DP', True)
        #cxn.pulser.switch_manual('866DP', False)

        #np.save('temp_PMT', data)
        #print "saved ion data"