from pylab import *
import labrad
import numpy as np
from twisted.internet.defer import inlineCallbacks

class plotwikidata():
    
#     @inlineCallbacks
#     def get_data(self,datadir,datafile):
#         self.cxn = yield labrad.connect()
#         self.dv = yield self.cxn.data_vault
#         yield self.dv.cd ['',datadir]
#         yield self.dv.open(datafile)
#         self.data = yield np.array(self.dv.get())
#         
    def get_plot(self,data):
        self.data = data
        x = self.data[:,0]
        y = self.data[:,1]
        self.wikiplot = plot(x,y)
        return self.wikiplot 

