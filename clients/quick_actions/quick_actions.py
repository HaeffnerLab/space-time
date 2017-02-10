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
        self.use_second_397 = False

        self.second_397_DC_box = QtGui.QCheckBox('Second 397 DC')
        self.second_397_SD_box = QtGui.QCheckBox('Second 397 SD')
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
        layout.addWidget(self.second_397_DC_box, 3, 0)
        layout.addWidget(self.second_397_SD_box, 3, 1)
    
    	self.setLayout(layout)

        self.connect()   
        
        self.initialize_check_boxes()        
    
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
        self.second_397_DC_box.stateChanged.connect(self.include_second_397_DC)   
        self.second_397_SD_box.stateChanged.connect(self.include_second_397_SD)   
        
    @inlineCallbacks
    def initialize_check_boxes(self):
        pv = yield self.cxn.get_server('ParameterVault')
        DC_state = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        SD_state = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield self.second_397_DC_box.setChecked(DC_state)   
        yield self.second_397_SD_box.setChecked(SD_state)             
    
    @inlineCallbacks
    def loading(self):
        
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = self.WithUnit(-5.0, 'dBm')
        ampl397Extra = self.WithUnit(-7.0, 'dBm')
        ampl866 = self.WithUnit(-5.0, 'dBm')
        freq397 = self.WithUnit(190.0, 'MHz')
        freq397Extra = self.WithUnit(193.0, 'MHz')
        freq866 = self.WithUnit(80.0, 'MHz')
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)
        yield pulser.frequency('397Extra', freq397Extra)
        yield pulser.amplitude('397Extra', ampl397Extra)

        return
    
    @inlineCallbacks
    def on_to_state(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude('397DP')
        ampl397Extra = yield pulser.amplitude('397Extra')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency('397DP')
        freq397Extra = yield pulser.frequency('397Extra')
        freq866 = yield pulser.frequency('866DP')
        use_second_397_SD = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield pv.set_parameter('StateReadout','state_readout_amplitude_397',ampl397)
        yield pv.set_parameter('StateReadout','state_readout_amplitude_866',ampl866)
        yield pv.set_parameter('StateReadout','state_readout_frequency_397',freq397)
        yield pv.set_parameter('StateReadout','state_readout_frequency_866',freq866)
        if use_second_397_SD:
            yield pv.set_parameter('StateReadout','state_readout_amplitude_397Extra',ampl397Extra)
            yield pv.set_parameter('StateReadout','state_readout_frequency_397Extra',freq397Extra)
    
    @inlineCallbacks
    def on_to_dc(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pulser.amplitude('397DP')
        ampl397Extra = yield pulser.amplitude('397Extra')
        ampl866 = yield pulser.amplitude('866DP')
        freq397 = yield pulser.frequency('397DP')
        freq397Extra = yield pulser.frequency('397Extra')
        freq866 = yield pulser.frequency('866DP')
        use_second_397_DC = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397',ampl397)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397Extra',ampl397Extra)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_866',ampl866)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397',freq397)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397Extra',freq397Extra)
        yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_866',freq866)
        if use_second_397_DC:
            yield pv.set_parameter('DopplerCooling','doppler_cooling_amplitude_397Extra',ampl397Extra)
            yield pv.set_parameter('DopplerCooling','doppler_cooling_frequency_397Extra',freq397Extra)


        
    @inlineCallbacks
    def on_from_dc(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397'))
        ampl397Extra = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_397Extra'))
        ampl866 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_amplitude_866'))
        freq397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_397'))
        freq397Extra = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_397Extra'))
        freq866 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_frequency_866'))
        doppler_cooling_with_second_397 = yield pv.get_parameter(('DopplerCooling','doppler_cooling_include_second_397'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)
        if doppler_cooling_with_second_397:
            yield pulser.frequency('397Extra', freq397Extra)
            yield pulser.amplitude('397Extra', ampl397Extra)
    
    @inlineCallbacks
    def on_from_state(self):
        pv = yield self.cxn.get_server('ParameterVault')
        pulser = yield self.cxn.get_server('Pulser')
        ampl397 = yield pv.get_parameter(('StateReadout','state_readout_amplitude_397'))
        ampl397Extra = yield pv.get_parameter(('StateReadout','state_readout_amplitude_397Extra'))
        ampl866 = yield pv.get_parameter(('StateReadout','state_readout_amplitude_866'))
        freq397 = yield pv.get_parameter(('StateReadout','state_readout_frequency_397'))
        freq397Extra = yield pv.get_parameter(('StateReadout','state_readout_frequency_397Extra'))
        freq866 = yield pv.get_parameter(('StateReadout','state_readout_frequency_866'))
        state_readout_with_second_397 = yield pv.get_parameter(('StateReadout','state_readout_include_second_397'))
        yield pulser.frequency('866DP', freq866)
        yield pulser.amplitude('866DP', ampl866)
        yield pulser.frequency('397DP', freq397)
        yield pulser.amplitude('397DP', ampl397)
        if state_readout_with_second_397:
            yield pulser.frequency('397Extra', freq397Extra)
            yield pulser.amplitude('397Extra', ampl397Extra)
        
    @inlineCallbacks
    def include_second_397_DC(self, event):
        pv = yield self.cxn.get_server('ParameterVault')
        self.use_second_397_DC = yield self.second_397_DC_box.isChecked()
        yield pv.set_parameter('DopplerCooling','doppler_cooling_include_second_397', self.use_second_397_DC)
        
    @inlineCallbacks
    def include_second_397_SD(self, event):
        pv = yield self.cxn.get_server('ParameterVault')
        self.use_second_397_SD = yield self.second_397_SD_box.isChecked()
        yield pv.set_parameter('StateReadout','state_readout_include_second_397', self.use_second_397_SD)
    
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
