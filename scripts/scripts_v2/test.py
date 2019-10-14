from common.devel.bum.sequences.pulse_sequence import pulse_sequence
from labrad.units import WithUnit as U
from treedict import TreeDict

class test(pulse_sequence):
	scannable_params = {

						}

	show_params= [
				]

	def sequence(self):
		from StatePreparation import StatePreparation
		from subsequences.StateReadout import StateReadout
		self.end = U(10., 'us')
		self.addSequence(StatePreparation)
		self.addSequence(StateReadout)

	@classmethod
	def run_initial(cls,cxn, parameters_dict):
		pass
	
	@classmethod
	def run_in_loop(cls,cxn, parameters_dict, data, x):
		pass
	
	@classmethod
	def run_finally(cls,cxn, parameters_dict, data, x):
		pass