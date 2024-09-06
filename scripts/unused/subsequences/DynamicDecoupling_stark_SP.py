from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit

class DynamicDecoupling_stark_SP(pulse_sequence):
    
    def sequence(self):
        
        dd = self.parameters.DynamicDecoupling
        bfi = self.parameters.BfieldIncoh
        bf2 = self.parameters.Bfield2
        ac = self.parameters.ACStarkShift
        r = self.parameters.Ramsey
        ampl_off = WithUnit(-63.0, 'dBm')
        frequency_advance_duration = WithUnit(6, 'us')
        self.end = self.start + dd.dd_duration

        dd_echo_frequency = self.calc_freq_from_array(dd.dd_line_selection, dd.dd_sideband)+r.detuning
        ac_stark_freq_729 = self.calc_freq_from_array(ac.line_selection) + ac.frequency729
            
        if dd.dd_repititions != 0:
            echo_centers = [(i-0.5)*dd.dd_duration/(dd.dd_repetitions) for i in range(1,int(dd.dd_repetitions+1))] #CPMG sequence
            self.addDDS(dd.dd_channel_729, self.start, frequency_advance_duration, dd_echo_frequency, ampl_off)
        
        if r.dynamic_decoupling_enable:
            dur = echo_centers[0]-0.5*dd.dd_pi_time
            ## First Ramsey section
            ## if bfield is on:
                ## turn on AC stark shift beam
                ## turn on TTL that controls the switch to let through the Marconi 
                ## turn on TTL that controls the switch to let through the AWG modulation
                    ## we reuse AWG_off for this since the AWG doesn't care if it gets more burst signals while it's running.
            if (bfi.bfield_enable or bf2.bfield_enable) and ac.acstark_enable:
                self.addTTL('awg_on',self.start,dur)
                self.addTTL('awg_off',self.start,dur)
                self.addDDS(ac.channel729, self.start, dur, ac_stark_freq_729, ac.amplitude729)

            for i in range(0,int(dd.dd_repetitions)):
                # echo_phase = (((-1)**(i+1))*(45)) + 45  #XY phase configuration
                # print echo_phase
                echo_phase = 0
                self.addDDS(dd.dd_channel_729, self.start + echo_centers[i] - 0.5*dd.dd_pi_time, dd.dd_pi_time, dd_echo_frequency, dd.dd_amplitude_729, WithUnit(echo_phase,'deg'))

                ## Other Ramsey sections
                ## if bfield is on:
                    ## turn on AC stark shift beam
                    ## turn on TTOL that controls the switch to let through the Marconi
                    ## if not first_only:
                        ## turn on TTL that controls the switch to let through the AWG modulation.
                if i < dd.dd_repetitions - 1:
                    dur = echo_centers[i+1] - echo_centers[i] - dd.dd_pi_time
                else: 
                    dur = dd.dd_duration - echo_centers[i] - 0.5*dd.dd_pi_time

                if (bfi.bfield_enable or bf2.bfield_enable) and ac.acstark_enable:
                    self.addTTL('awg_on',self.start + echo_centers[i] + 0.5*dd.dd_pi_time, dur)
                    self.addDDS(ac.channel729, self.start + echo_centers[i] + 0.5*dd.dd_pi_time, dur, ac_stark_freq_729, ac.amplitude729)
                    if ((bfi.bfield_enable and not bfi.first_only) or (bf2.bfield_enable and not bf2.first_only)):
                        self.addTTL('awg_off',self.start + echo_centers[i] + 0.5*dd.dd_pi_time, dur)    
                    
        


