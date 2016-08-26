from PyQt4 import QtGui, uic
import os
from common.clients.connection import connection
from twisted.internet.defer import inlineCallbacks


class actions_widget(QtGui.QWidget):
    def __init__(self,reactor,cxn = None, parent=None):
        super(actions_widget, self).__init__(parent)
        self.reactor = reactor
        self.cxn = cxn
        QtGui.QDialog.__init__(self)

        self.loading_button = QtGui.QPushButton('Loading')
	self.fromdc_button = QtGui.QPushButton('From Doppler Cooling')
	self.fromstate_button = QtGui.QPushButton('From State Detection')
	self.todc_button = QtGui.QPushButton('To Doppler Cooling')
	self.tostate_button = QtGui.QPushButton('To State Detection')
        #widget_ui.__init__(self)

	#self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)

	layout = QtGui.QGridLayout()
	layout.addWidget(self.loading_button, 0, 0)
	layout.addWidget(self.fromdc_button, 1, 0)
	layout.addWidget(self.todc_button, 1, 1)
	layout.addWidget(self.fromstate_button, 2, 0)
	layout.addWidget(self.tostate_button, 2, 1)

	self.setLayout(layout)

        self.connect()
    
    @inlineCallbacks
    def connect(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            self.connect_layout()
        except Exception, e:
            print e
            self.setDisabled(True)
    
    def connect_layout(self):
        self.loading_button.pressed.connect(self.loading)
        self.fromdc_button.pressed.connect(self.on_from_dc)
        self.fromstate_button.pressed.connect(self.on_from_state)
        self.todc_button.pressed.connect(self.on_to_dc)
        self.tostate_button.pressed.connect(self.on_to_state)
    
    @inlineCallbacks
    def loading(self):
        
	pulser = yield self.cxn.get_server('Pulser')

	ampl397 = self.WithUnit(-5.0, 'dBm')
        ampl866 = self.WithUnit(-5.0, 'dBm')
        freq397 = self.WithUnit(190.0, 'MHz')
        freq866 = self.WithUnit(80.0, 'MHz')
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)

        return
    
    @inlineCallbacks
    def on_to_state(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude('397DP')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency('397DP')
        freq866 = yield pulser.frequency('866DP')
        yield pv.set_parameter('StateReadout','state_readout_amplitude_397',ampl397)
        yield pv.set_parameter('StateReadout','state_readout_amplitude_866',ampl866)
        yield pv.set_parameter('StateReadout','state_readout_frequency_397',freq397)
        yield pv.set_parameter('StateReadout','state_readout_frequency_866',freq866)
    
    @inlineCallbacks
    def on_to_dc(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude('397DP')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency('397DP')
        freq866 = yield pulser.frequency('866DP')
        yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397',ampl397)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_866',ampl866)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397',freq397)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_866',freq866)
        
    @inlineCallbacks
    def on_from_dc(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397'))
        ampl866 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_866'))
        freq397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_397'))
        freq866 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_866'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)
    
    @inlineCallbacks
    def on_from_state(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pv.get_parameter(('StateReadout','state_readout_amplitude_397'))
        ampl866 = yield pv.get_parameter(('StateReadout','state_readout_amplitude_866'))
        freq397 = yield pv.get_parameter(('StateReadout','state_readout_frequency_397'))
        freq866 = yield pv.get_parameter(('StateReadout','state_readout_frequency_866'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)
    
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
    
    def closeEvent(self, x):
        self.reactor.stop()  
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    electrodes = actions_widget(reactor)
    electrodes.show()
    reactor.run()
