from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.experiments.Experiments729.rabi_flop_scannable import rabi_flopping_scannable as rf
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.scriptLibrary import dvParameters
from labrad.units import WithUnit
from treedict import TreeDict
import numpy as np
import labrad
import time

class scan_micromotion(experiment):

    name = 'ScanMicromotion'
    required_parameters = [('MicromotionCalibration', 'multipole_scan'),
                           ('MicromotionCalibration', 'multipole_to_calibrate'),
                           ('MicromotionCalibration', 'relative_fields'),
                           ('MicromotionCalibration', 'carrier_time'),
                           ('MicromotionCalibration', 'sideband_time'),
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(rf.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        #parameters.remove(('SidebandCooling','stark_shift'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.drift_tracker = cxn.sd_tracker
        self.rabi_flop = self.make_experiment(rf)
        self.rabi_flop.initialize(cxn, context, ident)
        self.save_context = cxn.context()
        self.dv = cxn.data_vault
        self.dac_server = cxn.dac_server
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        
    def run(self, cxn, context):
        
        dv_args = {'output_size': 3, #self.rabi_flop.excite.output_size,
                   'experiment_name': self.name,
                   'window_name': 'other',
                   'dataset_name': 'det_scan'
                   }
        scan_methods.setup_data_vault(cxn, self.save_context, dv_args)
        
        scan_param = self.parameters.MicromotionCalibration.multipole_scan
        start = scan_param[0]['Vmm']
        stop = scan_param[1]['Vmm']
        steps = scan_param[2]
       
        carrier_time = self.parameters.MicromotionCalibration.carrier_time
        sideband_time = self.parameters.MicromotionCalibration.sideband_time

        #self.scan = range(100)

        mv = self.dac_server.get_multipole_values()
        time.sleep(1)

        # make dictionary out of tupel list
        self.mv_dict = {}
        [self.mv_dict.update({n:v}) for n,v in mv]

        self.scanned_multipole = self.parameters.MicromotionCalibration.multipole_to_calibrate
        self.curr_value_multipole = self.mv_dict[self.scanned_multipole]
        
        relative = self.parameters.MicromotionCalibration.relative_fields
        if relative:
            self.scan = np.linspace(start+self.curr_value_multipole, stop+self.curr_value_multipole, steps)
        else:
            self.scan = np.linspace(start, stop, steps)
        
        
        self.mv_dict[self.scanned_multipole] = self.scan[0]
        print self.scan[0]

        self.dac_server.set_multipole_values(self.mv_dict.items()) 
        time.sleep(2)
        
        
        for i, multipole_value in enumerate(self.scan):

            self.mv_dict[self.scanned_multipole] = multipole_value
            print multipole_value

            self.dac_server.set_multipole_values(self.mv_dict.items())
            time.sleep(2)

            should_stop = self.pause_or_stop()
            if should_stop: break

            replace = TreeDict.fromdict({
                                     'RabiFlopping.sideband_selection':[0, 0, 0, 0],
                                     'RabiFlopping_Sit.sit_on_excitation':carrier_time
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation_carr = self.rabi_flop.run(cxn, context)
            if excitation_carr is None: break 

            replace = TreeDict.fromdict({
                                     'RabiFlopping.sideband_selection':[0, 0, 0, +1],
          'RabiFlopping_Sit.sit_on_excitation':sideband_time
                                    })
            self.rabi_flop.set_parameters(replace)
            excitation_1st = self.rabi_flop.run(cxn, context)
            if excitation_1st is None: break 
            
            
            replace = TreeDict.fromdict({
                                     'RabiFlopping.sideband_selection':[0, 0, 0, +2],
          'RabiFlopping_Sit.sit_on_excitation':sideband_time
                                    })

            self.rabi_flop.set_parameters(replace)
            excitation_2nd = self.rabi_flop.run(cxn, context)
            if excitation_2nd is None: break 

                        
            submission = [multipole_value]
            submission.extend([excitation_carr, excitation_1st, excitation_2nd])
            
            self.dv.add(submission, context = self.save_context)
            self.update_progress(i)

    def finalize(self, cxn, context):
        
        self.mv_dict[self.scanned_multipole] = self.curr_value_multipole
        print self.curr_value_multipole
        self.dac_server.set_multipole_values(self.mv_dict.items()) 
    
        self.save_parameters(self.dv, cxn, self.cxnlab, self.save_context)
        self.rabi_flop.finalize(cxn, context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)     

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_micromotion(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
