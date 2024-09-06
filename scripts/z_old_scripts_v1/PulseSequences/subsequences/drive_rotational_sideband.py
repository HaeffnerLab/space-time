from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from OpticalPumping import optical_pumping
from SidebandCoolingContinuous import sideband_cooling_continuous
from treedict import TreeDict

class drive_rotational_sideband_after_heating(pulse_sequence):
    
    required_parameters = [
                           ('RotationalPumping','rotational_pumping_cycles'),
                           ('RotationalPumping','rotational_pumping_optical_pumping_duration'),
                           ('RotationalPumping','rotational_pumping_amplitude_866'),
                           ('RotationalPumping','rotational_pumping_amplitude_854'),
                           ('RotationalPumping','rotational_pumping_amplitude_729'),
                           ('RotationalPumping','rotational_pumping_frequency_854'),
                           ('RotationalPumping', 'rotational_pumping_frequency_866'),
                           ('RotationalPumping', 'rotational_pumping_frequency_729'),
                           ('RotationalPumping', 'channel_729'),
                           ('RotationalPumping','rotational_pumping_continuous_duration'),                        
                           ]
    
    required_subsequences = [sideband_cooling_continuous, optical_pumping]
    replaced_parameters = {
                           sideband_cooling_continuous:[
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_duration'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_frequency_854'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_frequency_729'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_frequency_866'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_amplitude_854'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_amplitude_729'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_amplitude_866'),
                                                        ('SidebandCoolingContinuous','sideband_cooling_continuous_channel_729'),
                                                        ],

                           optical_pumping:[
                                            ('OpticalPumping','optical_pumping_continuous'),
                                            ('OpticalPumpingContinuous','optical_pumping_continuous_duration')
                                            ]
                           }
    
    def sequence(self):
        
        rp = self.parameters.RotationalPumping
  
        cooling = sideband_cooling_continuous
        cooling_replace = {
                           'SidebandCoolingContinuous.sideband_cooling_continuous_duration':self.parameters.RotationalPumping.rotational_pumping_continuous_duration,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_frequency_854':rp.rotational_pumping_frequency_854,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_frequency_729':rp.rotational_pumping_frequency_729,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_frequency_866':rp.rotational_pumping_frequency_866,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_amplitude_854':rp.rotational_pumping_amplitude_854,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_amplitude_729':rp.rotational_pumping_amplitude_729,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_amplitude_866':rp.rotational_pumping_amplitude_866,
                           'SidebandCoolingContinuous.sideband_cooling_continuous_channel_729':rp.channel_729,
                           }
            
        optical_pump_replace = {
                                #'OpticalPumping.optical_pumping_continuous':True,
                                #'OpticalPumpingContinuous.optical_pumping_continuous_duration':sc.sideband_cooling_optical_pumping_duration,
                                }

        for i in range(int(rp.rotational_pumping_cycles)):
            #each cycle, increment the 729 duration
            self.addSequence(cooling, TreeDict.fromdict(cooling_replace))

        self.addSequence(optical_pumping, TreeDict.fromdict(optical_pump_replace))           
