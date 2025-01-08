from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
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
        scctt = self.parameters.SidebandCoolingContTwoTone
        scseq = self.parameters.SequentialSBCooling
        
        Nsb = 1
        if sc.sequential_sbc_enable:
            Nsb += int(scseq.additional_stages) 

        amp866 = sc.sideband_cooling_amplitude_866
        
        if sc.match_866_frequency_to_doppler:
            freq866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
        else:
            freq866 = sc.sideband_cooling_frequency_866       

        amps854 = [sc.sideband_cooling_amplitude_854,
                scseq.stage2_amplitude_854,
                scseq.stage3_amplitude_854,
                scseq.stage4_amplitude_854,
                scseq.stage5_amplitude_854,
                scseq.stage6_amplitude_854]

        freq854 = sc.sideband_cooling_frequency_854

        amps729 = [sc.sideband_cooling_amplitude_729,
                scseq.stage2_amplitude_729,
                scseq.stage3_amplitude_729,
                scseq.stage4_amplitude_729,
                scseq.stage5_amplitude_729,
                scseq.stage6_amplitude_729]

        channels729 = [sc.channel_729,
                scseq.stage2_channel_729,
                scseq.stage3_channel_729,
                scseq.stage4_channel_729,
                scseq.stage5_channel_729,
                scseq.stage6_channel_729]
        duration_arr = [scc.sideband_cooling_continuous_duration,
                        scc.sideband_cooling_continuous_duration_stage2,
                        scc.sideband_cooling_continuous_duration_stage3,
                        scc.sideband_cooling_continuous_duration_stage4,
                        scc.sideband_cooling_continuous_duration_stage5,
                        scc.sideband_cooling_continuous_duration_stage6
        ]
        Nc_arr = [int(scc.sideband_cooling_continuous_cycles),
                  int(scc.sideband_cooling_continuous_cycles_stage2),
                  int(scc.sideband_cooling_continuous_cycles_stage3),
                  int(scc.sideband_cooling_continuous_cycles_stage4),
                  int(scc.sideband_cooling_continuous_cycles_stage5),
                  int(scc.sideband_cooling_continuous_cycles_stage6) 
        ]
        stark_shift_arr = [sc.stark_shift,
            scseq.stage2_stark_shift,
            scseq.stage3_stark_shift,
            scseq.stage4_stark_shift,
            scseq.stage5_stark_shift,
            scseq.stage6_stark_shift
        ]
        freq729_base = sc.line_selection

        sidebands = [sc.sideband_selection,
                    scseq.stage2_sideband_selection,
                    scseq.stage3_sideband_selection,
                    scseq.stage4_sideband_selection,
                    scseq.stage5_sideband_selection,
                    scseq.stage6_sideband_selection]
        freq729_op = self.calc_freq_from_array(self.parameters.OpticalPumping.line_selection)

        sbc_op_duration = sc.sideband_cooling_optical_pumping_duration
        
        def add_sbc_sequence(dur, f729, index):
            self.addSequence(OpticalPumping,
                {"OpticalPumping.optical_pumping_type":sc.sideband_cooling_type,
                "OpticalPumpingContinuous.optical_pumping_continuous_duration":dur,
                "OpticalPumping.optical_pumping_frequency_854":freq854,
                "OpticalPumping.optical_pumping_amplitude_854":amps854[j],
                "OpticalPumping.optical_pumping_frequency_729":f729,
                "OpticalPumping.optical_pumping_amplitude_729":amps729[j],
                "OpticalPumping.optical_pumping_frequency_866":freq866,
                "OpticalPumping.optical_pumping_amplitude_866":amp866,
                "OpticalPumping.match_866_frequency_to_doppler":sc.match_866_frequency_to_doppler,
                "OpticalPumping.channel_729":channels729[index]})

        def add_sbc_op_sequence():
            self.addSequence(OpticalPumping,{'OpticalPumping.optical_pumping_frequency_729':freq729_op,
                                            'OpticalPumpingContinuous.optical_pumping_continuous_duration':sbc_op_duration})

        if sc.sideband_cooling_type == 'continuous':
            duration = scc.sideband_cooling_continuous_duration
            Nc = int(scc.sideband_cooling_continuous_cycles) 

            if scseq.interleave:
                for i in range(Nc):
                    duration += sc.sideband_cooling_duration_729_increment_per_cycle 
                    for j in range(Nsb):
                        freq729 = self.calc_freq_from_array(sc.line_selection, sidebands[j])
                        freq729 += sc.stark_shift
                        add_sbc_sequence(duration, freq729, j)
                        add_sbc_op_sequence()
            else:
                for j in range(Nsb):
                    freq729 = self.calc_freq_from_array(sc.line_selection, sidebands[j])
                    freq729 += stark_shift_arr[j]
                    for i in range(Nc_arr[j]):
                        add_sbc_sequence(duration_arr[j], freq729, j)
                        add_sbc_op_sequence()

                    # for i in range(Nc):
                    #     duration += sc.sideband_cooling_duration_729_increment_per_cycle
                    #     add_sbc_sequence(duration, freq729, j)
                    #     add_sbc_op_sequence()


        elif sc.sideband_cooling_type == 'pulsed':
            duration = scp.sideband_cooling_pulsed_duration_729
            Nc = int(scp.sideband_cooling_pulsed_cycles) 

            if scseq.interleave:
                for i in range(Nc):
                    duration += sc.sideband_cooling_duration_729_increment_per_cycle 
                    for j in range(Nsb):
                        freq729 = self.calc_freq_from_array(sc.line_selection, sidebands[j])
                        freq729 += sc.stark_shift
                        add_sbc_sequence(duration, freq729, j)
                        add_sbc_op_sequence()
            else:
                for j in range(Nsb):
                    freq729 = self.calc_freq_from_array(sc.line_selection, sidebands[j])
                    freq729 += stark_shift_arr[j]
                    for i in range(Nc):
                        duration += sc.sideband_cooling_duration_729_increment_per_cycle
                        add_sbc_sequence(duration, freq729, j)
                        add_sbc_op_sequence()


        elif sc.sideband_cooling_type == 'cont_twotone':
            
            # Continuous "two-tone" sideband cooling
            # Instead of sideband cooling in cycles where optical pumping is necessary in between them, this scheme simultaneously pumps the +-1/2 -> +-1/2 or the +-1/2 -> +-5/2 lines.
            # That way, population is always being driven. Might be more time efficient.
            # Requires an extra DDS channel; currently this is required to be "729horizExtra" or "729vertExtra".
            # Automatically decides which line to drive with the secondary channel based on SidebandCooling.line_selection.
            # Sequential cycles, interleaved or not, are still possible.
            # In all cases, optical pumping only occurs once at the end of sideband cooling. 

            duration = scctt.sideband_cooling_cont_twotone_duration
            Nc = int(scctt.sideband_cooling_cont_twotone_cycles) 

            channels729secondary = [scctt.channel_729_secondary,
                                    scctt.channel_729_secondary,
                                    scctt.channel_729_secondary,
                                    scctt.channel_729_secondary,
                                    scctt.channel_729_secondary] # Hardcoded to all be the same for now since we only have one extra channel. Later, add ability to change.
            lines = [sc.line_selection,
                        scctt.stage2_line,
                        scctt.stage3_line,
                        scctt.stage4_line,
                        scctt.stage5_line]

            def add_sbc_twotone_sequence(dur, index):
                self.addSequence(SBCTwoTonePulse,
                    {"SidebandCoolingContTwoTone.sideband_cooling_cont_twotone_duration": dur,
                     "SidebandCooling.channel_729": channels729[index],
                     "SidebandCoolingContTwoTone.channel_729_secondary": channels729secondary[index],
                     "SidebandCooling.line_selection": lines[index],
                     "SidebandCooling.sideband_selection": sidebands[index], 
                     "SidebandCooling.sideband_cooling_amplitude_729": amps729[index],
                     "SidebandCooling.sideband_cooling_amplitude_854": amps854[index]})

            if scseq.interleave:
                for i in range(Nc):
                    duration += sc.sideband_cooling_duration_729_increment_per_cycle
                    for j in range(Nsb):
                        add_sbc_twotone_sequence(duration, j)
            else:
                for j in range(Nsb):
                    for i in range(Nc):
                        duration += sc.sideband_cooling_duration_729_increment_per_cycle
                        add_sbc_twotone_sequence(duration, j)

            add_sbc_op_sequence()



        else:
            raise Exception ("Incorrect Sideband cooling type {}".format(sc.sideband_cooling_type))



