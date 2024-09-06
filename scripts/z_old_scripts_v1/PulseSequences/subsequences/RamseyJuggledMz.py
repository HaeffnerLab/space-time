from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from RabiExcitation import rabi_excitation, rabi_excitation_no_offset
from EmptySequence import empty_sequence
from treedict import TreeDict
from labrad.units import WithUnit
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm

class ramsey_juggled_mz_excitation(pulse_sequence):
    
    required_parameters = [ 
                          ('Ramsey','ramsey_time'),
                          ('Ramsey','frequency_selection'),
                          ('Ramsey','ramsey_manual_frequency_729'),
                          ('Ramsey','ramsey_line'),

                          ('Ramsey','carrier_frequency'),
                          ('Ramsey','carrier_pi_time'),
                          ('Ramsey','carrier_channel'),
                          ('Ramsey','carrier_power'),

                          ('Ramsey','first_order_frequency'),
                          ('Ramsey','first_order_channel'),
                          ('Ramsey','first_order_pi_time'),
                          ('Ramsey','first_order_power'),

                          ('Ramsey','second_order_frequency'),
                          ('Ramsey','second_order_channel'),
                          ('Ramsey','second_order_pi_time'),
                          ('Ramsey','second_order_power'),

                          ('Ramsey','second_pulse_phase'),
                          ]

    required_subsequences = [rabi_excitation, empty_sequence, rabi_excitation_no_offset]
    replaced_parameters = {
                           rabi_excitation:[('Excitation_729','rabi_excitation_duration'),
                                            ('Excitation_729','rabi_excitation_phase'),
                                            ('Excitation_729', 'channel_729'),
                                            ('Excitation_729','rabi_excitation_frequency'),
                                            ('Excitation_729','rabi_excitation_amplitude')
                                            ],
                           rabi_excitation_no_offset:[('Excitation_729','rabi_excitation_duration'),
                                                      ('Excitation_729','rabi_excitation_phase'),
                                                      ('Excitation_729', 'channel_729'),
                                                      ('Excitation_729','rabi_excitation_frequency'),
                                                      ('Excitation_729','rabi_excitation_amplitude')
                                                      ],
                           empty_sequence:[('EmptySequence','empty_sequence_duration')]
                           }


    def sequence(self):
        awg_wait_time = WithUnit(2,'ms')
        r = self.parameters.Ramsey
        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':awg_wait_time}))
        fad = WithUnit(6, 'us')  #frequency_advance_duration  
        T0 = r.ramsey_time/12. - ((r.carrier_pi_time/2.)+r.first_order_pi_time)/2.
        T1 = r.ramsey_time/6. - (r.first_order_pi_time+r.second_order_pi_time)/2.
        T2 = r.ramsey_time/3. - (r.second_order_pi_time)
        T0p = r.ramsey_time/12. - (r.carrier_pi_time+r.first_order_pi_time)/2.
        Tend = r.ramsey_time/6. - (r.carrier_pi_time+(r.carrier_pi_time/2.))/2.

        # T0 = WithUnit(0,'us')
        if T0['us']<0:
          print "T0 is less than 0"
          raise 
        if T1['us']<0:
          print "T1 is less than 0"
          raise 
        if T2['us']<0:
          print "T2 is less than 0"
          raise 
        if Tend['us']<0:
          print "Tend is less than 0"
          raise 

        print T0,T1,T2

        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.carrier_pi_time/2.,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                             'Excitation_729.channel_729':r.carrier_channel,
                             'Excitation_729.rabi_excitation_frequency':r.carrier_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.carrier_power
                                     }) 
        self.addSequence(rabi_excitation, replace)

        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':T0-fad}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.first_order_pi_time,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                             'Excitation_729.channel_729':r.first_order_channel,
                             'Excitation_729.rabi_excitation_frequency':r.first_order_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.first_order_power
                                     }) 
        self.addSequence(rabi_excitation, replace)


        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':T1-fad}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.second_order_pi_time,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                             'Excitation_729.channel_729':r.second_order_channel,
                             'Excitation_729.rabi_excitation_frequency':r.second_order_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.second_order_power
                                     }) 
        self.addSequence(rabi_excitation, replace)


        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':T2}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.second_order_pi_time,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                             'Excitation_729.channel_729':r.second_order_channel,
                             'Excitation_729.rabi_excitation_frequency':r.second_order_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.second_order_power
                                     }) 
        self.addSequence(rabi_excitation_no_offset, replace)


        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':T1}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.first_order_pi_time,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0, 'deg'),
                             # 'Excitation_729.rabi_excitation_phase':r.second_pulse_phase,
                             'Excitation_729.channel_729':r.first_order_channel,
                             'Excitation_729.rabi_excitation_frequency':r.first_order_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.first_order_power
                                     }) 
        self.addSequence(rabi_excitation_no_offset, replace)


        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':T0p}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.carrier_pi_time,
                             'Excitation_729.rabi_excitation_phase':WithUnit(0,'deg'),
                             'Excitation_729.channel_729':r.carrier_channel,
                             'Excitation_729.rabi_excitation_frequency':r.carrier_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.carrier_power
                             })
        self.addSequence(rabi_excitation_no_offset, replace)


        self.addSequence(empty_sequence, TreeDict.fromdict({'EmptySequence.empty_sequence_duration':Tend}))
        replace = TreeDict.fromdict({
                             'Excitation_729.rabi_excitation_duration':r.carrier_pi_time/2.,
                             'Excitation_729.rabi_excitation_phase':r.second_pulse_phase,
                             'Excitation_729.channel_729':r.carrier_channel,
                             'Excitation_729.rabi_excitation_frequency':r.carrier_frequency,
                             'Excitation_729.rabi_excitation_amplitude':r.carrier_power
                             })
        self.addSequence(rabi_excitation_no_offset, replace)
