from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import numpy as np

class Excitation729(pulse_sequence):
    scannable_params = {
        'DopplerCooling.doppler_cooling_frequency_397':  [(180., 210., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_397':  [(-30., -15., .5, 'dBm'), 'other'],
        'DopplerCooling.doppler_cooling_frequency_866':  [(60., 90., .5, 'MHz'), 'calib_doppler'],
        'DopplerCooling.doppler_cooling_amplitude_866':  [(-20., -6., .5, 'dBm'), 'other'],
        'SidebandCooling.sideband_cooling_amplitude_854': [(-30.,-10., 1., 'dBm'), 'scan_854'],
        'Excitation_729.duration729':  [(0., 200., 10., 'us'), 'rabi'],
        'Excitation_729.frequency729': [(-50., 50., 5., 'kHz'), 'spectrum',True],
        'SidebandCooling.stark_shift': [(-20., 20., 2., 'kHz'), 'other'],
        'EmptySequence.empty_sequence_duration_readout': [(0.,1000.,100.,'us'),'rabi']
              }

    show_params= [
                  'Excitation_729.line_selection',
                  'Excitation_729.amplitude729',
                  'Excitation_729.duration729',
                  'Excitation_729.sideband_selection',
                  'Excitation_729.channel729',
                  'Excitation_729.stark_shift_729',
                  'Rotation.rotation_enable',
                  'Rotation.drive_frequency',
                  'Rotation.end_hold',
                  'Rotation.frequency_ramp_time',
                  'Rotation.middle_hold',
                  'Rotation.ramp_down_time',
                  'Rotation.start_hold',
                  'Rotation.start_phase',
                  'Rotation.voltage_pp',
                  'EmptySequence.empty_sequence_duration',
                  'EmptySequence.empty_sequence_duration_readout'
                  ]


    def sequence(self):

      from subsequences.StatePreparation import StatePreparation
      from subsequences.EmptySequence import EmptySequence
      from subsequences.RabiExcitation import RabiExcitation
      from subsequences.StateReadout import StateReadout

      e = self.parameters.Excitation_729
      es = self.parameters.EmptySequence

        
      ## calculate the scan params
      if e.frequency_selection == "auto":
        freq_729_pos = self.calc_freq_from_array(e.line_selection, [sb*e.invert_sb for sb in e.sideband_selection])
        freq_729 = freq_729_pos + e.stark_shift_729 + e.frequency729
        print "FREQUENCY 729 = {}".format(freq_729)
      elif e.frequency_selection == "manual":
        freq_729 = e.frequency729
      else:
        raise Exception ('Incorrect frequency selection type {0}'.format(e.frequency_selection))

      ## build the sequence
      self.addSequence(StatePreparation)
      self.addSequence(EmptySequence)
      self.addSequence(RabiExcitation,{  'Excitation_729.frequency729': freq_729,
                                         'Excitation_729.rabi_change_DDS': True})
      self.addSequence(EmptySequence,{'EmptySequence.empty_sequence_duration':es.empty_sequence_duration_readout})
      self.addSequence(StateReadout)  
        
    @classmethod
    def run_initial(cls,cxn, parameters_dict):
      r = parameters_dict.Rotation
      e = parameters_dict.Excitation_729

      ## add rotation if necessary
      if r.rotation_enable:
        awg_rotation = cxn.keysight_33500b
        
        frequency_ramp_time = r.frequency_ramp_time
        start_hold = r.start_hold
        ramp_down_time = r.ramp_down_time
        start_phase = r.start_phase
        middle_hold = r.middle_hold
        end_hold = r.end_hold
        voltage_pp = r.voltage_pp
        drive_frequency = r.drive_frequency
        
        awg_rotation.program_awf(start_phase['deg'],start_hold['ms'],frequency_ramp_time['ms'],middle_hold['ms'],ramp_down_time['ms'],end_hold['ms'],voltage_pp['V'],drive_frequency['kHz'],'free_rotation_sin_spin')
      
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
        for order,sideband_frequency in zip([sb*e.invert_sb for sb in e.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency
      else:
        #shift by sideband + carrier (spectrum "0" will be AO center frequency)
        shift += parameters_dict.Carriers[carrier_translation[e.line_selection]]
        for order,sideband_frequency in zip([sb*e.invert_sb for sb in e.sideband_selection], sideband_frequencies):
            shift += order * sideband_frequency

      pv = cxn.parametervault
      pv.set_parameter('Display','shift',shift)

    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        pass

    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
      ## if rotating set back to pinning parameters
      r = parameters_dict.Rotation
      rcw = parameters_dict.RotationCW
      if r.rotation_enable:
        old_freq = rcw.drive_frequency['kHz']
        old_phase = rcw.start_phase['deg']
        old_amp = rcw.voltage_pp['V']
        cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase)   
        
