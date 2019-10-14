from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict


class Spectrum(pulse_sequence):
    
    scannable_params = {
        #'Spectrum.carrier_detuning':  [(-50, 50, 100, 'kHz'), 'window']
        'Spectrum.carrier_detuning' : [(-150, 150, 10, 'kHz'),'spectrum'],
        'Spectrum.sideband_detuning' :[(-25, 25, 2, 'kHz'),'spectrum']
              }

    show_params= ['Spectrum.manual_amplitude_729',
                  'Spectrum.manual_excitation_time',
                  'Spectrum.line_selection',
                  'Spectrum.sideband_selection',
                  'Display.relative_frequencies',
                  'OpticalPumping.optical_pumping_enable', 
                  'SidebandCooling.sideband_cooling_enable',
		  'StateReadout.readout_duration'	 
                  ]
   
    fixed_params = {'OpticalPumpingAux.aux_optical_pumping_enable': False,
                    'StateReadout.readout_mode': 'pmt',
                    }
    
    def sequence(self):
        
        from StatePreparation import StatePreparation

        #
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.TurnOffAll import TurnOffAll
           
        ## calculate the scan params
        spc = self.parameters.Spectrum   
        
        # if spc.selection_sideband == "off":         
        #     freq_729=self.calc_freq(spc.line_selection)
        # else:
        #     freq_729=self.calc_freq(spc.line_selection, spc.selection_sideband ,int(spc.order))

        freq_729=self.calc_freq_from_array(spc.line_selection, spc.sideband_selection)
        
        freq_729=freq_729 + spc.carrier_detuning + spc.sideband_detuning
        
        amp=spc.manual_amplitude_729
        duration=spc.manual_excitation_time
        print "Spectrum scan 555"
        print "spc.line_selection : " ,spc.line_selection
        # print "spc.selection_sideband : " ,spc.selection_sideband
        # print "spc.order : " , int(spc.order)
        print "spc.sideband_selection : " ,spc.sideband_selection
        
        print "729 freq: {}".format(freq_729.inUnitsOf('MHz'))
        # print "729 detuning: {}".format(freq_729-self.calc_freq(spc.line_selection))
        print "729 detuning: {}".format(freq_729-self.calc_freq_from_array(spc.line_selection, spc.sideband_selection))
        print "729 amp is {}".format(amp)
        print "729 duration is {}".format(duration)
        
        

                
        # building the sequence
        # needs a 10 micro sec for some reason
        self.end = U(10., 'us')
        self.addSequence(TurnOffAll)           
        self.addSequence(StatePreparation)      
        self.addSequence(RabiExcitation,{'Excitation_729.rabi_excitation_frequency': freq_729,
                                         'Excitation_729.rabi_excitation_amplitude': amp,
                                         'Excitation_729.rabi_excitation_duration':  duration })
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
        
if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    sc = cxn.scriptscanner
    #scan = [('ReferenceImage',   ('temp', 0, 1, 1, 'us'))]
    scan =[('Spectrum',   ('Spectrum.carrier_detuning', -150, 150, 10, 'kHz'))] 
    ident = sc.new_sequence('Spectrum', scan)
    sc.sequence_completed(ident)
    cxn.disconnect()
