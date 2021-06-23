import numpy as np
import math as m
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey_stark_SP import Ramsey_stark_SP

## An Experiment solely for doing the intermittent sensing experiment. 
## For every frequency separation it takes two points at phi0 and phi0 + 180deg. This is for data verification.
## Plots the 2 of them on different graphs.

class pop0(Ramsey_stark_SP):
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if len(data_x)==1:
            final =  data.sum(1)[0]
        else:   
            data_y = data.sum(1)
            final = min(data_y)
        return final

class pop1(Ramsey_stark_SP):
    @classmethod
    def run_finally(cls, cxn, parameters_dict, data, data_x):
        if len(data_x)==1:
            final =  data.sum(1)[0]
        else:   
            data_y = data.sum(1)
            final = max(data_y)
        return final


class IntermittentSensingPoint(pulse_sequence):

    sequence = [(pop0, {'Ramsey.phase_offset': U(0, 'deg')}), 
                (pop1, {'Ramsey.phase_offset': U(90, 'deg')})]

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        try:
            return data[1] - data[0]
        except:
            pass 

class IntermittentSensingPoint1(pulse_sequence):

    sequence = [(pop0, {'Ramsey.phase_offset': U(0, 'deg')})]

    @classmethod
    def run_finally(cls, cxn, parameter_dict, data, data_x):
        return data

class IntermittentSensing(pulse_sequence):

    scannable_params = {'BfieldIncoh.frequency_separation': [(0., 1., .1, 'kHz'), 'ramsey_contrast']}
    sequence = IntermittentSensingPoint


class IntermittentSensing_1pt(pulse_sequence):

    scannable_params = {'BfieldIncoh.frequency_separation': [(0., 1., .1, 'kHz'), 'ramsey_contrast']}
    sequence = IntermittentSensingPoint1


