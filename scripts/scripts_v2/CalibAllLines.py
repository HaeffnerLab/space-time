import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from common.client_config import client_info as cl

class CalibLine1(pulse_sequence):

    scannable_params = {'Excitation729.frequency729' : [(-10, 10, 1, 'kHz'), 'car1',True]}

    def sequence(self):
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout

        p = self.parameters
        line1 = p.CalibrateLines.line_selection_1

        freq729 = self.calc_freq(line1)
        freq729 = freq729 + p.Excitation729.frequency729
        amp729 = p.CalibrateLines.amplitude729_line1
        channel729 = p.CalibrateLines.channel729
        dur729 = p.CalibrateLines.duration729

        self.addSequence(StatePreparation,{'StatePreparation.sideband_cooling_enable': False,
                                           'StatePreparation.rotation_enable': False,
                                           'EmptySequence.empty_sequence_duration': U(0, 'ms'),
                                           'EmptySequence.noise_enable': False,
                                           'DopplerCooling.doppler_cooling_duration': p.CalibrateLines.calibration_doppler_duration})
        self.addSequence(RabiExcitation,{'Excitation729.frequency729': freq729,
                                         'Excitation729.amplitude729': amp729,
                                         'Excitation729.duration729': dur729,
                                         'Excitation729.channel729': channel729,
                                         'Excitation729.rabi_change_DDS': True})
        self.addSequence(StateReadout, {'StateReadout.repeat_each_measurement': 100,
                                        'StateReadout.readout_mode': "pmt_excitation"})

    @classmethod
    def run_initial(cls,cxn, parameters_dict):
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
        line = parameters_dict.CalibrateLines.line_selection_1
        shift = parameters_dict.Carriers[carrier_translation[line]]

        pv = cxn.parametervault
        pv.set_parameter('Display','shift',shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, all_data, freq_data):
        if parameters_dict.CalibrationControl.save_calibrations:
          global carr_1_global

          try:
              all_data = all_data.sum(1)
          except ValueError:
              print "error with the data"
              return

          peak_fit = cls.gaussian_fit(freq_data, all_data)
          if not peak_fit:
              carr_1_global = None
              ident = int(cxn.scriptscanner.get_running()[0][0])
              print "Can't fit peak, stopping sequence {}".format(ident)                   
              cxn.scriptscanner.stop_sequence(ident)
              return

          print "peak_fit{}".format(peak_fit)
          peak_fit = U(peak_fit,'MHz')

          carr_1_global = peak_fit


class CalibLine2(pulse_sequence):

    scannable_params = {'Excitation729.frequency729':[(-10, 10, 1, 'kHz'),'car2',True]}

    def sequence(self):
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout

        p = self.parameters
        line2 = p.CalibrateLines.line_selection_2

        freq729 = self.calc_freq(line2)
        freq729 = freq729 + p.Excitation729.frequency729
        amp729 = p.CalibrateLines.amplitude729_line2
        channel729 = p.CalibrateLines.channel729
        dur729 = p.CalibrateLines.duration729

        self.addSequence(StatePreparation,{'StatePreparation.sideband_cooling_enable': False,
                                           'StatePreparation.rotation_enable': False,
                                           'EmptySequence.empty_sequence_duration': U(0, 'ms'),
                                           'EmptySequence.noise_enable': False,
                                           'DopplerCooling.doppler_cooling_duration': p.CalibrateLines.calibration_doppler_duration})
        self.addSequence(RabiExcitation,{'Excitation729.frequency729': freq729,
                                         'Excitation729.amplitude729': amp729,
                                         'Excitation729.duration729': dur729,
                                         'Excitation729.channel729': channel729,
                                         'Excitation729.rabi_change_DDS': True})
        self.addSequence(StateReadout, {'StateReadout.repeat_each_measurement': 100,
                                        'StateReadout.readout_mode': "pmt_excitation"})

    @classmethod
    def run_initial(cls,cxn, parameters_dict):
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
        line = parameters_dict.CalibrateLines.line_selection_2
        shift = parameters_dict.Carriers[carrier_translation[line]]

        pv = cxn.parametervault
        pv.set_parameter('Display','shift',shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, all_data, freq_data):
        
        if parameters_dict.CalibrationControl.save_calibrations:
            global carr_1_global 
            
            carr_1 = carr_1_global
            
            if not carr_1:
                return
            
            try:
                all_data = all_data.sum(1)
            except ValueError:
                print "ValueError"
                return
                
            peak_fit = cls.gaussian_fit(freq_data, all_data)
            
            if not peak_fit:
                print "peak fitting did not work"
                return
            
            peak_fit = U(peak_fit, "MHz") 
              
            carr_2 = peak_fit
            
            line_1 = parameters_dict.CalibrateLines.line_selection_1
            line_2 = parameters_dict.CalibrateLines.line_selection_2

            submission = [(line_1, carr_1), (line_2, carr_2)]

            #cxn.sd_tracker.set_measurements(submission) 
            import labrad
            global_sd_cxn = labrad.connect(cl.global_address, password = cl.global_password,tls_mode='off')
            print cl.client_name , "is sub lines to global SD" , 
            print submission 
            global_sd_cxn.sd_tracker_global.set_measurements(submission,cl.client_name) 
            global_sd_cxn.disconnect()


class CalibAllLines(pulse_sequence):
    is_composite = True

    fixed_params = {'Display.relative_frequencies': False}
                    
    sequence = [CalibLine1, CalibLine2] 

    show_params = ['CalibrateLines.line_selection_1',
                   'CalibrateLines.line_selection_2',
                   'CalibrateLines.amplitude729_line1',
                   'CalibrateLines.amplitude729_line2',
                   'CalibrateLines.channel729',
                   'CalibrateLines.duration729',
                   'CalibrateLines.calibration_doppler_duration'
                  ]