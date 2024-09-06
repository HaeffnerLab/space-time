import numpy as np
from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Excitation729 import Excitation729

class rsb(Excitation729):

    scannable_params = {'Excitation729.frequency729': [(-30., 30., 2., 'kHz'), 'temp_rsb',True]}

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        if parameter_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()

        data = data.sum(1)
        # peak_guess =  cls.peak_guess(data_x, data)[0]
        # print "@@@@@@@@@@@@@@", peak_guess
        #print data_x
        #print data
        fit_params = cls.gaussian_fit(data_x, data, return_all_params = True)
        if fit_params == None:
            fit_params = (0,0)
        print "red sideband"
        print "############## fit params: ", fit_params
        print "Amplitude: ", fit_params[1]
        return fit_params[1]

class bsb(Excitation729):

    scannable_params = {'Excitation729.frequency729': [(-30., 30., 2., 'kHz'), 'temp_bsb',True]}

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        if parameter_dict.StatePreparation.rotation_enable:
            cxn.keysight_33500b.rotation_run_finally()

        data = data.sum(1)
        # peak_guess =  cls.peak_guess(data_x, data)[0]
        # print "@@@@@@@@@@@@@@", peak_guess
        #print data_x
        #print data
        fit_params = cls.gaussian_fit(data_x, data, return_all_params = True)
        if fit_params == None:
            fit_params = (0,0)
        print "blue sideband"
        print "############## fit params: ", fit_params
        print "Amplitude: ", fit_params[1]
        return fit_params[1]

class Temperature(pulse_sequence):
    
    sequence = [(rsb, {'Excitation729.invert_sb': -1.0}), 
                (bsb, {'Excitation729.invert_sb': 1.0})]

    @classmethod
    def run_finally(cls, cxn, parameter_dict, amp, seq_name):
        try:
            R = 1.0 * amp[0] / amp[1]
            return 1.0*R/(1.0-1.0*R)
        except:
            pass

class Heating_Rate(pulse_sequence):

    scannable_params = {'EmptySequence.empty_sequence_duration': [(0., 5., .5, 'ms'), 'nbar']}

    sequence = Temperature