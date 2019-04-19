from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from RepumpD import repump_d
from DopplerCooling import doppler_cooling
from treedict import TreeDict

class excite_with_397(pulse_sequence):
    
    required_parameters = [
                           ('Spectroscopy_397','calibration_channel_397'),
                           ('Spectroscopy_397','power_397'),
                           ('Spectroscopy_397','readout_duration'),
                           ('Spectroscopy_397','frequency_397'),

                           ('Spectroscopy_397','power_866'),
                           ('Spectroscopy_397','frequency_866'),
                           
                           ('StatePreparation','channel_397_linear'),
                           ('StatePreparation','channel_397_sigma')
                           ]
    required_subsequences = [doppler_cooling]
    replaced_parameters = {doppler_cooling:[
                                            ('DopplerCooling','doppler_cooling_duration'),
                                            ('DopplerCooling','doppler_cooling_amplitude_397'),
                                            ('DopplerCooling','doppler_cooling_frequency_397'),
                                            ('DopplerCooling','doppler_cooling_amplitude_866'),
                                            ('DopplerCooling','doppler_cooling_frequency_866'),

                                            ('StatePreparation','channel_397_linear')
                                            ]
                           }
    
    def sequence(self):
        spec_time = self.parameters.Spectroscopy_397.readout_duration
        spec_power = self.parameters.Spectroscopy_397.power_397
        spec_freq = self.parameters.Spectroscopy_397.frequency_397
        power_866 = self.parameters.Spectroscopy_397.power_866
        freq_866 = self.parameters.Spectroscopy_397.frequency_866
        
        channel = self.parameters.Spectroscopy_397.calibration_channel_397
        if channel == 'linear':
            calib_channel = self.parameters.StatePreparation.channel_397_linear
        elif channel == 'sigma':
            calib_channel = self.parameters.StatePreparation.channel_397_sigma
            
        
        print spec_freq
        #add the sequence
        #self.addSequence(repump_d)
        
        #self.end = self.start + spec_time
        replacement = TreeDict.fromdict({
                                            'DopplerCooling.doppler_cooling_duration':spec_time,
                                            'DopplerCooling.doppler_cooling_amplitude_397':spec_power,
                                            'DopplerCooling.doppler_cooling_frequency_397':spec_freq, #divide by two because sending to a double pass AOM 
                                            'DopplerCooling.doppler_cooling_amplitude_866':power_866,
                                            'DopplerCooling.doppler_cooling_frequency_866':freq_866,
                                            'StatePreparation.channel_397_linear':calib_channel
                                        })
        
        self.addSequence(doppler_cooling, replacement)
        self.addTTL('ReadoutCount', self.start, spec_time)

