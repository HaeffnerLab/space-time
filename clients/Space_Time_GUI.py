from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks

class SPACETIME_GUI(QtGui.QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(SPACETIME_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect_labrad()

    @inlineCallbacks
    def connect_labrad(self):
        from common.clients.connection import connection
        cxn = connection()
        yield cxn.connect()
        self.create_layout(cxn)
    
    def create_layout(self, cxn):
        laser_room = self.makeLaserRoomWidget(reactor, cxn)
        laser_control = self.makeControlWidget(reactor, cxn)
       # histogram = self.make_histogram_widget(reactor, cxn)
#       drift_tracker = self.make_drift_tracker_widget(reactor, cxn)
        centralWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout() 
#      from common.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
  #      script_scanner = script_scanner_gui(reactor, cxn)
  #      script_scanner.show()

        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.addTab(laser_room,'&Laser Room')
        self.tabWidget.addTab(laser_control,'&Control')
#       self.tabWidget.addTab(translationStageWidget,'&Translation Stages')
       # self.tabWidget.addTab(histogram, '&Readout Histogram')
#        self.tabWidget.addTab(drift_tracker, '&SD Drift Tracker')
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def makeLaserRoomWidget(self, reactor, cxn):
        widget = QtGui.QWidget()
 
        from common.clients.CAVITY_CONTROL import cavityWidget
        from common.clients.multiplexer.MULTIPLEXER_CONTROL import multiplexerWidget
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(cavityWidget(reactor),             0,0)
        gridLayout.addWidget(multiplexerWidget(reactor),        0,1)

        widget.setLayout(gridLayout)
        return widget
    
    def make_drift_tracker_widget(self, reactor, cxn):
        from common.clients.drift_tracker.drift_tracker import drift_tracker
        widget = drift_tracker(reactor, cxn = cxn, clipboard = self.clipboard)
        return widget
    
    def make_histogram_widget(self, reactor, cxn):
        histograms_tab = QtGui.QTabWidget()
        from common.clients.readout_histogram import readout_histogram
        pmt_readout = readout_histogram(reactor, cxn)
        histograms_tab.addTab(pmt_readout, "PMT")
        return histograms_tab
    
    def makeControlWidget(self, reactor, cxn):
        widget = QtGui.QWidget()

        from common.clients.PMT_CONTROL import pmtWidget
#	from cct.clients.PMT_CONTROL_SLAVE import pmtWidget
        from common.clients.SWITCH_CONTROL import switchWidget
        from common.clients.DDS_CONTROL import DDS_CONTROL
        from common.clients.LINETRIGGER_CONTROL import linetriggerWidget
        from common.clients.DAC_CONTROL import DAC_Control
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(switchWidget(reactor, cxn),        0,4,1,1)
        gridLayout.addWidget(pmtWidget(reactor),                0,3,1,1)
        gridLayout.addWidget(linetriggerWidget(reactor, cxn),   1,3,1,1)
        gridLayout.addWidget(DDS_CONTROL(reactor, cxn),         2,3,4,3)
        gridLayout.addWidget(DAC_Control(reactor),         0,0,7,3)
        widget.setLayout(gridLayout)
        return widget

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import common.clients.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    spacetimeGUI = SPACETIME_GUI(reactor, clipboard)
    spacetimeGUI.setWindowTitle('Space-Time GUI')
    spacetimeGUI.show()
    reactor.run()
