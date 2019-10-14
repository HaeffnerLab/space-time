import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from common.client_config import client_info as cl

class CalibAllLines_global(pulse_sequence):

    fixed_params = {
                    'Display.relative_frequencies': False,
                    # 'StatePreparation.sideband_cooling_enable': False,
                    'StateReadout.readout_mode': "pmt"}
    show_params= ['CalibrationScans.calibration_channel_729',
                  'Spectrum.car1_amp',
                  'Spectrum.manual_excitation_time',
                  'DriftTracker.line_selection_1',
                  # 'Display.relative_frequencies',
                  # 'CalibrationScans.readout_mode'
                  ]

    scannable_params = {'Spectrum.carrier_detuning' : [(-5, 5, .75, 'kHz'), 'car1']}
    # fixed parmas doesn't work -> you can declare fixed params for all the seq at the main class

    def sequence(self):

        from StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.TurnOffAll import TurnOffAll

        self.end = U(10., 'us')
        p = self.parameters
        line = p.DriftTracker.line_selection_1
        
        freq_729 = self.calc_freq_from_array(line)
        freq_729 = freq_729 + p.Spectrum.carrier_detuning
        
        amp = p.Spectrum.car1_amp
        duration = p.Spectrum.manual_excitation_time
        channel_729= p.CalibrationScans.calibration_channel_729
        
        self.addSequence(TurnOffAll)
        self.addSequence(StatePreparation)
        self.addSequence(RabiExcitation,{'Excitation_729.channel_729': channel_729,
                                         'Excitation_729.rabi_excitation_frequency': freq_729,
                                         'Excitation_729.rabi_excitation_amplitude': amp,
                                         'Excitation_729.rabi_excitation_duration':  duration })
        
        self.addSequence(StateReadout)
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        pass

        
    @classmethod
    def run_finally(cls, cxn, parameters_dict, all_data, freq_data):
        

        
#        print " running finally the CalibLine2"

        
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
        
          
        # for the multiple case we summ the probabilities, this also
        # reduces the dimension to 1 for single ion case 
        all_data = np.array(all_data)
        try:
            all_data = all_data.sum(1)
        except ValueError:
            return
            
        peak_fit = cls.gaussian_fit(freq_data, all_data)
        
        if not peak_fit:
            return
        
        peak_fit = U(peak_fit, "MHz") 
          
        carr = peak_fit
        
        line = parameters_dict.DriftTracker.line_selection_1
        
        if parameters_dict.Display.relative_frequencies:
            #print "using relative units"
            carr = carr+parameters_dict.Carriers[carrier_translation[line]]
        
        
        submission = [(line, carr)]

        print "submission", submission

        # if parameters_dict.DriftTracker.global_sd_enable:
        import labrad
        global_sd_cxn = labrad.connect(cl.global_address, password = cl.global_password,tls_mode='off')
        print cl.client_name , "is sub one line to global SD" , 
        print submission 
        global_sd_cxn.sd_tracker_global.set_measurements_with_one_line(submission,cl.client_name) 
        global_sd_cxn.disconnect()