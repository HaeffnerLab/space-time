import numpy as np
from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict
from Ramsey import Ramsey

class ramsey_gap(Ramsey):
	scannable_params = {'Ramsey.ramsey_time': [(0, 360., 30, 'deg') ,'ramsey'],}
	@classmethod
	def run_finally(cls, cxn, parameters_dict, data, data_x):
		rot = parameters_dict.Rotation
		rcw = parameters_dict.RotationCW
		if rot.rotation_enable:
			old_freq = rcw.drive_frequency['kHz']
			old_phase = rcw.start_phase['deg']
			old_amp = rcw.voltage_pp['V']
			cxn.keysight_33500b.update_awg(old_freq*1e3,old_amp,old_phase) 

		data_y = data.sum(1)
		fit_params = cls.rot_ramsey_fit(data_x, data_y, return_all_params = True)
		return fit_params[0]

class Diffusion(pulse_sequence):

	scannable_params = {'EmptySequency.empty_sequence_duration': [(0., 8., .1, 'ms'), 'sigma_ell']}

	sequence = ramsey_gap