from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
import time


class point(pulse_sequence):
    
    
    scannable_params = {
        'MicromotionCalibration.point' : [(1., 1., 1., ''),'current'],
              }

    show_params= ['MicromotionCalibration.multipole_to_calibrate',
                  'MicromotionCalibration.carrier_time',
                  'MicromotionCalibration.sideband_time',
                  'MicromotionCalibration.amplitude729',
                  'MicromotionCalibration.line_selection',
                  'MicromotionCalibration.channel729',
                  'RFModulation.enable',
                  'RFModulation.turn_on_before',
                        ] 
                  
   
    def sequence(self):
        
        from subsequences.StatePreparation import StatePreparation
        from subsequences.RabiExcitation import RabiExcitation
        from subsequences.StateReadout import StateReadout
        from subsequences.TurnOffAll import TurnOffAll
        from subsequences.RFModulation import RFModulation
           
                
        # building the sequence
        # needs a 10 micro sec for some reason
        self.end = U(10., 'us')

        mc = self.parameters.MicromotionCalibration   
        e729 = self.parameters.Excitation729

        #self.addSequence(TurnOffAll)           
        self.addSequence(StatePreparation, {'StatePreparation.rotation_enable': False})   # Never rotate for this experiment
        self.addSequence(RabiExcitation,{'Excitation729.frequency729': self.calc_freq_from_array(mc.line_selection, e729.sideband_selection),
                                         'Excitation729.amplitude729': mc.amplitude729,
                                         'Excitation729.channel729': mc.channel729
                                         })
        time_start_readout = self.end # This is for RF modulation
        self.addSequence(StateReadout)

        #Add RF modulation TTL pulse if applicable
        if self.parameters.RFModulation.enable:
            RFModulation(self, time_start_readout)

class carrier(point):

    pass

class micromotion_sideband_1(point):

    pass

class micromotion_sideband_2(point):

    pass

class Scan3points(pulse_sequence):


    sequence = [(carrier,                {'Excitation729.sideband_selection': [0,0,0,0,0],
                                          'Excitation729.duration729': 'MicromotionCalibration.carrier_time'}), 
                (micromotion_sideband_1, {'Excitation729.sideband_selection': [0,0,0,1,0],
                                          'Excitation729.duration729': 'MicromotionCalibration.sideband_time'}),
                (micromotion_sideband_2, {'Excitation729.sideband_selection': [0,0,0,2,0],
                                          'Excitation729.duration729': 'MicromotionCalibration.sideband_time'})
                ]


    @classmethod
    def run_initial(cls,cxn, parameters_dict):
        dac = cxn.dac_server
        global multipoles_initial
        multipoles_initial = dac.get_multipole_values() 

        
    @classmethod
    def run_in_loop(cls,cxn, parameters_dict, data, x):
        dac = cxn.dac_server
        multipoles_current = dac.get_multipole_values()
        multipoles_new = multipoles_current
        multipole_to_calibrate = parameters_dict.MicromotionCalibration.multipole_to_calibrate
        scan_value = parameters_dict.MicromotionCalibration.multipole_value
        print "scan value = "
        print scan_value

        for i in range(len(multipoles_current)):
            if multipoles_current[i][0] == multipole_to_calibrate:
                multipoles_new[i] = (multipole_to_calibrate, scan_value['Vmm'])

        if dac.get_multipole_values() != multipoles_new:
            dac.set_multipole_values(multipoles_new)
            print "new multipole values:"
            print dac.get_multipole_values()
            time.sleep(2)
        
    
    @classmethod
    def run_finally(cls,cxn, parameters_dict, data, x):
        dac = cxn.dac_server
        #dac.set_multipole_values(multipoles_initial)
        print data
        carrier = data[0][0][0][0]
        sideband1 = data[1][0][0][0]
        sideband2 = data[2][0][0][0]
        return carrier, sideband1, sideband2    



class ScanMicromotion(pulse_sequence):

    scannable_params = {
        'MicromotionCalibration.multipole_value' : [(-.02, .02, .002, 'Vmm'),'Efields'],
              }

    sequence = Scan3points