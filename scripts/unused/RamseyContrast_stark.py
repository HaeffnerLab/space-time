import numpy as np
import math as m
from common.abstractdevices.script_scanner2.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey_stark import Ramsey_stark

class contrast(Ramsey_stark):
	scannable_params = {'Ramsey.second_pulse_phase': [(0, 360., 30, 'deg') ,'ramsey_phase_scan']}
	@classmethod
	def run_finally(cls, cxn, parameters_dict, data, data_x):

		if len(data_x)==1:
			final =  data.sum(1)[0]
		else:	
			data_y = data.sum(1)
			fit_params = cls.sin_fit(data_x, data_y, return_all_params = True)
			final = 2.*fit_params[0]
		return final

class RamseyContrast_stark(pulse_sequence):

	scannable_params = {'BfieldIncoh.frequency_separation': [(0., 1., .1, 'kHz'), 'ramsey_contrast']}

	sequence = contrast