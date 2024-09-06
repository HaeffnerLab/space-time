from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class OpticalPumping(pulse_sequence):
    
    '''
    Optical pumping using a frequency selective transition  
    '''


    def sequence(self):
        op = self.parameters.OpticalPumping
        opc = self.parameters.OpticalPumpingContinuous
        opp = self.parameters.OpticalPumpingPulsed 
        ops = self.parameters.OpticalPumping397Sigma
        sp = self.parameters.StatePreparation
        freq_729 = op.optical_pumping_frequency_729  # This is basically a dummy parameter that will get replaced by higher-level sequences calling this one
        if op.optical_pumping_type == 'continuous':
            continuous = True
        elif op.optical_pumping_type == 'pulsed':
            continuous = False
        else:
            raise Exception ('Incorrect optical pumping type {0}'.format(op.optical_pumping_type))
        if op.optical_pumping_type == 'continuous':
            duration_854 = opc.optical_pumping_continuous_duration + opc.optical_pumping_continuous_repump_additional
            duration_866 = opc.optical_pumping_continuous_duration + 2 * opc.optical_pumping_continuous_repump_additional
            if op.match_866_frequency_to_doppler:
                freq866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
            else:
                freq866 = op.optical_pumping_frequency_866
            ampl866 = op.optical_pumping_amplitude_866
            freq854 = op.optical_pumping_frequency_854
            ampl854 = op.optical_pumping_amplitude_854
            self.end = self.start + duration_866
            
            self.addDDS(sp.channel_729, self.start, opc.optical_pumping_continuous_duration, freq_729, op.optical_pumping_amplitude_729)
            #self.addTTL('854TTL',self.start, duration_854)
            self.addDDS('854DP', self.start, duration_854, freq854, ampl854)
            self.addDDS('866DP', self.start, duration_866, freq866, ampl866)
        elif op.optical_pumping_type == 'pulsed':
            cycles = int(opp.optical_pumping_pulsed_cycles)
            cycle_duration = opp.optical_pumping_pulsed_duration_729 + opp.optical_pumping_pulsed_duration_repumps + opp.optical_pumping_pulsed_duration_additional_866 + 2 * opp.optical_pumping_pulsed_duration_between_pulses
            cycles_start = [self.start + cycle_duration * i for i in range(cycles)]
            self.end = self.start + cycles * cycle_duration
            ampl729 = op.optical_pumping_amplitude_729
            if op.match_866_frequency_to_doppler:
                freq866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
            else:
                freq866 = op.optical_pumping_frequency_866
            ampl866 = op.optical_pumping_amplitude_866
            freq854 = op.optical_pumping_frequency_854
            ampl854 = op.optical_pumping_amplitude_854
            for start in cycles_start:
                start_repumps = start + opp.optical_pumping_pulsed_duration_729 + opp.optical_pumping_pulsed_duration_between_pulses
                duration_866 =  opp.optical_pumping_pulsed_duration_repumps + opp.optical_pumping_pulsed_duration_additional_866
                self.addDDS(sp.channel_729, start, opp.optical_pumping_pulsed_duration_729 , freq_729 , ampl729)
                #self.addTTL('854TTL',start_repumps, opp.optical_pumping_pulsed_duration_repumps)
                self.addDDS('854DP', start_repumps, opp.optical_pumping_pulsed_duration_repumps, freq854, ampl854)
                self.addDDS('866DP', start_repumps, duration_866, freq866 , ampl866)
        elif op.optical_pumping_type == '397sigma':
            duration_866 = ops.optical_pumping_397sigma_duration + ops.optical_pumping_397sigma_additional
            freq397 = ops.optical_pumping_397sigma_frequency_397
            amp397 = ops.optical_pumping_397sigma_amplitude_397
            if op.match_866_frequency_to_doppler:
                freq866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
            else:
                freq866 = ops.optical_pumping_397sigma_frequency_866
            amp866 = ops.optical_pumping_397sigma_amplitude_866
            self.end = self.start + duration_866
            self.addDDS(ops.channel_397_sigma, self.start, ops.optical_pumping_397sigma_duration, freq397, amp397)
            self.addDDS('866', self.start, duration_866, freq866, amp866)
            
        else:
            raise Exception ('Incorrect optical pumping type {}'.format(op.optical_pumping_type))  
