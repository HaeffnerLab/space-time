from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit
#from OpticalPumpingContinuous import optical_pumping_continuous
#from treedict import TreeDict

class SidebandCooling(pulse_sequence):
    #all cycles of sidband cooling. continuous or pulsed, allows for up to 5 stages (1 + 4 extra under sequential SBC)
    #uses optical pumping sequence
    def sequence(self):
        from OpticalPumping import OpticalPumping
        
        sc = self.parameters.SidebandCooling
        scc = self.parameters.SidebandCoolingContinuous
        scp = self.parameters.SidebandCoolingPulsed
        scseq = self.parameters.SequentialSBCooling
        
        Nc = int(sc.sideband_cooling_cycles) 
        Nsb = 1
        if scseq.enable:
            Nsb += int(scseq.additional_stages) 

        amp866 = sc.sideband_cooling_amplitude_866
        freq866 = sc.sideband_cooling_frequency_866       

        amps854 = [sc.sideband_cooling_amplitude_854,
                scseq.stage2_amplitude_854,
                scseq.stage3_amplitude_854,
                scseq.stage4_amplitude_854,
                scseq.stage5_amplitude_854]

        freq854 = sc.sideband_cooling_frequency_854

        amps729 = [sc.sideband_cooling_amplitude_729,
                scseq.stage2_amplitude_729,
                scseq.stage3_amplitude_729,
                scseq.stage4_amplitude_729,
                scseq.stage5_amplitude_729]

        channels729 = [sc.channel_729,
                scseq.stage2_channel_729,
                scseq.stage3_channel_729,
                scseq.stage4_channel_729,
                scseq.stage5_channel_729]

        freq729_base = sc.line_selection

        sidebands = [sc.sideband_selection,
                    scseq.stage2_sideband_selection,
                    scseq.stage3_sideband_selection,
                    scseq.stage4_sideband_selection,
                    scseq.stage5_sideband_selection]
        freq729_op = self.calc_freq_from_array(self.parameters.OpticalPumping.line_selection)

        sbc_op_duration = sc.sideband_cooling_optical_pumping_duration
        
        if sc.sideband_cooling_type == 'continuous':
            duration = sc.sideband_cooling_continuous_duration

            if scseq.interleave:

                for i in range(Nc):
                    duration += sc.sideband_cooling_duration_729_increment_per_cycle 
                    for j in range(Nsb):
                        freq729 = self.calc_freq_from_array(sc.line_selection,sidebands[j])
                        freq729 += sc.stark_shift
                        #sideband cooling sequence
                        self.addSequence(OpticalPumping,
                            {"OpticalPumping.optical_pumping_type":sc.sideband_cooling_type,
                            "OpticalPumpingContinuous.optical_pumping_continuous_duration":duration,
                            "OpticalPumping.optical_pumping_frequency_854":freq854,
                            "OpticalPumping.optical_pumping_amplitude_854":amps854[j],
                            "OpticalPumping.optical_pumping_frequency_729":freq729,
                            "OpticalPumping.optical_pumping_amplitude_729":amps729[j],
                            "OpticalPumping.optical_pumping_frequency_866":freq866,
                            "OpticalPumping.optical_pumping_amplitude_866":amp866,
                            "StatePreparation.channel_729":channels729[j]})
                        #optical pumping sequence
                        self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729_op,
                                                        'OpticalPumpingContinuous.optical_pumping_continuous_duration':sbc_op_duration})

            else:

                for j in range(Nsb):
                    freq729 = self.calc_freq_from_array(sc.line_selection,sidebands[j])
                    freq729 += sc.stark_shift
                    for i in range(Nc):
                        duration += sc.sideband_cooling_duration_729_increment_per_cycle
                        #sideband cooling sequence
                        self.addSequence(OpticalPumping,
                            {"OpticalPumping.optical_pumping_type":sc.sideband_cooling_type,
                            "OpticalPumpingContinuous.optical_pumping_continuous_duration":duration,
                            "OpticalPumping.optical_pumping_frequency_854":freq854,
                            "OpticalPumping.optical_pumping_amplitude_854":amps854[j],
                            "OpticalPumping.optical_pumping_frequency_729":freq729,
                            "OpticalPumping.optical_pumping_amplitude_729":amps729[j],
                            "OpticalPumping.optical_pumping_requency_866":freq866,
                            "OpticalPumping.optical_pumping_amplitude_866":amp866,
                            "StatePreparation.channel_729":channels729[j]})
                        #optical pumping sequence
                        self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729_op,
                                                        'OpticalPumpingContinuous.optical_pumping_continuous_duration':sbc_op_duration})


        elif sc.sideband_cooling_type == 'pulsed':
            duration = scp.sideband_cooling_pulsed_duration_729

            if scseq.interleave:

                for i in range(Nc):
                    duration += sc.sideband_cooling_duration_729_increment_per_cycle 
                    for j in range(Nsb):
                        freq729 = self.calc_freq_from_array(sc.line_selection,sidebands[j])
                        freq729 += sc.stark_shift
                        #sideband cooling sequence
                        self.addSequence(OpticalPumping,
                            {"OpticalPumping.optical_pumping_type":sc.sideband_cooling_type,
                            "OpticalPumpingPulsed.optical_pumping_pulsed_duration_729":duration,
                            "OpticalPumping.optical_pumping_frequency_854":freq854,
                            "OpticalPumping.optical_pumping_amplitude_854":amps854[j],
                            "OpticalPumping.optical_pumping_frequency_729":freq729,
                            "OpticalPumping.optical_pumping_amplitude_729":amps729[j],
                            "OpticalPumping.optical_pumping_frequency_866":freq866,
                            "OpticalPumping.optical_pumping_amplitude_866":amp866,
                            "StatePreparation.channel_729":channels729[j]})
                        #optical pumping sequence
                        self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729_op,
                                                        'OpticalPumpingContinuous.optical_pumping_continuous_duration':sbc_op_duration})
            else:

                for j in range(Nsb):
                    freq729 = self.calc_freq_from_array(sc.line_selection,sidebands[j])
                    freq729 += sc.stark_shift
                    for i in range(Nc):
                        duration += sc.sideband_cooling_duration_729_increment_per_cycle
                        #sideband cooling sequence
                        self.addSequence(OpticalPumping,
                            {"OpticalPumping.optical_pumping_type":sc.sideband_cooling_type,
                            "OpticalPumpingPulsed.optical_pumping_pulsed_duration_729":duration,
                            "OpticalPumping.optical_pumping_frequency_854":freq854,
                            "OpticalPumping.optical_pumping_amplitude_854":amps854[j],
                            "OpticalPumping.optical_pumping_frequency_729":freq729,
                            "OpticalPumping.optical_pumping_amplitude_729":amps729[j],
                            "OpticalPumping.optical_pumping_frequency_866":freq866,
                            "OpticalPumping.optical_pumping_amplitude_866":amp866,
                            "StatePreparation.channel_729":channels729[j]})
                        #optical pumping sequence
                        self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729_op,
                                                        'OpticalPumpingContinuous.optical_pumping_continuous_duration':sbc_op_duration})

        else:
            raise Exception ("Incorrect Sideband cooling type {}".format(sc.sideband_cooling_type))