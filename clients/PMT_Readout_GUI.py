from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks

class PMT_GUI(QtGui.QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(PMT_GUI, self).__init__(parent)
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
       # laser_room = self.makeLaserRoomWidget(reactor, cxn)
       # laser_control = self.makeControlWidget(reactor, cxn)
        histogram = self.make_histogram_widget(reactor, cxn)
#       drift_tracker = self.make_drift_tracker_widget(reactor, cxn)
        centralWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout() 
#      from common.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
  #      script_scanner = script_scanner_gui(reactor, cxn)
  #      script_scanner.show()

        self.tabWidget = QtGui.QTabWidget()
       # self.tabWidget.addTab(laser_room,'&Laser Room')
        #self.tabWidget.addTab(laser_control,'&Control')
#       self.tabWidget.addTab(translationStageWidget,'&Translation Stages')
        self.tabWidget.addTab(histogram, '&Readout Histogram')
#        self.tabWidget.addTab(drift_tracker, '&SD Drift Tracker')
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    
    def make_histogram_widget(self, reactor, cxn):
        histograms_tab = QtGui.QTabWidget()
        from common.clients.readout_histogram import readout_histogram
        pmt_readout = readout_histogram(reactor, cxn)
        histograms_tab.addTab(pmt_readout, "PMT")
        return histograms_tab
   
    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import common.clients.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    pmtGUI = PMT_GUI(reactor, clipboard)
    pmtGUI.setWindowTitle('PMT Readout')
    pmtGUI.show()
    reactor.run()