class SBCTwoTonePulse(pulse_sequence):
    # Defined as its own class since the pulse pattern is not quite identical to optical pumping, unlike the other types of SBC, which prevents utilizing OP subsequence for two-tone SBC.
    def sequence(self):
        sc = self.parameters.SidebandCooling
        scctt = self.parameters.SidebandCoolingContTwoTone
        opc = self.parameters.OpticalPumpingContinuous
        
        line1 = sc.line_selection
        if line1 == "S-1/2D-5/2":
            line2 = "S+1/2D+5/2"
        elif line1 == "S+1/2D+5/2":
            line2 = "S-1/2D-5/2"
        elif line1 == "S-1/2D-1/2":
            line2 = "S+1/2D+1/2"
        elif line1 == "S+1/2D+1/2":
            line2 = "S-1/2D-1/2"
        freq729_1 = self.calc_freq_from_array(line1, sc.sideband_selection)
        freq729_1 += sc.stark_shift
        freq729_2 = self.calc_freq_from_array(line2, sc.sideband_selection)
        freq729_2 += sc.stark_shift


        duration_729 = scctt.sideband_cooling_cont_twotone_duration
        duration_854 = duration_729 + opc.optical_pumping_continuous_repump_additional
        duration_866 = duration_729 + 2 * opc.optical_pumping_continuous_repump_additional
        
        if sc.match_866_frequency_to_doppler:
            freq866 = self.parameters.DopplerCooling.doppler_cooling_frequency_866
        else:
            freq866 = sc.sideband_cooling_frequency_866       

        self.end = self.start + duration_866
        self.addDDS(sc.channel_729,              self.start, duration_729, freq729_1, sc.sideband_cooling_amplitude_729)
        self.addDDS(scctt.channel_729_secondary, self.start, duration_729, freq729_2, sc.sideband_cooling_amplitude_729)
        self.addDDS('854DP', self.start, duration_854, sc.sideband_cooling_frequency_854, sc.sideband_cooling_amplitude_854)
        self.addDDS('866DP', self.start, duration_866, freq866,                           sc.sideband_cooling_amplitude_866)

