from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class Ramsey(pulse_sequence):
    
    #name = 'Ramsey'

    scannable_params = {
                        
        'Ramsey.ramsey_time': [(0, 1.0, 0.05, 'ms') ,'ramsey'],
        'Ramsey.second_pulse_phase': [(0, 360., 30, 'deg') ,'ramsey_phase_scan'],
        'Bfield2.frequency_separation': [(0.0, 1.0, 0.1,'kHz'), 'sigma_ell']

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
                  # 'DynamicDecoupling.dd_duration',
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

                  'Bfield.bfield_enable',
                  'Bfield.end_hold',
                  'Bfield.frequency',
                  'Bfield.on_time',
                  'Bfield.phase',
                  'Bfield.start_hold',
                  'Bfield.voltage_pp',
                  'Bfield.offset',

                  'Bfield2.bfield_enable',
                  'Bfield2.center_frequency',
                  'Bfield2.phase1',
                  'Bfield2.phase2',
                  'Bfield2.frequency_separation',
                  'Bfield2.voltage_pp',

                  'ACStarkShift.amplitude729',
                  'ACStarkShift.channel729',
                  'ACStarkShift.frequency729',
                  'ACStarkShift.line_selection',
                  'ACStarkShift.acstark_enable',

                  'EmptySequence.empty_sequence_duration',
                      ]

    
    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.DynamicDecoupling import DynamicDecoupling
        from subsequences.EmptySequence import EmptySequence
        
        
        r = self.parameters.Ramsey   
        rot = self.parameters.Rotation
        bf = self.parameters.Bfield
        bf2 = self.parameters.Bfield2
        ac = self.parameters.ACStarkShift
        initial_freq_729 = self.calc_freq_from_array(r.first_pulse_line, r.first_pulse_sideband)
        final_freq_729 = self.calc_freq_from_array(r.second_pulse_line, r.second_pulse_sideband)
        ac_stark_freq_729 = self.calc_freq_from_array(ac.line_selection) + ac.frequency729

        # adding the Ramsey detuning
        initial_freq_729 += self.parameters.Ramsey.detuning
        final_freq_729 += self.parameters.Ramsey.detuning

        ampl_off = U(-63.0, 'dBm')
        fad = U(6, 'us')
        
        # building the sequence
        self.addSequence(StatePreparation)     
        self.addSequence(EmptySequence)
        self.addDDS(ac.channel729, self.end, fad, ac_stark_freq_729, ampl_off)       

        ###ttl for turning on b field during ramsey with a function generator switch
        if bf.bfield_enable or bf2.bfield_enable:
          dur = U(50, 'us')
          #ttl_dur = r.ramsey_time-r.first_pulse_duration/2-r.second_pulse_duration/2.0 + awg_wait_time
          self.addTTL('awg_off',self.end,dur)
          self.addSequence(EmptySequence,{'EmptySequence.empty_sequence_duration':U(1,'ms')})
        
        ####for use with switching circuit to switch AWG to ground when not in use
        #awg_wait_time = U(0,'ms')
        #self.addTTL('awg_off',self.start+rot.start_hold+rot.frequency_ramp_time+rot.ramp_down_time+awg_wait_time/2,awg_wait_time+r.ramsey_time+r.first_pulse_duration+r.second_pulse_duration)
        #self.addSequence(EmptySequence,{"EmptySequence.empty_sequence_duration":awg_wait_time})

        self.addSequence(RabiExcitation, { "Excitation_729.frequency729": initial_freq_729,
                                           "Excitation_729.duration729": r.first_pulse_duration,
                                           "Excitation_729.amplitude729": r.amplitude_729,
                                           "Excitation_729.phase729": U(0, 'deg'),
                                           "Excitation_729.channel729":r.channel_729,
                                           "Excitation_729.rabi_change_DDS":True
                                          })



        if not r.dynamic_decoupling_enable and ac.acstark_enable:
          self.addDDS(ac.channel729, self.end, r.ramsey_time, ac_stark_freq_729, ac.amplitude729, U(0,'deg'))

        self.addSequence(DynamicDecoupling,  {"DynamicDecoupling.dd_duration" : r.ramsey_time})
        
        self.addSequence(RabiExcitation, { "Excitation_729.frequency729": final_freq_729,
                                           "Excitation_729.duration729": r.second_pulse_duration,
                                           "Excitation_729.amplitude729": r.amplitude_729,
                                           "Excitation_729.phase729": r.second_pulse_phase,
                                           "Excitation_729.channel729":r.channel_729,
                                           "Excitation_729.rabi_change_DDS":False
                                          })

        self.addSequence(StateReadout)
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      rot = parameters_dict.Rotation
      bf = parameters_dict.Bfield 
      bf2 = parameters_dict.Bfield2

      ## add rotation if necessary
      if rot.rotation_enable:
        awg_rotation = cxn.keysight_33500b
        
        frequency_ramp_time = rot.frequency_ramp_time
        start_hold = rot.start_hold
        ramp_down_time = rot.ramp_down_time
        start_phase = rot.start_phase
        middle_hold = rot.middle_hold
        end_hold = rot.end_hold
        voltage_pp = rot.voltage_pp
        drive_frequency = rot.drive_frequency
        
        awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation_sin_spin')


      ## add AC magnetic field if necessary 
      
      if bf.bfield_enable:
        awg_bfield = cxn.keysight_33600a
        start_hold = bf.start_hold
        on_time = bf.on_time
        end_hold = bf.end_hold
        voltage_pp = bf.voltage_pp
        offset = bf.offset
        phase = bf.phase
        frequency = bf.frequency

        awg_bfield.program_b_field(phase['deg'],frequency['kHz'],start_hold['ms'],on_time['us'],end_hold['ms'],voltage_pp['V'],offset['V'])

      if bf2.bfield_enable:
          print 'setting b field'
          awg_bfield = cxn.keysight_33600a
          start_hold = bf.start_hold
          on_time = bf.on_time
          end_hold = bf.end_hold
          phases = [bf2.phase1['deg'],bf2.phase2['deg']]
          center_freq = bf2.center_frequency
          freq_sep = bf2.frequency_separation
          voltage_pp = bf2.voltage_pp

          awg_bfield.program_b_field_2freq(phases, center_freq['kHz'], freq_sep['kHz'], start_hold['ms'],on_time['us'],end_hold['ms'],voltage_pp['V'])

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        bf2 = parameters_dict.Bfield2
        bf = parameters_dict.Bfield 
        #print "Running in loop Rabi_floping"
        if bf2.bfield_enable:
          print 'setting b field'
          awg_bfield = cxn.keysight_33600a
          start_hold = bf.start_hold
          on_time = bf.on_time
          end_hold = bf.end_hold
          phases = [bf2.phase1['deg'],bf2.phase2['deg']]
          center_freq = bf2.center_frequency
          freq_sep = bf2.frequency_separation
          voltage_pp = bf2.voltage_pp

          awg_bfield.program_b_field_2freq(phases, center_freq['kHz'], freq_sep['kHz'], start_hold['ms'],on_time['us'],end_hold['ms'],voltage_pp['V'])
    
    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
      ## if rotating set back to pinning parameters
      rot = parameters_dict.Rotation
      rcw = parameters_dict.RotationCW
      bf = parameters_dict.Bfield 
      bf2 = parameters_dict.Bfield2
      if rot.rotation_enable:
        old_freq = rcw.drive_frequency['kHz']
        old_phase = rcw.start_phase['deg']
        old_amp = rcw.voltage_pp['V']
        cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase)
      if bf.bfield_enable:
        awg_bfield = cxn.keysight_33600a
        awg_bfield.set_state(1,0) 
      if bf2.bfield_enable:
        awg_bfield = cxn.keysight_33600a
        awg_bfield.set_state(1,0)    
        

