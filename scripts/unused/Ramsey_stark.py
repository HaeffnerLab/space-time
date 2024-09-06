from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np
import math as m
import time

class Ramsey_stark(pulse_sequence):
    
    #name = 'Ramsey'

    scannable_params = {
                        
        'BfieldIncoh.frequency_separation': [(0.0, 1.0, 0.1,'kHz'), 'ramsey_contrast'],
        #'Bfield2.frequency_separation': [(0.0, 1.0, 0.1,'kHz'), 'ramsey_contrast'],
        'Ramsey.second_pulse_phase': [(0, 360., 30, 'deg') ,'ramsey_phase_scan'],
        'Ramsey.ramsey_time': [(0, 1.0, 0.05, 'ms') ,'ramsey'],

        }

    show_params= ['Ramsey.ramsey_time',
                  'Ramsey.detuning',
                  'Ramsey.amplitude_729',
                  'Ramsey.channel_729',
                  'Ramsey.dynamic_decoupling_enable',

                  'Ramsey.first_pulse_line',
                  'Ramsey.first_pulse_sideband',
                  'Ramsey.first_pulse_duration',

                  'Ramsey.second_pulse_line',
                  'Ramsey.second_pulse_sideband',
                  'Ramsey.second_pulse_duration',
                  'Ramsey.second_pulse_phase',

                  'DynamicDecoupling.dd_line_selection',
                  'DynamicDecoupling.dd_sideband',
                  'DynamicDecoupling.dd_channel_729',
                  'DynamicDecoupling.dd_repetitions',
                  'DynamicDecoupling.dd_pi_time',
                  'DynamicDecoupling.dd_amplitude_729',

                  'Rotation.rotation_enable',
                  'Rotation.drive_frequency',
                  'Rotation.end_hold',
                  'Rotation.frequency_ramp_time',
                  'Rotation.middle_hold',
                  'Rotation.ramp_down_time',
                  'Rotation.start_hold',
                  'Rotation.start_phase',
                  'Rotation.voltage_pp',

                  'Bfield2.bfield_enable',
                  'Bfield2.center_frequency',
                  'Bfield2.phase1',
                  'Bfield2.phase2',
                  'Bfield2.frequency_separation',
                  'Bfield2.voltage_pp',
                  'Bfield2.first_only',
                  'Bfield2.on_time',
                  'Bfield2.on_before',

                  'BfieldIncoh.bfield_enable',
                  'BfieldIncoh.center_frequency',
                  'BfieldIncoh.n_points',
                  'BfieldIncoh.frequency_separation',
                  'BfieldIncoh.voltage_std',
                  'BfieldIncoh.tot_time',
                  'BfieldIncoh.n_exp',
                  'BfieldIncoh.on_before',
                  'BfieldIncoh.first_only',

                  'ACStarkShift.amplitude729',
                  'ACStarkShift.channel729',
                  'ACStarkShift.frequency729',
                  'ACStarkShift.line_selection',
                  'ACStarkShift.acstark_enable',

                  'EmptySequence.empty_sequence_duration',
                  'StateReadout.repeat_each_measurement',
                      ]

    
    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.DynamicDecoupling_stark import DynamicDecoupling_stark
        from subsequences.EmptySequence import EmptySequence
        print "beginning sequence"
        
        
        r = self.parameters.Ramsey   
        rot = self.parameters.Rotation
        bf = self.parameters.Bfield
        bf2 = self.parameters.Bfield2
        bfi = self.parameters.BfieldIncoh
        ac = self.parameters.ACStarkShift
        dd = self.parameters.DynamicDecoupling
        initial_freq_729 = self.calc_freq_from_array(r.first_pulse_line, r.first_pulse_sideband)
        final_freq_729 = self.calc_freq_from_array(r.second_pulse_line, r.second_pulse_sideband)
        ac_stark_freq_729 = self.calc_freq_from_array(ac.line_selection) + ac.frequency729

        # adding the Ramsey detuning
        initial_freq_729 += self.parameters.Ramsey.detuning
        final_freq_729 += self.parameters.Ramsey.detuning

        ampl_off = U(-63.0, 'dBm')
        fad = U(6, 'us')

        if bfi.bfield_enable:
          # for an incoherent signal, this starts a long sequence that covers all n experiments.
          # luckily the awg ignores pulses while it's running a sequence, so only the first matters
          dur = U(50, 'us')
          self.addTTL('awg_off',self.end,dur)
        
        # building the sequence
        self.addSequence(StatePreparation)     
        self.addSequence(EmptySequence)
        self.addDDS(ac.channel729, self.end, fad, ac_stark_freq_729, ampl_off)       
        
        if bf2.bfield_enable:
          #for a coherent field it's the same every time.
          dur = U(50,'us')
          self.addTTL('awg_off',self.end,dur)
          self.addSequence(EmptySequence,{"EmptySequence.empty_sequence_duration":bf2.on_before})

        self.addSequence(RabiExcitation, { "Excitation729.frequency729": initial_freq_729,
                                           "Excitation729.duration729": r.first_pulse_duration,
                                           "Excitation729.amplitude729": r.amplitude_729,
                                           "Excitation729.phase729": U(0, 'deg'),
                                           "Excitation729.channel729":r.channel_729,
                                           "Excitation729.rabi_change_DDS":True
                                          })

        if not r.dynamic_decoupling_enable:
          now = self.end
          if (bfi.bfield_enable or bf2.bfield_enable) and ac.acstark_enable:
            self.addDDS(ac.channel729,now,r.ramsey_time,ac_stark_freq_729,ac.amplitude729)

        # we need the free evolution time to be actually ramseytime/2 for each arm of the echo in this particular
        # case, so we need to account for the pi time.

        extra = r.dynamic_decoupling_enable * dd.dd_repetitions * dd.dd_pi_time['ms']
        self.addSequence(DynamicDecoupling_stark,  {"DynamicDecoupling.dd_duration" : r.ramsey_time + U(extra,'ms')})
        
        self.addSequence(RabiExcitation, { "Excitation729.frequency729": final_freq_729,
                                           "Excitation729.duration729": r.second_pulse_duration,
                                           "Excitation729.amplitude729": r.amplitude_729,
                                           "Excitation729.phase729": r.second_pulse_phase,
                                           "Excitation729.channel729":r.channel_729,
                                           "Excitation729.rabi_change_DDS":False
                                          })

        self.addSequence(StateReadout,{'StateReadout.repeat_each_measurement':bfi.n_exp})
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      pd = parameters_dict
      bf2 = pd.Bfield2
      bfi = pd.BfieldIncoh
      sr = pd.StateReadout
      sp = pd.StatePreparation
      r = pd.Ramsey


      ## add AC magnetic field if necessary 

      if bf2.bfield_enable:
        print 'setting coherent b field'
        awg_bfield = cxn.keysight_33600a
        start_hold = U(0,'ms')
        on_time = bf2.on_time
        end_hold = U(0,'ms')
        phases = [bf2.phase1['deg'],bf2.phase2['deg']]
        center_freq = bf2.center_frequency
        freq_sep = bf2.frequency_separation
        voltage_pp = bf2.voltage_pp

        awg_bfield.program_b_field_2freq(phases, center_freq['kHz'], freq_sep['kHz'], start_hold['ms'],on_time['us'],end_hold['ms'],voltage_pp['V'],True)

      if bfi.bfield_enable:
        'setting incoherent b field'
        awg_bfield = cxn.keysight_33600a

        #user set parameters
        center_freq = bfi.center_frequency
        freq_sep = bfi.frequency_separation
        std = bfi.voltage_std
        n_points = bfi.n_points
        n_exp = bfi.n_exp
        tot_time = m.ceil(bfi.tot_time['ms']*(60.0/1000.0))/(60.0/1000.0) # could take from parameters, but that's hard as it's written now.

        print 'total time is ', tot_time 

        awg_bfield.program_b_field_incoh(center_freq['kHz'],freq_sep['kHz'],std['V'],tot_time,n_exp,n_points,True)


    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
      pass
      # pd = parameters_dict
      # bfi = pd.BfieldIncoh
      # bf2 = pd.Bfield2
      # sr = pd.StateReadout
      # sp = pd.StatePreparation
      # r = pd.Ramsey

      # if bf2.bfield_enable:
      #   print 'setting coherent b field'
      #   awg_bfield = cxn.keysight_33600a
      #   start_hold = U(0,'ms')
      #   on_time = bf2.on_time
      #   end_hold = U(0,'ms')
      #   phases = [bf2.phase1['deg'],bf2.phase2['deg']]
      #   center_freq = bf2.center_frequency
      #   freq_sep = bf2.frequency_separation
      #   voltage_pp = bf2.voltage_pp

      #   awg_bfield.program_b_field_2freq(phases, center_freq['kHz'], freq_sep['kHz'], start_hold['ms'],on_time['us'],end_hold['ms'],voltage_pp['V'],True)

      # if bfi.bfield_enable:
      #   'setting incoherent b field'
      #   awg_bfield = cxn.keysight_33600a

      #   #user set parameters
      #   center_freq = bfi.center_frequency
      #   freq_sep = bfi.frequency_separation
      #   std = bfi.voltage_std
      #   n_points = bfi.n_points
      #   n_exp = bfi.n_exp
      #   tot_time = m.ceil(bfi.tot_time['ms']*(60.0/1000.0))/(60.0/1000.0) # could take from parameters, but that's hard as it's written now.

      #   print 'total time is ', tot_time 

      #   awg_bfield.program_b_field_incoh(center_freq['kHz'],freq_sep['kHz'],std['V'],tot_time,n_exp,n_points,True)

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
      ## if bfield on make sure it's off.
      bf2 = parameters_dict.Bfield2
      bfi = parameters_dict.BfieldIncoh
      if bf2.bfield_enable:
        awg_bfield = cxn.keysight_33600a
        awg_bfield.set_state(1,0)  
      if bfi.bfield_enable:
        awg_bfield = cxn.keysight_33600a
        awg_bfield.set_state(1,0)  
        

